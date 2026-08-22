from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Lease:
    resource_id: str
    owner_id: str
    lease_token: str
    expires_at: str


class RuntimeControlPlane:
    """Durable coordination primitives for AEC v1.1.

    SQLite is the reference backend. The schema and semantics are intentionally
    backend-neutral so the same contracts can be implemented over D1/Postgres.
    """

    def __init__(self, path: str | Path = "runtime/aec-control.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def _init_schema(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    key TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leases (
                    resource_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    lease_token TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS heartbeats (
                    worker_id TEXT PRIMARY KEY,
                    at TEXT NOT NULL,
                    detail_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS dead_letters (
                    dead_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_chain (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                );
                """
            )

    def reserve_idempotency(self, key: str, job_id: str) -> bool:
        if not key.strip() or not job_id.strip():
            raise ValueError("idempotency key and job_id are required")
        try:
            with self._connect() as db:
                db.execute(
                    "INSERT INTO idempotency_keys(key, job_id, created_at) VALUES(?,?,?)",
                    (key, job_id, _now()),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def acquire_lease(self, resource_id: str, owner_id: str, *, ttl_seconds: int = 120) -> Lease | None:
        if ttl_seconds < 5 or ttl_seconds > 3600:
            raise ValueError("ttl_seconds must be between 5 and 3600")
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)
        token = uuid.uuid4().hex
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM leases WHERE resource_id=?", (resource_id,)).fetchone()
            if row is not None and datetime.fromisoformat(str(row["expires_at"])) > now:
                db.rollback()
                return None
            db.execute(
                """INSERT INTO leases(resource_id, owner_id, lease_token, expires_at, updated_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(resource_id) DO UPDATE SET
                     owner_id=excluded.owner_id,
                     lease_token=excluded.lease_token,
                     expires_at=excluded.expires_at,
                     updated_at=excluded.updated_at""",
                (resource_id, owner_id, token, expires.isoformat(), now.isoformat()),
            )
            db.commit()
        return Lease(resource_id, owner_id, token, expires.isoformat())

    def release_lease(self, lease: Lease) -> bool:
        with self._connect() as db:
            cur = db.execute(
                "DELETE FROM leases WHERE resource_id=? AND owner_id=? AND lease_token=?",
                (lease.resource_id, lease.owner_id, lease.lease_token),
            )
        return cur.rowcount == 1

    def heartbeat(self, worker_id: str, detail: dict[str, Any] | None = None) -> None:
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        with self._connect() as db:
            db.execute(
                """INSERT INTO heartbeats(worker_id, at, detail_json) VALUES(?,?,?)
                   ON CONFLICT(worker_id) DO UPDATE SET at=excluded.at, detail_json=excluded.detail_json""",
                (worker_id, _now(), json.dumps(detail or {}, sort_keys=True, default=str)),
            )

    def stale_workers(self, *, older_than_seconds: int) -> tuple[str, ...]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)
        with self._connect() as db:
            rows = db.execute("SELECT worker_id, at FROM heartbeats").fetchall()
        return tuple(
            str(row["worker_id"])
            for row in rows
            if datetime.fromisoformat(str(row["at"])) < cutoff
        )

    def dead_letter(self, job_id: str, reason: str, payload: dict[str, Any]) -> str:
        dead_id = f"dead_{uuid.uuid4().hex}"
        with self._connect() as db:
            db.execute(
                "INSERT INTO dead_letters(dead_id, job_id, reason, payload_json, created_at) VALUES(?,?,?,?,?)",
                (dead_id, job_id, reason, json.dumps(payload, sort_keys=True, default=str), _now()),
            )
        self.append_audit("runtime", "DEAD_LETTERED", {"dead_id": dead_id, "job_id": job_id, "reason": reason})
        return dead_id

    def append_audit(self, actor: str, event: str, payload: dict[str, Any]) -> str:
        if not actor.strip() or not event.strip():
            raise ValueError("actor and event are required")
        at = _now()
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        with self._connect() as db:
            row = db.execute("SELECT event_hash FROM audit_chain ORDER BY seq DESC LIMIT 1").fetchone()
            prev_hash = str(row["event_hash"]) if row else "GENESIS"
            material = "|".join((prev_hash, at, actor, event, payload_json)).encode("utf-8")
            event_hash = hashlib.sha256(material).hexdigest()
            db.execute(
                "INSERT INTO audit_chain(at, actor, event, payload_json, prev_hash, event_hash) VALUES(?,?,?,?,?,?)",
                (at, actor, event, payload_json, prev_hash, event_hash),
            )
        return event_hash

    def verify_audit_chain(self) -> bool:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM audit_chain ORDER BY seq").fetchall()
        prev = "GENESIS"
        for row in rows:
            if str(row["prev_hash"]) != prev:
                return False
            material = "|".join(
                (prev, str(row["at"]), str(row["actor"]), str(row["event"]), str(row["payload_json"]))
            ).encode("utf-8")
            expected = hashlib.sha256(material).hexdigest()
            if expected != str(row["event_hash"]):
                return False
            prev = expected
        return True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

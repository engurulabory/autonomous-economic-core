from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Protocol


class JobState(str, Enum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    RETRY_WAIT = "RETRY_WAIT"
    HOLD = "HOLD"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


TERMINAL_STATES = {JobState.HOLD, JobState.COMPLETED, JobState.BLOCKED}


@dataclass(frozen=True)
class Job:
    job_id: str
    capability: str
    payload: dict[str, Any]
    state: JobState
    attempts: int
    max_attempts: int
    assigned_worker: str | None
    human_threshold_required: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EvidenceEvent:
    event_id: int
    job_id: str
    at: str
    actor: str
    event: str
    detail: dict[str, Any]


@dataclass(frozen=True)
class WorkerSpec:
    worker_id: str
    capabilities: frozenset[str]
    autonomous: bool = True

    def __post_init__(self) -> None:
        if not self.worker_id.strip():
            raise ValueError("worker_id is required")
        if not self.capabilities:
            raise ValueError("worker must expose at least one capability")


class RuntimeWorker(Protocol):
    spec: WorkerSpec

    def execute(self, job: Job) -> "WorkerOutcome": ...


@dataclass(frozen=True)
class WorkerOutcome:
    next_state: JobState
    evidence: dict[str, Any]
    reason: str

    def __post_init__(self) -> None:
        if self.next_state in {JobState.QUEUED, JobState.ASSIGNED}:
            raise ValueError("worker outcome cannot move backward to queued/assigned")
        if not self.reason.strip():
            raise ValueError("worker outcome reason is required")


class SQLiteJobQueue:
    """Persistent zero-dependency queue + evidence ledger for AEC workers."""

    def __init__(self, path: str | Path = "runtime/aec-worker.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    capability TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL,
                    assigned_worker TEXT,
                    human_threshold_required INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS jobs_state_capability_idx
                    ON jobs(state, capability, created_at);

                CREATE TABLE IF NOT EXISTS job_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event TEXT NOT NULL,
                    detail_json TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
                );
                """
            )

    def enqueue(
        self,
        capability: str,
        payload: dict[str, Any],
        *,
        max_attempts: int = 3,
        human_threshold_required: bool = False,
        job_id: str | None = None,
    ) -> Job:
        if not capability.strip():
            raise ValueError("capability is required")
        if max_attempts < 1 or max_attempts > 20:
            raise ValueError("max_attempts must be between 1 and 20")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dict")

        now = _now()
        resolved_id = job_id or f"job_{uuid.uuid4().hex}"
        initial_state = JobState.HOLD if human_threshold_required else JobState.QUEUED
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO jobs(job_id, capability, payload_json, state, attempts, max_attempts,
                                 assigned_worker, human_threshold_required, created_at, updated_at)
                VALUES(?,?,?,?,0,?,?,?, ?, ?)
                """,
                (
                    resolved_id,
                    capability,
                    json.dumps(payload, sort_keys=True),
                    initial_state.value,
                    max_attempts,
                    None,
                    int(human_threshold_required),
                    now,
                    now,
                ),
            )
            self._record_event_db(
                db,
                resolved_id,
                "runtime",
                "ENQUEUED" if initial_state is JobState.QUEUED else "HUMAN_THRESHOLD_HOLD",
                {"capability": capability},
            )
        return self.get(resolved_id)

    def release_human_threshold(self, job_id: str, *, actor: str, evidence: dict[str, Any]) -> Job:
        job = self.get(job_id)
        if not job.human_threshold_required or job.state is not JobState.HOLD:
            raise ValueError("job is not waiting on a human threshold")
        with self._connect() as db:
            db.execute(
                "UPDATE jobs SET state=?, human_threshold_required=0, updated_at=? WHERE job_id=?",
                (JobState.QUEUED.value, _now(), job_id),
            )
            self._record_event_db(db, job_id, actor, "HUMAN_THRESHOLD_RELEASED", evidence)
        return self.get(job_id)

    def lease_next(self, worker: WorkerSpec) -> Job | None:
        placeholders = ",".join("?" for _ in worker.capabilities)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                f"""
                SELECT * FROM jobs
                WHERE state IN (?,?)
                  AND human_threshold_required=0
                  AND capability IN ({placeholders})
                  AND attempts < max_attempts
                ORDER BY created_at, job_id
                LIMIT 1
                """,
                (JobState.QUEUED.value, JobState.RETRY_WAIT.value, *sorted(worker.capabilities)),
            ).fetchone()
            if row is None:
                db.commit()
                return None
            attempts = int(row["attempts"]) + 1
            now = _now()
            db.execute(
                "UPDATE jobs SET state=?, attempts=?, assigned_worker=?, updated_at=? WHERE job_id=?",
                (JobState.ASSIGNED.value, attempts, worker.worker_id, now, row["job_id"]),
            )
            self._record_event_db(
                db,
                row["job_id"],
                worker.worker_id,
                "ASSIGNED",
                {"attempt": attempts},
            )
            db.commit()
        return self.get(str(row["job_id"]))

    def start(self, job_id: str, worker_id: str) -> Job:
        job = self.get(job_id)
        if job.state is not JobState.ASSIGNED or job.assigned_worker != worker_id:
            raise ValueError("job is not assigned to this worker")
        return self._transition(job_id, JobState.RUNNING, worker_id, "STARTED", {})

    def finish(self, job_id: str, worker_id: str, outcome: WorkerOutcome) -> Job:
        job = self.get(job_id)
        if job.assigned_worker != worker_id or job.state not in {JobState.RUNNING, JobState.VERIFYING}:
            raise ValueError("worker cannot finish this job from current state")

        state = outcome.next_state
        if state is JobState.RETRY_WAIT and job.attempts >= job.max_attempts:
            state = JobState.BLOCKED
            reason = f"retry budget exhausted: {outcome.reason}"
        else:
            reason = outcome.reason

        return self._transition(
            job_id,
            state,
            worker_id,
            "OUTCOME",
            {"reason": reason, "evidence": outcome.evidence},
        )

    def set_verifying(self, job_id: str, actor: str, evidence: dict[str, Any]) -> Job:
        return self._transition(job_id, JobState.VERIFYING, actor, "VERIFYING", evidence)

    def get(self, job_id: str) -> Job:
        with self._connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return _job_from_row(row)

    def events(self, job_id: str) -> tuple[EvidenceEvent, ...]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM job_events WHERE job_id=? ORDER BY event_id", (job_id,)
            ).fetchall()
        return tuple(
            EvidenceEvent(
                event_id=int(row["event_id"]),
                job_id=str(row["job_id"]),
                at=str(row["at"]),
                actor=str(row["actor"]),
                event=str(row["event"]),
                detail=json.loads(str(row["detail_json"])),
            )
            for row in rows
        )

    def counts(self) -> dict[str, int]:
        with self._connect() as db:
            rows = db.execute("SELECT state, COUNT(*) AS n FROM jobs GROUP BY state").fetchall()
        return {str(row["state"]): int(row["n"]) for row in rows}

    def _transition(
        self,
        job_id: str,
        state: JobState,
        actor: str,
        event: str,
        detail: dict[str, Any],
    ) -> Job:
        with self._connect() as db:
            db.execute("UPDATE jobs SET state=?, updated_at=? WHERE job_id=?", (state.value, _now(), job_id))
            self._record_event_db(db, job_id, actor, event, {"state": state.value, **detail})
        return self.get(job_id)

    @staticmethod
    def _record_event_db(
        db: sqlite3.Connection,
        job_id: str,
        actor: str,
        event: str,
        detail: dict[str, Any],
    ) -> None:
        db.execute(
            "INSERT INTO job_events(job_id, at, actor, event, detail_json) VALUES(?,?,?,?,?)",
            (job_id, _now(), actor, event, json.dumps(detail, sort_keys=True, default=str)),
        )


class WorkerRegistry:
    def __init__(self, workers: Iterable[RuntimeWorker]) -> None:
        resolved = tuple(workers)
        ids = [worker.spec.worker_id for worker in resolved]
        if len(ids) != len(set(ids)):
            raise ValueError("worker ids must be unique")
        self._workers = resolved

    @property
    def workers(self) -> tuple[RuntimeWorker, ...]:
        return self._workers

    def capable(self, capability: str) -> tuple[RuntimeWorker, ...]:
        return tuple(worker for worker in self._workers if capability in worker.spec.capabilities)


def run_worker_once(queue: SQLiteJobQueue, worker: RuntimeWorker) -> Job | None:
    """Lease and execute at most one job for a worker.

    Exceptions become bounded retries rather than escaping the runtime.
    """
    job = queue.lease_next(worker.spec)
    if job is None:
        return None
    queue.start(job.job_id, worker.spec.worker_id)
    try:
        outcome = worker.execute(queue.get(job.job_id))
    except Exception as exc:
        outcome = WorkerOutcome(
            next_state=JobState.RETRY_WAIT,
            reason=f"{type(exc).__name__}: {exc}",
            evidence={"exception_type": type(exc).__name__},
        )
    return queue.finish(job.job_id, worker.spec.worker_id, outcome)


def run_registry_cycle(queue: SQLiteJobQueue, registry: WorkerRegistry) -> tuple[Job, ...]:
    completed: list[Job] = []
    for worker in registry.workers:
        result = run_worker_once(queue, worker)
        if result is not None:
            completed.append(result)
    return tuple(completed)


def _job_from_row(row: sqlite3.Row) -> Job:
    return Job(
        job_id=str(row["job_id"]),
        capability=str(row["capability"]),
        payload=json.loads(str(row["payload_json"])),
        state=JobState(str(row["state"])),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        assigned_worker=str(row["assigned_worker"]) if row["assigned_worker"] else None,
        human_threshold_required=bool(row["human_threshold_required"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

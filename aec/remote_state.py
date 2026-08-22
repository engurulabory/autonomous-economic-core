from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


class RemoteStateError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


@dataclass(frozen=True)
class RemoteLease:
    resource_id: str
    owner_id: str
    lease_token: str
    expires_at: str


@dataclass(frozen=True)
class RemoteJob:
    job_id: str
    capability: str
    payload: dict[str, Any]
    state: str
    attempts: int
    max_attempts: int
    assigned_worker: str | None
    human_threshold_required: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class RemoteJobLease:
    job: RemoteJob
    lease_token: str
    lease_expires_at: str


@dataclass(frozen=True)
class RemoteArtifact:
    artifact_id: str
    job_id: str
    media_type: str
    content: bytes
    sha256: str
    bytes: int
    created_at: str


class RemoteStateClient:
    """Authenticated zero-dependency client for AEC Durable State Core™ v1.1."""

    def __init__(self, base_url: str, token: str, timeout_seconds: int = 15) -> None:
        parsed = urlparse(base_url.strip())
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("durable state endpoint must be a credential-free HTTPS origin")
        if parsed.query or parsed.fragment:
            raise ValueError("durable state endpoint must not include query/fragment")
        if not token.strip():
            raise ValueError("durable state token is required")
        if timeout_seconds < 1 or timeout_seconds > 120:
            raise ValueError("timeout_seconds must be between 1 and 120")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health", auth=False)

    def reserve_idempotency(self, key: str, job_id: str) -> bool:
        payload = self._request("POST", "/idempotency/reserve", {"key": key, "job_id": job_id})
        return bool(payload.get("reserved"))

    def heartbeat(self, worker_id: str, detail: dict[str, Any] | None = None) -> None:
        self._request("POST", "/heartbeat", {"worker_id": worker_id, "detail": detail or {}})

    def stale_workers(self, older_than_seconds: int = 900) -> tuple[dict[str, Any], ...]:
        payload = self._request("GET", f"/heartbeats/stale?{urlencode({'older_than_seconds': older_than_seconds})}")
        return tuple(item for item in payload.get("workers", []) if isinstance(item, dict))

    def acquire_lease(self, resource_id: str, owner_id: str, ttl_seconds: int = 120) -> RemoteLease | None:
        payload = self._request(
            "POST", "/lease/acquire",
            {"resource_id": resource_id, "owner_id": owner_id, "ttl_seconds": ttl_seconds},
        )
        if not payload.get("acquired"):
            return None
        return RemoteLease(resource_id, owner_id, str(payload["lease_token"]), str(payload["expires_at"]))

    def release_lease(self, lease: RemoteLease) -> bool:
        payload = self._request(
            "POST", "/lease/release",
            {"resource_id": lease.resource_id, "owner_id": lease.owner_id, "lease_token": lease.lease_token},
        )
        return bool(payload.get("released"))

    def enqueue_job(
        self,
        *,
        job_id: str,
        capability: str,
        payload: dict[str, Any],
        qualification_evidence_id: str,
        idempotency_key: str,
        human_threshold_required: bool = False,
        max_attempts: int = 3,
    ) -> RemoteJob:
        result = self._request(
            "POST", "/jobs/enqueue",
            {
                "job_id": job_id,
                "capability": capability,
                "payload": payload,
                "qualification_state": "QUALIFIED",
                "qualification_evidence_id": qualification_evidence_id,
                "idempotency_key": idempotency_key,
                "human_threshold_required": human_threshold_required,
                "max_attempts": max_attempts,
            },
        )
        return _remote_job(result["job"])

    def lease_job(self, worker_id: str, capabilities: tuple[str, ...] | list[str], ttl_seconds: int = 300) -> RemoteJobLease | None:
        result = self._request(
            "POST", "/jobs/lease",
            {"worker_id": worker_id, "capabilities": list(capabilities), "ttl_seconds": ttl_seconds},
        )
        if not result.get("leased"):
            return None
        return RemoteJobLease(
            job=_remote_job(result["job"]),
            lease_token=str(result["lease_token"]),
            lease_expires_at=str(result["lease_expires_at"]),
        )

    def start_job(self, leased: RemoteJobLease, worker_id: str) -> None:
        self._request(
            "POST", "/jobs/start",
            {"job_id": leased.job.job_id, "worker_id": worker_id, "lease_token": leased.lease_token},
        )

    def set_job_verifying(self, leased: RemoteJobLease, worker_id: str, evidence: dict[str, Any] | None = None) -> None:
        self._request(
            "POST", "/jobs/verifying",
            {
                "job_id": leased.job.job_id,
                "worker_id": worker_id,
                "lease_token": leased.lease_token,
                "evidence": evidence or {},
            },
        )

    def finish_job(
        self,
        leased: RemoteJobLease,
        worker_id: str,
        *,
        outcome_state: str,
        reason: str,
        evidence: dict[str, Any] | None = None,
    ) -> str:
        result = self._request(
            "POST", "/jobs/finish",
            {
                "job_id": leased.job.job_id,
                "worker_id": worker_id,
                "lease_token": leased.lease_token,
                "outcome_state": outcome_state,
                "reason": reason,
                "evidence": evidence or {},
            },
        )
        return str(result["state"])

    def release_human_threshold(
        self,
        job_id: str,
        *,
        actor: str,
        authority_evidence_id: str,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        self._request(
            "POST", "/jobs/human-release",
            {
                "job_id": job_id,
                "actor": actor,
                "authority_evidence_id": authority_evidence_id,
                "evidence": evidence or {},
            },
        )

    def get_job(self, job_id: str) -> tuple[RemoteJob, tuple[dict[str, Any], ...]]:
        result = self._request("GET", f"/jobs/{quote(job_id, safe='')}")
        events = tuple(item for item in result.get("events", []) if isinstance(item, dict))
        return _remote_job(result["job"]), events

    def job_counts(self) -> dict[str, int]:
        result = self._request("GET", "/jobs/counts")
        return {str(key): int(value) for key, value in dict(result.get("counts", {})).items()}

    def put_artifact(self, *, artifact_id: str, job_id: str, media_type: str, content: bytes) -> dict[str, Any]:
        digest = hashlib.sha256(content).hexdigest()
        result = self._request(
            "POST", "/artifacts/put",
            {
                "artifact_id": artifact_id,
                "job_id": job_id,
                "media_type": media_type,
                "content_base64": base64.b64encode(content).decode("ascii"),
                "sha256": digest,
                "bytes": len(content),
            },
        )
        return {**result, "sha256": digest, "bytes": len(content)}

    def put_artifact_file(self, *, artifact_id: str, job_id: str, path: str | Path, media_type: str = "application/octet-stream") -> dict[str, Any]:
        data = Path(path).read_bytes()
        return self.put_artifact(artifact_id=artifact_id, job_id=job_id, media_type=media_type, content=data)

    def get_artifact(self, artifact_id: str) -> RemoteArtifact:
        result = self._request("GET", f"/artifacts/{quote(artifact_id, safe='')}")
        row = result["artifact"]
        content = base64.b64decode(str(row["content_base64"]), validate=True)
        digest = hashlib.sha256(content).hexdigest()
        expected = str(row["sha256"])
        if digest != expected or len(content) != int(row["bytes"]):
            raise RemoteStateError("remote artifact integrity verification failed")
        return RemoteArtifact(
            artifact_id=str(row["artifact_id"]),
            job_id=str(row["job_id"]),
            media_type=str(row["media_type"]),
            content=content,
            sha256=expected,
            bytes=len(content),
            created_at=str(row["created_at"]),
        )

    def watchdog_sweep(self, actor: str = "github-actions-watchdog") -> dict[str, Any]:
        return self._request("POST", "/watchdog/sweep", {"actor": actor})

    def append_audit(self, actor: str, event: str, payload: dict[str, Any]) -> str:
        result = self._request("POST", "/audit/append", {"actor": actor, "event": event, "payload": payload})
        return str(result["event_hash"])

    def verify_audit_chain(self) -> dict[str, Any]:
        return self._request("GET", "/audit/verify")

    def record_cycle(
        self,
        *,
        cycle_id: str,
        started_at: str,
        finished_at: str,
        status: str,
        source_sha: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self._request(
            "POST", "/cycles/record",
            {
                "cycle_id": cycle_id,
                "started_at": started_at,
                "finished_at": finished_at,
                "status": status,
                "source_sha": source_sha,
                "detail": detail or {},
            },
        )

    def recent_cycles(self, limit: int = 24) -> tuple[dict[str, Any], ...]:
        result = self._request("GET", f"/cycles/recent?{urlencode({'limit': limit})}")
        return tuple(item for item in result.get("cycles", []) if isinstance(item, dict))

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None, *, auth: bool = True) -> dict[str, Any]:
        data = None if body is None else json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        headers = {"Accept": "application/json", "User-Agent": "AEC-Durable-State-Client/1.1"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(f"{self.base_url}{path}", data=data, method=method, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310 - validated HTTPS origin
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw[:1000]}
            raise RemoteStateError(
                f"durable state HTTP {exc.code}: {payload.get('error', 'request_failed')}",
                status=exc.code,
                payload=payload if isinstance(payload, dict) else {},
            ) from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RemoteStateError("durable state returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RemoteStateError("durable state response must be an object")
        return payload


def _remote_job(row: Any) -> RemoteJob:
    if not isinstance(row, dict):
        raise RemoteStateError("remote job payload must be an object")
    payload = row.get("payload", {})
    if not isinstance(payload, dict):
        raise RemoteStateError("remote job payload field must be an object")
    return RemoteJob(
        job_id=str(row["job_id"]),
        capability=str(row["capability"]),
        payload=payload,
        state=str(row["state"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        assigned_worker=str(row["assigned_worker"]) if row.get("assigned_worker") else None,
        human_threshold_required=bool(row.get("human_threshold_required")),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )

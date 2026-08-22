from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from aec.remote_state import RemoteJob, RemoteJobLease, RemoteStateClient
from aec.worker_runtime import Job, JobState, RuntimeWorker, WorkerOutcome


@dataclass(frozen=True)
class RemoteRunResult:
    worker_id: str
    job_id: str | None
    state: str
    reason: str
    artifact_id: str | None = None
    chained_job_id: str | None = None


class RemoteWorkerRunner:
    """Execute existing AEC workers against the durable remote queue."""

    def __init__(
        self,
        client: RemoteStateClient,
        workers: Iterable[RuntimeWorker],
        *,
        workspace: str | Path = "runtime/remote-artifacts",
        lease_ttl_seconds: int = 300,
    ) -> None:
        self.client = client
        self.workers = tuple(workers)
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.lease_ttl_seconds = lease_ttl_seconds

    def run_cycle(self, *, max_jobs_per_worker: int = 1) -> tuple[RemoteRunResult, ...]:
        if max_jobs_per_worker < 1 or max_jobs_per_worker > 20:
            raise ValueError("max_jobs_per_worker must be between 1 and 20")
        results: list[RemoteRunResult] = []
        for worker in self.workers:
            self.client.heartbeat(worker.spec.worker_id, {"phase": "ready", "capabilities": sorted(worker.spec.capabilities)})
            processed = False
            for _ in range(max_jobs_per_worker):
                leased = self.client.lease_job(
                    worker.spec.worker_id,
                    tuple(sorted(worker.spec.capabilities)),
                    ttl_seconds=self.lease_ttl_seconds,
                )
                if leased is None:
                    if not processed:
                        results.append(RemoteRunResult(worker.spec.worker_id, None, "IDLE", "no compatible queued job"))
                    break
                processed = True
                results.append(self._execute_leased(worker, leased))
        return tuple(results)

    def _execute_leased(self, worker: RuntimeWorker, leased: RemoteJobLease) -> RemoteRunResult:
        worker_id = worker.spec.worker_id
        job_id = leased.job.job_id
        self.client.start_job(leased, worker_id)
        self.client.heartbeat(worker_id, {"phase": "running", "job_id": job_id})
        try:
            local_job = self._materialize_remote_inputs(leased.job)
            if "verify_artifact" in worker.spec.capabilities:
                self.client.set_job_verifying(leased, worker_id, {"prepared": True})
            outcome = worker.execute(local_job)
        except Exception as exc:
            outcome = WorkerOutcome(
                next_state=JobState.RETRY_WAIT,
                reason=f"{type(exc).__name__}: {exc}",
                evidence={"exception_type": type(exc).__name__},
            )

        artifact_id: str | None = None
        chained_job_id: str | None = None
        evidence = dict(outcome.evidence)
        if outcome.next_state is JobState.COMPLETED and "produce_artifact" in worker.spec.capabilities:
            artifact_id = self._persist_production_artifact(job_id, evidence)
            if artifact_id:
                evidence["remote_artifact_id"] = artifact_id
                chained_job_id = self._enqueue_next_verify(leased.job, artifact_id, evidence)
                if chained_job_id:
                    evidence["chained_verify_job_id"] = chained_job_id

        final_state = self.client.finish_job(
            leased,
            worker_id,
            outcome_state=outcome.next_state.value,
            reason=outcome.reason,
            evidence=evidence,
        )
        self.client.heartbeat(worker_id, {"phase": "finished", "job_id": job_id, "state": final_state})
        return RemoteRunResult(worker_id, job_id, final_state, outcome.reason, artifact_id, chained_job_id)

    def _materialize_remote_inputs(self, remote_job: RemoteJob) -> Job:
        payload = dict(remote_job.payload)
        artifact_id = payload.get("remote_artifact_id")
        if artifact_id:
            artifact = self.client.get_artifact(str(artifact_id))
            suffix = _suffix_for_media_type(artifact.media_type)
            target = self.workspace / f"{artifact.sha256}{suffix}"
            target.write_bytes(artifact.content)
            payload["artifact_path"] = str(target)
            expected = payload.get("sha256")
            if expected and str(expected) != artifact.sha256:
                raise ValueError("remote artifact SHA-256 does not match job expectation")
            payload["sha256"] = artifact.sha256

        return Job(
            job_id=remote_job.job_id,
            capability=remote_job.capability,
            payload=payload,
            state=JobState.RUNNING,
            attempts=remote_job.attempts,
            max_attempts=remote_job.max_attempts,
            assigned_worker=remote_job.assigned_worker,
            human_threshold_required=remote_job.human_threshold_required,
            created_at=remote_job.created_at,
            updated_at=remote_job.updated_at,
        )

    def _persist_production_artifact(self, job_id: str, evidence: dict[str, object]) -> str | None:
        raw_path = evidence.get("artifact_path")
        raw_sha = evidence.get("sha256")
        if not raw_path or not raw_sha:
            return None
        path = Path(str(raw_path))
        if not path.is_file():
            raise ValueError("production evidence points to a missing artifact")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != str(raw_sha):
            raise ValueError("production artifact changed before durable persistence")
        artifact_id = f"artifact_{job_id}_{digest[:16]}"
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.client.put_artifact(
            artifact_id=artifact_id,
            job_id=job_id,
            media_type=media_type,
            content=data,
        )
        return artifact_id

    def _enqueue_next_verify(self, source_job: RemoteJob, artifact_id: str, evidence: dict[str, object]) -> str | None:
        config = source_job.payload.get("next_verify")
        if not isinstance(config, dict):
            return None
        qualification_evidence_id = str(source_job.payload.get("qualification_evidence_id", "")).strip()
        if not qualification_evidence_id:
            raise ValueError("source job is missing qualification evidence id")
        digest = str(evidence.get("sha256", ""))
        deterministic = hashlib.sha256(f"{source_job.job_id}|verify|{artifact_id}|{digest}".encode()).hexdigest()[:24]
        job_id = f"job_verify_{deterministic}"
        payload = {
            "remote_artifact_id": artifact_id,
            "sha256": digest,
            "contains": list(config.get("contains", [])),
            "forbidden": list(config.get("forbidden", [])),
            "min_bytes": int(config.get("min_bytes", 1)),
            "max_bytes": int(config.get("max_bytes", 524288)),
            "source_job_id": source_job.job_id,
        }
        self.client.enqueue_job(
            job_id=job_id,
            capability="verify_artifact",
            payload=payload,
            qualification_evidence_id=qualification_evidence_id,
            idempotency_key=f"verify:{source_job.job_id}:{digest}",
            max_attempts=3,
        )
        return job_id


def _suffix_for_media_type(media_type: str) -> str:
    guessed = mimetypes.guess_extension(media_type, strict=False)
    if guessed in {".html", ".htm", ".txt", ".json", ".csv", ".xml", ".md"}:
        return guessed
    return ".bin"

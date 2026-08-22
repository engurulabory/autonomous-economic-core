from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from aec.execution_workers import DEFAULT_EXECUTION_WORKERS
from aec.runtime_control import RuntimeControlPlane
from aec.worker_runtime import SQLiteJobQueue, WorkerRegistry, run_registry_cycle


@dataclass(frozen=True)
class SupervisorReport:
    started_at: str
    finished_at: str
    workers: tuple[str, ...]
    processed_jobs: tuple[str, ...]
    queue_counts: dict[str, int]
    audit_chain_valid: bool


def run_supervised_cycle(
    queue: SQLiteJobQueue,
    control: RuntimeControlPlane,
    registry: WorkerRegistry | None = None,
) -> SupervisorReport:
    resolved = registry or WorkerRegistry(DEFAULT_EXECUTION_WORKERS)
    started = datetime.now(timezone.utc).isoformat()

    for worker in resolved.workers:
        control.heartbeat(worker.spec.worker_id, {"phase": "cycle-start"})
        control.append_audit(worker.spec.worker_id, "HEARTBEAT", {"phase": "cycle-start"})

    results = run_registry_cycle(queue, resolved)

    for job in results:
        control.append_audit(
            job.assigned_worker or "runtime",
            "JOB_RESULT",
            {
                "job_id": job.job_id,
                "capability": job.capability,
                "state": job.state.value,
                "attempts": job.attempts,
            },
        )
        if job.state.value == "BLOCKED":
            control.dead_letter(job.job_id, "worker terminal BLOCKED", job.payload)

    for worker in resolved.workers:
        control.heartbeat(worker.spec.worker_id, {"phase": "cycle-finish"})

    return SupervisorReport(
        started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(),
        workers=tuple(worker.spec.worker_id for worker in resolved.workers),
        processed_jobs=tuple(job.job_id for job in results),
        queue_counts=queue.counts(),
        audit_chain_valid=control.verify_audit_chain(),
    )

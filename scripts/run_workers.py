from __future__ import annotations

import json
from pathlib import Path

from aec.execution_workers import DEFAULT_EXECUTION_WORKERS
from aec.worker_runtime import SQLiteJobQueue, WorkerRegistry, run_registry_cycle


STATUS = Path("runtime/worker-runtime-latest.json")


def main() -> int:
    queue = SQLiteJobQueue()
    registry = WorkerRegistry(DEFAULT_EXECUTION_WORKERS)
    results = run_registry_cycle(queue, registry)

    STATUS.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "workers": [worker.spec.worker_id for worker in registry.workers],
        "processed_jobs": [
            {
                "job_id": job.job_id,
                "capability": job.capability,
                "state": job.state.value,
                "attempts": job.attempts,
                "assigned_worker": job.assigned_worker,
            }
            for job in results
        ],
        "queue_counts": queue.counts(),
    }
    STATUS.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"AEC worker cycle: workers={len(registry.workers)} processed={len(results)} counts={queue.counts()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

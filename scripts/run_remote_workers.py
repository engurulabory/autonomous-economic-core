from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from aec.execution_workers import DEFAULT_EXECUTION_WORKERS
from aec.remote_state import RemoteStateClient
from aec.remote_worker_runtime import RemoteWorkerRunner


OUT = Path("runtime/remote-worker-latest.json")


def main() -> int:
    base_url = os.environ.get("AEC_STATE_URL", "").strip()
    token = os.environ.get("AEC_STATE_TOKEN", "").strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    if not base_url or not token:
        OUT.write_text(json.dumps({"state": "HOLD", "reason": "AEC_STATE_URL/TOKEN not configured"}, indent=2) + "\n")
        print("AEC remote workers: HOLD (durable state not configured)")
        return 0

    try:
        client = RemoteStateClient(base_url, token)
        runner = RemoteWorkerRunner(client, DEFAULT_EXECUTION_WORKERS)
        watchdog = client.watchdog_sweep("github-actions-preflight")
        results = runner.run_cycle(max_jobs_per_worker=1)
        audit = client.verify_audit_chain()
        payload = {
            "state": "PASS" if bool(audit.get("ok")) else "BLOCKED",
            "watchdog": watchdog,
            "workers": [worker.spec.worker_id for worker in DEFAULT_EXECUTION_WORKERS],
            "results": [asdict(result) for result in results],
            "job_counts": client.job_counts(),
            "audit": audit,
        }
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"AEC remote workers: {payload['state']} jobs={sum(1 for r in results if r.job_id)}")
        return 0 if payload["state"] == "PASS" else 1
    except Exception as exc:
        payload = {"state": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(payload["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from aec.remote_state import RemoteStateClient, RemoteStateError


OUT = Path("runtime/durability-canary-latest.json")
JOB_ID = "job_v1_1_durability_canary"


def main() -> int:
    base_url = os.environ.get("AEC_STATE_URL", "").strip()
    token = os.environ.get("AEC_STATE_TOKEN", "").strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not base_url or not token:
        OUT.write_text(json.dumps({"state": "HOLD", "reason": "durable state not configured"}, indent=2) + "\n")
        print("AEC durability canary: HOLD")
        return 0

    try:
        client = RemoteStateClient(base_url, token)
        created = False
        try:
            job, events = client.get_job(JOB_ID)
        except RemoteStateError as exc:
            if exc.status != 404:
                raise
            job = client.enqueue_job(
                job_id=JOB_ID,
                capability="durability_canary_no_worker",
                payload={"purpose": "prove durable queued state survives separate scheduler invocations"},
                qualification_evidence_id="internal-controlled-v1.1-durability-canary",
                idempotency_key="v1.1:durability-canary",
                max_attempts=1,
            )
            events = ()
            created = True

        created_at = datetime.fromisoformat(job.created_at.replace("Z", "+00:00"))
        age_seconds = max(0, int((datetime.now(timezone.utc) - created_at).total_seconds()))
        survived_cross_invocation = not created and age_seconds >= 1800 and job.state == "QUEUED"
        payload = {
            "state": "PASS" if job.state == "QUEUED" else "BLOCKED",
            "job_id": job.job_id,
            "job_state": job.state,
            "created_this_run": created,
            "age_seconds": age_seconds,
            "event_count": len(events),
            "cross_invocation_survival": "PASS" if survived_cross_invocation else "HOLD",
        }
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"AEC durability canary: {payload['state']} cross_invocation={payload['cross_invocation_survival']}")
        return 0 if payload["state"] == "PASS" else 1
    except Exception as exc:
        payload = {"state": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(payload["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

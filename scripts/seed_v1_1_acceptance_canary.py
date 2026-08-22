from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from aec.remote_state import RemoteStateClient


OUT = Path("runtime/v1_1-acceptance-canary-latest.json")
JOB_ID = "job_v1_1_controlled_production_canary"
MARKER = "AEC-V1.1-CONTROLLED-EXECUTION-PROOF"


def main() -> int:
    base_url = os.environ.get("AEC_STATE_URL", "").strip()
    token = os.environ.get("AEC_STATE_TOKEN", "").strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    if not base_url or not token:
        payload = {"state": "HOLD", "reason": "durable state not configured"}
        OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("AEC execution canary: HOLD")
        return 0

    try:
        client = RemoteStateClient(base_url, token)
        job = client.enqueue_job(
            job_id=JOB_ID,
            capability="produce_artifact",
            payload={
                "output_path": "v1_1_canary/proof.txt",
                "content": f"{MARKER}\nThis is a controlled non-economic runtime acceptance artifact.\n",
                "next_verify": {
                    "contains": [MARKER, "controlled non-economic runtime acceptance artifact"],
                    "forbidden": ["PRIVATE_KEY", "SEED_PHRASE", "SECRET_TOKEN"],
                    "min_bytes": 32,
                    "max_bytes": 4096,
                },
            },
            qualification_evidence_id="internal-controlled-v1.1-runtime-acceptance",
            idempotency_key="v1.1:controlled-production-canary",
            max_attempts=3,
        )
        payload = {
            "state": "PASS",
            "job_id": job.job_id,
            "job_state": job.state,
            "purpose": "controlled non-economic queue→production→artifact→QA evidence",
        }
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"AEC execution canary: PASS job_state={job.state}")
        return 0
    except Exception as exc:
        payload = {"state": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(payload["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

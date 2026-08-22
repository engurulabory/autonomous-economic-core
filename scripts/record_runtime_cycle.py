from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from aec.remote_state import RemoteStateClient


OUT = Path("runtime/v1_1-cycle-latest.json")


def _load(path: str) -> dict:
    file = Path(path)
    if not file.exists():
        return {"state": "BLOCKED", "reason": f"missing {path}"}
    try:
        value = json.loads(file.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"state": "BLOCKED", "reason": f"invalid {path}: {type(exc).__name__}"}
    return value if isinstance(value, dict) else {"state": "BLOCKED", "reason": f"non-object {path}"}


def main() -> int:
    base_url = os.environ.get("AEC_STATE_URL", "").strip()
    token = os.environ.get("AEC_STATE_TOKEN", "").strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not base_url or not token:
        payload = {"state": "HOLD", "reason": "durable state not configured; cycle cannot be recorded durably"}
        OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("AEC cycle record: HOLD")
        return 0

    durable = _load("runtime/durable-state-latest.json")
    remote = _load("runtime/remote-worker-latest.json")
    states = [str(durable.get("state", "BLOCKED")), str(remote.get("state", "BLOCKED"))]
    status = "BLOCKED" if "BLOCKED" in states else "HOLD" if "HOLD" in states else "PASS"
    run_id = os.environ.get("GITHUB_RUN_ID", "manual")
    source_sha = os.environ.get("GITHUB_SHA", "") or None
    at = datetime.now(timezone.utc).isoformat()
    cycle_id = f"gh-{run_id}"

    try:
        client = RemoteStateClient(base_url, token)
        client.record_cycle(
            cycle_id=cycle_id,
            started_at=at,
            finished_at=at,
            status=status,
            source_sha=source_sha,
            detail={"durable_state": durable.get("state"), "remote_workers": remote.get("state")},
        )
        recent = client.recent_cycles(168)
        github_cycles = [c for c in recent if str(c.get("cycle_id", "")).startswith("gh-")]
        latest_24 = github_cycles[:24]
        consecutive_pass = len(latest_24) == 24 and all(c.get("status") == "PASS" for c in latest_24)
        distinct_run_ids = len({str(c.get("cycle_id")) for c in latest_24}) == len(latest_24)
        payload = {
            "state": status,
            "cycle_id": cycle_id,
            "source_sha": source_sha,
            "observed_github_cycles": len(github_cycles),
            "latest_24_all_pass": consecutive_pass,
            "latest_24_distinct": distinct_run_ids,
            "v1_1_24h_gate": "PASS" if consecutive_pass and distinct_run_ids else "HOLD",
        }
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"AEC cycle record: {status}; 24h_gate={payload['v1_1_24h_gate']}")
        return 0 if status != "BLOCKED" else 1
    except Exception as exc:
        payload = {"state": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(payload["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

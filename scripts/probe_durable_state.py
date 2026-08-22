from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from aec.remote_state import RemoteStateClient


OUT = Path("runtime/durable-state-latest.json")


def main() -> int:
    base_url = os.environ.get("AEC_STATE_URL", "").strip()
    token = os.environ.get("AEC_STATE_TOKEN", "").strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    if not base_url or not token:
        OUT.write_text(json.dumps({"state": "HOLD", "reason": "AEC_STATE_URL/TOKEN not configured"}, indent=2) + "\n")
        print("AEC durable state: HOLD (not configured)")
        return 0

    try:
        client = RemoteStateClient(base_url, token)
        health = client.health()
        if health.get("ok") is not True or str(health.get("version")) != "1.1":
            raise RuntimeError(f"unexpected durable-state health payload: {health}")
        client.heartbeat("github-actions-runtime", {"source": "probe", "version": "1.1"})
        event_hash = client.append_audit("github-actions-runtime", "DURABLE_STATE_PROBE", {"health": health})
        audit = client.verify_audit_chain()
        if audit.get("ok") is not True:
            raise RuntimeError(f"audit chain verification failed: {audit}")
        payload = {
            "state": "PASS",
            "health": health,
            "audit_event_hash": event_hash,
            "audit": audit,
            "job_counts": client.job_counts(),
        }
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("AEC durable state: PASS")
        return 0
    except Exception as exc:
        payload = {"state": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(payload["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS = REPO_ROOT / "runtime" / "field-runtime-latest.json"
FIELD_CYCLE = REPO_ROOT / "scripts" / "run_field_cycle.py"
WORKER_CYCLE = REPO_ROOT / "scripts" / "run_workers.py"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def repository_truth() -> dict[str, Any]:
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    sha = _git("rev-parse", "HEAD")
    dirty = bool(_git("status", "--porcelain"))
    return {"branch": branch, "sha": sha, "dirty": dirty}


def run_python(script: Path) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(REPO_ROOT)
        if not existing_pythonpath
        else f"{REPO_ROOT}{os.pathsep}{existing_pythonpath}"
    )
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return {
        "script": str(script.relative_to(REPO_ROOT)),
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "returncode": result.returncode,
        "stdout": result.stdout[-100_000:],
        "stderr": result.stderr[-50_000:],
    }


def write_status(payload: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    try:
        truth = repository_truth()
    except Exception as exc:
        write_status(
            {
                "kind": "AEC_MAC_FIELD_RUNTIME_V1",
                "state": "BLOCKED",
                "started_at": started,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "reason": f"repository truth unavailable: {type(exc).__name__}: {exc}",
            }
        )
        return 2

    if truth["branch"] != "main":
        write_status(
            {
                "kind": "AEC_MAC_FIELD_RUNTIME_V1",
                "state": "HOLD",
                "started_at": started,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "repository": truth,
                "reason": "field runtime requires canonical main branch",
            }
        )
        return 3

    if truth["dirty"]:
        write_status(
            {
                "kind": "AEC_MAC_FIELD_RUNTIME_V1",
                "state": "HOLD",
                "started_at": started,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "repository": truth,
                "reason": "field runtime requires a clean working tree",
            }
        )
        return 4

    field = run_python(FIELD_CYCLE)
    workers = run_python(WORKER_CYCLE)

    success = field["returncode"] == 0 and workers["returncode"] == 0
    payload = {
        "kind": "AEC_MAC_FIELD_RUNTIME_V1",
        "state": "PASS" if success else "HOLD",
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "repository": truth,
        "cycles": {
            "field_discovery": field,
            "workers": workers,
        },
        "authority_boundary": {
            "claim": False,
            "submit": False,
            "sign": False,
            "spend": False,
            "kyc": False,
            "payout_change": False,
            "money_movement": False,
        },
        "reason": (
            "read-only discovery and local worker cycle completed"
            if success
            else "one or more runtime cycles require review"
        ),
    }
    write_status(payload)
    print(
        f"AEC Mac Field Runtime: state={payload['state']} "
        f"sha={truth['sha']} status={STATUS}"
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

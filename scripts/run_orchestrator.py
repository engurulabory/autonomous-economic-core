from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aec.door_adapters import FIRST_FIVE_ADAPTERS
from aec.orchestrator import run_cycle


OUTPUT = ROOT / "runtime/orchestrator-latest.json"


def _jsonable(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return str(value)


def main() -> int:
    cycle = run_cycle(FIRST_FIVE_ADAPTERS)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(cycle)
    OUTPUT.write_text(json.dumps(payload, indent=2, default=_jsonable) + "\n", encoding="utf-8")

    print(
        f"AEC cycle complete: adapters={len(cycle.results)} "
        f"healthy={cycle.healthy_adapter_count} candidates={cycle.candidate_count}"
    )
    for result in cycle.results:
        suffix = f" error={result.error}" if result.error else ""
        print(f"- {result.adapter}: {result.state.value} candidates={len(result.candidates)}{suffix}")

    # Provider failures are evidence, not a reason to suppress the cycle artifact.
    # Exit 0 unless the orchestrator itself could not complete.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

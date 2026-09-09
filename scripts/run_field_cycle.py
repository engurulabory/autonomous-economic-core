from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from aec.door_adapters import FIRST_FIVE_ADAPTERS
from aec.economic_execution import qualify_candidate
from aec.orchestrator import run_cycle


def main() -> None:
    """Run one live, read-only AEC field discovery + qualification cycle.

    This script may discover public economic opportunities and classify whether they
    are eligible for controlled internal production. It never claims, submits, signs,
    spends, accepts legal terms, changes payout settings, or moves money.

    External execution remains behind Human Threshold and the canonical economic
    finality gates. Unknown critical facts fail closed to HOLD.
    """
    cycle = run_cycle(FIRST_FIVE_ADAPTERS)

    decisions: list[dict[str, object]] = []
    for result in cycle.results:
        for candidate in result.candidates:
            decision = qualify_candidate(candidate)
            decisions.append(
                {
                    "door": candidate.door,
                    "source": candidate.source,
                    "external_id": candidate.external_id,
                    "title": candidate.title,
                    "canonical_url": candidate.canonical_url,
                    "reward_amount": str(candidate.reward_amount) if candidate.reward_amount is not None else None,
                    "reward_currency": candidate.reward_currency,
                    "state": decision.state.value,
                    "reason": decision.reason,
                    "human_threshold_required": decision.human_threshold_required,
                }
            )

    payload = {
        "kind": "AEC_FIELD_CYCLE_V1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "READ_ONLY_DISCOVERY_AND_FAIL_CLOSED_QUALIFICATION",
        "candidate_count": cycle.candidate_count,
        "healthy_adapter_count": cycle.healthy_adapter_count,
        "adapters": [
            {
                "adapter": result.adapter,
                "door": result.door,
                "state": result.state.value,
                "candidate_count": len(result.candidates),
                "error": result.error,
            }
            for result in cycle.results
        ],
        "decisions": decisions,
        "authority_boundary": {
            "claim": False,
            "submit": False,
            "sign": False,
            "spend": False,
            "kyc": False,
            "payout_change": False,
            "money_movement": False,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

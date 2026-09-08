from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from aec.commercial_closure import (
    CapabilityGap,
    CommercialEvidence,
    DemandProof,
    MarketSignal,
    capability_decision,
    evaluate_commercial_closure,
    evaluate_demand_proof,
    saturation_decision,
)


def main() -> None:
    # Fail-closed baseline. External market/customer/bank evidence must replace
    # unknown values before commercial PASS or a new Revenue Agent is authorized.
    demand = DemandProof(None, None, None, None, None, True)
    commercial = CommercialEvidence(
        independent_counterparty=False,
        accepted_output=False,
        invoice_recorded=False,
        payment_settled=False,
        approved_account_receipt=False,
        bank_receipt=False,
        gross_value=None,
        direct_costs=None,
        currency="EUR",
    )
    saturation = MarketSignal()
    gap = CapabilityGap(
        repeated_verified_demand=False,
        existing_capability_can_deliver=False,
        extension_sufficient=False,
        adapter_sufficient=False,
        positive_expected_net_value=False,
        distribution_path_ready=False,
        settlement_path_ready=False,
        donecheck_contract_defined=False,
        policy_safe=True,
    )

    closure = evaluate_commercial_closure(commercial)
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "state": closure.state.value,
        "claim": "Commercial Closure Pass executed against currently available evidence.",
        "evidence": {
            "demand_proof": evaluate_demand_proof(demand).value,
            "commercial_closure": closure.state.value,
            "commercial_reason": closure.reason,
            "verified_banked_net_value": str(closure.verified_banked_net_value) if closure.verified_banked_net_value is not None else None,
            "currency": closure.currency,
            "saturation_decision": saturation_decision(saturation).value,
            "capability_decision": capability_decision(gap).value,
        },
        "next_action": "Ingest verified demand, distribution, customer acceptance, settlement and bank evidence; keep HOLD until positive VBNV exists.",
    }

    target = Path("runtime/commercial-closure-latest.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()

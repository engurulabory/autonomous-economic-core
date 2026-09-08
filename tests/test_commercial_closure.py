from decimal import Decimal
import unittest

from aec.commercial_closure import (
    CapabilityDecision,
    CapabilityGap,
    ClosureState,
    CommercialEvidence,
    DemandProof,
    MarketSignal,
    ServiceDecision,
    capability_decision,
    evaluate_commercial_closure,
    evaluate_demand_proof,
    saturation_decision,
)


class CommercialClosureTests(unittest.TestCase):
    def test_demand_proof_holds_on_unknown(self):
        proof = DemandProof(True, True, None, True, True, True)
        self.assertEqual(evaluate_demand_proof(proof), ClosureState.HOLD)

    def test_commercial_closure_requires_bank_receipt(self):
        evidence = CommercialEvidence(True, True, True, True, True, False, Decimal("5"), Decimal("1"), "EUR")
        result = evaluate_commercial_closure(evidence)
        self.assertEqual(result.state, ClosureState.HOLD)
        self.assertIsNone(result.verified_banked_net_value)

    def test_positive_banked_net_value_passes(self):
        evidence = CommercialEvidence(True, True, True, True, True, True, Decimal("5"), Decimal("1"), "USD")
        result = evaluate_commercial_closure(evidence)
        self.assertEqual(result.state, ClosureState.PASS)
        self.assertEqual(result.verified_banked_net_value, Decimal("4"))

    def test_saturation_extends_before_reposition(self):
        signal = MarketSignal(price_falling=True, conversion_falling=True)
        self.assertEqual(saturation_decision(signal), ServiceDecision.EXTEND)

    def test_new_revenue_agent_requires_verified_readiness(self):
        gap = CapabilityGap(
            repeated_verified_demand=True,
            existing_capability_can_deliver=False,
            extension_sufficient=False,
            adapter_sufficient=False,
            positive_expected_net_value=True,
            distribution_path_ready=True,
            settlement_path_ready=True,
            donecheck_contract_defined=True,
            policy_safe=True,
        )
        self.assertEqual(capability_decision(gap), CapabilityDecision.NEW_REVENUE_AGENT)


if __name__ == "__main__":
    unittest.main()

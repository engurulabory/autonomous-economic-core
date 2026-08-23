import unittest
from decimal import Decimal

from aec.micro_earning_policy import (
    MicroEarningOpportunity,
    MicroEarningState,
    assess_micro_earning,
)


class MicroEarningPolicyTests(unittest.TestCase):
    def test_verified_eur_opportunity_passes_with_risk_adjusted_hourly_value(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("1.00"),
            currency="EUR",
            estimated_minutes=Decimal("30"),
            acceptance_probability=Decimal("0.80"),
            payment_probability=Decimal("0.90"),
            expected_fees=Decimal("0.10"),
            expected_taxes=Decimal("0.10"),
            expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.PASS)
        self.assertEqual(result.expected_net_eur, Decimal("0.8000"))
        self.assertEqual(result.risk_adjusted_net_eur, Decimal("0.5760"))
        self.assertEqual(result.expected_net_per_hour_eur, Decimal("1.1520"))

    def test_unknown_probability_holds_fail_closed(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("1"),
            currency="EUR",
            estimated_minutes=Decimal("10"),
            acceptance_probability=None,
            payment_probability=Decimal("1"),
            expected_fees=Decimal("0"),
            expected_taxes=Decimal("0"),
            expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.HOLD)

    def test_positive_upfront_cost_is_blocked(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("100"),
            currency="EUR",
            estimated_minutes=Decimal("10"),
            acceptance_probability=Decimal("1"),
            payment_probability=Decimal("1"),
            expected_fees=Decimal("0"),
            expected_taxes=Decimal("0"),
            expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0.01"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.BLOCKED)

    def test_non_positive_net_value_is_blocked(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("0.50"),
            currency="EUR",
            estimated_minutes=Decimal("5"),
            acceptance_probability=Decimal("1"),
            payment_probability=Decimal("1"),
            expected_fees=Decimal("0.30"),
            expected_taxes=Decimal("0.20"),
            expected_other_cost=Decimal("0.10"),
            worker_side_upfront_cost=Decimal("0"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.BLOCKED)
        self.assertEqual(result.expected_net_eur, Decimal("-0.1000"))

    def test_non_eur_without_fx_holds(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("1"),
            currency="USD",
            estimated_minutes=Decimal("10"),
            acceptance_probability=Decimal("1"),
            payment_probability=Decimal("1"),
            expected_fees=Decimal("0"),
            expected_taxes=Decimal("0"),
            expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.HOLD)

    def test_non_eur_with_verified_fx_normalizes_to_eur(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("2"),
            currency="USD",
            estimated_minutes=Decimal("60"),
            acceptance_probability=Decimal("1"),
            payment_probability=Decimal("1"),
            expected_fees=Decimal("0"),
            expected_taxes=Decimal("0"),
            expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0"),
            fx_to_eur=Decimal("0.85"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.PASS)
        self.assertEqual(result.gross_eur, Decimal("1.7000"))
        self.assertEqual(result.expected_net_per_hour_eur, Decimal("1.7000"))


if __name__ == "__main__":
    unittest.main()

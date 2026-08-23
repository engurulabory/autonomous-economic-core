import unittest
from decimal import Decimal

from aec.micro_earning_policy import (
    MicroEarningOpportunity,
    MicroEarningState,
    assess_micro_earning,
)


class MicroEarningPolicyTests(unittest.TestCase):
    def test_verified_eur_opportunity_outputs_eur_and_usd(self):
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
            eur_to_usd=Decimal("1.10"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.PASS)
        self.assertEqual(result.expected_net_eur, Decimal("0.8000"))
        self.assertEqual(result.expected_net_usd, Decimal("0.8800"))
        self.assertEqual(result.expected_net_per_hour_eur, Decimal("1.1520"))
        self.assertEqual(result.expected_net_per_hour_usd, Decimal("1.2672"))

    def test_verified_usd_opportunity_outputs_usd_and_eur(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("2.20"),
            currency="USD",
            estimated_minutes=Decimal("60"),
            acceptance_probability=Decimal("1"),
            payment_probability=Decimal("1"),
            expected_fees=Decimal("0.20"),
            expected_taxes=Decimal("0"),
            expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0"),
            eur_to_usd=Decimal("1.10"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.PASS)
        self.assertEqual(result.expected_net_usd, Decimal("2.0000"))
        self.assertEqual(result.expected_net_eur, Decimal("1.8182"))

    def test_unknown_probability_holds_fail_closed(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("1"), currency="EUR", estimated_minutes=Decimal("10"),
            acceptance_probability=None, payment_probability=Decimal("1"),
            expected_fees=Decimal("0"), expected_taxes=Decimal("0"), expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0"), eur_to_usd=Decimal("1.10"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.HOLD)

    def test_missing_eur_usd_fx_holds(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("1"), currency="USD", estimated_minutes=Decimal("10"),
            acceptance_probability=Decimal("1"), payment_probability=Decimal("1"),
            expected_fees=Decimal("0"), expected_taxes=Decimal("0"), expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0"), independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.HOLD)

    def test_positive_upfront_cost_is_blocked(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("100"), currency="EUR", estimated_minutes=Decimal("10"),
            acceptance_probability=Decimal("1"), payment_probability=Decimal("1"),
            expected_fees=Decimal("0"), expected_taxes=Decimal("0"), expected_other_cost=Decimal("0"),
            worker_side_upfront_cost=Decimal("0.01"), eur_to_usd=Decimal("1.10"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.BLOCKED)

    def test_non_positive_net_value_is_blocked(self):
        result = assess_micro_earning(MicroEarningOpportunity(
            gross_value=Decimal("0.50"), currency="EUR", estimated_minutes=Decimal("5"),
            acceptance_probability=Decimal("1"), payment_probability=Decimal("1"),
            expected_fees=Decimal("0.30"), expected_taxes=Decimal("0.20"), expected_other_cost=Decimal("0.10"),
            worker_side_upfront_cost=Decimal("0"), eur_to_usd=Decimal("1.10"),
            independent_external_counterparty=True,
        ))
        self.assertEqual(result.state, MicroEarningState.BLOCKED)
        self.assertEqual(result.expected_net_eur, Decimal("-0.1000"))
        self.assertEqual(result.expected_net_usd, Decimal("-0.1100"))


if __name__ == "__main__":
    unittest.main()

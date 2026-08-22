import unittest
from decimal import Decimal

from aec import EconomicRun, Judgment, evaluate_run, threshold_status


class EconomicTruthTests(unittest.TestCase):
    def test_one_cent_economic_pass_without_bank_is_hold_for_bank(self):
        run = EconomicRun(
            run_id="run-001",
            external_counterparty=True,
            accepted=True,
            settled_revenue_eur=Decimal("0.02"),
            direct_cost_eur=Decimal("0.00"),
            active_minutes=Decimal("2"),
            reconciled=True,
            costs_finalized=True,
            bank_receipt_verified=False,
        )
        result = evaluate_run(run)
        self.assertEqual(result.vnev_eur, Decimal("0.0200"))
        self.assertEqual(result.one_cent_economic_test, Judgment.PASS)
        self.assertEqual(result.one_cent_bank_test, Judgment.HOLD)

    def test_one_cent_bank_pass_requires_verified_receipt(self):
        run = EconomicRun(
            run_id="run-002",
            external_counterparty=True,
            accepted=True,
            settled_revenue_eur=Decimal("0.04"),
            direct_cost_eur=Decimal("0.01"),
            active_minutes=Decimal("3"),
            reconciled=True,
            costs_finalized=True,
            bank_receipt_verified=True,
            bank_received_eur=Decimal("0.04"),
        )
        result = evaluate_run(run)
        self.assertEqual(result.vnev_eur, Decimal("0.0300"))
        self.assertEqual(result.vbnv_eur, Decimal("0.0300"))
        self.assertEqual(result.one_cent_economic_test, Judgment.PASS)
        self.assertEqual(result.one_cent_bank_test, Judgment.PASS)

    def test_no_external_counterparty_blocks_and_zeroes_fake_economy(self):
        run = EconomicRun(
            run_id="self-transfer",
            external_counterparty=False,
            accepted=True,
            settled_revenue_eur=Decimal("100"),
            direct_cost_eur=Decimal("0"),
            active_minutes=Decimal("1"),
            reconciled=True,
            costs_finalized=True,
            bank_receipt_verified=True,
            bank_received_eur=Decimal("100"),
        )
        result = evaluate_run(run)
        self.assertEqual(result.vnev_eur, Decimal("0.0000"))
        self.assertEqual(result.vbnv_eur, Decimal("0.0000"))
        self.assertEqual(result.net_per_hour_eur, Decimal("0.0000"))
        self.assertEqual(result.one_cent_economic_test, Judgment.BLOCKED)
        self.assertEqual(result.one_cent_bank_test, Judgment.BLOCKED)

    def test_missing_reconciliation_holds_claim(self):
        run = EconomicRun(
            run_id="pending-reconciliation",
            external_counterparty=True,
            accepted=True,
            settled_revenue_eur=Decimal("5"),
            direct_cost_eur=Decimal("0"),
            active_minutes=Decimal("5"),
            reconciled=False,
            costs_finalized=True,
        )
        result = evaluate_run(run)
        self.assertEqual(result.one_cent_economic_test, Judgment.HOLD)

    def test_thresholds_match_locked_targets(self):
        statuses = threshold_status(Decimal("1.00"), positive_runs=10)
        self.assertTrue(all(value is Judgment.PASS for value in statuses.values()))

        statuses = threshold_status(Decimal("0.49"), positive_runs=9)
        self.assertEqual(statuses["repeatability_10_runs"], Judgment.HOLD)
        self.assertEqual(statuses["economic_engine_0_10_per_hour"], Judgment.PASS)
        self.assertEqual(statuses["utility_0_50_per_hour"], Judgment.HOLD)
        self.assertEqual(statuses["serious_target_1_00_per_hour"], Judgment.HOLD)

    def test_negative_values_are_rejected(self):
        with self.assertRaises(ValueError):
            EconomicRun(
                run_id="bad",
                external_counterparty=True,
                accepted=True,
                settled_revenue_eur=Decimal("-1"),
                direct_cost_eur=Decimal("0"),
                active_minutes=Decimal("1"),
                reconciled=True,
                costs_finalized=True,
            )


if __name__ == "__main__":
    unittest.main()

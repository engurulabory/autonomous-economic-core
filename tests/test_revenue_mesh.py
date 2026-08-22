from decimal import Decimal
import unittest

from aec.revenue_mesh import (
    EconomicPassState,
    EndToEndEconomicRun,
    REVENUE_DOORS,
    RevenueDoorMetrics,
    RevenueDoorState,
    mesh_is_complete,
)


class RevenueMeshTests(unittest.TestCase):
    def test_exactly_twenty_unique_revenue_doors(self):
        self.assertEqual(len(REVENUE_DOORS), 20)
        self.assertEqual(len(set(REVENUE_DOORS)), 20)
        self.assertTrue(mesh_is_complete())

    def test_positive_door_vnev(self):
        metrics = RevenueDoorMetrics(
            door="static_mini_tools",
            state=RevenueDoorState.ACTIVE,
            settled_external_revenue_eur=Decimal("1.00"),
            direct_cost_eur=Decimal("0.00"),
            human_minutes=Decimal("30"),
            accepted_runs=1,
            settled_runs=1,
            banked_runs=1,
        )
        self.assertEqual(metrics.vnev_eur, Decimal("1.00"))
        self.assertEqual(metrics.vnev_per_human_hour_eur, Decimal("2.0000"))

    def test_full_pass_requires_bank_receipt(self):
        run = EndToEndEconomicRun(
            external_customer_or_counterparty=True,
            work_or_asset_verified=True,
            accepted_or_sold=True,
            payment_settled=True,
            payout_eligible=True,
            payout_executed=True,
            approved_account_receipt_verified=True,
            bank_receipt_verified=False,
            direct_costs_finalized=True,
            settled_revenue_eur=Decimal("2.00"),
            direct_cost_eur=Decimal("0.00"),
        )
        self.assertEqual(run.full_pass(), EconomicPassState.HOLD)

    def test_full_pass_requires_positive_net_and_every_gate(self):
        run = EndToEndEconomicRun(
            external_customer_or_counterparty=True,
            work_or_asset_verified=True,
            accepted_or_sold=True,
            payment_settled=True,
            payout_eligible=True,
            payout_executed=True,
            approved_account_receipt_verified=True,
            bank_receipt_verified=True,
            direct_costs_finalized=True,
            settled_revenue_eur=Decimal("2.00"),
            direct_cost_eur=Decimal("0.25"),
        )
        self.assertEqual(run.vnev_eur, Decimal("1.75"))
        self.assertEqual(run.full_pass(), EconomicPassState.PASS)

    def test_self_or_nonexternal_value_is_blocked(self):
        run = EndToEndEconomicRun(
            external_customer_or_counterparty=False,
            work_or_asset_verified=True,
            accepted_or_sold=True,
            payment_settled=True,
            payout_eligible=True,
            payout_executed=True,
            approved_account_receipt_verified=True,
            bank_receipt_verified=True,
            direct_costs_finalized=True,
            settled_revenue_eur=Decimal("5.00"),
            direct_cost_eur=Decimal("0.00"),
        )
        self.assertEqual(run.vnev_eur, Decimal("0"))
        self.assertEqual(run.full_pass(), EconomicPassState.BLOCKED)


if __name__ == "__main__":
    unittest.main()

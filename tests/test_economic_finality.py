from __future__ import annotations

import unittest
from decimal import Decimal

from aec.economic_finality import EconomicFinalityEvidence, FinalityState, one_cent_test


class EconomicFinalityTests(unittest.TestCase):
    def make(self, **overrides):
        base = dict(
            run_id="run-1",
            external_counterparty_verified=True,
            work_or_sale_verified=True,
            acceptance_verified=True,
            payment_settled=True,
            settlement_reference="settle-1",
            payout_executed=True,
            payout_reference="payout-1",
            approved_account_receipt_verified=True,
            bank_receipt_verified=True,
            bank_receipt_reference="bank-1",
            gross_revenue_eur=Decimal("1.00"),
            direct_cost_eur=Decimal("0.10"),
            taxes_fees_known=True,
            taxes_fees_eur=Decimal("0.10"),
            reconciliation_complete=True,
        )
        base.update(overrides)
        return EconomicFinalityEvidence(**base)

    def test_full_external_banked_positive_run_passes(self):
        evidence = self.make()
        self.assertEqual(evidence.judge(), FinalityState.PASS)
        self.assertEqual(evidence.verified_banked_net_value_eur, Decimal("0.80"))
        self.assertEqual(one_cent_test(evidence), FinalityState.PASS)

    def test_missing_bank_receipt_holds(self):
        evidence = self.make(bank_receipt_verified=False, bank_receipt_reference=None)
        self.assertEqual(evidence.judge(), FinalityState.HOLD)
        self.assertEqual(evidence.verified_banked_net_value_eur, Decimal("0"))

    def test_self_economy_blocks(self):
        self.assertEqual(self.make(external_counterparty_verified=False).judge(), FinalityState.BLOCKED)

    def test_non_positive_net_value_does_not_pass(self):
        evidence = self.make(direct_cost_eur=Decimal("0.90"), taxes_fees_eur=Decimal("0.10"))
        self.assertEqual(evidence.judge(), FinalityState.HOLD)

    def test_less_than_one_cent_is_not_one_cent_proof(self):
        evidence = self.make(gross_revenue_eur=Decimal("0.009"), direct_cost_eur=Decimal("0"), taxes_fees_eur=Decimal("0"))
        self.assertEqual(evidence.judge(), FinalityState.PASS)
        self.assertEqual(one_cent_test(evidence), FinalityState.HOLD)


if __name__ == "__main__":
    unittest.main()

from decimal import Decimal
import unittest

from aec.action_gate import ActionDecision, PendingEconomicAction, assess_zero_capital_action


class ActionGateTests(unittest.TestCase):
    def test_free_available_action_allows(self):
        result = assess_zero_capital_action(
            PendingEconomicAction(
                action="submit",
                available=True,
                requires_payment=False,
                payment_amount=Decimal("0"),
                deposit_required=False,
                deposit_amount=Decimal("0"),
                public_commitment=True,
            )
        )
        self.assertEqual(result.decision, ActionDecision.ALLOW)
        self.assertTrue(result.human_threshold_required)

    def test_positive_payment_rejects(self):
        result = assess_zero_capital_action(
            PendingEconomicAction(
                action="pitch",
                available=True,
                requires_payment=True,
                payment_amount=Decimal("0.001"),
                currency="USDC",
                deposit_required=False,
                deposit_amount=Decimal("0"),
            )
        )
        self.assertEqual(result.decision, ActionDecision.REJECT)

    def test_positive_bond_rejects(self):
        result = assess_zero_capital_action(
            PendingEconomicAction(
                action="claim",
                available=True,
                requires_payment=False,
                payment_amount=Decimal("0"),
                deposit_required=True,
                deposit_amount=Decimal("0.01"),
                currency="USDC",
            )
        )
        self.assertEqual(result.decision, ActionDecision.REJECT)

    def test_unknown_payment_holds(self):
        result = assess_zero_capital_action(
            PendingEconomicAction(
                action="submit",
                available=True,
                requires_payment=None,
                payment_amount=None,
                deposit_required=False,
                deposit_amount=Decimal("0"),
            )
        )
        self.assertEqual(result.decision, ActionDecision.HOLD)

    def test_unavailable_action_rejects(self):
        result = assess_zero_capital_action(
            PendingEconomicAction(
                action="submit",
                available=False,
                requires_payment=False,
                payment_amount=Decimal("0"),
                deposit_required=False,
                deposit_amount=Decimal("0"),
            )
        )
        self.assertEqual(result.decision, ActionDecision.REJECT)


if __name__ == "__main__":
    unittest.main()

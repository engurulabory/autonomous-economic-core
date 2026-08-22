import unittest
from decimal import Decimal

from aec.shadow import ShadowDecision, ShadowOpportunity, assess_shadow


class ShadowEconomyTests(unittest.TestCase):
    def test_stale_source_is_rejected_even_if_marketplace_says_open(self):
        result = assess_shadow(ShadowOpportunity(
            source="algora",
            external_id="projectdiscovery/nuclei#6674",
            title="Replace panic with error handling",
            reward_eur=Decimal("90"),
            estimated_minutes=Decimal("120"),
            source_claims_open=True,
            canonical_open=False,
            automation_policy_verified=False,
            zero_capital_required=True,
            payout_path_known=True,
        ))
        self.assertEqual(result.decision, ShadowDecision.REJECTED)
        self.assertEqual(result.expected_net_eur, Decimal("0"))

    def test_unknown_canonical_state_holds(self):
        result = assess_shadow(ShadowOpportunity(
            source="example",
            external_id="x-1",
            title="Example",
            reward_eur=Decimal("1"),
            estimated_minutes=Decimal("10"),
            source_claims_open=True,
            canonical_open=None,
            automation_policy_verified=True,
            zero_capital_required=True,
            payout_path_known=True,
        ))
        self.assertEqual(result.decision, ShadowDecision.HOLD)

    def test_paid_entry_is_rejected(self):
        result = assess_shadow(ShadowOpportunity(
            source="example",
            external_id="x-2",
            title="Pay first",
            reward_eur=Decimal("100"),
            estimated_minutes=Decimal("30"),
            source_claims_open=True,
            canonical_open=True,
            automation_policy_verified=True,
            zero_capital_required=False,
            payout_path_known=True,
        ))
        self.assertEqual(result.decision, ShadowDecision.REJECTED)

    def test_unverified_automation_policy_holds_external_action(self):
        result = assess_shadow(ShadowOpportunity(
            source="algora",
            external_id="org/repo#1",
            title="Open bounty",
            reward_eur=Decimal("20"),
            estimated_minutes=Decimal("60"),
            source_claims_open=True,
            canonical_open=True,
            automation_policy_verified=False,
            zero_capital_required=True,
            payout_path_known=True,
        ))
        self.assertEqual(result.decision, ShadowDecision.HOLD)
        self.assertEqual(result.expected_net_per_hour_eur, Decimal("20.0000"))

    def test_only_fully_verified_shadow_opportunity_qualifies(self):
        result = assess_shadow(ShadowOpportunity(
            source="api-native",
            external_id="verified-1",
            title="Verified task",
            reward_eur=Decimal("0.50"),
            estimated_minutes=Decimal("30"),
            source_claims_open=True,
            canonical_open=True,
            automation_policy_verified=True,
            zero_capital_required=True,
            payout_path_known=True,
        ))
        self.assertEqual(result.decision, ShadowDecision.QUALIFIED)
        self.assertEqual(result.expected_net_per_hour_eur, Decimal("1.0000"))


if __name__ == "__main__":
    unittest.main()

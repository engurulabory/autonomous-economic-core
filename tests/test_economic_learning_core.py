import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aec.economic_learning_core import (
    CAPABILITY_CATALOG,
    FxQuote,
    LearningState,
    OneCentEvidence,
    RecurringService,
    RoutedEconomics,
    ThroughputEvent,
    VerifiedLearningSample,
    capability_by_id,
    evaluate_one_cent_test,
    learn_verified_profiles,
    recurring_service_state,
    rolling_throughput,
    route_eur_usd,
    validate_fx_quote,
)


class EconomicLearningCoreTests(unittest.TestCase):
    def test_p10_one_cent_passes_only_with_full_banked_chain(self):
        result = evaluate_one_cent_test(OneCentEvidence(
            True, True, True, True, True, True, True,
            Decimal("0.02"), Decimal("0.005"),
        ))
        self.assertEqual(result.state, LearningState.PASS)
        self.assertEqual(result.verified_banked_net_value_eur, Decimal("0.015"))

    def test_p10_missing_bank_receipt_holds(self):
        result = evaluate_one_cent_test(OneCentEvidence(
            True, True, True, True, True, True, False,
            Decimal("1"), Decimal("0"),
        ))
        self.assertEqual(result.state, LearningState.HOLD)

    def test_p11_stale_fx_holds(self):
        now = datetime.now(timezone.utc)
        quote = FxQuote(Decimal("1.10"), now - timedelta(days=2), "source", "evidence")
        self.assertEqual(validate_fx_quote(quote, now=now), LearningState.HOLD)

    def test_p11_routes_eur_and_usd_on_single_economic_plane(self):
        now = datetime.now(timezone.utc)
        quote = FxQuote(Decimal("1.10"), now, "source", "evidence")
        ranked = route_eur_usd((
            RoutedEconomics("eur", "EUR", Decimal("1"), Decimal("60"), Decimal("1"), Decimal("1"), quote),
            RoutedEconomics("usd", "USD", Decimal("2.20"), Decimal("60"), Decimal("1"), Decimal("1"), quote),
        ), now=now)
        self.assertEqual(ranked[0].opportunity_id, "usd")

    def test_p12_rolling_throughput_reports_target_and_idle_reason(self):
        now = datetime.now(timezone.utc)
        snap = rolling_throughput((
            ThroughputEvent(now - timedelta(minutes=10), realized_net_eur=Decimal("0.5"), banked_net_eur=Decimal("0.2"), qualified=2, executed=1, accepted=1, idle_minutes=Decimal("20"), idle_reason="no-opportunity"),
        ), now=now)
        self.assertTrue(snap.below_one_euro_target)
        self.assertIn("no-opportunity", snap.idle_reasons)

    def test_p13_recurring_service_requires_verified_contracts(self):
        service = RecurringService("s1", "monitor", 60, True, True, True, Decimal("5"))
        self.assertEqual(recurring_service_state(service), LearningState.PASS)
        hold = RecurringService("s2", "monitor", 60, True, None, True, Decimal("5"))
        self.assertEqual(recurring_service_state(hold), LearningState.HOLD)

    def test_p14_learning_uses_only_verified_samples_and_minimum_sample(self):
        now = datetime.now(timezone.utc)
        samples = [
            VerifiedLearningSample(f"s{i}", "qa", "door", "worker", True, True, True, True, Decimal("10"), Decimal("1"), now)
            for i in range(3)
        ]
        samples.append(VerifiedLearningSample("bad", "qa", "door", "worker", True, None, None, None, Decimal("1"), Decimal("100"), now))
        profiles = learn_verified_profiles(samples, minimum_samples=3, now=now)
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].sample_count, 3)
        self.assertEqual(profiles[0].realized_net_per_hour_eur, Decimal("6"))

    def test_p15_capability_catalog_is_machine_readable_and_broad(self):
        self.assertGreaterEqual(len(CAPABILITY_CATALOG), 20)
        self.assertIsNotNone(capability_by_id("web-qa"))
        self.assertIsNone(capability_by_id("legal-decision"))


if __name__ == "__main__":
    unittest.main()

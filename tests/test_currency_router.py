import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aec.currency_router import (
    SUPPORTED_CURRENCIES,
    CurrencyOpportunity,
    CurrencyRouteState,
    FxEvidence,
    evaluate_currency_opportunity,
    route_currency_opportunities,
)


class CurrencyRouterTests(unittest.TestCase):
    def test_supported_currency_set_is_locked(self):
        self.assertEqual(SUPPORTED_CURRENCIES, frozenset({"EUR", "USD", "GBP", "JPY", "CNY"}))

    def test_all_supported_non_eur_currencies_normalize_to_eur(self):
        now = datetime.now(timezone.utc)
        samples = (
            ("USD", "0.91"),
            ("GBP", "1.17"),
            ("JPY", "0.0062"),
            ("CNY", "0.127"),
        )
        for code, rate in samples:
            opportunity = CurrencyOpportunity(
                code.lower(), code, Decimal("10"), Decimal("1"), Decimal("0"),
                Decimal("30"), Decimal("1"), Decimal("1"),
                FxEvidence(code, Decimal(rate), now, "test-source", f"fx-{code}"),
            )
            decision = evaluate_currency_opportunity(opportunity, now=now)
            self.assertEqual(decision.state, CurrencyRouteState.PASS)
            self.assertGreater(decision.expected_net_eur, Decimal("0"))

    def test_stale_fx_holds(self):
        now = datetime.now(timezone.utc)
        opportunity = CurrencyOpportunity(
            "usd", "USD", Decimal("1"), Decimal("0"), Decimal("0"),
            Decimal("10"), Decimal("1"), Decimal("1"),
            FxEvidence("USD", Decimal("0.9"), now - timedelta(days=2), "source", "ref"),
        )
        self.assertEqual(evaluate_currency_opportunity(opportunity, now=now).state, CurrencyRouteState.HOLD)

    def test_fee_aware_negative_net_blocks(self):
        now = datetime.now(timezone.utc)
        opportunity = CurrencyOpportunity(
            "gbp", "GBP", Decimal("1"), Decimal("0"), Decimal("2"),
            Decimal("10"), Decimal("1"), Decimal("1"),
            FxEvidence("GBP", Decimal("1.17"), now, "source", "ref"),
        )
        self.assertEqual(evaluate_currency_opportunity(opportunity, now=now).state, CurrencyRouteState.BLOCKED)

    def test_router_ranks_on_risk_adjusted_eur_per_hour(self):
        now = datetime.now(timezone.utc)
        eur = CurrencyOpportunity(
            "eur", "EUR", Decimal("1"), Decimal("0"), Decimal("0"),
            Decimal("60"), Decimal("1"), Decimal("1"), None,
        )
        usd = CurrencyOpportunity(
            "usd", "USD", Decimal("2"), Decimal("0"), Decimal("0"),
            Decimal("60"), Decimal("1"), Decimal("1"),
            FxEvidence("USD", Decimal("0.9"), now, "source", "ref-usd"),
        )
        ranked = route_currency_opportunities((eur, usd), now=now)
        self.assertEqual(ranked[0].opportunity.opportunity_id, "usd")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Iterable


SUPPORTED_CURRENCIES = frozenset({"EUR", "USD", "GBP", "JPY", "CNY"})
CANONICAL_COMPARISON_CURRENCY = "EUR"


class CurrencyRouteState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class FxEvidence:
    currency: str
    eur_per_unit: Decimal
    observed_at: datetime
    source: str
    evidence_ref: str

    def __post_init__(self) -> None:
        code = self.currency.upper()
        if code not in SUPPORTED_CURRENCIES - {"EUR"}:
            raise ValueError("FX evidence currency must be USD, GBP, JPY or CNY")
        if self.eur_per_unit <= 0:
            raise ValueError("eur_per_unit must be positive")
        if not self.source.strip() or not self.evidence_ref.strip():
            raise ValueError("FX source and evidence_ref are required")


@dataclass(frozen=True)
class CurrencyOpportunity:
    opportunity_id: str
    natural_currency: str
    gross_native: Decimal
    native_fees: Decimal
    payout_and_conversion_cost_eur: Decimal
    expected_minutes: Decimal
    acceptance_probability: Decimal
    payment_probability: Decimal
    fx: FxEvidence | None = None

    def __post_init__(self) -> None:
        code = self.natural_currency.upper()
        if code not in SUPPORTED_CURRENCIES:
            raise ValueError("unsupported currency")
        if not self.opportunity_id.strip():
            raise ValueError("opportunity_id is required")
        if self.gross_native < 0 or self.native_fees < 0 or self.payout_and_conversion_cost_eur < 0:
            raise ValueError("economic amounts cannot be negative")
        if self.expected_minutes <= 0:
            raise ValueError("expected_minutes must be positive")
        for probability in (self.acceptance_probability, self.payment_probability):
            if probability < 0 or probability > 1:
                raise ValueError("probabilities must be between 0 and 1")


@dataclass(frozen=True)
class CurrencyRouteDecision:
    state: CurrencyRouteState
    reason: str
    opportunity: CurrencyOpportunity
    expected_net_eur: Decimal | None
    risk_adjusted_eur_per_hour: Decimal | None


def fx_state(
    fx: FxEvidence | None,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=24),
) -> CurrencyRouteState:
    if fx is None:
        return CurrencyRouteState.HOLD
    current = now or datetime.now(timezone.utc)
    observed = fx.observed_at if fx.observed_at.tzinfo else fx.observed_at.replace(tzinfo=timezone.utc)
    if observed > current + timedelta(minutes=5):
        return CurrencyRouteState.BLOCKED
    if current - observed > max_age:
        return CurrencyRouteState.HOLD
    return CurrencyRouteState.PASS


def evaluate_currency_opportunity(
    opportunity: CurrencyOpportunity,
    *,
    now: datetime | None = None,
) -> CurrencyRouteDecision:
    code = opportunity.natural_currency.upper()
    net_native = opportunity.gross_native - opportunity.native_fees
    if net_native <= 0:
        return CurrencyRouteDecision(
            CurrencyRouteState.BLOCKED,
            "native net value is not positive",
            opportunity,
            None,
            None,
        )

    if code == "EUR":
        expected_net_eur = net_native - opportunity.payout_and_conversion_cost_eur
    else:
        if opportunity.fx is None or opportunity.fx.currency.upper() != code:
            return CurrencyRouteDecision(
                CurrencyRouteState.HOLD,
                "matching FX evidence is required",
                opportunity,
                None,
                None,
            )
        state = fx_state(opportunity.fx, now=now)
        if state is not CurrencyRouteState.PASS:
            return CurrencyRouteDecision(
                state,
                "FX evidence is stale, missing, or temporally invalid",
                opportunity,
                None,
                None,
            )
        expected_net_eur = net_native * opportunity.fx.eur_per_unit - opportunity.payout_and_conversion_cost_eur

    if expected_net_eur <= 0:
        return CurrencyRouteDecision(
            CurrencyRouteState.BLOCKED,
            "fee-aware normalized net value is not positive",
            opportunity,
            expected_net_eur,
            Decimal("0"),
        )

    hourly = (
        expected_net_eur
        * opportunity.acceptance_probability
        * opportunity.payment_probability
        / opportunity.expected_minutes
        * Decimal("60")
    )
    return CurrencyRouteDecision(
        CurrencyRouteState.PASS,
        "opportunity normalized to EUR comparison plane with fresh FX and fees",
        opportunity,
        expected_net_eur,
        hourly,
    )


def route_currency_opportunities(
    opportunities: Iterable[CurrencyOpportunity],
    *,
    now: datetime | None = None,
) -> tuple[CurrencyRouteDecision, ...]:
    decisions = [evaluate_currency_opportunity(item, now=now) for item in opportunities]
    eligible = [decision for decision in decisions if decision.state is CurrencyRouteState.PASS]
    return tuple(
        sorted(
            eligible,
            key=lambda decision: (
                -(decision.risk_adjusted_eur_per_hour or Decimal("0")),
                decision.opportunity.opportunity_id,
            ),
        )
    )

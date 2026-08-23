from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


MONEY_QUANTUM = Decimal("0.0001")
RATE_QUANTUM = Decimal("0.0001")


class MicroEarningState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class MicroEarningOpportunity:
    gross_value: Decimal | None
    currency: str | None
    estimated_minutes: Decimal | None
    acceptance_probability: Decimal | None
    payment_probability: Decimal | None
    expected_fees: Decimal | None
    expected_taxes: Decimal | None
    expected_other_cost: Decimal | None
    worker_side_upfront_cost: Decimal | None
    fx_to_eur: Decimal | None = None
    eur_to_usd: Decimal | None = None
    independent_external_counterparty: bool | None = None

    def __post_init__(self) -> None:
        for name in (
            "gross_value",
            "estimated_minutes",
            "acceptance_probability",
            "payment_probability",
            "expected_fees",
            "expected_taxes",
            "expected_other_cost",
            "worker_side_upfront_cost",
            "fx_to_eur",
            "eur_to_usd",
        ):
            value = getattr(self, name)
            if value is not None and value < Decimal("0"):
                raise ValueError(f"{name} cannot be negative")

        for name in ("acceptance_probability", "payment_probability"):
            value = getattr(self, name)
            if value is not None and value > Decimal("1"):
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class MicroEarningAssessment:
    state: MicroEarningState
    reason: str
    gross_eur: Decimal | None
    gross_usd: Decimal | None
    expected_total_cost_eur: Decimal | None
    expected_total_cost_usd: Decimal | None
    expected_net_eur: Decimal | None
    expected_net_usd: Decimal | None
    risk_adjusted_net_eur: Decimal | None
    risk_adjusted_net_usd: Decimal | None
    expected_net_per_hour_eur: Decimal | None
    expected_net_per_hour_usd: Decimal | None

    @property
    def selectable(self) -> bool:
        return self.state is MicroEarningState.PASS


def assess_micro_earning(opportunity: MicroEarningOpportunity) -> MicroEarningAssessment:
    """Evaluate a discovered opportunity in both EUR and USD without authorizing external action."""
    if opportunity.independent_external_counterparty is False:
        return _blocked("independent external counterparty is required")
    if opportunity.independent_external_counterparty is None:
        return _hold("counterparty independence is unverified")

    if opportunity.worker_side_upfront_cost is None:
        return _hold("exact worker-side upfront cost is unverified")
    if opportunity.worker_side_upfront_cost != Decimal("0"):
        return _blocked("worker-side upfront capital must be exactly zero")

    required = {
        "gross value": opportunity.gross_value,
        "estimated execution time": opportunity.estimated_minutes,
        "acceptance probability": opportunity.acceptance_probability,
        "payment probability": opportunity.payment_probability,
        "expected fees": opportunity.expected_fees,
        "expected taxes": opportunity.expected_taxes,
        "expected other cost": opportunity.expected_other_cost,
        "EUR/USD FX rate": opportunity.eur_to_usd,
    }
    unknown = next((name for name, value in required.items() if value is None), None)
    if unknown is not None:
        return _hold(f"{unknown} is unverified")

    assert opportunity.gross_value is not None
    assert opportunity.estimated_minutes is not None
    assert opportunity.acceptance_probability is not None
    assert opportunity.payment_probability is not None
    assert opportunity.expected_fees is not None
    assert opportunity.expected_taxes is not None
    assert opportunity.expected_other_cost is not None
    assert opportunity.eur_to_usd is not None

    if opportunity.gross_value <= Decimal("0"):
        return _blocked("gross value must be positive")
    if opportunity.estimated_minutes <= Decimal("0"):
        return _blocked("estimated execution time must be positive")
    if opportunity.eur_to_usd <= Decimal("0"):
        return _blocked("EUR/USD FX rate must be positive")

    currency = (opportunity.currency or "").strip().upper()
    if not currency:
        return _hold("currency is unverified")

    if currency == "EUR":
        fx_to_eur = Decimal("1")
    elif currency == "USD":
        fx_to_eur = Decimal("1") / opportunity.eur_to_usd
    else:
        if opportunity.fx_to_eur is None:
            return _hold("FX rate to EUR is unverified")
        if opportunity.fx_to_eur <= Decimal("0"):
            return _blocked("FX rate to EUR must be positive")
        fx_to_eur = opportunity.fx_to_eur

    total_cost_native = opportunity.expected_fees + opportunity.expected_taxes + opportunity.expected_other_cost
    gross_eur = _money(opportunity.gross_value * fx_to_eur)
    total_cost_eur = _money(total_cost_native * fx_to_eur)
    net_eur = _money(gross_eur - total_cost_eur)

    gross_usd = _money(gross_eur * opportunity.eur_to_usd)
    total_cost_usd = _money(total_cost_eur * opportunity.eur_to_usd)
    net_usd = _money(net_eur * opportunity.eur_to_usd)

    if net_eur <= Decimal("0"):
        return MicroEarningAssessment(
            MicroEarningState.BLOCKED,
            "expected net value is not positive",
            gross_eur, gross_usd,
            total_cost_eur, total_cost_usd,
            net_eur, net_usd,
            Decimal("0.0000"), Decimal("0.0000"),
            Decimal("0.0000"), Decimal("0.0000"),
        )

    risk_adjusted_net_eur = _money(
        net_eur * opportunity.acceptance_probability * opportunity.payment_probability
    )
    risk_adjusted_net_usd = _money(risk_adjusted_net_eur * opportunity.eur_to_usd)
    expected_per_hour_eur = _rate(
        risk_adjusted_net_eur / opportunity.estimated_minutes * Decimal("60")
    )
    expected_per_hour_usd = _rate(
        risk_adjusted_net_usd / opportunity.estimated_minutes * Decimal("60")
    )

    if risk_adjusted_net_eur <= Decimal("0"):
        return MicroEarningAssessment(
            MicroEarningState.BLOCKED,
            "risk-adjusted expected net value is not positive",
            gross_eur, gross_usd,
            total_cost_eur, total_cost_usd,
            net_eur, net_usd,
            risk_adjusted_net_eur, risk_adjusted_net_usd,
            expected_per_hour_eur, expected_per_hour_usd,
        )

    return MicroEarningAssessment(
        MicroEarningState.PASS,
        "economic data verified; opportunity may enter later selection gates",
        gross_eur, gross_usd,
        total_cost_eur, total_cost_usd,
        net_eur, net_usd,
        risk_adjusted_net_eur, risk_adjusted_net_usd,
        expected_per_hour_eur, expected_per_hour_usd,
    )


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def _rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP)


def _hold(reason: str) -> MicroEarningAssessment:
    return MicroEarningAssessment(MicroEarningState.HOLD, reason, None, None, None, None, None, None, None, None, None, None)


def _blocked(reason: str) -> MicroEarningAssessment:
    return MicroEarningAssessment(MicroEarningState.BLOCKED, reason, None, None, None, None, None, None, None, None, None, None)

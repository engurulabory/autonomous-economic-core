from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ShadowDecision(str, Enum):
    QUALIFIED = "QUALIFIED"
    HOLD = "HOLD"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ShadowOpportunity:
    source: str
    external_id: str
    title: str
    reward_eur: Decimal
    estimated_minutes: Decimal
    source_claims_open: bool
    canonical_open: bool | None
    automation_policy_verified: bool
    zero_capital_required: bool
    payout_path_known: bool
    external_counterparty: bool = True

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.external_id.strip() or not self.title.strip():
            raise ValueError("source, external_id and title are required")
        if self.reward_eur < 0 or self.estimated_minutes < 0:
            raise ValueError("reward_eur and estimated_minutes cannot be negative")


@dataclass(frozen=True)
class ShadowAssessment:
    decision: ShadowDecision
    reason: str
    expected_gross_eur: Decimal
    expected_net_eur: Decimal
    expected_net_per_hour_eur: Decimal


def assess_shadow(opportunity: ShadowOpportunity) -> ShadowAssessment:
    """Fail-closed economic preflight. No external action is performed."""

    if not opportunity.external_counterparty:
        return ShadowAssessment(
            ShadowDecision.REJECTED,
            "no independent external counterparty",
            Decimal("0"), Decimal("0"), Decimal("0"),
        )

    if not opportunity.zero_capital_required:
        return ShadowAssessment(
            ShadowDecision.REJECTED,
            "opportunity requires capital outlay",
            Decimal("0"), Decimal("0"), Decimal("0"),
        )

    if not opportunity.source_claims_open:
        return ShadowAssessment(
            ShadowDecision.REJECTED,
            "source does not claim opportunity is open",
            Decimal("0"), Decimal("0"), Decimal("0"),
        )

    if opportunity.canonical_open is False:
        return ShadowAssessment(
            ShadowDecision.REJECTED,
            "canonical source shows opportunity is closed/stale",
            Decimal("0"), Decimal("0"), Decimal("0"),
        )

    if opportunity.canonical_open is None:
        return ShadowAssessment(
            ShadowDecision.HOLD,
            "canonical freshness has not been verified",
            Decimal("0"), Decimal("0"), Decimal("0"),
        )

    if not opportunity.automation_policy_verified:
        return ShadowAssessment(
            ShadowDecision.HOLD,
            "automation policy is not explicitly verified",
            opportunity.reward_eur,
            opportunity.reward_eur,
            _per_hour(opportunity.reward_eur, opportunity.estimated_minutes),
        )

    if not opportunity.payout_path_known:
        return ShadowAssessment(
            ShadowDecision.HOLD,
            "payout path is not verified",
            opportunity.reward_eur,
            opportunity.reward_eur,
            _per_hour(opportunity.reward_eur, opportunity.estimated_minutes),
        )

    return ShadowAssessment(
        ShadowDecision.QUALIFIED,
        "shadow qualification passed; execution still requires authority/policy gate",
        opportunity.reward_eur,
        opportunity.reward_eur,
        _per_hour(opportunity.reward_eur, opportunity.estimated_minutes),
    )


def _per_hour(net_eur: Decimal, minutes: Decimal) -> Decimal:
    if minutes <= 0:
        return Decimal("0")
    return (net_eur / minutes * Decimal("60")).quantize(Decimal("0.0001"))

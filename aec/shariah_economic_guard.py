from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ShariahEconomicState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ShariahEconomicOpportunity:
    """Policy facts for one economic opportunity.

    This guard is a conservative operational policy layer, not a fatwa engine.
    Unknown material facts fail closed to HOLD; explicit prohibited conditions
    fail closed to BLOCKED.
    """

    opportunity_id: str
    work_is_permissible: bool | None
    real_value_or_service: bool | None
    compensation_is_clear: bool | None
    contains_riba: bool | None
    contains_maysir: bool | None
    contains_excessive_gharar: bool | None
    contains_fraud_or_deception: bool | None
    ownership_or_entitlement_is_clear: bool | None
    payment_rail_is_approved: bool | None
    requires_human_financial_authority: bool = False


@dataclass(frozen=True)
class ShariahEconomicAssessment:
    opportunity_id: str
    state: ShariahEconomicState
    reason: str
    evidence_needed: tuple[str, ...] = ()
    human_threshold_required: bool = False

    @property
    def selectable(self) -> bool:
        return self.state is ShariahEconomicState.PASS


def assess_shariah_economic_guard(
    opportunity: ShariahEconomicOpportunity,
) -> ShariahEconomicAssessment:
    """Classify one revenue opportunity as PASS / HOLD / BLOCKED.

    Ordering is intentional:
    1. Explicitly prohibited conditions block immediately.
    2. Missing material facts hold.
    3. Human financial authority never becomes autonomous authorization.
    4. Only verified permissible opportunities pass to later economic gates.
    """

    if opportunity.work_is_permissible is False:
        return _blocked(opportunity, "underlying work is prohibited by policy")
    if opportunity.real_value_or_service is False:
        return _blocked(opportunity, "no verified real value, service, or legitimate consideration")
    if opportunity.compensation_is_clear is False:
        return _blocked(opportunity, "compensation terms are materially unclear")
    if opportunity.contains_riba is True:
        return _blocked(opportunity, "riba / interest-bearing economic structure detected")
    if opportunity.contains_maysir is True:
        return _blocked(opportunity, "maysir / gambling-like payoff structure detected")
    if opportunity.contains_excessive_gharar is True:
        return _blocked(opportunity, "excessive gharar / material contractual uncertainty detected")
    if opportunity.contains_fraud_or_deception is True:
        return _blocked(opportunity, "fraud, deception, manipulation, or unjust enrichment detected")
    if opportunity.ownership_or_entitlement_is_clear is False:
        return _blocked(opportunity, "ownership or entitlement to payment is not legitimate")
    if opportunity.payment_rail_is_approved is False:
        return _blocked(opportunity, "payment rail is not approved by policy")

    unknowns: list[str] = []
    required_facts = {
        "work permissibility": opportunity.work_is_permissible,
        "real value or service": opportunity.real_value_or_service,
        "compensation clarity": opportunity.compensation_is_clear,
        "riba exposure": opportunity.contains_riba,
        "maysir exposure": opportunity.contains_maysir,
        "excessive gharar exposure": opportunity.contains_excessive_gharar,
        "fraud or deception exposure": opportunity.contains_fraud_or_deception,
        "ownership or entitlement": opportunity.ownership_or_entitlement_is_clear,
        "payment rail approval": opportunity.payment_rail_is_approved,
    }
    for label, value in required_facts.items():
        if value is None:
            unknowns.append(label)

    if unknowns:
        return ShariahEconomicAssessment(
            opportunity_id=opportunity.opportunity_id,
            state=ShariahEconomicState.HOLD,
            reason="material Shariah-economic facts remain unverified",
            evidence_needed=tuple(unknowns),
            human_threshold_required=opportunity.requires_human_financial_authority,
        )

    if opportunity.requires_human_financial_authority:
        return ShariahEconomicAssessment(
            opportunity_id=opportunity.opportunity_id,
            state=ShariahEconomicState.HOLD,
            reason="Human Threshold required for financial authority or irreversible settlement action",
            evidence_needed=("explicit human authorization",),
            human_threshold_required=True,
        )

    return ShariahEconomicAssessment(
        opportunity_id=opportunity.opportunity_id,
        state=ShariahEconomicState.PASS,
        reason="verified permissible work and payment structure may enter later economic selection gates",
    )


def classify_revenue_doors(
    opportunities: Iterable[ShariahEconomicOpportunity],
) -> tuple[ShariahEconomicAssessment, ...]:
    """Apply the permanent guard uniformly to a revenue-door candidate set."""
    return tuple(assess_shariah_economic_guard(opportunity) for opportunity in opportunities)


def _blocked(
    opportunity: ShariahEconomicOpportunity,
    reason: str,
) -> ShariahEconomicAssessment:
    return ShariahEconomicAssessment(
        opportunity_id=opportunity.opportunity_id,
        state=ShariahEconomicState.BLOCKED,
        reason=reason,
        human_threshold_required=opportunity.requires_human_financial_authority,
    )

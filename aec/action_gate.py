from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ActionDecision(str, Enum):
    ALLOW = "ALLOW"
    HOLD = "HOLD"
    REJECT = "REJECT"


@dataclass(frozen=True)
class PendingEconomicAction:
    action: str
    available: bool
    requires_payment: bool | None
    payment_amount: Decimal | None
    currency: str | None = None
    network: str | None = None
    deposit_required: bool | None = None
    deposit_amount: Decimal | None = None
    irreversible: bool = False
    money_moving: bool = False
    public_commitment: bool = False


@dataclass(frozen=True)
class ActionAssessment:
    decision: ActionDecision
    reason: str
    human_threshold_required: bool


def assess_zero_capital_action(action: PendingEconomicAction) -> ActionAssessment:
    """Evaluate the exact intended action for the locked EUR 0.00 first-proof rule."""

    if not action.action.strip():
        raise ValueError("action is required")

    if not action.available:
        return ActionAssessment(ActionDecision.REJECT, "action is not currently available", False)

    if action.requires_payment is None:
        return ActionAssessment(ActionDecision.HOLD, "payment requirement is unknown", False)

    if action.deposit_required is None:
        return ActionAssessment(ActionDecision.HOLD, "deposit requirement is unknown", False)

    if action.requires_payment:
        if action.payment_amount is None:
            return ActionAssessment(ActionDecision.HOLD, "payment amount is unknown", False)
        if action.payment_amount > 0:
            return ActionAssessment(ActionDecision.REJECT, "positive worker payment violates zero-capital rule", False)

    if action.deposit_required:
        if action.deposit_amount is None:
            return ActionAssessment(ActionDecision.HOLD, "deposit amount is unknown", False)
        if action.deposit_amount > 0:
            return ActionAssessment(ActionDecision.REJECT, "positive deposit/bond violates zero-capital rule", False)

    threshold = action.irreversible or action.money_moving or action.public_commitment
    return ActionAssessment(
        ActionDecision.ALLOW,
        "exact action is available and requires no worker capital",
        threshold,
    )

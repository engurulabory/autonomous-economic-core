from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from aec.action_gate import (
    ActionAssessment,
    PendingEconomicAction,
    assess_zero_capital_action,
)
from aec.market_evidence import MarketEvidenceRecord
from aec.opportunity_integrity import (
    IntegrityAssessment,
    OpportunityEvidence,
    OpportunityScore,
    assess_opportunity,
)
from connectors.taskmarket import TaskmarketTask


TASKMARKET_SOURCE = "Taskmarket"
TASKMARKET_NETWORK = "Base Mainnet"
TASKMARKET_CURRENCY = "USDC"
TASKMARKET_DISCOVERY_URL = "https://taskmarket.dev/"
TASKMARKET_TASK_URL = "https://taskmarket.dev/tasks/{task_id}"


@dataclass(frozen=True)
class TaskmarketCanonicalAssessment:
    task: TaskmarketTask
    market_evidence: MarketEvidenceRecord
    exact_action: PendingEconomicAction
    action_assessment: ActionAssessment
    opportunity_evidence: OpportunityEvidence
    score: OpportunityScore
    integrity_assessment: IntegrityAssessment


def assess_taskmarket_bounty(
    task: TaskmarketTask,
    *,
    country_eligible: bool | None,
    observed_at: datetime | None = None,
    task_simplicity_score: int = 5,
    payout_speed_score: int = 4,
) -> TaskmarketCanonicalAssessment:
    """Map one canonical Taskmarket bounty read into AEC's hard gates.

    This adapter is intentionally limited to the first-proof path: an open bounty whose
    exact worker action is `submit`. It performs no external write, signing, payment, or
    legal acceptance.
    """

    if task.mode != "bounty":
        raise ValueError("first-proof Taskmarket adapter only accepts bounty mode")
    if not 0 <= task_simplicity_score <= 5:
        raise ValueError("task_simplicity_score must be between 0 and 5")
    if not 0 <= payout_speed_score <= 5:
        raise ValueError("payout_speed_score must be between 0 and 5")

    observed = observed_at or datetime.now(timezone.utc)
    if observed.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")

    submit = _worker_action(task, "submit")
    exact_action = _map_pending_action(task, submit, "submit")
    action_assessment = assess_zero_capital_action(exact_action)

    funded = bool(task.escrow_tx_hash) and task.reward_usdc > 0
    canonical_open = task.status == "open" and task.submission_window_open is True
    claimable = canonical_open and submit is not None
    action_zero_capital = action_assessment.decision.value == "ALLOW"

    opportunity_evidence = OpportunityEvidence(
        source_open=task.status == "open",
        canonical_open=canonical_open,
        funded=funded,
        claimable=claimable,
        zero_capital=action_zero_capital,
        automation_allowed=True,  # first-party Taskmarket docs/CLI are explicitly agent-oriented
        payout_path_known=bool(task.escrow_tx_hash) and task.net_reward_usdc is not None,
        acceptance_path_known=True,  # bounty requester accepts one submitted deliverable
        country_eligible=country_eligible,
        upfront_cost_eur=Decimal("0"),
        submission_cost_eur=_action_cost_usdc(exact_action),
        wallet_receipt_supported=True,
        bank_receipt_supported=False,
        human_identity_required=True,
        kyc_required=False,
        public_submission_required=True,
        untrusted_texts=(task.description,),
    )

    score = OpportunityScore(
        funding_certainty=25 if funded else 0,
        zero_capital_purity=20 if action_zero_capital else 0,
        claimability=15 if claimable else 0,
        acceptance_clarity=15,
        payout_clarity=10 if opportunity_evidence.payout_path_known else 0,
        agent_compatibility=5,
        task_simplicity=task_simplicity_score,
        payout_speed=payout_speed_score,
    )
    integrity = assess_opportunity(opportunity_evidence, score)

    market_evidence = MarketEvidenceRecord(
        source_name=TASKMARKET_SOURCE,
        discovery_url=TASKMARKET_DISCOVERY_URL,
        canonical_url=TASKMARKET_TASK_URL.format(task_id=task.task_id),
        observed_at=observed,
        external_id=task.task_id,
        reward_amount=task.net_reward_usdc if task.net_reward_usdc is not None else task.reward_usdc,
        reward_currency=TASKMARKET_CURRENCY,
        status=task.status,
        funded=funded,
        claimable=claimable,
        automation_allowed=True,
        country_eligible=country_eligible,
        exact_action="submit",
        exact_action_cost=_action_cost_usdc(exact_action),
        exact_action_currency=TASKMARKET_CURRENCY,
        acceptance_path="requester accepts selected bounty submission; canonical completion/award is settlement evidence",
        payout_path="Taskmarket on-chain USDC worker payment; award settlementTxHash is wallet receipt evidence",
        available_slots=None,
        submission_count=_optional_nonnegative_int(task.raw.get("submissionCount")),
        attempt_count=_optional_nonnegative_int(task.raw.get("pitchCount")),
        deadline_at=_parse_iso(task.expiry_time),
        evidence_hash=None,
    )

    return TaskmarketCanonicalAssessment(
        task=task,
        market_evidence=market_evidence,
        exact_action=exact_action,
        action_assessment=action_assessment,
        opportunity_evidence=opportunity_evidence,
        score=score,
        integrity_assessment=integrity,
    )


def _worker_action(task: TaskmarketTask, action_name: str) -> dict[str, Any] | None:
    for action in task.pending_actions:
        if action.get("action") == action_name and action.get("role") in {"worker", "anyone"}:
            return action
    return None


def _map_pending_action(
    task: TaskmarketTask,
    action: dict[str, Any] | None,
    action_name: str,
) -> PendingEconomicAction:
    if action is None:
        return PendingEconomicAction(
            action=action_name,
            available=False,
            requires_payment=None,
            payment_amount=None,
            currency=TASKMARKET_CURRENCY,
            network=TASKMARKET_NETWORK,
            deposit_required=False,
            deposit_amount=Decimal("0"),
            public_commitment=True,
        )

    requires_payment = action.get("requiresPayment")
    if not isinstance(requires_payment, bool):
        requires_payment = None

    payment_amount = _optional_base_units_usdc(action.get("paymentAmount"))

    return PendingEconomicAction(
        action=action_name,
        available=task.submission_window_open is True,
        requires_payment=requires_payment,
        payment_amount=payment_amount,
        currency=TASKMARKET_CURRENCY,
        network=TASKMARKET_NETWORK,
        # Bounty-mode `submit` has no claim bond. Claim-mode deposits are deliberately
        # outside this first-proof adapter and must be evaluated by a separate mapper.
        deposit_required=False,
        deposit_amount=Decimal("0"),
        irreversible=False,
        money_moving=False,
        public_commitment=True,
    )


def _action_cost_usdc(action: PendingEconomicAction) -> Decimal:
    if action.requires_payment is not False:
        return action.payment_amount if action.payment_amount is not None else Decimal("0")
    return Decimal("0")


def _optional_base_units_usdc(value: Any) -> Decimal | None:
    if value is None:
        return None
    return (Decimal(str(value)) / Decimal("1000000")).quantize(Decimal("0.000001"))


def _optional_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed

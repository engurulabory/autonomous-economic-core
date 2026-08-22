from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from aec.orchestrator import RevenueCandidate


class QualificationState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class EconomicExecutionDecision:
    state: QualificationState
    reason: str
    candidate: RevenueCandidate
    human_threshold_required: bool

    @property
    def can_enqueue_internal_work(self) -> bool:
        return self.state is QualificationState.PASS



def qualify_candidate(candidate: RevenueCandidate) -> EconomicExecutionDecision:
    """Fail-closed gate from discovery to internal execution.

    PASS here means only that AEC may create internal production work. It does not
    authorize public submission, signing, spending, KYC, payout changes, or any
    claim of earned/settled/banked revenue.
    """
    if candidate.open_now is False:
        return EconomicExecutionDecision(QualificationState.BLOCKED, "opportunity is closed", candidate, False)
    if candidate.open_now is None:
        return EconomicExecutionDecision(QualificationState.HOLD, "open state is unverified", candidate, False)

    if candidate.zero_capital is False:
        return EconomicExecutionDecision(QualificationState.BLOCKED, "positive worker-side cost is not allowed", candidate, False)
    if candidate.zero_capital is None:
        return EconomicExecutionDecision(QualificationState.HOLD, "exact action cost is unverified", candidate, False)

    if candidate.agent_allowed is False:
        return EconomicExecutionDecision(QualificationState.BLOCKED, "agent execution is not allowed", candidate, False)
    if candidate.agent_allowed is None:
        return EconomicExecutionDecision(QualificationState.HOLD, "agent policy is unverified", candidate, False)

    if candidate.reward_amount is None or candidate.reward_currency is None:
        return EconomicExecutionDecision(QualificationState.HOLD, "reward value or currency is unverified", candidate, False)
    if candidate.reward_amount <= Decimal("0"):
        return EconomicExecutionDecision(QualificationState.BLOCKED, "reward must be positive", candidate, False)

    return EconomicExecutionDecision(
        QualificationState.PASS,
        "candidate may enter controlled internal production; external write remains separately gated",
        candidate,
        candidate.human_threshold_required,
    )



def production_job_payload(candidate: RevenueCandidate, *, output_path: str, content: str) -> dict[str, object]:
    decision = qualify_candidate(candidate)
    if not decision.can_enqueue_internal_work:
        raise ValueError(f"candidate is not qualified for internal execution: {decision.state.value}: {decision.reason}")
    if not output_path.strip() or output_path.startswith("/") or ".." in output_path.split("/"):
        raise ValueError("output_path must stay inside the controlled runtime workspace")
    if not content:
        raise ValueError("content is required")

    return {
        "output_path": output_path,
        "content": content,
        "economic_context": {
            "door": candidate.door,
            "source": candidate.source,
            "external_id": candidate.external_id,
            "canonical_url": candidate.canonical_url,
            "reward_amount": str(candidate.reward_amount),
            "reward_currency": candidate.reward_currency,
            "human_threshold_required": candidate.human_threshold_required,
        },
    }

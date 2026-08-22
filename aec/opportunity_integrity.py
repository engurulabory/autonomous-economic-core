from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable


class IntegrityDecision(str, Enum):
    QUALIFIED = "QUALIFIED"
    HOLD = "HOLD"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class OpportunityEvidence:
    source_open: bool
    canonical_open: bool | None
    funded: bool | None
    claimable: bool | None
    zero_capital: bool
    automation_allowed: bool | None
    payout_path_known: bool
    acceptance_path_known: bool
    country_eligible: bool | None
    external_counterparty: bool = True
    upfront_cost_eur: Decimal = Decimal("0")
    submission_cost_eur: Decimal = Decimal("0")
    wallet_receipt_supported: bool = False
    bank_receipt_supported: bool = False
    human_identity_required: bool = False
    kyc_required: bool = False
    public_submission_required: bool = False
    untrusted_texts: tuple[str, ...] = ()


@dataclass(frozen=True)
class OpportunityScore:
    funding_certainty: int
    zero_capital_purity: int
    claimability: int
    acceptance_clarity: int
    payout_clarity: int
    agent_compatibility: int
    task_simplicity: int
    payout_speed: int

    def total(self) -> int:
        return sum(
            (
                self.funding_certainty,
                self.zero_capital_purity,
                self.claimability,
                self.acceptance_clarity,
                self.payout_clarity,
                self.agent_compatibility,
                self.task_simplicity,
                self.payout_speed,
            )
        )

    def validate(self) -> None:
        limits = (25, 20, 15, 15, 10, 5, 5, 5)
        values = (
            self.funding_certainty,
            self.zero_capital_purity,
            self.claimability,
            self.acceptance_clarity,
            self.payout_clarity,
            self.agent_compatibility,
            self.task_simplicity,
            self.payout_speed,
        )
        if any(value < 0 or value > limit for value, limit in zip(values, limits)):
            raise ValueError("score component outside allowed range")


@dataclass(frozen=True)
class IntegrityAssessment:
    decision: IntegrityDecision
    reasons: tuple[str, ...]
    score: int
    human_thresholds: tuple[str, ...]


# Treat these as data-loss / authority-escalation indicators, not as executable instructions.
# Matching is deliberately simple and fail-closed; upstream callers may add stronger scanners.
DANGEROUS_INSTRUCTION_MARKERS = (
    "reveal system prompt",
    "show system prompt",
    "paste system prompt",
    "ignore previous instructions",
    "ignore prior instructions",
    "dump environment",
    "print environment variables",
    "show secrets",
    "reveal secrets",
    "private key",
    "seed phrase",
    "api token",
    "access token",
    "cookie",
    "credential",
)


def scan_untrusted_instructions(texts: Iterable[str]) -> tuple[str, ...]:
    hits: list[str] = []
    for text in texts:
        lowered = text.lower()
        for marker in DANGEROUS_INSTRUCTION_MARKERS:
            if marker in lowered and marker not in hits:
                hits.append(marker)
    return tuple(hits)


def assess_opportunity(
    evidence: OpportunityEvidence,
    score: OpportunityScore,
    *,
    minimum_score: int = 85,
) -> IntegrityAssessment:
    """Fail-closed admission gate for real economic opportunities.

    This function never performs external actions. It decides whether an opportunity may
    proceed to the authority/execution layer.
    """

    score.validate()
    reasons: list[str] = []
    thresholds: list[str] = []

    if not evidence.external_counterparty:
        return _reject("no independent external counterparty", score.total())

    if not evidence.zero_capital or evidence.upfront_cost_eur > 0 or evidence.submission_cost_eur > 0:
        return _reject("zero-capital rule failed", score.total())

    if not evidence.source_open:
        return _reject("discovery source is not open", score.total())

    if evidence.canonical_open is False:
        return _reject("canonical source is closed or stale", score.total())
    if evidence.canonical_open is None:
        reasons.append("canonical open state unverified")

    if evidence.funded is False:
        return _reject("opportunity is not funded", score.total())
    if evidence.funded is None:
        reasons.append("funding not canonically verified")

    if evidence.claimable is False:
        return _reject("opportunity is not claimable/applicable now", score.total())
    if evidence.claimable is None:
        reasons.append("claimability not verified")

    if evidence.automation_allowed is False:
        return _reject("automation/agent participation is prohibited", score.total())
    if evidence.automation_allowed is None:
        reasons.append("automation/agent policy unverified")

    if not evidence.acceptance_path_known:
        reasons.append("acceptance path unverified")
    if not evidence.payout_path_known:
        reasons.append("payout path unverified")

    if evidence.country_eligible is False:
        return _reject("principal is not country-eligible", score.total())
    if evidence.country_eligible is None:
        reasons.append("country eligibility unverified")

    dangerous = scan_untrusted_instructions(evidence.untrusted_texts)
    if dangerous:
        return _reject(
            "adversarial instruction / credential-exfiltration marker detected: "
            + ", ".join(dangerous),
            score.total(),
        )

    if evidence.human_identity_required:
        thresholds.append("identity/account authority")
    if evidence.kyc_required:
        thresholds.append("KYC/tax/banking authority")
    if evidence.public_submission_required:
        thresholds.append("public external submission")

    if score.total() < minimum_score:
        return _reject(f"score below qualification threshold ({score.total()} < {minimum_score})", score.total())

    if reasons:
        return IntegrityAssessment(
            decision=IntegrityDecision.HOLD,
            reasons=tuple(reasons),
            score=score.total(),
            human_thresholds=tuple(thresholds),
        )

    return IntegrityAssessment(
        decision=IntegrityDecision.QUALIFIED,
        reasons=("canonical market gate passed",),
        score=score.total(),
        human_thresholds=tuple(thresholds),
    )


def _reject(reason: str, score: int) -> IntegrityAssessment:
    return IntegrityAssessment(
        decision=IntegrityDecision.REJECTED,
        reasons=(reason,),
        score=score,
        human_thresholds=(),
    )

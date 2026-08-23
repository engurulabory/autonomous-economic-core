from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Iterable

from aec.micro_earning_policy import MicroEarningAssessment, MicroEarningState


class FieldState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


# P2 — Smallest-Profitable-Work Selector™
@dataclass(frozen=True)
class SelectableOpportunity:
    opportunity_id: str
    assessment: MicroEarningAssessment
    estimated_minutes: Decimal
    risk_score: Decimal
    human_threshold_required: bool = False

    def __post_init__(self) -> None:
        if not self.opportunity_id.strip():
            raise ValueError("opportunity_id is required")
        if self.estimated_minutes <= 0:
            raise ValueError("estimated_minutes must be positive")
        if self.risk_score < 0:
            raise ValueError("risk_score cannot be negative")

    @property
    def micro_task_priority(self) -> int:
        return 1 if Decimal("0.5") <= self.estimated_minutes <= Decimal("10") else 0


def rank_smallest_profitable(opportunities: Iterable[SelectableOpportunity]) -> tuple[SelectableOpportunity, ...]:
    eligible = [
        item for item in opportunities
        if item.assessment.state is MicroEarningState.PASS
        and item.assessment.risk_adjusted_net_eur is not None
        and item.assessment.risk_adjusted_net_eur > 0
        and item.assessment.expected_net_per_hour_eur is not None
        and not item.human_threshold_required
    ]
    return tuple(sorted(
        eligible,
        key=lambda item: (
            item.risk_score,
            -item.assessment.expected_net_per_hour_eur,
            -item.micro_task_priority,
            item.estimated_minutes,
            item.opportunity_id,
        ),
    ))


# P3 — Task Decomposition Core™
@dataclass(frozen=True)
class DecompositionRequest:
    task_id: str
    task_class: str
    units: tuple[str, ...]
    platform_allows_decomposition: bool | None
    acceptance_contract_allows_decomposition: bool | None


@dataclass(frozen=True)
class DecompositionResult:
    state: FieldState
    reason: str
    subtasks: tuple[str, ...] = ()


def decompose_task(request: DecompositionRequest) -> DecompositionResult:
    if not request.task_id.strip() or not request.task_class.strip():
        return DecompositionResult(FieldState.BLOCKED, "task identity is invalid")
    if request.platform_allows_decomposition is None or request.acceptance_contract_allows_decomposition is None:
        return DecompositionResult(FieldState.HOLD, "decomposition permission is unverified")
    if not request.platform_allows_decomposition or not request.acceptance_contract_allows_decomposition:
        return DecompositionResult(FieldState.BLOCKED, "decomposition is not permitted")
    clean = tuple(unit.strip() for unit in request.units if unit.strip())
    if not clean:
        return DecompositionResult(FieldState.HOLD, "no independently verifiable work units supplied")
    subtasks = tuple(f"{request.task_id}:{index + 1}:{request.task_class}:{unit}" for index, unit in enumerate(clean))
    return DecompositionResult(FieldState.PASS, "task decomposed into verifiable units", subtasks)


# P4 — Parallel Worker Economy™
@dataclass(frozen=True)
class ParallelCapacity:
    queue_depth: int
    healthy_workers: int
    provider_limit: int
    configured_max: int
    human_threshold_jobs: int = 0


def bounded_concurrency(capacity: ParallelCapacity) -> int:
    if min(capacity.queue_depth, capacity.healthy_workers, capacity.provider_limit, capacity.configured_max) < 0:
        raise ValueError("capacity values cannot be negative")
    executable = max(0, capacity.queue_depth - max(0, capacity.human_threshold_jobs))
    return min(executable, capacity.healthy_workers, capacity.provider_limit, capacity.configured_max)


# P5 — Economic Learning Ledger™ contract
@dataclass(frozen=True)
class EconomicEvidenceRecord:
    job_id: str
    discovered_at: datetime
    qualified_at: datetime | None = None
    started_at: datetime | None = None
    first_output_at: datetime | None = None
    accepted_at: datetime | None = None
    settled_at: datetime | None = None
    banked_at: datetime | None = None
    estimated_duration_minutes: Decimal | None = None
    actual_duration_minutes: Decimal | None = None
    expected_revenue_eur: Decimal | None = None
    actual_gross_eur: Decimal | None = None
    fees_taxes_cost_eur: Decimal | None = None
    actual_net_eur: Decimal | None = None
    expected_net_per_hour_eur: Decimal | None = None
    realized_net_per_hour_eur: Decimal | None = None
    rejection_count: int = 0
    revision_count: int = 0
    payment_latency_minutes: Decimal | None = None
    revenue_door: str = ""
    source: str = ""
    worker_type: str = ""

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("job_id is required")
        if self.rejection_count < 0 or self.revision_count < 0:
            raise ValueError("counts cannot be negative")

    @property
    def banked_verified(self) -> bool:
        return self.banked_at is not None and self.actual_net_eur is not None


class EconomicLearningLedger:
    def __init__(self) -> None:
        self._records: dict[str, EconomicEvidenceRecord] = {}

    def append(self, record: EconomicEvidenceRecord) -> None:
        if record.job_id in self._records:
            raise ValueError("duplicate economic evidence record")
        self._records[record.job_id] = record

    def records(self) -> tuple[EconomicEvidenceRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


# P6 — Revenue Door Ranking™
@dataclass(frozen=True)
class DoorPerformance:
    door: str
    realized_net_per_hour_eur: Decimal
    acceptance_rate: Decimal
    payment_reliability: Decimal
    payment_latency_minutes: Decimal
    opportunity_frequency_per_hour: Decimal
    risk_score: Decimal

    def score(self) -> Decimal:
        latency_factor = Decimal("1") / (Decimal("1") + max(Decimal("0"), self.payment_latency_minutes) / Decimal("60"))
        risk_factor = Decimal("1") / (Decimal("1") + max(Decimal("0"), self.risk_score))
        return (
            self.realized_net_per_hour_eur
            * self.acceptance_rate
            * self.payment_reliability
            * max(Decimal("0"), self.opportunity_frequency_per_hour)
            * latency_factor
            * risk_factor
        )


def rank_revenue_doors(doors: Iterable[DoorPerformance]) -> tuple[DoorPerformance, ...]:
    return tuple(sorted(doors, key=lambda item: (-item.score(), item.door)))


# P7 — KârMatik™ Operating Loop
class KarMatikStage(str, Enum):
    WAKE = "WAKE"
    DISCOVER = "DISCOVER"
    VERIFY = "VERIFY"
    QUALIFY = "QUALIFY"
    ESTIMATE = "ESTIMATE"
    SELECT = "SELECT"
    EXECUTE = "EXECUTE"
    DONECHECK = "DONECHECK"
    DELIVER = "DELIVER"
    ACCEPTANCE = "ACCEPTANCE"
    SETTLEMENT = "SETTLEMENT"
    BANKED_VALUE = "BANKED_VALUE"
    LEARN = "LEARN"
    REPEAT = "REPEAT"


_KARMATIK_ORDER = tuple(KarMatikStage)


def next_karmatik_stage(stage: KarMatikStage) -> KarMatikStage:
    index = _KARMATIK_ORDER.index(stage)
    return _KARMATIK_ORDER[(index + 1) % len(_KARMATIK_ORDER)]


# P8 — Economic Acceptance Ladder™
@dataclass(frozen=True)
class AcceptanceLevel:
    name: str
    minimum_rate_eur_per_hour: Decimal | None
    minimum_samples: int
    minimum_active_hours: Decimal
    requires_positive_banked_value: bool = True


DEFAULT_ACCEPTANCE_LEVELS = (
    AcceptanceLevel("ONE_CENT", None, 1, Decimal("0")),
    AcceptanceLevel("EUR_0_05_H", Decimal("0.05"), 5, Decimal("1")),
    AcceptanceLevel("EUR_0_25_H", Decimal("0.25"), 5, Decimal("1")),
    AcceptanceLevel("EUR_1_H", Decimal("1"), 10, Decimal("4")),
    AcceptanceLevel("EUR_2_H", Decimal("2"), 20, Decimal("8")),
    AcceptanceLevel("EUR_5_10_H_STRETCH", Decimal("5"), 30, Decimal("24")),
)


@dataclass(frozen=True)
class AcceptanceWindow:
    banked_net_eur: Decimal
    realized_net_per_hour_eur: Decimal
    independent_samples: int
    active_hours: Decimal


def evaluate_acceptance_level(window: AcceptanceWindow, level: AcceptanceLevel) -> FieldState:
    if level.requires_positive_banked_value and window.banked_net_eur <= 0:
        return FieldState.HOLD
    if level.name == "ONE_CENT":
        return FieldState.PASS if window.banked_net_eur >= Decimal("0.01") and window.independent_samples >= 1 else FieldState.HOLD
    if window.independent_samples < level.minimum_samples or window.active_hours < level.minimum_active_hours:
        return FieldState.HOLD
    if level.minimum_rate_eur_per_hour is None:
        return FieldState.HOLD
    return FieldState.PASS if window.realized_net_per_hour_eur >= level.minimum_rate_eur_per_hour else FieldState.HOLD


# P9 — Field Safety / Anti-Waste Gate™
@dataclass(frozen=True)
class FieldSafetyInput:
    pay_to_work: bool | None
    deposit_required: bool | None
    paid_bid_required: bool | None
    paid_proof_required: bool | None
    wallet_gas_risk: bool | None
    credential_request: bool | None
    automation_allowed: bool | None
    payout_clear: bool | None
    expected_net_eur: Decimal | None
    confidence: Decimal | None
    estimated_minutes: Decimal | None


@dataclass(frozen=True)
class FieldSafetyDecision:
    state: FieldState
    reason: str
    deprioritize: bool = False


def field_safety_gate(item: FieldSafetyInput) -> FieldSafetyDecision:
    hard_flags = {
        "pay-to-work": item.pay_to_work,
        "deposit": item.deposit_required,
        "paid bid": item.paid_bid_required,
        "paid proof": item.paid_proof_required,
        "wallet gas risk": item.wallet_gas_risk,
        "credential request": item.credential_request,
    }
    unknown_hard = next((name for name, value in hard_flags.items() if value is None), None)
    if unknown_hard:
        return FieldSafetyDecision(FieldState.HOLD, f"{unknown_hard} status is unverified")
    active_hard = next((name for name, value in hard_flags.items() if value), None)
    if active_hard:
        return FieldSafetyDecision(FieldState.BLOCKED, f"{active_hard} is prohibited")
    if item.automation_allowed is None or item.payout_clear is None:
        return FieldSafetyDecision(FieldState.HOLD, "automation or payout policy is unverified")
    if not item.automation_allowed:
        return FieldSafetyDecision(FieldState.BLOCKED, "automation is prohibited")
    if not item.payout_clear:
        return FieldSafetyDecision(FieldState.HOLD, "payout path is unclear")
    if item.expected_net_eur is None or item.confidence is None or item.estimated_minutes is None:
        return FieldSafetyDecision(FieldState.HOLD, "economic confidence data is incomplete")
    if item.expected_net_eur <= 0:
        return FieldSafetyDecision(FieldState.BLOCKED, "expected net value is not positive")
    deprioritize = item.confidence < Decimal("0.5") and item.estimated_minutes > Decimal("10")
    return FieldSafetyDecision(FieldState.PASS, "field safety gate passed", deprioritize)

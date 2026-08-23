from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Iterable


class ExpansionState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


# P16 — Worker Fleet & Adaptive Concurrency Core™
@dataclass(frozen=True)
class FleetWorker:
    worker_id: str
    pool: str
    capabilities: frozenset[str]
    healthy: bool
    heartbeat_at: datetime
    active_jobs: int = 0
    max_jobs: int = 1


@dataclass(frozen=True)
class FleetJob:
    job_id: str
    capability: str
    human_threshold_required: bool
    idempotency_key: str
    risk_score: Decimal = Decimal("0")


@dataclass(frozen=True)
class FleetAssignment:
    job_id: str
    worker_id: str
    pool: str


@dataclass(frozen=True)
class FleetPlan:
    state: ExpansionState
    assignments: tuple[FleetAssignment, ...]
    reason: str


def supervisor_plan(
    jobs: Iterable[FleetJob],
    workers: Iterable[FleetWorker],
    *,
    now: datetime | None = None,
    stale_after: timedelta = timedelta(minutes=10),
    global_concurrency_limit: int = 3,
) -> FleetPlan:
    if global_concurrency_limit < 1:
        return FleetPlan(ExpansionState.BLOCKED, (), "global concurrency limit must be positive")
    current = now or datetime.now(timezone.utc)
    jobs_list = list(jobs)
    keys = [job.idempotency_key for job in jobs_list]
    if len(keys) != len(set(keys)):
        return FleetPlan(ExpansionState.BLOCKED, (), "duplicate idempotency key detected")
    available = [
        worker for worker in workers
        if worker.healthy
        and current - worker.heartbeat_at <= stale_after
        and worker.active_jobs < worker.max_jobs
    ]
    assignments: list[FleetAssignment] = []
    used_slots: dict[str, int] = {worker.worker_id: worker.active_jobs for worker in available}
    for job in sorted(jobs_list, key=lambda item: (item.risk_score, item.job_id)):
        if len(assignments) >= global_concurrency_limit:
            break
        if job.human_threshold_required:
            continue
        candidates = [
            worker for worker in available
            if job.capability in worker.capabilities and used_slots[worker.worker_id] < worker.max_jobs
        ]
        if not candidates:
            continue
        worker = sorted(candidates, key=lambda item: (used_slots[item.worker_id], item.worker_id))[0]
        assignments.append(FleetAssignment(job.job_id, worker.worker_id, worker.pool))
        used_slots[worker.worker_id] += 1
    if not assignments:
        return FleetPlan(ExpansionState.HOLD, (), "no safe capability-matched assignment available")
    return FleetPlan(ExpansionState.PASS, tuple(assignments), "Supervisor produced bounded capability-matched assignments")


# P17 — Competitive Pattern Assimilation Core™
@dataclass(frozen=True)
class CompetitivePattern:
    pattern_id: str
    source: str
    observed_at: datetime
    hypothesis: str
    proprietary_copy: bool
    brand_or_design_copy: bool
    safety_pass: bool | None = None
    policy_pass: bool | None = None
    performance_pass: bool | None = None
    economic_value_pass: bool | None = None
    sandbox_tested: bool = False
    controlled_execution_measured: bool = False


@dataclass(frozen=True)
class PatternDecision:
    state: ExpansionState
    adoptable: bool
    reason: str


def evaluate_pattern(pattern: CompetitivePattern) -> PatternDecision:
    if pattern.proprietary_copy or pattern.brand_or_design_copy:
        return PatternDecision(ExpansionState.BLOCKED, False, "Anti-Copy / Originality Gate failed")
    gates = (pattern.safety_pass, pattern.policy_pass, pattern.performance_pass, pattern.economic_value_pass)
    if any(gate is None for gate in gates):
        return PatternDecision(ExpansionState.HOLD, False, "pattern evidence gates are incomplete")
    if not all(gates):
        return PatternDecision(ExpansionState.BLOCKED, False, "one or more adoption gates failed")
    if not pattern.sandbox_tested or not pattern.controlled_execution_measured:
        return PatternDecision(ExpansionState.HOLD, False, "sandbox or controlled execution evidence missing")
    return PatternDecision(ExpansionState.PASS, True, "pattern may be adopted as an original AEC implementation")


REFERENCE_SYSTEM_CLASSES = (
    "Agent Bounties",
    "Setix",
    "PlanetLoga",
    "Agent Earner / multi-market hunter",
    "x402 / agent payment infrastructure",
    "Circadian / economic-agent field examples",
)


# P18 — Agent-Native Micro-Service Revenue Core™
@dataclass(frozen=True)
class MicroServiceDefinition:
    service_id: str
    name: str
    capability: str
    canonical_priority: int | None
    machine_readable_input: bool
    machine_readable_output: bool
    acceptance_contract_defined: bool
    zero_capital: bool
    automation_policy_verified: bool | None
    expected_execution_minutes: Decimal
    price_eur: Decimal | None = None
    price_usd: Decimal | None = None


def service_qualification(service: MicroServiceDefinition) -> ExpansionState:
    if not service.service_id.strip() or not service.name.strip() or not service.capability.strip():
        return ExpansionState.BLOCKED
    if not service.zero_capital:
        return ExpansionState.BLOCKED
    if service.automation_policy_verified is None:
        return ExpansionState.HOLD
    if not service.automation_policy_verified:
        return ExpansionState.BLOCKED
    if not service.machine_readable_input or not service.machine_readable_output or not service.acceptance_contract_defined:
        return ExpansionState.HOLD
    if service.expected_execution_minutes <= 0:
        return ExpansionState.BLOCKED
    if service.price_eur is None and service.price_usd is None:
        return ExpansionState.HOLD
    if (service.price_eur is not None and service.price_eur <= 0) or (service.price_usd is not None and service.price_usd <= 0):
        return ExpansionState.BLOCKED
    return ExpansionState.PASS


MICRO_SERVICE_CATALOG = (
    MicroServiceDefinition("research-verify", "AEC Research & Verification Utility™", "research-mini", 1, True, True, True, True, True, Decimal("5"), Decimal("0.10"), Decimal("0.12")),
    MicroServiceDefinition("structured-web-extract", "AEC Structured Web Extraction Utility™", "structured-extract", 2, True, True, True, True, True, Decimal("5"), Decimal("0.10"), Decimal("0.12")),
    MicroServiceDefinition("public-signal-monitor", "AEC Public Signal Monitor™", "public-change-monitor", 3, True, True, True, True, True, Decimal("3"), Decimal("0.05"), Decimal("0.06")),
    MicroServiceDefinition("web-qa", "AEC Web QA Utility™", "web-qa", None, True, True, True, True, True, Decimal("7"), Decimal("0.15"), Decimal("0.18")),
    MicroServiceDefinition("data-clean", "AEC Structured Data Cleanup Utility™", "data-clean", None, True, True, True, True, True, Decimal("8"), Decimal("0.15"), Decimal("0.18")),
)


def canonical_micro_services() -> tuple[MicroServiceDefinition, ...]:
    return tuple(sorted((service for service in MICRO_SERVICE_CATALOG if service.canonical_priority is not None), key=lambda item: item.canonical_priority or 999))


# P19 — Payment / Payout Router™
@dataclass(frozen=True)
class PaymentRail:
    rail_id: str
    supported_revenue_doors: frozenset[str]
    supported_currencies: frozenset[str]
    total_fee_rate: Decimal
    fixed_fee_eur: Decimal
    payment_reliability: Decimal
    settlement_minutes: Decimal
    risk_score: Decimal
    policy_verified: bool | None
    available: bool | None
    human_threshold_required: bool


@dataclass(frozen=True)
class PaymentRouteRequest:
    revenue_door: str
    currency: str
    expected_gross_eur: Decimal


@dataclass(frozen=True)
class PaymentRouteDecision:
    state: ExpansionState
    rail: PaymentRail | None
    expected_net_settlement_eur: Decimal | None
    score: Decimal | None
    human_threshold_required: bool
    reason: str


def route_payment(request: PaymentRouteRequest, rails: Iterable[PaymentRail]) -> PaymentRouteDecision:
    if request.expected_gross_eur <= 0:
        return PaymentRouteDecision(ExpansionState.BLOCKED, None, None, None, False, "gross settlement value must be positive")
    candidates: list[tuple[Decimal, Decimal, PaymentRail]] = []
    saw_unknown = False
    for rail in rails:
        if request.revenue_door not in rail.supported_revenue_doors or request.currency.upper() not in rail.supported_currencies:
            continue
        if rail.available is None or rail.policy_verified is None:
            saw_unknown = True
            continue
        if not rail.available or not rail.policy_verified:
            continue
        fees = request.expected_gross_eur * rail.total_fee_rate + rail.fixed_fee_eur
        net = request.expected_gross_eur - fees
        if net <= 0:
            continue
        denominator = Decimal("1") + rail.settlement_minutes / Decimal("60") + rail.risk_score + rail.total_fee_rate
        score = net * rail.payment_reliability / denominator
        candidates.append((score, net, rail))
    if not candidates:
        state = ExpansionState.HOLD if saw_unknown else ExpansionState.BLOCKED
        return PaymentRouteDecision(state, None, None, None, False, "no verified compatible payout rail")
    score, net, rail = sorted(candidates, key=lambda item: (-item[0], item[2].rail_id))[0]
    return PaymentRouteDecision(
        ExpansionState.PASS,
        rail,
        net,
        score,
        rail.human_threshold_required,
        "verified payout rail selected; execution remains separately authorized",
    )

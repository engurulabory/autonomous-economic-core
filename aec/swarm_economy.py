from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping

from .economics import Judgment


MAX_WORKERS_PER_SWARM = 100
MAX_TOTAL_WORKER_SLOTS = 600


class SwarmKind(str, Enum):
    CODE = "CODE"
    RESEARCH = "RESEARCH"
    DATA = "DATA"
    QA = "QA"
    MONITOR = "MONITOR"
    MACHINE_PRODUCT = "MACHINE_PRODUCT"


class RevenueStage(str, Enum):
    EARNED = "EARNED"
    SETTLED = "SETTLED"
    BANKED = "BANKED"


@dataclass(frozen=True)
class EconomicGateInput:
    expected_gross_eur: Decimal
    compute_cost_eur: Decimal = Decimal("0")
    api_cost_eur: Decimal = Decimal("0")
    platform_fee_eur: Decimal = Decimal("0")
    payment_fee_eur: Decimal = Decimal("0")
    expected_failure_cost_eur: Decimal = Decimal("0")
    success_probability: Decimal = Decimal("1")
    collection_probability: Decimal = Decimal("1")
    requires_upfront_capital: bool = False
    human_threshold_required: bool = False

    def __post_init__(self) -> None:
        money_fields = (
            "expected_gross_eur",
            "compute_cost_eur",
            "api_cost_eur",
            "platform_fee_eur",
            "payment_fee_eur",
            "expected_failure_cost_eur",
        )
        for field_name in money_fields:
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} cannot be negative")
        for field_name in ("success_probability", "collection_probability"):
            value = getattr(self, field_name)
            if value < 0 or value > 1:
                raise ValueError(f"{field_name} must be between 0 and 1")


@dataclass(frozen=True)
class EconomicGateResult:
    judgment: Judgment
    expected_net_eur: Decimal
    reason: str


@dataclass(frozen=True)
class SettlementLedger:
    earned_eur: Decimal
    settled_eur: Decimal
    banked_eur: Decimal

    def __post_init__(self) -> None:
        if min(self.earned_eur, self.settled_eur, self.banked_eur) < 0:
            raise ValueError("ledger values cannot be negative")
        if self.settled_eur > self.earned_eur:
            raise ValueError("settled value cannot exceed earned value")
        if self.banked_eur > self.settled_eur:
            raise ValueError("banked value cannot exceed settled value")


@dataclass(frozen=True)
class SwarmPlan:
    active_slots: Mapping[SwarmKind, int]

    @property
    def total_active_slots(self) -> int:
        return sum(self.active_slots.values())


def evaluate_economic_gate(candidate: EconomicGateInput) -> EconomicGateResult:
    if candidate.requires_upfront_capital:
        return EconomicGateResult(
            Judgment.BLOCKED,
            Decimal("0"),
            "zero-capital rule blocks upfront capital",
        )
    if candidate.human_threshold_required:
        return EconomicGateResult(
            Judgment.HOLD,
            Decimal("0"),
            "human authority is required before economic execution",
        )

    expected_realized = (
        candidate.expected_gross_eur
        * candidate.success_probability
        * candidate.collection_probability
    )
    costs = (
        candidate.compute_cost_eur
        + candidate.api_cost_eur
        + candidate.platform_fee_eur
        + candidate.payment_fee_eur
        + candidate.expected_failure_cost_eur
    )
    expected_net = expected_realized - costs

    if expected_net > 0:
        return EconomicGateResult(Judgment.PASS, expected_net, "positive expected net value")
    return EconomicGateResult(Judgment.HOLD, expected_net, "expected net value is not positive")


def plan_swarm_capacity(requested: Mapping[SwarmKind, int]) -> SwarmPlan:
    resolved: dict[SwarmKind, int] = {}
    for swarm in SwarmKind:
        slots = int(requested.get(swarm, 0))
        if slots < 0:
            raise ValueError("worker slots cannot be negative")
        if slots > MAX_WORKERS_PER_SWARM:
            raise ValueError("worker slots exceed per-swarm capacity")
        if slots:
            resolved[swarm] = slots

    if sum(resolved.values()) > MAX_TOTAL_WORKER_SLOTS:
        raise ValueError("worker slots exceed global capacity")
    return SwarmPlan(resolved)


def next_scale_target(vbnv_per_day_eur: Decimal) -> Decimal:
    if vbnv_per_day_eur < 0:
        raise ValueError("VBNV cannot be negative")
    for target in (
        Decimal("0.01"),
        Decimal("1"),
        Decimal("10"),
        Decimal("50"),
        Decimal("120"),
    ):
        if vbnv_per_day_eur < target:
            return target
    return Decimal("120")

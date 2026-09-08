from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable


class ClosureState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


class ServiceDecision(str, Enum):
    KEEP = "KEEP"
    EXTEND = "EXTEND"
    REPOSITION = "REPOSITION"
    PAUSE = "PAUSE"
    RETIRE = "RETIRE"


class CapabilityDecision(str, Enum):
    REUSE = "REUSE"
    EXTEND = "EXTEND"
    ADAPTER = "ADAPTER"
    NEW_REVENUE_AGENT = "NEW_REVENUE_AGENT"
    HOLD = "HOLD"


@dataclass(frozen=True)
class DemandProof:
    real_problem: bool | None
    reachable_buyer: bool | None
    willingness_to_pay: bool | None
    measurable_outcome: bool | None
    settlement_path: bool | None
    policy_safe: bool | None


def evaluate_demand_proof(proof: DemandProof) -> ClosureState:
    values = (
        proof.real_problem,
        proof.reachable_buyer,
        proof.willingness_to_pay,
        proof.measurable_outcome,
        proof.settlement_path,
        proof.policy_safe,
    )
    if any(value is None for value in values):
        return ClosureState.HOLD
    if proof.policy_safe is False:
        return ClosureState.BLOCKED
    return ClosureState.PASS if all(values) else ClosureState.HOLD


@dataclass(frozen=True)
class CommercialEvidence:
    independent_counterparty: bool
    accepted_output: bool
    invoice_recorded: bool
    payment_settled: bool
    approved_account_receipt: bool
    bank_receipt: bool
    gross_value: Decimal | None
    direct_costs: Decimal | None
    currency: str


@dataclass(frozen=True)
class CommercialResult:
    state: ClosureState
    reason: str
    verified_banked_net_value: Decimal | None
    currency: str


def evaluate_commercial_closure(evidence: CommercialEvidence) -> CommercialResult:
    currency = evidence.currency.upper()
    if currency not in {"EUR", "USD"}:
        return CommercialResult(ClosureState.BLOCKED, "commercial closure supports EUR or USD", None, currency)
    chain = (
        (evidence.independent_counterparty, "independent counterparty"),
        (evidence.accepted_output, "customer acceptance"),
        (evidence.invoice_recorded, "invoice evidence"),
        (evidence.payment_settled, "settlement"),
        (evidence.approved_account_receipt, "approved account receipt"),
        (evidence.bank_receipt, "bank receipt"),
    )
    missing = next((name for ok, name in chain if not ok), None)
    if missing:
        return CommercialResult(ClosureState.HOLD, f"{missing} is not proven", None, currency)
    if evidence.gross_value is None or evidence.direct_costs is None:
        return CommercialResult(ClosureState.HOLD, "net reconciliation is incomplete", None, currency)
    net = evidence.gross_value - evidence.direct_costs
    if net <= Decimal("0"):
        return CommercialResult(ClosureState.HOLD, "verified banked net value is not positive", net, currency)
    return CommercialResult(ClosureState.PASS, "commercial closure evidence chain passed", net, currency)


@dataclass(frozen=True)
class MarketSignal:
    opportunities_falling: bool = False
    competitor_density_rising: bool = False
    price_falling: bool = False
    conversion_falling: bool = False
    acquisition_cost_rising: bool = False
    net_margin_falling: bool = False
    repeat_rate_falling: bool = False
    demand_shift_detected: bool = False

    def active_count(self) -> int:
        return sum(bool(value) for value in self.__dict__.values())


def saturation_decision(signal: MarketSignal) -> ServiceDecision:
    count = signal.active_count()
    if count <= 1:
        return ServiceDecision.KEEP
    if signal.demand_shift_detected and count >= 4:
        return ServiceDecision.REPOSITION
    if signal.net_margin_falling and signal.price_falling and count >= 5:
        return ServiceDecision.PAUSE
    if count >= 7:
        return ServiceDecision.RETIRE
    return ServiceDecision.EXTEND


@dataclass(frozen=True)
class CapabilityGap:
    repeated_verified_demand: bool
    existing_capability_can_deliver: bool
    extension_sufficient: bool
    adapter_sufficient: bool
    positive_expected_net_value: bool
    distribution_path_ready: bool
    settlement_path_ready: bool
    donecheck_contract_defined: bool
    policy_safe: bool


def capability_decision(gap: CapabilityGap) -> CapabilityDecision:
    if not gap.policy_safe:
        return CapabilityDecision.HOLD
    if not gap.repeated_verified_demand:
        return CapabilityDecision.HOLD
    if gap.existing_capability_can_deliver:
        return CapabilityDecision.REUSE
    if gap.extension_sufficient:
        return CapabilityDecision.EXTEND
    if gap.adapter_sufficient:
        return CapabilityDecision.ADAPTER
    readiness = (
        gap.positive_expected_net_value,
        gap.distribution_path_ready,
        gap.settlement_path_ready,
        gap.donecheck_contract_defined,
    )
    return CapabilityDecision.NEW_REVENUE_AGENT if all(readiness) else CapabilityDecision.HOLD


def choose_best_verified_opportunity(values: Iterable[tuple[str, Decimal]]) -> str | None:
    eligible = [(key, value) for key, value in values if value > 0]
    if not eligible:
        return None
    return max(eligible, key=lambda item: (item[1], item[0]))[0]

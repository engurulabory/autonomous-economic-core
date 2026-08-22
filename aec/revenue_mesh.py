from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class RevenueDoorState(str, Enum):
    ACTIVE = "ACTIVE"
    HOLD = "HOLD"
    PAUSED = "PAUSED"
    REJECTED = "REJECTED"


class EconomicPassState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


REVENUE_DOORS: tuple[str, ...] = (
    "agent_native_bounties",
    "open_source_bug_bounties",
    "documentation_bounties",
    "qa_test_benchmark_jobs",
    "research_analysis_tasks",
    "data_cleaning_transformation",
    "one_file_utilities",
    "templates_checklists",
    "curated_data_packs",
    "static_mini_tools",
    "hosted_micro_tools",
    "paid_api_endpoints",
    "evaluation_scoring_services",
    "automated_report_services",
    "white_label_widgets",
    "software_content_licensing",
    "marketplace_bundles",
    "ethical_affiliate_referral",
    "direct_b2b_micro_services",
    "recurring_monitoring_retainers",
)


@dataclass(frozen=True)
class RevenueDoorMetrics:
    door: str
    state: RevenueDoorState
    settled_external_revenue_eur: Decimal
    direct_cost_eur: Decimal
    human_minutes: Decimal
    accepted_runs: int = 0
    settled_runs: int = 0
    banked_runs: int = 0

    def __post_init__(self) -> None:
        if self.door not in REVENUE_DOORS:
            raise ValueError("unknown revenue door")
        if self.settled_external_revenue_eur < 0 or self.direct_cost_eur < 0 or self.human_minutes < 0:
            raise ValueError("economic metrics cannot be negative")
        if min(self.accepted_runs, self.settled_runs, self.banked_runs) < 0:
            raise ValueError("run counters cannot be negative")

    @property
    def vnev_eur(self) -> Decimal:
        return self.settled_external_revenue_eur - self.direct_cost_eur

    @property
    def vnev_per_human_hour_eur(self) -> Decimal:
        if self.human_minutes == 0:
            return Decimal("0") if self.vnev_eur == 0 else self.vnev_eur
        return (self.vnev_eur / self.human_minutes * Decimal("60")).quantize(Decimal("0.0001"))


@dataclass(frozen=True)
class EndToEndEconomicRun:
    external_customer_or_counterparty: bool
    work_or_asset_verified: bool
    accepted_or_sold: bool
    payment_settled: bool
    payout_eligible: bool
    payout_executed: bool
    approved_account_receipt_verified: bool
    bank_receipt_verified: bool
    direct_costs_finalized: bool
    settled_revenue_eur: Decimal
    direct_cost_eur: Decimal

    def __post_init__(self) -> None:
        if self.settled_revenue_eur < 0 or self.direct_cost_eur < 0:
            raise ValueError("money values cannot be negative")

    @property
    def vnev_eur(self) -> Decimal:
        if not self.external_customer_or_counterparty or not self.payment_settled:
            return Decimal("0")
        return self.settled_revenue_eur - self.direct_cost_eur

    def full_pass(self) -> EconomicPassState:
        if not self.external_customer_or_counterparty:
            return EconomicPassState.BLOCKED
        required = (
            self.work_or_asset_verified,
            self.accepted_or_sold,
            self.payment_settled,
            self.payout_eligible,
            self.payout_executed,
            self.approved_account_receipt_verified,
            self.bank_receipt_verified,
            self.direct_costs_finalized,
        )
        if not all(required):
            return EconomicPassState.HOLD
        if self.vnev_eur <= 0:
            return EconomicPassState.HOLD
        return EconomicPassState.PASS


def mesh_is_complete(doors: tuple[str, ...] = REVENUE_DOORS) -> bool:
    return len(doors) == 20 and len(set(doors)) == 20

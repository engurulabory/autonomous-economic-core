from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Iterable


class LearningState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


# P10 — First Field Run: One Cent Test™
@dataclass(frozen=True)
class OneCentEvidence:
    zero_capital: bool
    independent_external_counterparty: bool
    real_work_verified: bool
    accepted: bool
    payment_settled: bool
    approved_account_receipt: bool
    bank_receipt: bool
    gross_eur: Decimal | None
    fees_taxes_cost_eur: Decimal | None


@dataclass(frozen=True)
class OneCentResult:
    state: LearningState
    reason: str
    verified_banked_net_value_eur: Decimal | None


def evaluate_one_cent_test(evidence: OneCentEvidence) -> OneCentResult:
    if not evidence.zero_capital:
        return OneCentResult(LearningState.BLOCKED, "worker-side capital outlay occurred", None)
    chain = (
        (evidence.independent_external_counterparty, "independent external counterparty"),
        (evidence.real_work_verified, "real work verification"),
        (evidence.accepted, "acceptance"),
        (evidence.payment_settled, "settlement"),
        (evidence.approved_account_receipt, "approved account receipt"),
        (evidence.bank_receipt, "bank receipt"),
    )
    missing = next((name for ok, name in chain if not ok), None)
    if missing:
        return OneCentResult(LearningState.HOLD, f"{missing} is not proven", None)
    if evidence.gross_eur is None or evidence.fees_taxes_cost_eur is None:
        return OneCentResult(LearningState.HOLD, "economic reconciliation is incomplete", None)
    net = evidence.gross_eur - evidence.fees_taxes_cost_eur
    if net < Decimal("0.01"):
        return OneCentResult(LearningState.HOLD, "verified banked net value is below one cent", net)
    return OneCentResult(LearningState.PASS, "One Cent Test evidence chain passed", net)


# P11 — USD/EUR Opportunity Router™
@dataclass(frozen=True)
class FxQuote:
    eur_to_usd: Decimal
    observed_at: datetime
    source: str
    evidence_ref: str

    def __post_init__(self) -> None:
        if self.eur_to_usd <= 0:
            raise ValueError("EUR/USD rate must be positive")
        if not self.source.strip() or not self.evidence_ref.strip():
            raise ValueError("FX source and evidence_ref are required")


def validate_fx_quote(quote: FxQuote | None, *, now: datetime | None = None, max_age: timedelta = timedelta(hours=24)) -> LearningState:
    if quote is None:
        return LearningState.HOLD
    current = now or datetime.now(timezone.utc)
    observed = quote.observed_at if quote.observed_at.tzinfo else quote.observed_at.replace(tzinfo=timezone.utc)
    if observed > current + timedelta(minutes=5):
        return LearningState.BLOCKED
    return LearningState.PASS if current - observed <= max_age else LearningState.HOLD


@dataclass(frozen=True)
class RoutedEconomics:
    opportunity_id: str
    natural_currency: str
    expected_net_native: Decimal
    expected_minutes: Decimal
    acceptance_probability: Decimal
    payment_probability: Decimal
    fx_quote: FxQuote
    conversion_and_payout_cost_eur: Decimal = Decimal("0")

    def risk_adjusted_eur_per_hour(self) -> Decimal:
        currency = self.natural_currency.upper()
        if currency == "EUR":
            net_eur = self.expected_net_native
        elif currency == "USD":
            net_eur = self.expected_net_native / self.fx_quote.eur_to_usd
        else:
            raise ValueError("P11 router currently admits EUR or USD only")
        net_eur -= self.conversion_and_payout_cost_eur
        if self.expected_minutes <= 0 or net_eur <= 0:
            return Decimal("0")
        return net_eur * self.acceptance_probability * self.payment_probability / self.expected_minutes * Decimal("60")


def route_eur_usd(items: Iterable[RoutedEconomics], *, now: datetime | None = None) -> tuple[RoutedEconomics, ...]:
    eligible = [item for item in items if validate_fx_quote(item.fx_quote, now=now) is LearningState.PASS]
    return tuple(sorted(eligible, key=lambda item: (-item.risk_adjusted_eur_per_hour(), item.opportunity_id)))


# P12 — Throughput Target™
@dataclass(frozen=True)
class ThroughputEvent:
    at: datetime
    realized_net_eur: Decimal = Decimal("0")
    banked_net_eur: Decimal = Decimal("0")
    qualified: int = 0
    executed: int = 0
    accepted: int = 0
    idle_minutes: Decimal = Decimal("0")
    idle_reason: str | None = None


@dataclass(frozen=True)
class ThroughputSnapshot:
    realized_net_per_hour_eur: Decimal
    banked_value_per_hour_eur: Decimal
    qualified_per_hour: Decimal
    executed_per_hour: Decimal
    accepted_per_hour: Decimal
    idle_ratio: Decimal
    below_one_euro_target: bool
    idle_reasons: tuple[str, ...]


def rolling_throughput(events: Iterable[ThroughputEvent], *, now: datetime | None = None, window: timedelta = timedelta(hours=1)) -> ThroughputSnapshot:
    current = now or datetime.now(timezone.utc)
    start = current - window
    selected = [event for event in events if start <= event.at <= current]
    hours = Decimal(str(window.total_seconds() / 3600))
    realized = sum((event.realized_net_eur for event in selected), Decimal("0"))
    banked = sum((event.banked_net_eur for event in selected), Decimal("0"))
    qualified = sum(event.qualified for event in selected)
    executed = sum(event.executed for event in selected)
    accepted = sum(event.accepted for event in selected)
    idle = sum((event.idle_minutes for event in selected), Decimal("0"))
    window_minutes = Decimal(str(window.total_seconds() / 60))
    ratio = Decimal("0") if window_minutes <= 0 else min(Decimal("1"), idle / window_minutes)
    reasons = tuple(sorted({event.idle_reason for event in selected if event.idle_reason}))
    return ThroughputSnapshot(
        realized / hours if hours > 0 else Decimal("0"),
        banked / hours if hours > 0 else Decimal("0"),
        Decimal(qualified) / hours if hours > 0 else Decimal("0"),
        Decimal(executed) / hours if hours > 0 else Decimal("0"),
        Decimal(accepted) / hours if hours > 0 else Decimal("0"),
        ratio,
        (realized / hours if hours > 0 else Decimal("0")) < Decimal("1"),
        reasons,
    )


# P13 — Recurring Micro-Services™
@dataclass(frozen=True)
class RecurringService:
    service_id: str
    capability: str
    cadence_minutes: int
    acceptance_contract_verified: bool | None
    payout_contract_verified: bool | None
    automation_policy_verified: bool | None
    expected_effort_minutes: Decimal
    realized_net_per_hour_eur: Decimal | None = None
    renewal_probability: Decimal | None = None


def recurring_service_state(service: RecurringService) -> LearningState:
    if not service.service_id.strip() or not service.capability.strip() or service.cadence_minutes <= 0:
        return LearningState.BLOCKED
    checks = (service.acceptance_contract_verified, service.payout_contract_verified, service.automation_policy_verified)
    if any(value is None for value in checks):
        return LearningState.HOLD
    if not all(checks):
        return LearningState.BLOCKED
    if service.expected_effort_minutes <= 0:
        return LearningState.BLOCKED
    return LearningState.PASS


# P14 — Verified Economic Learning Core™
@dataclass(frozen=True)
class VerifiedLearningSample:
    sample_id: str
    task_class: str
    source: str
    worker_type: str
    completed: bool
    accepted: bool | None
    settled: bool | None
    banked: bool | None
    actual_minutes: Decimal | None
    actual_net_eur: Decimal | None
    observed_at: datetime
    revisions: int = 0
    failure_reason: str | None = None

    @property
    def learning_eligible(self) -> bool:
        return (
            self.completed
            and self.accepted is not None
            and self.settled is not None
            and self.actual_minutes is not None
            and self.actual_minutes > 0
            and self.actual_net_eur is not None
        )


@dataclass(frozen=True)
class LearnedProfile:
    key: tuple[str, str, str]
    sample_count: int
    confidence: Decimal
    acceptance_rate: Decimal
    payment_reliability: Decimal
    realized_net_per_hour_eur: Decimal
    revision_rate: Decimal


def learn_verified_profiles(samples: Iterable[VerifiedLearningSample], *, minimum_samples: int = 3, now: datetime | None = None, freshness_days: int = 90) -> tuple[LearnedProfile, ...]:
    current = now or datetime.now(timezone.utc)
    fresh_after = current - timedelta(days=freshness_days)
    groups: dict[tuple[str, str, str], list[VerifiedLearningSample]] = {}
    for sample in samples:
        if not sample.learning_eligible or sample.observed_at < fresh_after:
            continue
        key = (sample.task_class, sample.source, sample.worker_type)
        groups.setdefault(key, []).append(sample)
    profiles: list[LearnedProfile] = []
    for key, group in groups.items():
        if len(group) < minimum_samples:
            continue
        count = Decimal(len(group))
        accepted = sum(1 for sample in group if sample.accepted is True)
        paid = sum(1 for sample in group if sample.settled is True)
        total_net = sum((sample.actual_net_eur or Decimal("0") for sample in group), Decimal("0"))
        total_minutes = sum((sample.actual_minutes or Decimal("0") for sample in group), Decimal("0"))
        revisions = sum(sample.revisions for sample in group)
        confidence = min(Decimal("1"), count / Decimal(max(minimum_samples * 2, 1)))
        hourly = Decimal("0") if total_minutes <= 0 else total_net / total_minutes * Decimal("60")
        profiles.append(LearnedProfile(
            key,
            len(group),
            confidence,
            Decimal(accepted) / count,
            Decimal(paid) / count,
            hourly,
            Decimal(revisions) / count,
        ))
    return tuple(sorted(profiles, key=lambda profile: (-profile.realized_net_per_hour_eur, profile.key)))


# P15 — AEC Work Capability Catalog™ / Görev Evreni
@dataclass(frozen=True)
class CapabilityEntry:
    capability_id: str
    category: str
    description: str
    low_risk_digital: bool
    measurable_acceptance: bool
    human_threshold_default: bool = False


CAPABILITY_CATALOG = (
    CapabilityEntry("web-qa", "QA", "web page and flow QA", True, True),
    CapabilityEntry("link-check", "QA", "link and 404 verification", True, True),
    CapabilityEntry("data-verify", "DATA", "public data verification", True, True),
    CapabilityEntry("data-clean", "DATA", "structured data cleaning and deduplication", True, True),
    CapabilityEntry("research-mini", "RESEARCH", "bounded public-source research", True, True),
    CapabilityEntry("classify", "DATA", "classification and labeling", True, True),
    CapabilityEntry("proofread", "CONTENT", "proofreading and consistency check", True, True),
    CapabilityEntry("localize-tr-en", "CONTENT", "bounded TR/EN localization", True, True),
    CapabilityEntry("structured-extract", "DATA", "structured extraction from permitted content", True, True),
    CapabilityEntry("test-write", "CODE", "small automated test task", True, True),
    CapabilityEntry("bugfix-small", "CODE", "small bounded bug fix", True, True),
    CapabilityEntry("config-fix", "CODE", "small configuration correction", True, True),
    CapabilityEntry("docs-fix", "CODE", "README and documentation correction", True, True),
    CapabilityEntry("uptime-monitor", "MONITOR", "endpoint uptime monitoring", True, True),
    CapabilityEntry("public-change-monitor", "MONITOR", "permitted public-page change monitoring", True, True),
    CapabilityEntry("release-monitor", "MONITOR", "release and changelog monitoring", True, True),
    CapabilityEntry("csv-json-transform", "ARTIFACT", "CSV/JSON transformation", True, True),
    CapabilityEntry("artifact-pack", "ARTIFACT", "controlled digital artifact packaging", True, True),
    CapabilityEntry("bounty-triage", "AGENT_NATIVE", "permitted public bounty triage", True, True),
    CapabilityEntry("model-eval", "AGENT_NATIVE", "model-output evaluation and ranking", True, True),
    CapabilityEntry("direct-web-qa", "MICRO_SERVICE", "small business web QA service", True, True),
    CapabilityEntry("catalog-cleanup", "MICRO_SERVICE", "product/catalog data cleanup", True, True),
    CapabilityEntry("monitor-report", "MICRO_SERVICE", "periodic public monitoring report", True, True),
)

PROHIBITED_AUTONOMOUS_CLASSES = frozenset({
    "legal-decision",
    "medical-decision",
    "financial-decision",
    "binding-contract",
    "send-payment",
    "credential-secret-request",
    "captcha-bypass",
    "spam-manipulation",
    "prohibited-scraping",
    "high-risk-irreversible",
})


def capability_by_id(capability_id: str) -> CapabilityEntry | None:
    return next((entry for entry in CAPABILITY_CATALOG if entry.capability_id == capability_id), None)

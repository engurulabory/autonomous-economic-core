from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class MarketEvidenceRecord:
    source_name: str
    discovery_url: str
    canonical_url: str
    observed_at: datetime
    external_id: str
    reward_amount: Decimal
    reward_currency: str
    status: str
    funded: bool | None
    claimable: bool | None
    automation_allowed: bool | None
    country_eligible: bool | None
    exact_action: str
    exact_action_cost: Decimal | None
    exact_action_currency: str | None
    acceptance_path: str
    payout_path: str
    available_slots: int | None = None
    submission_count: int | None = None
    attempt_count: int | None = None
    deadline_at: datetime | None = None
    evidence_hash: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.source_name,
            self.discovery_url,
            self.canonical_url,
            self.external_id,
            self.reward_currency,
            self.status,
            self.exact_action,
            self.acceptance_path,
            self.payout_path,
        )
        if any(not value.strip() for value in required):
            raise ValueError("market evidence required text fields cannot be empty")
        if self.reward_amount < 0:
            raise ValueError("reward_amount cannot be negative")
        if self.exact_action_cost is not None and self.exact_action_cost < 0:
            raise ValueError("exact_action_cost cannot be negative")
        for value in (self.available_slots, self.submission_count, self.attempt_count):
            if value is not None and value < 0:
                raise ValueError("competition counters cannot be negative")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if self.deadline_at is not None and self.deadline_at.tzinfo is None:
            raise ValueError("deadline_at must be timezone-aware")

    @property
    def age_seconds(self) -> Decimal:
        now = datetime.now(timezone.utc)
        observed = self.observed_at.astimezone(timezone.utc)
        return Decimal(str(max(0.0, (now - observed).total_seconds())))

    def zero_capital_exact_action(self) -> bool | None:
        if self.exact_action_cost is None:
            return None
        return self.exact_action_cost == 0

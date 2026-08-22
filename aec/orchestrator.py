from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Protocol


class DoorCycleState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RevenueCandidate:
    door: str
    source: str
    external_id: str
    title: str
    canonical_url: str
    reward_amount: Decimal | None
    reward_currency: str | None
    open_now: bool | None
    zero_capital: bool | None
    agent_allowed: bool | None
    human_threshold_required: bool = False
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (self.door, self.source, self.external_id, self.title, self.canonical_url)
        if any(not value.strip() for value in required):
            raise ValueError("candidate identity fields cannot be empty")
        if self.reward_amount is not None and self.reward_amount < 0:
            raise ValueError("reward_amount cannot be negative")


class RevenueDoorAdapter(Protocol):
    name: str
    door: str

    def discover(self) -> list[RevenueCandidate]: ...


@dataclass(frozen=True)
class DoorCycleResult:
    adapter: str
    door: str
    state: DoorCycleState
    candidates: tuple[RevenueCandidate, ...]
    error: str | None = None


@dataclass(frozen=True)
class OrchestratorCycle:
    started_at: datetime
    finished_at: datetime
    results: tuple[DoorCycleResult, ...]

    @property
    def candidate_count(self) -> int:
        return sum(len(result.candidates) for result in self.results)

    @property
    def healthy_adapter_count(self) -> int:
        return sum(result.state is DoorCycleState.PASS for result in self.results)


def run_cycle(adapters: tuple[RevenueDoorAdapter, ...]) -> OrchestratorCycle:
    """Run one read-only economic discovery cycle.

    One failing door must never terminate the remaining market scan. External writes,
    wallet signing, account creation, purchases, bids, claims and submissions are out
    of scope for the unattended v0.1 cycle.
    """
    started = datetime.now(timezone.utc)
    results: list[DoorCycleResult] = []

    for adapter in adapters:
        try:
            candidates = tuple(adapter.discover())
            state = DoorCycleState.PASS if candidates else DoorCycleState.HOLD
            results.append(
                DoorCycleResult(
                    adapter=adapter.name,
                    door=adapter.door,
                    state=state,
                    candidates=candidates,
                )
            )
        except Exception as exc:  # isolate one provider from the whole cycle
            results.append(
                DoorCycleResult(
                    adapter=adapter.name,
                    door=adapter.door,
                    state=DoorCycleState.BLOCKED,
                    candidates=(),
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    return OrchestratorCycle(
        started_at=started,
        finished_at=datetime.now(timezone.utc),
        results=tuple(results),
    )

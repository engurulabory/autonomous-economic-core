from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

MONEY = Decimal("0.01")


class Judgment(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class EconomicRun:
    run_id: str
    external_counterparty: bool
    accepted: bool
    settled_revenue_eur: Decimal
    direct_cost_eur: Decimal
    active_minutes: Decimal
    reconciled: bool
    costs_finalized: bool
    bank_receipt_verified: bool = False
    bank_received_eur: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id is required")
        for field_name in (
            "settled_revenue_eur",
            "direct_cost_eur",
            "active_minutes",
            "bank_received_eur",
        ):
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")


@dataclass(frozen=True)
class EconomicResult:
    vnev_eur: Decimal
    vbnv_eur: Decimal
    net_per_hour_eur: Decimal
    one_cent_economic_test: Judgment
    one_cent_bank_test: Judgment


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def evaluate_run(run: EconomicRun) -> EconomicResult:
    """Evaluate evidence-backed economic truth for one run.

    A positive calculation cannot become PASS unless the external counterparty,
    acceptance, settlement reconciliation and cost finalization evidence exist.
    Banked proof additionally requires verified bank receipt evidence.
    """

    vnev = _money(run.settled_revenue_eur - run.direct_cost_eur)
    banked_base = run.bank_received_eur - run.direct_cost_eur
    vbnv = _money(banked_base) if run.bank_receipt_verified else Decimal("0.0000")

    evidence_complete = (
        run.external_counterparty
        and run.accepted
        and run.reconciled
        and run.costs_finalized
    )

    if not run.external_counterparty:
        economic_judgment = Judgment.BLOCKED
    elif not evidence_complete:
        economic_judgment = Judgment.HOLD
    elif vnev >= Decimal("0.01"):
        economic_judgment = Judgment.PASS
    else:
        economic_judgment = Judgment.HOLD

    if economic_judgment is Judgment.BLOCKED:
        bank_judgment = Judgment.BLOCKED
    elif not run.bank_receipt_verified:
        bank_judgment = Judgment.HOLD
    elif not evidence_complete:
        bank_judgment = Judgment.HOLD
    elif vbnv >= Decimal("0.01"):
        bank_judgment = Judgment.PASS
    else:
        bank_judgment = Judgment.HOLD

    if run.active_minutes > 0:
        net_per_hour = _money(vnev / run.active_minutes * Decimal("60"))
    else:
        net_per_hour = Decimal("0.0000")

    return EconomicResult(
        vnev_eur=vnev,
        vbnv_eur=vbnv,
        net_per_hour_eur=net_per_hour,
        one_cent_economic_test=economic_judgment,
        one_cent_bank_test=bank_judgment,
    )


def threshold_status(net_per_hour_eur: Decimal, positive_runs: int) -> dict[str, Judgment]:
    if positive_runs < 0:
        raise ValueError("positive_runs cannot be negative")

    return {
        "repeatability_10_runs": Judgment.PASS if positive_runs >= 10 else Judgment.HOLD,
        "economic_engine_0_10_per_hour": Judgment.PASS
        if net_per_hour_eur >= Decimal("0.10")
        else Judgment.HOLD,
        "utility_0_50_per_hour": Judgment.PASS
        if net_per_hour_eur >= Decimal("0.50")
        else Judgment.HOLD,
        "serious_target_1_00_per_hour": Judgment.PASS
        if net_per_hour_eur >= Decimal("1.00")
        else Judgment.HOLD,
    }

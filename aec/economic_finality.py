from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class FinalityState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class EconomicFinalityEvidence:
    run_id: str
    external_counterparty_verified: bool
    work_or_sale_verified: bool
    acceptance_verified: bool
    payment_settled: bool
    settlement_reference: str | None
    payout_executed: bool
    payout_reference: str | None
    approved_account_receipt_verified: bool
    bank_receipt_verified: bool
    bank_receipt_reference: str | None
    gross_revenue_eur: Decimal
    direct_cost_eur: Decimal
    taxes_fees_known: bool
    taxes_fees_eur: Decimal
    reconciliation_complete: bool

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id is required")
        for value in (self.gross_revenue_eur, self.direct_cost_eur, self.taxes_fees_eur):
            if value < 0:
                raise ValueError("economic amounts cannot be negative")

    @property
    def verified_banked_net_value_eur(self) -> Decimal:
        if not self.bank_receipt_verified or not self.reconciliation_complete or not self.taxes_fees_known:
            return Decimal("0")
        return self.gross_revenue_eur - self.direct_cost_eur - self.taxes_fees_eur

    def judge(self) -> FinalityState:
        if not self.external_counterparty_verified:
            return FinalityState.BLOCKED
        required = (
            self.work_or_sale_verified,
            self.acceptance_verified,
            self.payment_settled,
            bool(self.settlement_reference),
            self.payout_executed,
            bool(self.payout_reference),
            self.approved_account_receipt_verified,
            self.bank_receipt_verified,
            bool(self.bank_receipt_reference),
            self.taxes_fees_known,
            self.reconciliation_complete,
        )
        if not all(required):
            return FinalityState.HOLD
        if self.verified_banked_net_value_eur <= 0:
            return FinalityState.HOLD
        return FinalityState.PASS


def one_cent_test(evidence: EconomicFinalityEvidence) -> FinalityState:
    if evidence.judge() is not FinalityState.PASS:
        return evidence.judge()
    return FinalityState.PASS if evidence.verified_banked_net_value_eur >= Decimal("0.01") else FinalityState.HOLD

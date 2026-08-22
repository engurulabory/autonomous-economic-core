from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class WalletReceipt:
    network: str
    asset: str
    amount: Decimal
    destination_address: str
    transaction_id: str
    received_at: datetime
    independent_counterparty: bool

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("wallet receipt amount cannot be negative")
        if any(not value.strip() for value in (self.network, self.asset, self.destination_address, self.transaction_id)):
            raise ValueError("wallet receipt required fields cannot be empty")
        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")

    @property
    def verifies_external_settlement(self) -> bool:
        return self.independent_counterparty and self.amount > 0


@dataclass(frozen=True)
class BankReceipt:
    currency: str
    amount: Decimal
    payout_provider: str
    receipt_reference: str
    received_at: datetime
    independent_counterparty: bool

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("bank receipt amount cannot be negative")
        if any(not value.strip() for value in (self.currency, self.payout_provider, self.receipt_reference)):
            raise ValueError("bank receipt required fields cannot be empty")
        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")

    @property
    def verifies_banked_value(self) -> bool:
        return self.independent_counterparty and self.amount > 0

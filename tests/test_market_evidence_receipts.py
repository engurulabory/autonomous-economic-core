from datetime import datetime, timezone
from decimal import Decimal
import unittest

from aec.market_evidence import MarketEvidenceRecord
from aec.receipts import BankReceipt, WalletReceipt


class MarketEvidenceReceiptTests(unittest.TestCase):
    def test_market_record_zero_capital_exact_action(self):
        record = MarketEvidenceRecord(
            source_name="Taskmarket",
            discovery_url="https://taskmarket.dev",
            canonical_url="https://api.taskmarket.dev/api/tasks/0xabc",
            observed_at=datetime.now(timezone.utc),
            external_id="0xabc",
            reward_amount=Decimal("2"),
            reward_currency="USDC",
            status="open",
            funded=True,
            claimable=True,
            automation_allowed=True,
            country_eligible=True,
            exact_action="submit",
            exact_action_cost=Decimal("0"),
            exact_action_currency="USDC",
            acceptance_path="requester accept",
            payout_path="onchain USDC",
            submission_count=52,
        )
        self.assertTrue(record.zero_capital_exact_action())

    def test_wallet_receipt_is_not_bank_receipt(self):
        wallet = WalletReceipt(
            network="Base",
            asset="USDC",
            amount=Decimal("1.85"),
            destination_address="0x123",
            transaction_id="0xtx",
            received_at=datetime.now(timezone.utc),
            independent_counterparty=True,
        )
        self.assertTrue(wallet.verifies_external_settlement)

        bank = BankReceipt(
            currency="EUR",
            amount=Decimal("0"),
            payout_provider="off-ramp",
            receipt_reference="pending",
            received_at=datetime.now(timezone.utc),
            independent_counterparty=True,
        )
        self.assertFalse(bank.verifies_banked_value)

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            WalletReceipt(
                network="Base",
                asset="USDC",
                amount=Decimal("1"),
                destination_address="0x123",
                transaction_id="0xtx",
                received_at=datetime.now(),
                independent_counterparty=True,
            )


if __name__ == "__main__":
    unittest.main()

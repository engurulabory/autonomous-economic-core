# Verified Payout Core™

## Purpose
Verified Payout Core™ turns an economic claim into bank-receipt evidence.

Canonical payout chain:

`WORK → ACCEPTED → REVENUE_CREATED → SETTLED → PAYOUT_ELIGIBLE → BANK_PAYOUT → BANK_RECEIPT_VERIFIED → NET_ECONOMIC_VALUE_VERIFIED`

## Truth rules
1. Work completion is not revenue.
2. Revenue approval is not settlement.
3. Settlement is not bank receipt.
4. Bank receipt is not automatically net value; attributable costs must be finalized.
5. A banked-value claim requires evidence of the designated payout destination receiving the funds.

## Core records
A payout record SHOULD include:
- payout_id,
- economic_run_id,
- source/provider,
- gross settled amount,
- payout amount,
- payout fee,
- currency,
- initiated_at,
- confirmed_at,
- destination alias/fingerprint (never public raw banking secrets),
- receipt evidence reference,
- reconciliation status.

## Minimum payout threshold
If earned and settled funds cannot yet be paid out because a provider threshold is not met:

`EARNED = PASS`
`SETTLED = PASS`
`BANK_PAYOUT = HOLD`
`BANK_RECEIPT_VERIFIED = HOLD`

The ledger must retain the settled value without falsely claiming VBNV.

## Human Threshold™
Changing the payout destination, accepting new binding financial terms, KYC, withdrawals with material fees, or irreversible external financial actions require human review unless an explicit narrow delegation exists.

## Security
- Never commit bank account numbers, card numbers, credentials, tokens, or KYC material.
- Public evidence uses redacted/fingerprinted destination references.
- Secrets remain outside the public repository.
- The payout adapter must expose read/verify separately from write/initiate capabilities.

## Final metric
**Verified Banked Net Value™** is the long-term headline metric.

A banked-value event reaches PASS only when the receipt evidence, reconciliation, and cost finalization all pass.

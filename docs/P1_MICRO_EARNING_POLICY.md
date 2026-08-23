# P1 — Micro-Earning Policy™

## State

IMPLEMENTED — technical policy layer added after AEC v1.1 Technical Commissioning PASS.

## Claim

AEC can now evaluate a discovered opportunity on a fail-closed economic basis before later selection or execution gates.

P1 does not authorize external action and does not prove earned, settled or banked value.

## Canonical economic inputs

Each opportunity is evaluated with:

- expected gross value;
- currency;
- estimated execution time;
- acceptance probability;
- payment probability;
- expected fees;
- expected taxes;
- expected other cost;
- exact worker-side upfront cost;
- independent external counterparty status;
- verified FX-to-EUR rate when the natural currency is not EUR.

EUR is the canonical comparison currency. Native USD and other currencies remain permitted when a verified conversion rate is supplied. Unknown FX is HOLD.

## Zero-capital rule

Worker-side upfront capital must be exactly `0`.

Unknown upfront cost → HOLD.
Positive upfront cost → BLOCKED.

Post-acceptance fees, taxes and payout costs may be non-zero; they reduce expected net value but are not treated as permission to pre-fund work.

## Economic calculation

`expected net EUR = gross EUR - fees EUR - taxes EUR - other cost EUR`

`risk-adjusted expected net EUR = expected net EUR × acceptance probability × payment probability`

`expected net EUR/hour = risk-adjusted expected net EUR ÷ estimated minutes × 60`

Non-positive expected net value is BLOCKED.

## Fail-closed behavior

Critical unknowns produce HOLD, including:

- counterparty independence;
- exact worker-side upfront cost;
- gross value;
- execution time;
- acceptance probability;
- payment probability;
- fees/taxes/other cost;
- currency;
- required FX rate.

## Authority boundary

P1 PASS means only:

> Economic data is sufficiently verified for the opportunity to enter later selection gates.

It does not authorize bidding, account creation, signing, purchases, submissions, payout changes, money movement or any revenue claim.

Human Threshold™, action qualification, platform policy, DoneCheck™, settlement and Economic Finality remain separate authorities.

## Acceptance

P1 technical acceptance requires:

1. Exact €0 worker-side upfront-cost gate.
2. Fail-closed HOLD on critical unknowns.
3. Positive-net-value enforcement.
4. Acceptance/payment probability adjustment.
5. EUR normalization with verified FX for non-EUR opportunities.
6. Deterministic expected net €/hour output.
7. Unit coverage for PASS, HOLD and BLOCKED paths.

## Next action

P2 — Smallest-Profitable-Work Selector™ should consume P1 assessments and rank selectable opportunities while preserving all existing governance and authority gates.

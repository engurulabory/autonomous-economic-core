# P1 — Micro-Earning Policy™

## State

IMPLEMENTED — technical policy layer added after AEC v1.1 Technical Commissioning PASS.

## Claim

AEC evaluates discovered opportunities on a fail-closed economic basis in both EUR and USD before later selection or execution gates.

P1 does not authorize external action and does not prove earned, settled or banked value.

## Currency policy

EUR and USD are first-class working currencies.

- Opportunities may arrive naturally in EUR or USD.
- Opportunities in other supported currencies may be normalized only with verified FX evidence.
- Every selectable opportunity exposes both EUR and USD economic outputs.
- EUR/USD FX must be verified and time-stamped by the later market/FX evidence layer; unknown FX is HOLD.
- Neither EUR nor USD is treated as revenue evidence by itself; they are comparison/accounting views of the same opportunity.

## Canonical economic inputs

Each opportunity is evaluated with:

- expected gross value;
- native currency;
- estimated execution time;
- acceptance probability;
- payment probability;
- expected fees;
- expected taxes;
- expected other cost;
- exact worker-side upfront cost;
- independent external counterparty status;
- verified EUR/USD FX rate;
- verified FX-to-EUR rate when the natural currency is neither EUR nor USD.

## Zero-capital rule

Worker-side upfront capital must be exactly `0`.

Unknown upfront cost → HOLD.
Positive upfront cost → BLOCKED.

Post-acceptance fees, taxes and payout costs may be non-zero; they reduce expected net value but are not treated as permission to pre-fund work.

## Economic calculation

For the same opportunity P1 calculates both views:

`expected net EUR = gross EUR - fees EUR - taxes EUR - other cost EUR`

`expected net USD = gross USD - fees USD - taxes USD - other cost USD`

`risk-adjusted expected net = expected net × acceptance probability × payment probability`

`expected net/hour = risk-adjusted expected net ÷ estimated minutes × 60`

Outputs include at minimum:

- expected net EUR;
- expected net USD;
- risk-adjusted net EUR;
- risk-adjusted net USD;
- expected net €/hour;
- expected net $/hour.

Non-positive expected net value is BLOCKED.

## Fail-closed behavior

Critical unknowns produce HOLD, including counterparty independence, exact worker-side upfront cost, gross value, execution time, acceptance probability, payment probability, fees/taxes/other cost, currency and required FX evidence.

## Authority boundary

P1 PASS means only that economic data is sufficiently verified for the opportunity to enter later selection gates.

It does not authorize bidding, account creation, signing, purchases, submissions, payout changes, money movement or any revenue claim.

Human Threshold™, action qualification, platform policy, DoneCheck™, settlement and Economic Finality remain separate authorities.

## Acceptance

P1 technical acceptance requires:

1. Exact €0 / $0 worker-side upfront-cost gate.
2. Fail-closed HOLD on critical unknowns.
3. Positive-net-value enforcement.
4. Acceptance/payment probability adjustment.
5. EUR and USD as first-class economic outputs.
6. Verified EUR/USD normalization.
7. Deterministic expected net €/hour and $/hour outputs.
8. Unit coverage for EUR PASS, USD PASS, HOLD and BLOCKED paths.

## Next action

P2 — Smallest-Profitable-Work Selector™ consumes the dual-currency P1 assessments and ranks selectable opportunities while preserving all existing governance and authority gates.

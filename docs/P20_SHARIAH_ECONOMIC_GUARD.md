# P20 — ENGÜRÜ SHARIAH ECONOMIC GUARD™

## State

IMPLEMENTED ON FEATURE BRANCH — exact-main CI and field evidence remain separate gates.

## Purpose

AEC must not optimize revenue before legitimacy. P20 places a fail-closed economic permissibility gate in front of later selection, execution and payout logic.

This module is an operational policy guard, not an automated religious ruling or fatwa engine. Material uncertainty is escalated to HOLD and, where financial authority or irreversible settlement is involved, to Human Threshold™.

## Locked governing order

`PERMISSIBILITY → TRUST → NET VALUE → SPEED`

A higher-paying opportunity never outranks a BLOCKED opportunity.

## Canonical decision model

### PASS

Only when all material facts are verified:

- underlying work is permissible,
- real value, service or legitimate consideration exists,
- compensation terms are clear,
- no riba / interest-bearing economic structure is detected,
- no maysir / gambling-like payoff structure is detected,
- no excessive gharar / material contractual uncertainty is detected,
- no fraud, deception, manipulation or unjust enrichment is detected,
- ownership / entitlement to payment is legitimate,
- payment rail is approved,
- no unresolved Human Threshold financial authority remains.

PASS means the opportunity may enter later AEC economic gates. It does not authorize execution, payment movement or settlement by itself.

### HOLD

Used when:

- one or more material facts are unknown,
- a payment rail or token structure requires additional review,
- Human Threshold™ is required for KYC, account ownership, signing, payment, payout or irreversible settlement action.

Unknown is never interpreted as permissible.

### BLOCKED

Used when any explicit prohibited condition is present, including:

- prohibited underlying work,
- absence of legitimate real value or consideration,
- materially unclear compensation,
- riba / interest-bearing structure,
- maysir / gambling-like payoff,
- excessive gharar,
- fraud, deception, manipulation or unjust enrichment,
- illegitimate ownership / entitlement,
- disallowed payment rail.

## Revenue-door integration

Canonical classifier:

`classify_revenue_doors(opportunities)`

Every candidate revenue door must receive one of:

`PASS | HOLD | BLOCKED`

before it can enter Revenue Door Ranking™, Smallest-Profitable-Work Selector™ or execution routing.

## Stablecoin / crypto rule

AEC does not treat crypto speculation as a revenue strategy.

Locked economic principle:

`AEC earns from real work; crypto may only be a payment rail after policy review.`

Therefore leverage, futures/perpetual speculation, gambling-like trading, pump-and-dump activity and interest-bearing yield structures are outside the permitted economic surface.

A stablecoin or token is not auto-approved by name. Its actual payment, custody, conversion and yield structure must be reviewed. Unknown material structure is HOLD.

## Human Threshold™

P20 never grants autonomous financial authority.

Human Threshold remains mandatory wherever the action involves real-person or real-organization authority, KYC, account creation/ownership, signing, payment movement, payout routing, settlement or another irreversible external financial consequence.

## Evidence boundary

`implementation ≠ Shariah review ≠ field evidence ≠ economic finality`

Automated tests can prove classifier behavior. They cannot manufacture factual evidence about an external opportunity, token, contract or payment rail, and they cannot substitute for qualified human religious/legal review where that review is required.

## Acceptance criteria

1. PASS/HOLD/BLOCKED classifier is deterministic.
2. Explicit riba, maysir, excessive gharar, fraud and prohibited work fail closed to BLOCKED.
3. Unknown material facts fail closed to HOLD.
4. Financial authority requiring Human Threshold never auto-passes.
5. Batch revenue-door classification preserves candidate identity and order.
6. Later AEC ranking/execution layers accept only P20 PASS candidates.
7. Exact-main CI is green after merge.

## Next integration action

Wire P20 immediately before revenue-door ranking and execution selection, then classify every existing revenue-door candidate and persist the assessment evidence alongside the candidate record.

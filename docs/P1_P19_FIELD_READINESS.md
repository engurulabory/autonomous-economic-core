# AEC™ — P1–P20 Economic / Field Readiness

## State

HOLD — repository implementation is present through P20; exact-main CI and real-world economic acceptance remain separate gates.

## Governing rule

`implementation ≠ field evidence ≠ economic finality`

A package may be technically implemented and unit-tested while its real-field acceptance remains HOLD. No package is allowed to manufacture external evidence.

AEC Currency Router™ v1 locks five first-class working currencies:

`EUR + USD + GBP + JPY + CNY`

EUR remains the canonical comparison/accounting plane. Each opportunity keeps its natural currency, while fresh source-backed FX evidence normalizes fee-aware expected net value to EUR for ranking. Missing, stale, mismatched or temporally invalid FX evidence fails closed to HOLD/BLOCKED. Currency support never implies that a specific country, marketplace or payout rail is eligible.

Before revenue optimization, P20 enforces the locked order:

`PERMISSIBILITY → TRUST → NET VALUE → SPEED`

## Implementation matrix

| Package | Core implementation | Automated coverage | Real-field acceptance |
|---|---|---|---|
| P1 Micro-Earning Policy™ | `aec/micro_earning_policy.py` | dual-currency legacy coverage; field router extends multi-currency plane | CI HOLD |
| P2 Smallest-Profitable-Work Selector™ | `aec/economic_field_core.py` | positive-cent + risk/hour ranking tests | CI HOLD |
| P3 Task Decomposition Core™ | `aec/economic_field_core.py` | permission fail-closed tests | CI HOLD |
| P4 Parallel Worker Economy™ | `aec/economic_field_core.py` | bounded concurrency tests | runtime load evidence HOLD |
| P5 Economic Learning Ledger™ | `aec/economic_field_core.py` | evidence contract / duplicate protection tests | durable real-job evidence HOLD |
| P6 Revenue Door Ranking™ | `aec/economic_field_core.py` | economic-quality ranking tests | real door performance data HOLD |
| P7 KârMatik™ Operating Loop | `aec/economic_field_core.py` | canonical state-sequence tests | live economic loop HOLD |
| P8 Economic Acceptance Ladder™ | `aec/economic_field_core.py` | banked-value/sample/window tests | first real banked value HOLD |
| P9 Field Safety / Anti-Waste Gate™ | `aec/economic_field_core.py` | prohibited/unknown/deprioritize tests | field policy evidence HOLD |
| P10 One Cent Test™ | `aec/economic_learning_core.py` | full evidence-chain evaluator tests | real independent paid run HOLD |
| P11 AEC Currency Router™ v1 | `aec/currency_router.py` | EUR/USD/GBP/JPY/CNY, stale FX, fee-aware normalization/ranking tests | live FX evidence source HOLD |
| P12 Throughput Target™ | `aec/economic_learning_core.py` | rolling 60-minute metrics tests | real throughput observation HOLD |
| P13 Recurring Micro-Services™ | `aec/economic_learning_core.py` | contract/policy qualification tests | real recurring service evidence HOLD |
| P14 Verified Economic Learning Core™ | `aec/economic_learning_core.py` | verified-only/min-sample learning tests | sufficient verified economic samples HOLD |
| P15 AEC Work Capability Catalog™ | `aec/economic_learning_core.py` | 20+ machine-readable capability coverage | capability-specific field evidence HOLD |
| P16 Worker Fleet & Adaptive Concurrency Core™ | `aec/field_expansion_core.py` | Supervisor/capability/idempotency tests | 5-job bounded parallel runtime proof HOLD |
| P17 Competitive Pattern Assimilation Core™ | `aec/field_expansion_core.py` | Anti-Copy + adoption-gate tests | controlled external-pattern benefit proof HOLD |
| P18 Agent-Native Micro-Service Revenue Core™ | `aec/field_expansion_core.py` | canonical 3 + 5-service catalog tests | live endpoint + independent paid call HOLD |
| P19 Payment / Payout Router™ | `aec/field_expansion_core.py` | policy/currency/fee/speed routing tests | real compatible payout + settlement proof HOLD |
| P20 ENGÜRÜ SHARIAH ECONOMIC GUARD™ | `aec/shariah_economic_guard.py` | deterministic PASS/HOLD/BLOCKED + Human Threshold tests | external opportunity/payment-rail review HOLD |

## Field execution bridge

The post-discovery execution boundary is now explicit:

`PASS-QUALIFIED CANDIDATE → INTERNAL PRODUCTION → DONECHECK → HUMAN THRESHOLD ENVELOPE → PERMITTED SUBMISSION HANDOFF`

`aec/field_execution_bridge.py` separates internal production authority from external authority. A PASS-qualified candidate may enter internal Production and DoneCheck even when later public submission/signing requires Human Threshold. Human Threshold therefore does not freeze safe internal work; it gates only the authority-bearing external step.

The bridge never authorizes KYC, legal assent, account creation with binding terms, signing, spending, payout-account change, money movement or an unverified public submission route.

## Locked P18 canonical order

1. AEC Research & Verification Utility™
2. AEC Structured Web Extraction Utility™
3. AEC Public Signal Monitor™

The machine-service catalog contains at least five entries. Publishing a catalog is not a revenue claim. A paid-call claim requires an independent counterparty, verified service execution, settlement evidence and reconciliation.

## P19 authority boundary

The Payment / Payout Router™ selects a compatible verified rail by expected net settlement value, reliability, settlement speed, fees and risk. Selection never authorizes money movement. Human Threshold™ remains mandatory wherever payment, payout, account ownership, KYC, signing or irreversible financial action requires human authority.

## P20 authority boundary

The ENGÜRÜ SHARIAH ECONOMIC GUARD™ must classify every revenue-door candidate before economic ranking or execution selection. Explicit prohibited conditions are BLOCKED; material unknowns are HOLD; only verified candidates are PASS. P20 is an operational policy guard, not an automated fatwa engine, and cannot replace qualified human religious/legal review where that review is required.

## Economic acceptance sequence

`TECHNICAL IMPLEMENTATION → EXACT-MAIN CI → SHARIAH ECONOMIC GUARD → LIVE DISCOVERY → CURRENCY NORMALIZATION → PASS QUALIFICATION → PRODUCTION → DONECHECK → HUMAN THRESHOLD WHEN REQUIRED → PERMITTED DELIVERY → SETTLEMENT → INVOICE/ACCOUNTING EVIDENCE → APPROVED ACCOUNT RECEIPT → BANK RECEIPT → RECONCILIATION → VERIFIED BANKED NET VALUE`

Until the final chain exists, `economic_finality = HOLD`.

## Next acceptance action

1. Obtain exact-main CI evidence for the new Currency Router and Field Execution Bridge tests.
2. Feed live field candidates into the five-currency router with source/timestamped FX evidence.
3. Persist P20 + qualification + currency-routing evidence for each candidate.
4. Promote the first fully verified PASS candidate into `aec/field_execution_bridge.py`.
5. Run internal Production → DoneCheck without blocking on later external Human Threshold.
6. Release only the verified permitted submission handoff when authority evidence exists.
7. Complete Field Run #001 through settlement, invoice/accounting evidence, bank receipt and reconciled VBNV ≥ €0.01.

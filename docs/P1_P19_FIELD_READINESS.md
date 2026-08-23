# AEC™ — P1–P19 Economic / Field Readiness

## State

HOLD — repository implementation is present through P19; exact-main CI and real-world economic acceptance remain separate gates.

## Governing rule

`implementation ≠ field evidence ≠ economic finality`

A package may be technically implemented and unit-tested while its real-field acceptance remains HOLD. No package is allowed to manufacture external evidence.

EUR and USD are first-class economic working currencies. EUR remains a canonical comparison/accounting plane where normalization is required; USD values are retained and exposed rather than discarded.

## Implementation matrix

| Package | Core implementation | Automated coverage | Real-field acceptance |
|---|---|---|---|
| P1 Micro-Earning Policy™ | `aec/micro_earning_policy.py` | dual EUR/USD PASS/HOLD/BLOCKED tests | CI HOLD |
| P2 Smallest-Profitable-Work Selector™ | `aec/economic_field_core.py` | positive-cent + risk/hour ranking tests | CI HOLD |
| P3 Task Decomposition Core™ | `aec/economic_field_core.py` | permission fail-closed tests | CI HOLD |
| P4 Parallel Worker Economy™ | `aec/economic_field_core.py` | bounded concurrency tests | runtime load evidence HOLD |
| P5 Economic Learning Ledger™ | `aec/economic_field_core.py` | evidence contract / duplicate protection tests | durable real-job evidence HOLD |
| P6 Revenue Door Ranking™ | `aec/economic_field_core.py` | economic-quality ranking tests | real door performance data HOLD |
| P7 KârMatik™ Operating Loop | `aec/economic_field_core.py` | canonical state-sequence tests | live economic loop HOLD |
| P8 Economic Acceptance Ladder™ | `aec/economic_field_core.py` | banked-value/sample/window tests | first real banked value HOLD |
| P9 Field Safety / Anti-Waste Gate™ | `aec/economic_field_core.py` | prohibited/unknown/deprioritize tests | field policy evidence HOLD |
| P10 One Cent Test™ | `aec/economic_learning_core.py` | full evidence-chain evaluator tests | real independent paid run HOLD |
| P11 USD/EUR Opportunity Router™ | `aec/economic_learning_core.py` | stale FX + EUR/USD routing tests | live FX evidence source HOLD |
| P12 Throughput Target™ | `aec/economic_learning_core.py` | rolling 60-minute metrics tests | real throughput observation HOLD |
| P13 Recurring Micro-Services™ | `aec/economic_learning_core.py` | contract/policy qualification tests | real recurring service evidence HOLD |
| P14 Verified Economic Learning Core™ | `aec/economic_learning_core.py` | verified-only/min-sample learning tests | sufficient verified economic samples HOLD |
| P15 AEC Work Capability Catalog™ | `aec/economic_learning_core.py` | 20+ machine-readable capability coverage | capability-specific field evidence HOLD |
| P16 Worker Fleet & Adaptive Concurrency Core™ | `aec/field_expansion_core.py` | Supervisor/capability/idempotency tests | 5-job bounded parallel runtime proof HOLD |
| P17 Competitive Pattern Assimilation Core™ | `aec/field_expansion_core.py` | Anti-Copy + adoption-gate tests | controlled external-pattern benefit proof HOLD |
| P18 Agent-Native Micro-Service Revenue Core™ | `aec/field_expansion_core.py` | canonical 3 + 5-service catalog tests | live endpoint + independent paid call HOLD |
| P19 Payment / Payout Router™ | `aec/field_expansion_core.py` | policy/currency/fee/speed routing tests | real compatible payout + settlement proof HOLD |

## Locked P18 canonical order

1. AEC Research & Verification Utility™
2. AEC Structured Web Extraction Utility™
3. AEC Public Signal Monitor™

The machine-service catalog contains at least five entries. Publishing a catalog is not a revenue claim. A paid-call claim requires an independent counterparty, verified service execution, settlement evidence and reconciliation.

## P19 authority boundary

The Payment / Payout Router™ selects a compatible verified rail by expected net settlement value, reliability, settlement speed, fees and risk. Selection never authorizes money movement. Human Threshold™ remains mandatory wherever payment, payout, account ownership, KYC, signing or irreversible financial action requires human authority.

## Economic acceptance sequence

`TECHNICAL IMPLEMENTATION → EXACT-MAIN CI → SANDBOX/RUNTIME EVIDENCE → ONE CENT TEST → SETTLEMENT → APPROVED ACCOUNT RECEIPT → BANK RECEIPT → RECONCILIATION → VERIFIED BANKED NET VALUE`

Until the final chain exists, `economic_finality = HOLD`.

## Next acceptance action

1. Obtain exact-main CI evidence for P1–P19 implementation.
2. Run controlled runtime proofs for P4/P5/P7/P12/P16.
3. Publish one P18 canonical service endpoint without weakening policy/authority gates.
4. Perform one independent paid call and route its payout through P19.
5. Complete P10 One Cent Test™ with bank receipt and reconciled VBNV ≥ €0.01.

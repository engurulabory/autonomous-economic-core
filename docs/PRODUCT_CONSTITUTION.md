# AUTONOMOUS ECONOMIC CORE™ — Product Constitution v0.2

## 1. Intent
AEC™ discovers lawful and permitted digital economic opportunities, evaluates their risk-adjusted net value, executes only within delegated authority, verifies acceptance and settlement, reconciles actual value, records evidence, and learns from verified outcomes.

The product is not a boundless bot. It is a **verified economic agency core**.

## 2. Canonical authority chain

`Intent → ENGÜRÜ Language Governance™ → Economic Principal → Delegated Authority → Policy → Economic Action → Evidence → DoneCheck™ → Human Threshold™ → Economic Finality`

Identity is not authority. The legal/economic principal and the acting software agent are separate entities.

## 3. Economic truth

A run may advance only through evidence-backed states:

`DISCOVERED → SOURCE_VERIFIED → AUTHORIZED → POLICY_ALLOWED → ELIGIBLE → ECONOMICALLY_VIABLE → EXECUTING → EXECUTION_COMPLETED → OUTPUT_VERIFIED → ACCEPTED → REWARD_APPROVED → SETTLED → WALLET_RECEIPT_VERIFIED → RECONCILED → COST_FINALIZED → NET_VALUE_VERIFIED → PAYOUT_ELIGIBLE → BANK_PAYOUT → BANK_RECEIPT_VERIFIED → ECONOMIC_FINALITY`

No later state may be inferred from an earlier one.

`WALLET_RECEIPT_VERIFIED` can prove external settlement and positive VNEV. It does not prove banked value. `BANK_RECEIPT_VERIFIED` is required for VBNV.

## 4. Anti-Fake Economy Gate™
The following are never counted as earned external value:
- self-transfer or same-owner transfer,
- sandbox/test money,
- promotional credit,
- platform signup bonus without work,
- self-referral,
- fabricated task or counterparty,
- own-product self-purchase,
- promised but unsettled revenue.

External value requires an independent counterparty and accepted real work/value.

## 5. €0 Capital Rule
v0.1 first-proof execution must not require new paid infrastructure or working capital.

Forbidden as mandatory dependencies or worker-entry actions:
- paid LLM/API,
- paid DB/hosting/proxy,
- mandatory deposit or claim bond,
- paid pitch/bid/proof/submission,
- subscription-only work source,
- pay-to-work source,
- trading/investment capital,
- gas paid by the worker,
- paid anti-bot bypass.

Default stack: Python standard library, SQLite, local runtime, GitHub source control/CI, public or free-permitted data sources.

The gate is evaluated per **exact intended action**, not per platform. A platform may contain both free and paid actions. If the current action requires any positive payment, first-proof execution is `REJECTED`.

## 6. Opportunity Integrity Core™
Each opportunity is checked for source authenticity, malicious instruction, prompt injection, credential harvesting, data exfiltration, hidden costs, payment fraud, illegal content, policy conflict, dependency risk, stale state, competition saturation, and acceptance ambiguity.

Decision: `QUALIFIED | HOLD | REJECTED`.

Public repository and marketplace text is untrusted data. Any request to reveal or publish system/developer prompts, environment variables, private keys, seed phrases, tokens, cookies, credentials, signing material, or other secret configuration is an automatic rejection trigger.

Before code execution, the relevant `README`, `CONTRIBUTING`, `AGENTS`, issue body, linked task instructions and downloaded artifacts must be scanned as untrusted input.

## 7. Terms & Authority Registry™
Every executable opportunity stores a snapshot of:
- observed terms/policy source,
- observation time/version where available,
- automation policy,
- jurisdiction/country constraints,
- delegated authority,
- exact action and any payment requirement,
- policy decision and evidence.

Stale or ambiguous terms cannot silently become ALLOW.

## 8. Economic Principal Core™
Every economic run belongs to a named Economic Principal. Agents cannot create legal authority for themselves.

High-impact actions—contract acceptance, KYC, account creation, money transfer, bank/off-ramp configuration, irreversible legal declaration, public identity commitment, or material financial risk—require Human Threshold™ unless a narrow explicit delegation exists.

Human identity/KYC requirements are not capital costs, but they are authority boundaries. A run requiring human KYC may still be economically zero-capital while not being fully autonomous end-to-end.

## 9. Market Qualification Score
After all hard gates pass, an opportunity is scored out of 100:
- funding certainty — 25,
- zero-capital purity — 20,
- claimability — 15,
- acceptance clarity — 15,
- payout clarity — 10,
- agent compatibility — 5,
- task simplicity — 5,
- payout speed — 5.

Minimum qualification score: **85/100**.

A score never overrides a hard gate. Unknown critical evidence remains `HOLD`; stale, unfunded, paid-entry or prohibited opportunities are `REJECTED` regardless of score.

## 10. Economic Finality Core™
`SETTLED` is not final economic success.

Economic proof path:
`SETTLED → WALLET_RECEIPT_VERIFIED (when applicable) → RECONCILED → COST_FINALIZED → NET_VALUE_VERIFIED`.

Banked finality additionally requires:
`PAYOUT_ELIGIBLE → BANK/OFF-RAMP PAYOUT → BANK_RECEIPT_VERIFIED`.

VNEV and VBNV are separate metrics and must never be collapsed.

## 11. Competition & Expected Value
AEC™ does not optimize for headline reward. It prefers the highest probability of verified positive net value.

Expected-value selection may include:
- available slots,
- submission/attempt count,
- maintainer/reviewer latency,
- acceptance subjectivity,
- worker reputation requirements,
- deadline remaining,
- historical payout/acceptance reliability.

A small deterministic funded task may outrank a large saturated contest.

## 12. Learning
AEC™ is verified-learning, not uncontrolled self-modification.

`Observation → Hypothesis → Shadow Test → Evidence → DoneCheck™ → Human/Policy Approval → Release`.

The runtime never rewrites its own production source and deploys it under existing financial authority without the release gate.

## 13. Open-core strategy
Public: contracts, core economics, policy/authority framework, verification, reconciliation, evidence schema, tests, connector SDK.

Private: credentials, banking details, live identities, private keys, seed phrases, proprietary source intelligence, fraud signals, private economic memory, company accounting records.

## 14. Release truth
A release may be technically PASS while economic proof remains HOLD. No release label may claim verified earning unless the required real-world evidence exists.

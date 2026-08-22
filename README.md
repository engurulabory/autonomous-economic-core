# AUTONOMOUS ECONOMIC CORE™

**Verified economic agency core for lawful, policy-governed autonomous digital value creation.**

AEC™ is an open-core research and engineering project by Engürü Lab. Its first scientific objective is intentionally small and strict:

> **€0 → €0.01 VERIFIED NET ECONOMIC VALUE (VNEV)**

The system does not count promises, dashboard balances, test credits, self-transfers, or promotional value as earned economic value.

## Canonical economic loop

`DISCOVER → SOURCE VERIFY → AUTHORITY VERIFY → POLICY VERIFY → ELIGIBILITY → ECONOMIC ESTIMATE → SELECT → EXECUTE → OUTPUT VERIFY → ACCEPTANCE VERIFY → PAYMENT VERIFY → SETTLEMENT → WALLET RECEIPT VERIFY → RECONCILIATION → COST FINALIZATION → NET VALUE VERIFY → PAYOUT → BANK RECEIPT VERIFY → ECONOMIC FINALITY`

## Five economic thresholds

1. **Scientific proof** — €0 → €0.01 VNEV.
2. **Repeatability** — 10 separate real runs with positive net value.
3. **Economic engine proof** — ≥ €0.10/hour net.
4. **Utility** — ≥ €0.50/hour net.
5. **First serious target** — ≥ €1.00/hour VERIFIED NET ECONOMIC VALUE.

Long-term headline metric: **Verified Banked Net Value™** — net value that has actually reached the verified payout/bank account.

## €0 capital rule

v0.1 requires **zero new capital outlay**. No paid API, paid database, paid hosting, paid proxy, mandatory deposit/bond, paid pitch/bid/proof/submission, subscription-only connector, trading capital, gas paid by the worker, or pay-to-work source may be required for the first proof.

The rule is evaluated for the **exact intended action**, not just the platform. A platform may contain both free and paid actions.

Default runtime: local Python + SQLite + public/free sources + GitHub for source truth and CI.

> No capital required → No capital at risk → Earn before spend.

## Market qualification core

Before an opportunity can execute it must pass:

`DISCOVERY OPEN → CANONICAL OPEN → FUNDED → CLAIMABLE → EXACT-ACTION €0 → AGENT POLICY VERIFIED → COUNTRY ELIGIBLE → ACCEPTANCE KNOWN → PAYOUT KNOWN → INTEGRITY SCAN → SCORE >= 85 → AUTHORITY/HUMAN THRESHOLD`

Any unknown critical field is HOLD. Stale, unfunded, paid-entry, policy-prohibited or credential-exfiltration opportunities are rejected.

Opportunity score:
- funding certainty 25,
- zero-capital purity 20,
- claimability 15,
- acceptance clarity 15,
- payout clarity 10,
- agent compatibility 5,
- task simplicity 5,
- payout speed 5.

## Security and authority

Public task/repository content is untrusted data. Requests to expose system prompts, environment variables, private keys, seed phrases, credentials, cookies, tokens or signing material are automatic rejection triggers.

Economic Principal, agent identity and payout identity are separate concepts. Account creation, KYC/tax, withdrawal-address setup, public identity commitments and money movement remain Human Threshold™ events unless narrowly delegated.

## Current implementation

Core modules include:
- `aec/economics.py` — VNEV/VBNV and economic thresholds;
- `aec/shadow.py` — fail-closed shadow qualification;
- `aec/opportunity_integrity.py` — canonical funding/claimability/policy/security gates and 100-point score;
- `aec/action_gate.py` — exact-action zero-capital enforcement;
- `aec/market_evidence.py` — timestamped canonical market evidence records and competition fields;
- `aec/receipts.py` — separate wallet and bank receipt evidence schemas;
- `connectors/taskmarket.py` — zero-cost read-only Taskmarket discovery/canonical task connector.

Research and reference documents:
- `docs/RESEARCH_SYNTHESIS_2026-08-22.md`;
- `docs/REFERENCE_SYSTEMS.md`;
- `docs/SOURCE_REGISTRY.md`;
- `docs/PRODUCT_CONSTITUTION.md`.

## Governance

AEC™ inherits ENGÜRÜ governance discipline:

`state → claim → evidence → next action`

Final judgments never exceed evidence:

- **PASS** — required evidence exists.
- **HOLD** — evidence, external completion, or Human Threshold™ is pending.
- **BLOCKED** — a real constraint prevents safe progress.

`Task completed ≠ money earned.`  
`Money promised ≠ money settled.`  
`Wallet settlement ≠ banked value.`

## Open-core boundary

Public core: domain contracts, policy/authority logic, economics, verification, reconciliation, evidence schema, test suite, connector SDK.

Private operational data: credentials, private keys, seed phrases, live account identities, proprietary opportunity intelligence, private economic memory, fraud signals, banking details, and company accounting data.

## Status

**STATE — HOLD — HUMAN THRESHOLD / REAL-WORLD PROOF**  
**CLAIM —** Market qualification, exact-action zero-capital enforcement, adversarial opportunity screening, receipt separation and a zero-cost Taskmarket read connector are now represented in the public core.  
**EVIDENCE —** Real external earning, acceptance, settlement, reconciliation and bank receipt have not yet been proven. CI for the latest commits must also be independently verified before a technical PASS is claimed.  
**NEXT ACTION —** Revalidate one current Taskmarket bounty through the read connector and hard gates, obtain Human Threshold approval for external identity/wallet setup, then run The One Cent Test™.

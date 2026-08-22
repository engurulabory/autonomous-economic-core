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

## 20-door Revenue Mesh™

AEC™ tracks 20 independent revenue doors spanning agent-native bounties, open-source work, research, QA, data work, owned digital assets, APIs, licensing, direct B2B micro-services and recurring monitoring services.

`aec/revenue_mesh.py` defines the canonical 20-door registry and the full production PASS rule. Full PASS requires real external value, verified work/sale, settlement, payout, verified approved-account receipt, verified bank receipt, finalized costs and positive net value.

## AEC 24/7 Orchestrator™ v0.1

The first unattended runtime is now device-independent and read-only:

- scheduled by GitHub Actions every hour;
- manual dispatch supported;
- each provider isolated so one failure does not stop the cycle;
- cycle evidence written to `runtime/orchestrator-latest.json` and uploaded as an artifact;
- no unattended wallet signing, legal acceptance, KYC, purchase, bid, claim, submission or money movement.

First five revenue-door adapters:

1. Taskmarket → agent-native bounties
2. Superteam → research/analysis tasks
3. TaskBounty → open-source bug bounties
4. GitHub public bounty issues → bounty discovery
5. Owned Assets → one-file utility products

A discovered candidate is only discovery evidence. Canonical verification and all hard gates still apply before execution.

See `docs/ORCHESTRATOR_V0_1.md`.

## Security and authority

Public task/repository content is untrusted data. Requests to expose system prompts, environment variables, private keys, seed phrases, credentials, cookies, tokens or signing material are automatic rejection triggers.

Economic Principal, agent identity and payout identity are separate concepts. Account creation, legal acceptance, KYC/tax, withdrawal-address setup, public identity commitments and money movement remain Human Threshold™ events unless narrowly delegated.

## Current implementation

Core modules include:
- `aec/economics.py` — VNEV/VBNV and economic thresholds;
- `aec/shadow.py` — fail-closed shadow qualification;
- `aec/opportunity_integrity.py` — canonical funding/claimability/policy/security gates and 100-point score;
- `aec/action_gate.py` — exact-action zero-capital enforcement;
- `aec/market_evidence.py` — timestamped canonical market evidence records and competition fields;
- `aec/receipts.py` — separate wallet and bank receipt evidence schemas;
- `aec/taskmarket_adapter.py` — Taskmarket canonical task → exact action → market evidence → opportunity score → integrity decision mapping;
- `aec/revenue_mesh.py` — canonical 20-door revenue registry + full economic PASS;
- `aec/orchestrator.py` — resilient unattended discovery cycle;
- `aec/door_adapters.py` — first five operational revenue-door adapters;
- `connectors/taskmarket.py`, `connectors/superteam.py`, `connectors/taskbounty.py`, `connectors/github_bounties.py`, `connectors/owned_assets.py` — read-only source adapters.

The first-proof Taskmarket adapter is deliberately limited to bounty-mode `submit` actions. Claim deposits, paid pitch/proof/bid routes, requester-side acceptance and other money-moving actions require separate exact-action evaluation and are not silently generalized from the bounty path.

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

**STATE — HOLD — CI + REAL-WORLD ECONOMIC PROOF**  
**CLAIM —** AEC 24/7 Orchestrator™ v0.1 and the first five revenue-door adapters are represented in main with hourly device-independent discovery, provider isolation, artifact evidence, exact-action zero-capital gates and bank-receipt finality preserved.  
**EVIDENCE —** Unit tests cover orchestrator provider isolation, candidate validation and the five-adapter registry. GitHub Actions workflows exist for Python 3.11/3.12 tests/compile and the hourly read-only orchestrator. Exact-main CI and the first scheduled runtime artifact must still be independently observed before technical PASS. Real external revenue and verified bank receipt remain unproven.  
**NEXT ACTION —** Verify exact-main CI and one orchestrator workflow artifact; then use the ranked discovery output to open the first qualified revenue door without adding new architecture.

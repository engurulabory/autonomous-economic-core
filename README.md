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

## 20-door Revenue Mesh™

AEC™ tracks 20 independent revenue doors spanning agent-native bounties, open-source work, research, QA, data work, owned digital assets, APIs, licensing, direct B2B micro-services and recurring monitoring services.

`aec/revenue_mesh.py` defines the canonical 20-door registry and the full production PASS rule. Full PASS requires real external value, verified work/sale, settlement, payout, verified approved-account receipt, verified bank receipt, finalized costs and positive net value.

## AEC 24/7 Orchestrator™ v0.1

The device-independent scheduler runs hourly and isolates source failures:

- Taskmarket → agent-native bounties
- Superteam → research/analysis tasks
- TaskBounty → open-source bug bounties
- GitHub public bounty issues → discovery
- Owned Assets → one-file utility products

Discovery remains read-only. A discovered candidate is evidence, not execution permission.

## AEC Worker Runtime™ v0.1

Qualified work now has a persistent execution path:

`QUALIFIED EVIDENCE → JOB QUEUE → WORKER REGISTRY → CAPABILITY MATCH → ASSIGNMENT → EXECUTION → VERIFICATION → RETRY/HOLD → EVIDENCE`

Runtime properties:

- SQLite persistent queue + append-only job event evidence;
- exact capability matching;
- bounded retries with fail-closed exhaustion;
- Human Threshold jobs enter HOLD until explicit release;
- provider/worker exceptions become evidence-backed retry states;
- discovery cannot enqueue execution without `QUALIFIED` state + evidence id.

First three execution workers:

1. **Production Worker** — controlled-workspace artifact production/materialization with SHA-256 evidence.
2. **QA / DoneCheck Worker** — measurable file/acceptance verification.
3. **Settlement Collector** — independent-counterparty settlement evidence, direct cost and VNEV collection; bank finality remains separate.

The hourly workflow now boots the worker registry as well as discovery and uploads both runtime status artifacts. GitHub-hosted runners are ephemeral, so GitHub Actions is a scheduler/runtime probe, not yet the authoritative durable economic job-state store. Durable cloud queue state is required before unattended external writes are enabled.

See `docs/ORCHESTRATOR_V0_1.md` and `docs/WORKER_RUNTIME_V0_1.md`.

## Security and authority

Public task/repository content is untrusted data. Requests to expose system prompts, environment variables, private keys, seed phrases, credentials, cookies, tokens or signing material are automatic rejection triggers.

Economic Principal, agent identity and payout identity are separate concepts. Account creation, legal acceptance, KYC/tax, withdrawal-address setup, public identity commitments and money movement remain Human Threshold™ events unless narrowly delegated.

## Current implementation

Core modules include:
- `aec/economics.py` — VNEV/VBNV and economic thresholds;
- `aec/shadow.py` — fail-closed shadow qualification;
- `aec/opportunity_integrity.py` — canonical funding/claimability/policy/security gates;
- `aec/action_gate.py` — exact-action zero-capital enforcement;
- `aec/market_evidence.py` — timestamped canonical market evidence;
- `aec/receipts.py` — wallet/bank receipt separation;
- `aec/taskmarket_adapter.py` — Taskmarket canonical mapping;
- `aec/revenue_mesh.py` — 20-door revenue registry + full economic PASS;
- `aec/orchestrator.py` — resilient unattended discovery cycle;
- `aec/door_adapters.py` — first five operational revenue-door adapters;
- `aec/worker_runtime.py` — persistent queue, worker registry, capability matching, retry and evidence;
- `aec/execution_pipeline.py` — QUALIFIED evidence → worker queue bridge;
- `aec/execution_workers.py` — Production, QA/DoneCheck and Settlement Collector workers.

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

**STATE — HOLD — EXACT-MAIN CI + DURABLE CLOUD STATE + REAL-WORLD ECONOMIC PROOF**  
**CLAIM —** AEC now contains the 24/7 discovery orchestrator, 20-door Revenue Mesh, persistent Worker Runtime v0.1, qualification bridge, bounded retry/evidence ledger, and the first three execution workers.  
**EVIDENCE —** Tests cover queue assignment, capability matching, Human Threshold release, bounded retry exhaustion, controlled production, DoneCheck acceptance, anti-self-economy settlement, and QUALIFIED-only execution admission. Exact-main GitHub Actions must still show a verifiable successful run before technical PASS. No real banked external revenue has yet been proven.  
**NEXT ACTION —** Verify exact-main CI and hourly runtime artifacts, then add the durable cloud job-state backend and feed one truly QUALIFIED job through Production → QA/DoneCheck → Settlement evidence without relaxing Human Threshold or €0 gates.

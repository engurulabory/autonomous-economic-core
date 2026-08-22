# AUTONOMOUS ECONOMIC CORE™

**Verified economic agency core for lawful, policy-governed autonomous digital value creation.**

AEC™ is an open-core research and engineering project by Engürü Lab. Its first scientific objective is intentionally small and strict:

> **€0 → €0.01 VERIFIED BANKED NET VALUE (VBNV)**

The system does not count promises, dashboard balances, test credits, self-transfers, promotional value, wallet-only balances, or unreconciled gross revenue as banked economic finality.

## Canonical economic loop

`DISCOVER → SOURCE VERIFY → AUTHORITY VERIFY → POLICY VERIFY → ELIGIBILITY → ECONOMIC ESTIMATE → SELECT → EXECUTE → OUTPUT VERIFY → ACCEPTANCE VERIFY → PAYMENT VERIFY → SETTLEMENT → WALLET RECEIPT VERIFY → RECONCILIATION → COST FINALIZATION → PAYOUT → APPROVED ACCOUNT RECEIPT → BANK RECEIPT VERIFY → VERIFIED BANKED NET VALUE → ECONOMIC FINALITY`

## v1.1 target

AEC v1.1 targets evidence-backed 100/100 in three technical domains plus one real-world finality proof:

1. **Architecture / Governance — 100/100 by acceptance evidence.**
2. **Orchestrator + Worker Runtime — 100/100 by exact-main CI/runtime evidence.**
3. **Persistent 7/24 unattended execution — 100/100 by durable-state and 24-cycle evidence.**
4. **Economic Finality Proof — at least €0.01 Verified Banked Net Value from an independent external counterparty.**

See `docs/V1_1_ACCEPTANCE.md`.

## €0 capital rule

The first proof requires **zero new capital outlay**. No paid API, paid database, paid hosting, paid proxy, mandatory deposit/bond, paid pitch/bid/proof/submission, subscription-only connector, trading capital, worker-paid gas, or pay-to-work source may be required.

The rule is evaluated for the exact intended action, not merely the platform.

> No capital required → No capital at risk → Earn before spend.

## Market qualification core

Before an opportunity can execute it must pass:

`DISCOVERY OPEN → CANONICAL OPEN → FUNDED → CLAIMABLE → EXACT-ACTION €0 → AGENT POLICY VERIFIED → COUNTRY ELIGIBLE → ACCEPTANCE KNOWN → PAYOUT KNOWN → INTEGRITY SCAN → SCORE >= 85 → AUTHORITY/HUMAN THRESHOLD`

Unknown critical fields are HOLD. Stale, unfunded, paid-entry, policy-prohibited or credential-exfiltration opportunities are rejected.

## 20-door Revenue Mesh™

AEC tracks 20 independent revenue doors spanning agent-native bounties, open-source work, research, QA, data work, owned digital assets, APIs, licensing, direct B2B micro-services and recurring monitoring services.

## AEC 24/7 Orchestrator™

The device-independent scheduler runs hourly and isolates source failures. Initial live discovery adapters cover Taskmarket, Superteam, TaskBounty, GitHub public bounty issues and Owned Assets.

Discovery remains evidence, not execution permission.

## AEC Worker Runtime™

Qualified work follows:

`QUALIFIED EVIDENCE → JOB QUEUE → WORKER REGISTRY → CAPABILITY MATCH → ASSIGNMENT → EXECUTION → VERIFICATION → RETRY/HOLD → EVIDENCE`

First execution workers:

1. **Production Worker** — controlled artifact production/materialization with SHA-256 evidence.
2. **QA / DoneCheck Worker** — measurable acceptance verification.
3. **Settlement Collector** — independent-counterparty settlement, cost and VNEV evidence; bank finality remains separate.

## AEC Durable State Core™ v1.1

v1.1 adds the control-plane primitives required for safe unattended operation:

- idempotency keys to suppress duplicate economic actions;
- exclusive expiring leases for multi-worker coordination;
- worker heartbeats and stalled-worker detection;
- dead-letter capture for terminal failures;
- tamper-evident SHA-256 hash-chain audit events;
- authenticated HTTPS remote-state client;
- reference zero-capital Cloudflare Worker + D1 durable-state gateway and schema;
- hourly durable-state health/audit probe whose evidence is uploaded with the orchestrator artifacts.

SQLite remains the local/reference backend. GitHub-hosted runners remain ephemeral compute. Remote durable state must be deployed and observed before persistent 7/24 PASS is claimed.

## Economic Finality Core™ v1.1

`aec/economic_finality.py` requires independent external counterparty, verified work/sale, acceptance, settlement reference, payout reference, approved-account receipt, bank receipt, known fees/taxes, completed reconciliation and positive net value.

The One Cent Test™ passes only when **Verified Banked Net Value ≥ €0.01**.

## Governance

AEC inherits ENGÜRÜ governance discipline:

`state → claim → evidence → next action`

- **PASS** — required evidence exists.
- **HOLD** — evidence, external completion, Human Threshold or observation window is pending.
- **BLOCKED** — a real constraint prevents safe progress.

`Task completed ≠ money earned.`  
`Money promised ≠ money settled.`  
`Wallet settlement ≠ banked value.`

## Current implementation

Core modules include:

- `aec/economics.py` — VNEV/VBNV thresholds;
- `aec/opportunity_integrity.py` — funding/claimability/policy/security gates;
- `aec/action_gate.py` — exact-action zero-capital enforcement;
- `aec/market_evidence.py` — canonical market evidence;
- `aec/receipts.py` — wallet/bank receipt separation;
- `aec/revenue_mesh.py` — 20-door revenue registry;
- `aec/orchestrator.py` / `aec/door_adapters.py` — unattended discovery;
- `aec/worker_runtime.py` — queue, registry, capability matching, bounded retry and evidence;
- `aec/execution_pipeline.py` — QUALIFIED evidence → execution bridge;
- `aec/execution_workers.py` — Production, QA/DoneCheck and Settlement Collector;
- `aec/runtime_control.py` — idempotency, leases, heartbeat, dead-letter and hash-chain audit;
- `aec/remote_state.py` — authenticated HTTPS durable-state client;
- `aec/economic_finality.py` — banked-economic-finality judgment;
- `deploy/cloudflare/` — reference Worker + D1 state gateway.

## Open-core boundary

Public core: contracts, governance, economics, verification, reconciliation, evidence schemas, tests and connector SDK.

Private operational data: credentials, private keys, seed phrases, live account identities, proprietary opportunity intelligence, private economic memory, fraud signals, banking details and accounting data.

## Status

**STATE — HOLD — v1.1 OBSERVATION / REAL-WORLD FINALITY**  
**CLAIM —** The v1.1 technical infrastructure required to pursue 100/100 is now represented in main: durable coordination primitives, remote durable-state gateway/client, supervisor controls, Economic Finality Core, hourly durable-state probe, Worker Runtime and 20-door Revenue Mesh.  
**EVIDENCE —** Unit tests cover the existing Worker Runtime plus v1.1 idempotency, exclusive leases, hash-chain audit, dead-lettering and economic-finality judgments. Exact-main CI, deployed remote-state health, 24 consecutive hourly cycles, cross-run queue persistence and one real banked external economic run remain required before the corresponding PASS judgments can be issued.  
**NEXT ACTION —** Verify exact-main CI; deploy/configure the zero-capital durable-state backend and GitHub secrets; observe durable hourly cycles; then execute The One Cent Test™ together and reconcile the first real bank receipt.

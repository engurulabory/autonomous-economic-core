# AUTONOMOUS ECONOMIC CORE™

**Verified economic agency core for lawful, policy-governed autonomous digital value creation.**

AEC™ is an open-core research and engineering project by Engürü Lab. Its first scientific objective is intentionally small and strict:

> **€0 → €0.01 VERIFIED BANKED NET VALUE (VBNV)**

The system does not count promises, dashboard balances, test credits, self-transfers, promotional value, wallet-only balances, or unreconciled gross revenue as banked economic finality.

## Canonical economic loop

`DISCOVER → SOURCE VERIFY → AUTHORITY VERIFY → POLICY VERIFY → ELIGIBILITY → ECONOMIC ESTIMATE → SELECT → EXECUTE → OUTPUT VERIFY → ACCEPTANCE VERIFY → PAYMENT VERIFY → SETTLEMENT → WALLET RECEIPT VERIFY → RECONCILIATION → COST FINALIZATION → PAYOUT → APPROVED ACCOUNT RECEIPT → BANK RECEIPT VERIFY → VERIFIED BANKED NET VALUE → ECONOMIC FINALITY`

## v1.1 target

AEC v1.1 uses evidence-backed acceptance rather than subjective readiness scores:

1. **Architecture / Governance — 100/100 only when every canonical gate has PASS evidence.**
2. **Orchestrator + Worker Runtime — 100/100 only with exact-main CI and controlled end-to-end runtime evidence.**
3. **Persistent 7/24 unattended execution — 100/100 only with deployed durable state, cross-invocation persistence, recovery proof and 24 consecutive hourly PASS cycles.**
4. **Economic Finality Proof — PASS only with at least €0.01 Verified Banked Net Value from an independent external counterparty.**

`aec/v11_acceptance.py` is the machine-readable technical score contract. `docs/V1_1_ACCEPTANCE.md` is the canonical acceptance specification.

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

The device-independent scheduler runs hourly and isolates source failures. Initial discovery adapters cover Taskmarket, Superteam, TaskBounty, GitHub public bounty issues and Owned Assets.

Discovery remains evidence, not execution permission.

## AEC Worker Runtime™

Qualified work follows:

`QUALIFIED EVIDENCE → JOB QUEUE → WORKER REGISTRY → CAPABILITY MATCH → ASSIGNMENT → EXECUTION → VERIFICATION → RETRY/HOLD → EVIDENCE`

First execution workers:

1. **Production Worker** — controlled artifact production/materialization with SHA-256 evidence.
2. **QA / DoneCheck Worker** — measurable acceptance verification.
3. **Settlement Collector** — independent-counterparty settlement, cost and VNEV evidence; bank finality remains separate.

The remote runtime reuses these workers against the durable queue. Worker or durable post-processing failures are converted into bounded retry evidence instead of silently leaving a job successful.

## AEC Durable State Core™ v1.1

The Cloudflare Worker + D1 reference backend now represents the full durable job lifecycle required for commissioning:

- authenticated QUALIFIED-only durable enqueue;
- idempotency keys to suppress duplicate economic actions;
- exclusive expiring leases for multi-worker coordination;
- capability-scoped job leasing, assignment, start, verification and finish;
- Human Threshold HOLD/release carrying authority evidence;
- worker heartbeats and stale-worker detection;
- watchdog recovery of missing/expired worker leases;
- bounded retries and terminal dead-letter capture;
- SHA-256 checked small-artifact round-trip for controlled one-file work products;
- tamper-evident linear hash-chain audit and verification;
- durable scheduler-cycle history for the v1.1 24-hour gate;
- Cloudflare cron watchdog independent of the user's device and GitHub runner lifetime.

`aec/remote_state.py` is the authenticated HTTPS client. `aec/remote_worker_runtime.py` executes the existing workers against the durable queue.

The hourly GitHub workflow automatically performs:

`DISCOVERY → DURABLE HEALTH/AUDIT → CROSS-RUN CANARY → CONTROLLED QUALIFIED EXECUTION CANARY → REMOTE WORKERS → DURABLE CYCLE RECORD`

The controlled acceptance canary is deliberately non-economic. It proves queue → Production → durable artifact → QA/DoneCheck → evidence without pretending to prove revenue.

SQLite remains the local/reference backend. GitHub-hosted runners remain ephemeral compute. D1 deployment and observation are required before persistent 7/24 PASS is claimed.

## Cloud commissioning package

Repository-side deployment is encoded in `.github/workflows/deploy-cloudflare.yml` and `deploy/cloudflare/`.

No Cloudflare credential, runtime bearer token, wallet key, seed phrase or banking data is committed. Account-bound secrets remain Human Threshold commissioning inputs.

See `docs/V1_1_DURABLE_RUNTIME.md`.

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
- `aec/runtime_control.py` — local/reference idempotency, leases, heartbeat, dead-letter and hash-chain audit;
- `aec/remote_state.py` — authenticated durable job/artifact/control client;
- `aec/remote_worker_runtime.py` — durable execution runner;
- `aec/v11_acceptance.py` — evidence-driven 100/100 technical scoring;
- `aec/economic_finality.py` — banked-economic-finality judgment;
- `deploy/cloudflare/` — Worker + D1 durable-state gateway, schema and cron template;
- `scripts/durable_canary.py` — cross-invocation state survival proof;
- `scripts/seed_v1_1_acceptance_canary.py` — controlled QUALIFIED production/QA proof seed;
- `scripts/record_runtime_cycle.py` — durable 24-cycle observation ledger;
- `scripts/verify_cloudflare_bundle.py` — deployment-bundle CI gate.

## Open-core boundary

Public core: contracts, governance, economics, verification, reconciliation, evidence schemas, tests and connector SDK.

Private operational data: credentials, private keys, seed phrases, live account identities, proprietary opportunity intelligence, private economic memory, fraud signals, banking details and accounting data.

## Status

**STATE — HOLD — HUMAN COMMISSIONING + OBSERVATION + REAL-WORLD FINALITY**  
**CLAIM —** The repository-side v1.1 commissioning package is implemented: evidence-driven scoring, full durable job lifecycle, D1 schema, authenticated gateway/client, remote worker execution, controlled production→QA canary, cross-invocation canary, watchdog/recovery, durable cycle history, Cloudflare deployment workflow and Economic Finality Core are represented in main.  
**EVIDENCE —** CI definitions now test Python 3.11/3.12, compile all Python runtime code, validate the D1 schema/gateway contract and syntax-check the Cloudflare Worker. Exact-main CI still needs an observable successful run. Cloud deployment, cross-invocation survival, 24 consecutive hourly cycles and a real banked external economic run are external evidence gates and therefore remain HOLD.  
**NEXT ACTION —** Human Threshold commissioning only: authorize the Cloudflare account, create/select the zero-cost D1 database and store scoped credentials/secrets without exposing them in chat. Then dispatch the prepared deployment workflow. From that point the system automatically collects the controlled execution, persistence and 24-cycle evidence. After technical evidence closes, execute The One Cent Test™ together and reconcile the first real bank receipt.

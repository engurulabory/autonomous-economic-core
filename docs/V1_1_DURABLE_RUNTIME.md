# AEC™ v1.1 — Durable Runtime & Finality Commissioning

## State

The repository contains the zero-dependency durable-state reference implementation required for the v1.1 acceptance gates. Deployment credentials and the first real banked economic run remain external commissioning evidence.

## Runtime architecture

`GitHub schedule → Revenue Mesh discovery → Durable State probe → durable canary → Remote Worker Runner → cycle record`

Cloudflare reference control plane:

`Worker HTTPS gateway → D1 jobs/events/idempotency/leases/heartbeats/dead-letter/artifacts/audit/runtime_cycles`

The local SQLite runtime remains a reference and test backend. It is not the source of truth for unattended cloud execution.

## Durable State contracts

The Cloudflare gateway provides:

- authenticated QUALIFIED-only job enqueue;
- idempotency-key reservation;
- atomic lease acquisition with expiry;
- capability-scoped durable job leasing;
- STARTED / VERIFYING / OUTCOME evidence transitions;
- Human Threshold HOLD/release with authority evidence id;
- bounded retries and automatic BLOCKED/dead-letter on exhaustion;
- worker heartbeat and stale-worker query;
- watchdog recovery of jobs whose lease disappeared or expired;
- SHA-256 verified small-artifact persistence for v1.1 one-file work products;
- tamper-evident linear audit chain with concurrency conflict retry;
- durable scheduler-cycle history for the 24-hour acceptance gate.

No secret, wallet key, seed phrase, banking identity or Cloudflare credential is committed.

## Remote worker runtime

`aec/remote_worker_runtime.py` reuses the existing capability-scoped execution workers against the remote durable queue.

The first three workers remain:

1. Production Worker — controlled artifact production;
2. QA / DoneCheck Worker — measurable verification;
3. Settlement Collector — external settlement evidence and VNEV collection.

A completed production job may include an explicit `next_verify` contract. The runtime persists the produced artifact to durable storage and creates a deterministic idempotent QA job tied to the original qualification evidence. It does not invent settlement evidence or bypass Human Threshold.

## 7/24 proof instruments

The hourly workflow records six evidence artifacts:

- `orchestrator-latest.json`
- `worker-runtime-latest.json`
- `durable-state-latest.json`
- `durability-canary-latest.json`
- `remote-worker-latest.json`
- `v1_1-cycle-latest.json`

A fixed controlled queue canary has no matching worker capability and therefore remains QUEUED. Once the same job is observed in a later scheduler invocation, the cross-invocation durability gate can PASS without performing an external economic action.

`runtime_cycles` preserves scheduler history. v1.1 persistent execution receives its 24-hour gate only after 24 distinct GitHub scheduler cycles are observed as PASS.

## Cloudflare deployment boundary

Deployment is defined by `.github/workflows/deploy-cloudflare.yml` and `deploy/cloudflare/`.

The workflow requires four secrets:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `AEC_D1_DATABASE_ID`
- `AEC_STATE_TOKEN`

After deployment, the runtime also needs:

- `AEC_STATE_URL` — deployed HTTPS Worker URL
- `AEC_STATE_TOKEN` — same randomly generated bearer secret

These values are commissioning data and must never be committed.

## Human Threshold — intentionally last

Only after repository CI is clean, the remaining human commissioning steps are:

1. authorize/connect the Cloudflare account;
2. create or select the zero-cost D1 database if it does not exist;
3. create narrowly scoped Cloudflare API credentials and a random AEC state token;
4. store the required values as repository secrets;
5. dispatch the durable-state deployment workflow once;
6. store the resulting Worker HTTPS URL as `AEC_STATE_URL`;
7. observe the scheduled runtime and 24-hour durability evidence.

No human action is required before these steps for the repository-side implementation.

## Economic Finality

Infrastructure readiness is not economic proof.

The One Cent Test™ remains:

`independent external counterparty → verified work/sale → acceptance → settled payment → payout → approved account receipt → bank receipt → fees/cost reconciliation → VBNV >= €0.01 → PASS`

A dashboard balance, promise, self-transfer, promotional value or wallet-only balance cannot close v1.1 Economic Finality.

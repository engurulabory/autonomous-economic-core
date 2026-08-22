# AEC™ v1.1 — Live Commissioning Runbook

## State

HOLD — live external commissioning required.

## Goal

Turn the repository-complete v1.1 package into observable production evidence without weakening Human Threshold™, €0 capital, authority, settlement or bank-finality rules.

## Human Threshold — Cloudflare bootstrap

1. Sign in to Cloudflare on the Free plan.
2. Create a D1 database named `aec-durable-state`.
3. Prefer EU jurisdiction when available and appropriate for the operating account/data policy.
4. Create a Worker named `aec-durable-state`.
5. Bind the D1 database to the Worker with binding name `DB`.
6. Load `deploy/cloudflare/schema.sql` into the D1 database.
7. Connect the Worker build source to `engurulabory/autonomous-economic-core`, production branch `main`, root directory `deploy/cloudflare`, with no build command and deploy command `npx wrangler deploy`.
8. Keep non-production/preview builds disabled for the first commissioning pass so preview branches cannot touch the production D1 state.
9. Create a strong secret named `AEC_STATE_TOKEN` in the Worker. Never paste the value into chat or commit it.
10. Record the Worker HTTPS URL. The public `/health` endpoint should return an object with `ok: true`, service `aec-durable-state`, version `1.1`.

No paid plan, card charge, paid add-on, Workers Paid upgrade or other capital outlay is required for this first proof. If Cloudflare presents a required payment before the listed actions can continue, stop and classify the commissioning step HOLD/BLOCKED pending review.

## Human Threshold — GitHub secrets

After the Worker is live, add repository Actions secrets:

- `AEC_STATE_URL` = deployed Worker HTTPS base URL
- `AEC_STATE_TOKEN` = the same Worker secret value

Never commit either value into source files, screenshots, issues or chat.

## Automated commissioning sequence

The hourly/manual `aec-orchestrator` workflow then runs:

`DISCOVERY → LOCAL REFERENCE RUNTIME → DURABLE HEALTH/AUDIT PROBE → CROSS-RUN DURABILITY CANARY → REMOTE WORKERS → DURABLE CYCLE RECORD → EVIDENCE ARTIFACT`

## Canary evidence

The canary must prove a controlled, non-economic job can traverse the durable queue without Human Threshold:

`QUALIFIED CANARY → durable enqueue → Production Worker → durable artifact → QA/DoneCheck Worker → evidence`

The canary cannot be counted as economic value.

## Cross-run persistence gate

At least one canary/job marker must survive runner termination and be observed in a later independent scheduler invocation.

## Recovery gate

Deliberately inject or observe one bounded provider/worker failure and prove:

`failure → retry/HOLD/BLOCKED as appropriate → lease expiry/recovery → no duplicate economic action → evidence`

Terminal failures must reach dead-letter rather than loop forever.

## 24-cycle gate

Persistent 7/24 unattended execution remains HOLD until 24 consecutive scheduled hourly cycles are observed with:

- remote health PASS;
- no authoritative state loss;
- no duplicate execution;
- audit chain valid;
- worker heartbeat present;
- cross-run persistence proven;
- secrets absent from artifacts/log output.

## Technical 100/100 gate

Architecture/Governance and Orchestrator/Worker Runtime can only receive 100/100 after exact-main CI and the corresponding runtime evidence satisfy `docs/V1_1_ACCEPTANCE.md`.

## Economic Finality — The One Cent Test™

After technical commissioning:

`REAL EXTERNAL COUNTERPARTY → REAL WORK/SALE → ACCEPTANCE → PAYMENT SETTLED → PAYOUT → APPROVED ACCOUNT RECEIPT → BANK RECEIPT → COST/FEE RECONCILIATION → VBNV >= €0.01 → PASS`

Task completion, promises, promotional credit, self-transfer, marketplace balance or wallet-only balance do not satisfy v1.1 banked finality.

## Final release judgment

AEC™ v1.1 is fully PASS only when:

1. Architecture / Governance = evidence-backed 100/100;
2. Orchestrator + Worker Runtime = evidence-backed 100/100;
3. Persistent 7/24 unattended execution = evidence-backed 100/100;
4. Economic Finality has at least one independent real run with Verified Banked Net Value >= €0.01.

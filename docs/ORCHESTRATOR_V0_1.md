# AEC 24/7 Orchestrator™ v0.1

## Intent

Run revenue discovery independently of the operator device. The v0.1 scheduler is read-only and fail-closed: it discovers and records opportunities but performs no unattended wallet signing, account creation, legal acceptance, purchase, bid, claim, submission, payout configuration, KYC, or money movement.

## Runtime

GitHub Actions schedule:

- workflow: `.github/workflows/orchestrator.yml`
- cadence: hourly at minute 17 UTC
- manual trigger: supported
- permissions: `contents: read`
- evidence: `runtime/orchestrator-latest.json` uploaded as a workflow artifact for 14 days

Scheduled cloud execution is device-independent but not a hard real-time SLA. Provider or GitHub scheduling delays are recorded as runtime evidence rather than hidden.

## First five revenue-door adapters

1. `taskmarket` → `agent_native_bounties`
2. `superteam` → `research_analysis_tasks`
3. `taskbounty` → `open_source_bug_bounties`
4. `github_bounties` → `documentation_bounties`
5. `owned_assets` → `one_file_utilities`

These five are the first operational discovery set, not the entire 20-door Revenue Mesh™.

## Fail-closed behavior

A provider failure is isolated to that provider. The cycle continues across the remaining doors and records:

- `PASS` — adapter returned one or more candidates;
- `HOLD` — adapter ran successfully but returned no current candidates;
- `BLOCKED` — provider or adapter failed.

A discovered candidate is not automatically executable. Each candidate still requires canonical verification, exact-action €0 evaluation, automation policy, country eligibility, acceptance/payout path, integrity scan, score and authority/Human Threshold gates.

## Economic PASS

Orchestrator health is not economic success.

Full production economic PASS remains:

`REAL EXTERNAL COUNTERPARTY → VERIFIED WORK/ASSET → ACCEPTED/SOLD → PAYMENT SETTLED → PAYOUT ELIGIBLE → PAYOUT EXECUTED → APPROVED ACCOUNT RECEIPT VERIFIED → BANK RECEIPT VERIFIED → DIRECT COSTS FINALIZED → POSITIVE NET VALUE`

No dashboard balance, promise, submission, accepted task, wallet display or payout eligibility alone may be called full PASS.

## Next expansion

After v0.1 proves reliable discovery, expand the 20-door mesh in evidence-led batches. Do not add unattended financial writes until each provider's exact action and authority model has its own explicit gate and tests.

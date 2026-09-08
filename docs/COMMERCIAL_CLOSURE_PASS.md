# AEC Commercial Closure & Revenue Evolution Pass™

## Canonical loop

`Demand Proof → Revenue Door → Outcome Contract → Execution → DoneCheck™ → Distribution → Customer Acceptance → Invoice → Settlement → Bank Evidence → Net Margin → Learning`

## Placement

This is not a new product or repository. It is an AEC core extension:

- `aec/commercial_closure.py` — fail-closed commercial gates, saturation decisions and capability evolution.
- `scripts/run_commercial_closure.py` — runtime evidence pass.
- `tests/test_commercial_closure.py` — acceptance tests.
- `.github/workflows/orchestrator.yml` — invokes the pass during each orchestrator run and uploads the evidence artifact.

## Commercial PASS gate

PASS requires a real independent counterparty, accepted output, invoice evidence, settled payment, approved-account receipt, bank receipt, complete reconciliation and positive verified banked net value in EUR or USD.

Until this chain is complete, the economic system remains HOLD.

## Market observation and saturation

AEC evaluates multiple signals together: opportunity decline, competitor density, price, conversion, acquisition cost, net margin, repeat rate and demand shift. One signal is not enough to declare saturation.

Result classes:

`KEEP / EXTEND / REPOSITION / PAUSE / RETIRE`

## Revenue capability evolution

AEC follows:

`REUSE → EXTEND → ADAPTER → NEW_REVENUE_AGENT`

A new Revenue Agent is eligible only when repeated verified demand exists, current capability cannot deliver, extension/adapter are insufficient, expected net value is positive, distribution and settlement paths are ready, DoneCheck™ is defined and policy is safe.

The runtime pass is intentionally fail-closed. It does not invent market evidence. Existing Revenue Mesh™ discovery and future verified market evidence feeds must supply the observations. Critical payment, contract, legal and irreversible actions remain Human Threshold™ decisions.

## Governance

`state → claim → evidence → next action`

The system is verified-learning, not unrestricted self-improvement:

`Observe → Evidence → Hypothesis → Controlled Change → Test → DoneCheck™ → Economic Validation → Adopt / Revert`

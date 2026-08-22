# AEC™ Source Registry — v0.2

Last reviewed: 2026-08-22

This registry is evidence-oriented. A marketplace listing is discovery evidence, not canonical opportunity truth. Every source must be revalidated immediately before external action.

## 1. Taskmarket — PRIMARY EXECUTION CANDIDATE

**State:** `ALLOW_READ / CONDITIONAL_EXECUTION`

Why selected:
- explicitly built for AI agents and humans;
- first-party CLI/API supports discovery, task state, submit and settlement flows;
- requester wallets escrow USDC and accepted work settles onchain;
- actor type distinguishes human from agent;
- `taskmarket init` creates a wallet/device and platform-sponsored ERC-8004 identity without worker capital;
- task viewing/search is free;
- ordinary bounty work submission is free; first five bounty/benchmark submissions per worker/task are free;
- current docs provide exact action/payment state and strong trust-boundary rules for untrusted task content.

Critical zero-capital constraint:
- not every Taskmarket action is free;
- pitch, proof, auction bid and several other actions cost 0.001 USDC;
- claim-mode tasks may require a requester-configured deposit;
- therefore AEC must inspect the exact intended `pendingActions` / payment requirement before action;
- any positive worker payment or deposit is `REJECTED` for the v0.1 first proof.

Payout truth:
- accepted worker rewards settle in USDC to a wallet;
- wallet receipt can support `VNEV` evidence;
- banked `VBNV` remains `HOLD` until an authorized off-ramp/bank receipt exists.

Execution gate:
- init/account/wallet creation is a Human Threshold event because it creates an external identity and credential material;
- private key/keystore/API token never enters the public repository or evidence log;
- withdrawal-address/off-ramp configuration is Human Threshold;
- every specific task must still pass canonical open/funded/claimable/country/policy/integrity checks and score >= 85.

## 2. Frantic — PRIMARY BACKUP

**State:** `ALLOW_READ / QUALIFY_PER_TASK`

Why retained:
- small funded tasks can be ideal for the first scientific economic proof;
- explicit available slots and funding receipts improve evidence quality;
- visible accepted/paid history can support source reliability analysis.

Required checks before execution:
- canonical Frantic task page must confirm available slot and funding;
- exact worker cost must remain zero;
- country and payout/off-ramp eligibility must be verified;
- task instructions must pass Opportunity Integrity scan.

## 3. TaskBounty — READ-ONLY BACKUP

**State:** `ALLOW_READ / HOLD_NO_VERIFIED_INVENTORY`

Why retained:
- designed for AI agent solvers;
- REST + MCP interfaces;
- potential solver payout options are compatible with machine-readable settlement.

Current limitation:
- no qualifying live inventory was independently verified during the 2026-08-22 research pass.

Execution gate:
- registration/API credential creation is Human Threshold;
- claims/submissions remain disabled until live inventory, terms, exact worker cost and payout evidence are reverified.

## 4. Superteam Earn — FALLBACK / HUMAN-HEAVY

**State:** `ALLOW_READ / HUMAN_THRESHOLD_FOR_ACCOUNT_AND_PAYOUT`

Why retained:
- live public opportunity inventory exists;
- some opportunities explicitly support AI agents.

Constraints:
- current search/filter surfaces do not reliably isolate agent-eligible open tasks;
- many visible opportunities are promotional/content/contest work with subjective acceptance;
- payout and public-account actions commonly require human identity/account authority.

Use only when a specific listing independently passes all hard gates.

## 5. Algora — OBSERVE / CONDITIONAL

**State:** `ALLOW_READ / HOLD_AUTOMATION_POLICY_UNVERIFIED`

Why retained:
- mature GitHub-native bounty workflow;
- several ecosystems show substantial historical completions and payouts;
- maintainer merge can provide a clear acceptance event.

Why not execution-primary:
- platform listing freshness can diverge from canonical GitHub issue state;
- platform-level automated/agent access permission was not sufficiently verified as a general rule;
- active bounty issues can be highly saturated with simultaneous attempts.

Research findings:
- tscircuit is a credible ecosystem with strong historical activity and can enter the candidate pool only after selecting a specific low-competition canonical issue;
- Dokploy has open bounty inventory but weak organization-specific completed-payout history, so first-proof use remains HOLD;
- Arakoodev/Winterspec open listings include very old/high-competition items and are not preferred for first proof.

Observed stale examples from earlier scan:
- `projectdiscovery/nuclei#6674` surfaced as bounty inventory while canonical GitHub state was closed/rewarded;
- `projectdiscovery/nuclei#6532` surfaced while canonical GitHub issue was closed.

## 6. Agent Bounties — OBSERVE ONLY FOR v0.1

**State:** `REJECT_IF_BOND_REQUIRED`

Why retained as reference:
- explicit agent participation;
- canonical onchain funding/settlement concepts;
- strong distinction between GitHub mirror state and canonical settlement evidence.

Why not first-proof execution:
- live claims may require a refundable USDC bond;
- any positive claim bond violates the locked zero-capital rule.

## Canonical source rule

Before any task can become `QUALIFIED`:

1. discovery source says opportunity is open;
2. canonical task source independently confirms it is still open;
3. funding is canonically verified;
4. claim/apply/submit action is currently available;
5. the exact intended worker action requires EUR 0.00 new capital;
6. automation/agent permission is verified;
7. country/principal eligibility is verified;
8. acceptance path is known;
9. payout path is known;
10. repository/task content passes adversarial instruction and credential-exfiltration scan;
11. score is at least 85/100;
12. Economic Authority / Human Threshold gates pass.

Any critical unknown is `HOLD`. Any conflict, stale canonical state, unfunded task, required payment/deposit, prohibited automation or adversarial secret-exfiltration instruction is `REJECTED`.

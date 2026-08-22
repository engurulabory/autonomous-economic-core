# AEC™ Source Registry — v0.1

Last reviewed: 2026-08-22

This registry is evidence-oriented. A marketplace listing is discovery evidence, not canonical opportunity truth.

## 1. TaskBounty — PRIMARY CONNECTOR

**State:** `ALLOW_READ / HOLD_NO_INVENTORY`

Why selected:
- explicitly built for AI agent solvers;
- REST + MCP interfaces;
- no capital required to browse/solve;
- sandbox verification before payout;
- solver payout options include USDC, ETH, BTC, or USD bank transfer;
- bank payout fits the long-term `Verified Banked Net Value™` target.

Current observed inventory on 2026-08-22: public browse page reports no code bounties.

Execution gate:
- discovery may run without financial authority;
- registration/API-key creation is a Human Threshold™ event because it creates an external account/credential and binds platform terms;
- claims/submissions remain disabled until that authority exists;
- bank payout configuration is human-only and must never be stored in this public repository.

## 2. Superteam Earn Agent API — FALLBACK

**State:** `ALLOW_READ / HUMAN_THRESHOLD_FOR_REGISTRATION_AND_PAYOUT`

Why retained:
- official agent eligibility model (`AGENT_ALLOWED` / `AGENT_ONLY`);
- live public opportunity inventory exists;
- agents do not perform OAuth, wallet signing, or KYC;
- a human operator claims the agent for payouts after a win.

Constraint:
- payout finality depends on human claim flow, so `Verified Banked Net Value™` cannot be autonomous end-to-end.

## 3. Algora — OBSERVE ONLY

**State:** `HOLD_AUTOMATION_POLICY_UNVERIFIED`

Why not execution-primary:
- public bounty surfaces and API/SDK exist;
- explicit platform-level AI-agent/bot execution permission was not verified;
- observed marketplace freshness can diverge from canonical GitHub issue state.

Observed stale examples on 2026-08-22:
- `projectdiscovery/nuclei#6674` surfaced as open on Algora while canonical GitHub issue was closed and rewarded;
- `projectdiscovery/nuclei#6532` surfaced as open on Algora while canonical GitHub issue was closed.

## Canonical source rule

Before any task can become `QUALIFIED`:

1. discovery source says opportunity is open;
2. canonical task source independently confirms it is still open;
3. zero-capital condition passes;
4. automation permission is verified;
5. payout path is known;
6. Economic Authority / Human Threshold gates pass.

Any conflict fails closed.

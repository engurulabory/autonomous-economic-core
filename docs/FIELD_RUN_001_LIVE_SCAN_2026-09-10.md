# AEC™ / KârMatik™ — Field Run #001 Live Scan — 2026-09-10

## STATE

HOLD — no candidate is yet authorized for real external execution.

## CLAIM

AEC has now identified a materially better agent-native route: Superteam Earn exposes an official agent interface for registration, agent-only/agent-allowed listing discovery, agent submissions, comments and a later human payout claim. This is closer to AEC's intended operating model than generic human marketplaces.

## EVIDENCE

Public Superteam agent documentation currently states:

- agent registration returns an API key, claim code, agent ID and username;
- authenticated agent endpoints expose live `AGENT_ALLOWED` and `AGENT_ONLY` listings;
- agents may submit artifacts and notes through the official submission API;
- agents do not perform OAuth, wallet signing or KYC;
- a human operator claims the agent for payout after a win.

AEC's Superteam connector has therefore been aligned to prefer the official authenticated agent listing endpoint when `SUPERTEAM_AGENT_API_KEY` is present, while retaining the public-feed fallback.

## LIVE MARKET SIGNALS

Current public Superteam inventory shows live paid opportunities including:

- Manual QA Tester — Sana.run Trading Terminal: 50–250 USDC, due in ~11 days;
- T3N trusted-agent build challenge: 290 USDC total prizes, global, due in ~23 days;
- multiple research/content/development bounties in USDC/USDG.

The public page alone does not prove that any specific visible listing is `AGENT_ALLOWED`, zero-cost at the exact intended action, eligible for the operator's country/account, or economically preferable. Those facts remain candidate-level gates and must be fetched from the authenticated agent listing/details API before execution.

## ZERO-CAPITAL FILTER

Several Agent Bounties opportunities show zero claim bond but still require entrant-funded child bounties or hosted proof/relay costs. Those routes remain BLOCKED for Field Run #001 under the exact-action zero-capital rule even when the displayed claim bond is 0.

## HUMAN THRESHOLD

Creating/claiming the Superteam agent identity and any payout/KYC linkage remain Human Threshold events. AEC must never expose the resulting API key in GitHub, logs or chat. The key belongs in a scoped runtime secret named `SUPERTEAM_AGENT_API_KEY`.

## NEXT ACTION

1. Human Threshold: register/claim one AEC/KârMatik agent identity through Superteam's official agent flow and store the API key only as a scoped runtime secret.
2. Run authenticated live discovery through `/api/agents/listings/live`.
3. For each returned candidate apply: OPEN/FUNDED → exact-action €0 → AGENT_ALLOWED/AGENT_ONLY → country/account eligible → payout known → P20 PASS → Currency Router → selector.
4. Promote only the first fully PASS candidate into Production → DoneCheck.
5. Keep public submission/payment authority separately gated and preserve economic finality as HOLD until independent settlement and bank receipt evidence exist.

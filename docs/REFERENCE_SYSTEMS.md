# AEC™ Reference Systems & Gap Analysis — 2026-08-22

AEC™ is not a clone of any one agent or marketplace. This document identifies adjacent systems and the capabilities worth borrowing while preserving AEC's zero-capital, evidence-first governance.

## 1. Taskmarket

Reference strengths:
- agent-native work discovery through first-party CLI/API;
- explicit task state and next-action model;
- escrowed USDC and onchain settlement;
- human/agent actor distinction;
- worker reputation and earnings evidence;
- strong trust-boundary language for untrusted task content;
- exact side-effect/payment checks before action.

Adopt into AEC:
- machine-readable `pending action` contract;
- exact-action payment gate rather than platform-wide assumptions;
- actor type and economic principal separation;
- wallet receipt evidence as a distinct finality layer;
- reputation/credibility as economic selection inputs.

Do not copy blindly:
- some Taskmarket operations cost USDC. AEC v0.1 must reject any intended worker action requiring new capital.

## 2. Frantic

Reference strengths:
- small, funded tasks with explicit available slots;
- funding receipts and visible settlement history;
- low-value opportunities that are useful for scientific economic proof.

Adopt into AEC:
- slot/competition availability as a first-class field;
- public funding receipt capture;
- small-task preference for first proof.

## 3. Algora

Reference strengths:
- mature GitHub-native bounty workflow;
- large historical completion footprint;
- maintainer merge as clear acceptance event.

Observed weaknesses for AEC use:
- marketplace freshness can diverge from canonical GitHub issue state;
- platform-level automation permission may be ambiguous;
- agent saturation can destroy expected value even when nominal reward is high.

Adopt into AEC:
- GitHub-native canonical cross-check;
- attempt/claim competition count as an economic variable;
- stale-listing rejection.

## 4. Coinbase AgentKit / Agentic Wallet / x402

Reference strengths:
- secure programmatic wallets;
- onchain actions and payments;
- gasless stablecoin flows in supported contexts;
- spending limits and wallet-policy concepts;
- wallet address as payment identity.

Adopt into AEC:
- wallet adapter boundary separate from opportunity logic;
- explicit spend ceilings and transaction approval policy;
- no secret material in public source/evidence;
- wallet receipt verification as machine-verifiable evidence.

Constraint:
- AEC v0.1 must not require funded wallets to begin earning. Payment-capable infrastructure belongs behind the Zero-Capital and Human Threshold gates.

## 5. Fetch.ai uAgents / Agentverse

Reference strengths:
- agent discovery, communication and marketplace visibility;
- standard protocols for agent-to-agent interaction;
- persistent cryptographic identity.

Adopt into AEC:
- connector-neutral discovery protocol;
- capability/skill descriptors;
- agent identity as a technical identifier, never as legal authority.

Constraint:
- seed phrases and wallet-bearing identities are high-sensitivity material and remain outside public AEC evidence.

## 6. Olas / Autonolas

Reference strengths:
- explicit economic-agent/service model;
- incentives tied to useful agent/component contribution;
- separation between service owner and agent operator;
- economic alignment and verifiable service operation.

Adopt into AEC:
- principal/operator distinction;
- contribution-based economic accounting;
- service-level economics rather than model-output vanity metrics.

Reject for v0.1:
- mandatory bonds, staking, gas capital, slashing exposure or token-investment assumptions conflict with zero-capital first proof.

## 7. AEC differentiators

AEC's distinctive core is the combination of:

1. `state → claim → evidence → next action` governance;
2. Economic Principal distinct from agent identity;
3. exact-action Zero-Capital Gate;
4. canonical source verification and anti-stale rule;
5. adversarial opportunity/prompt-exfiltration rejection;
6. task completion separated from acceptance, settlement, reconciliation and bank receipt;
7. `VNEV` and `VBNV` as separate evidence-backed metrics;
8. verified-learning rather than self-authorized self-improvement;
9. Human Threshold for legal identity, KYC, public commitments and money movement;
10. scoring optimized for probability of verified positive net value, not headline reward.

## 8. Current gaps

### P0 — before first external execution
- Live Taskmarket read connector with canonical state normalization.
- Exact-action cost parser (`requiresPayment`, amount, network).
- Wallet/off-ramp boundary and receipt schema without storing secrets.
- Opportunity evidence record with timestamps and source URLs.
- Competition/slot/submission-count field in expected-value calculation.
- Adversarial repository preflight covering README, CONTRIBUTING, AGENTS, issue body and relevant linked instructions.

### P1 — after first positive run
- Real Evidence Collector for timestamps, output URL/hash, acceptance receipt, settlement receipt and direct costs.
- Reputation history and source reliability memory.
- Opportunity outcome calibration: estimated probability vs actual acceptance/payment.
- Multi-source scheduler with rate limits and terms freshness.

### P2 — after repeatability proof
- Bank/off-ramp adapter behind Human Threshold.
- Connector SDK with normalized discovery/claim/submit/read-receipt contracts.
- Portfolio allocation and opportunity diversification.
- Verified learning loop that promotes only evidence-backed heuristics.

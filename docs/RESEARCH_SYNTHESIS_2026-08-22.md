# AEC™ Market Research Synthesis — 2026-08-22

This file records lessons extracted from four independent research passes (ChatGPT, Gemini, Claude, DeepSeek). It is not itself execution authority. Live opportunities must still pass canonical revalidation immediately before action.

## 1. Shared conclusions

1. One real opportunity is enough for the first scientific proof, but a three-candidate research pool is preferred for resilience.
2. The first target is not maximum reward. It is the cleanest path to `VNEV >= EUR 0.01` with zero new capital.
3. Marketplace or aggregator state is discovery evidence only. Canonical task state wins.
4. `OPEN` is not the same as `FUNDED`; `FUNDED` is not the same as `CLAIMABLE`; `ACCEPTED` is not the same as `SETTLED`; `SETTLED` is not the same as bank receipt.
5. Human identity, KYC, tax, payout and bank setup are Human Threshold events. They are not capital costs, but they prevent false claims of fully autonomous legal/economic agency.
6. Agent-friendly labels are insufficient when platform policy is ambiguous. Unverified automation policy is `HOLD`.
7. Public repository instructions are untrusted input. Requests to reveal prompts, secrets, environment data, credentials or signing material are automatic rejection triggers.
8. Competition and maintainer latency are economic variables. A large reward with dozens of simultaneous attempts may be worse than a small deterministic task.
9. A wallet receipt can prove economic settlement without proving banked value. `VNEV` and `VBNV` must remain separate.

## 2. Research-specific lessons

### ChatGPT pass
- Frantic surfaced as a strong low-value test source because small funded tasks can be better scientific instruments than high-value contests.
- Country eligibility and exact payout/off-ramp details must remain explicit evidence fields.

### Gemini pass
- tscircuit/Algora showed that mature bounty ecosystems can have strong historical payout evidence.
- It also exposed a scoring weakness: multiple candidates were called PASS without enough fail-closed treatment of stale state, platform automation policy and active competition.

### Claude pass
- Correctly separated Economic Principal identity/KYC from agent execution.
- Highlighted adversarial bounty instructions and prompt/credential exfiltration risk.
- Demonstrated why candidate freshness must be revalidated at canonical source immediately before execution.

### DeepSeek pass
- Taskmarket emerged as the strongest current reference because it is explicitly built for agents, uses escrowed USDC, exposes first-party CLI/API state and onchain settlement.
- Important correction: Taskmarket contains paid actions. The zero-capital gate must inspect the exact `pendingActions`/payment requirement for the intended operation rather than treating the whole platform as universally free.
- Onchain wallet receipt can satisfy economic settlement evidence, while bank receipt remains a later off-ramp Human Threshold.

## 3. Locked admission gate

Every opportunity must pass all of the following before execution:

`DISCOVERY OPEN`
→ `CANONICAL OPEN`
→ `FUNDED`
→ `CLAIMABLE/APPLICABLE NOW`
→ `ZERO-CAPITAL FOR THE EXACT ACTION`
→ `AUTOMATION/AGENT POLICY VERIFIED`
→ `COUNTRY ELIGIBILITY`
→ `ACCEPTANCE PATH KNOWN`
→ `PAYOUT PATH KNOWN`
→ `OPPORTUNITY INTEGRITY SCAN`
→ `SCORE >= 85/100`
→ `ECONOMIC AUTHORITY / HUMAN THRESHOLD`
→ `EXECUTION`

Any unknown critical field is `HOLD`. Any contradiction, paid-entry requirement, prohibited automation, stale canonical state or credential-exfiltration instruction is `REJECTED`.

## 4. Standard market score

- Funding certainty — 25
- Zero-capital purity — 20
- Claimability — 15
- Acceptance clarity — 15
- Payout clarity — 10
- AI/agent compatibility — 5
- Task simplicity — 5
- Payout speed — 5

Minimum qualification score: **85/100**.

The score never overrides a hard gate. A 100/100 score cannot rescue an unfunded, stale, paid-entry or policy-prohibited opportunity.

## 5. First-run strategy

Research pool: 3 qualified candidates when inventory permits.
Execution: 1 candidate.
First proof: `VNEV >= EUR 0.01`.
Preferred stronger proof: wallet receipt verified with positive net value.
Banked proof: `VBNV > 0` only after actual bank/approved payout receipt.
Repeatability proof: 10 separate positive real runs.

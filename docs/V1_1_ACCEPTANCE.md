# AEC™ v1.1 — 100/100 Acceptance Gates

v1.1 is not awarded by design intent. Each 100/100 requires observable evidence.

## A. Architecture / Governance — 100/100

PASS requires all of the following:

1. Canonical state → claim → evidence → next action discipline.
2. Economic Principal, agent identity, payout identity and delegated authority remain separate.
3. Discovery cannot bypass qualification.
4. Exact-action €0 gate is fail-closed.
5. Country/policy/acceptance/payout unknowns are HOLD.
6. Credential/prompt-exfiltration patterns are rejected.
7. Idempotency prevents duplicate economic action.
8. Distributed leases prevent two workers owning one external action simultaneously.
9. Human Threshold blocks legal/KYC/signing/money movement unless narrowly delegated.
10. Worker capability matching is explicit.
11. Retry budgets are bounded; exhaustion enters BLOCKED/dead-letter.
12. Evidence events are durable and hash-chained.
13. Self-economy/promotional/fake-counterparty value cannot count as earned value.
14. Settlement, wallet receipt, approved-account receipt and bank receipt are separate facts.
15. Economic PASS requires positive reconciled net value.

## B. Orchestrator + Worker Runtime — 100/100

PASS requires:

1. 20-door registry represented.
2. At least five live discovery adapters boot independently.
3. One provider failure does not terminate the cycle.
4. Persistent Job Queue.
5. Worker Registry.
6. Capability Matching.
7. Assignment.
8. Execution.
9. Verification.
10. Retry.
11. Human Threshold HOLD/release.
12. Evidence ledger.
13. Idempotency key reservation.
14. Lease acquisition/release.
15. Worker heartbeat.
16. Dead-letter queue.
17. Tamper-evident audit chain.
18. Production Worker.
19. QA / DoneCheck Worker.
20. Settlement Collector.
21. Exact-main CI PASS on supported Python matrix.
22. One controlled QUALIFIED job traverses queue → worker → evidence in CI/runtime.

## C. Persistent 7/24 Unattended Execution — 100/100

PASS requires:

1. Runtime scheduling is device-independent.
2. Durable state survives individual compute-runner termination.
3. State backend health is probed from the scheduled runtime.
4. Authentication token is secret-managed; never committed.
5. Durable state uses HTTPS only.
6. Duplicate execution is prevented by idempotency + lease semantics.
7. Heartbeat identifies stalled workers.
8. Failed work reaches bounded retry/dead-letter rather than infinite loops.
9. Runtime artifacts expose operational status without exposing secrets.
10. At least 24 consecutive hourly scheduled cycles are observed without state loss.
11. A queued controlled job survives across two separate scheduler invocations.
12. Recovery after a deliberately failed worker/provider is demonstrated.

The reference zero-capital durable backend is Cloudflare Worker + D1 under `deploy/cloudflare/`. SQLite remains the local/reference backend. Other backends may be accepted if they preserve the same contracts.

## D. Economic Finality Proof — The One Cent Test™

Economic finality is a real-world test and cannot be satisfied by unit tests.

Required chain:

`EXTERNAL COUNTERPARTY → WORK/SALE VERIFIED → ACCEPTED → PAYMENT SETTLED → SETTLEMENT REFERENCE → PAYOUT EXECUTED → PAYOUT REFERENCE → APPROVED ACCOUNT RECEIPT → BANK RECEIPT → COST/FEE RECONCILIATION → VBNV >= €0.01 → PASS`

Not sufficient:

- task completed;
- requester promise;
- marketplace balance;
- promotional credit;
- self-transfer;
- wallet-only balance when the v1.1 finality claim is banked value;
- unreconciled gross revenue.

## v1.1 Release Judgment

AEC v1.1 is fully PASS only when A, B and C are 100/100 by evidence and D has at least one independent real economic run with Verified Banked Net Value ≥ €0.01.

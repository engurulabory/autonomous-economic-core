# AEC Worker Runtime™ v0.1

## Purpose

Turn qualified economic opportunities into bounded, evidence-producing jobs without letting discovery bypass governance.

Canonical path:

`QUALIFIED EVIDENCE → JOB QUEUE → WORKER REGISTRY → CAPABILITY MATCH → ASSIGNMENT → EXECUTION → VERIFICATION → RETRY/HOLD → EVIDENCE`

Discovery is not execution permission.

## Runtime components

### Persistent Job Queue

`aec/worker_runtime.py` implements a SQLite-backed queue and evidence ledger using Python standard library only.

States:

`QUEUED → ASSIGNED → RUNNING → VERIFYING → COMPLETED`

Exceptional states:

- `RETRY_WAIT` — bounded retry is permitted;
- `HOLD` — Human Threshold or incomplete evidence;
- `BLOCKED` — fail-closed terminal failure.

Every assignment, start, outcome, Human Threshold release and retry decision creates a `job_events` evidence record.

### Worker Registry + Capability Matching

Workers register immutable capability sets. Jobs are leased only to workers that advertise the exact requested capability. One worker cannot silently steal a different task class.

### Retry discipline

Each job carries a bounded `max_attempts`. Provider/runtime exceptions become `RETRY_WAIT`. When the retry budget is exhausted the job becomes `BLOCKED`; the runtime does not loop forever.

### Qualification bridge

`aec/execution_pipeline.py` requires:

- `qualification_state == QUALIFIED`;
- a non-empty qualification evidence id.

If Human Threshold is required, the job enters `HOLD`, never `QUEUED`, until explicit authority evidence releases it.

## First three execution workers

### 1. Production Worker

Capability: `produce_artifact`

v0.1 performs deterministic controlled-workspace artifact materialization. It cannot write outside `runtime/work`, cannot traverse parent directories, and records SHA-256 + byte count as evidence.

This is infrastructure for production, not a claim that general autonomous synthesis is solved.

### 2. QA / DoneCheck Worker

Capability: `verify_artifact`

Checks measurable acceptance criteria:

- file existence;
- min/max size;
- required text;
- forbidden text;
- optional SHA-256 equality.

Failure is `BLOCKED`; missing artifact is retryable.

### 3. Settlement Collector

Capability: `collect_settlement`

Collects only independent-counterparty settlement evidence. It rejects self-economy, retries unsettled payments, requires settlement id/currency/positive amount, records direct costs and VNEV, and keeps wallet/bank receipt flags separate.

Settlement completion is not bank finality.

## Cloud runtime

The hourly Orchestrator workflow boots both discovery and worker runtime status generation. Current v0.1 worker jobs are persistent when run against a durable SQLite store; GitHub-hosted runners themselves are ephemeral.

Therefore GitHub Actions is currently a device-independent scheduler and runtime probe, **not yet the authoritative durable job-state store**.

Before unattended external execution is enabled, cloud-persistent queue state must use a durable, auditable backend or a safe repository-native state mechanism. Do not treat Actions cache/artifacts as economic source of truth.

## Security boundary

v0.1 workers do not autonomously:

- accept external legal terms;
- perform KYC;
- expose secrets;
- sign arbitrary wallet messages;
- spend capital;
- transfer money;
- submit public external work without an execution adapter and authority gate.

## Acceptance target for v0.1

Worker Runtime v0.1 is technically ready for PASS only when:

1. unit tests pass on exact main;
2. hourly workflow boots the registry with 3 workers;
3. one controlled qualified job traverses queue → assignment → execution → evidence;
4. bounded retry and Human Threshold tests pass.

Economic PASS remains separate and requires real external revenue and finality evidence.

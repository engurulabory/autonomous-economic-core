# AEC/KârMatik — Specialist Capability Audit v1

## STATE

Repository execution plumbing is verified separately from specialist synthesis.

## Capability levels

- **L4 — Economically Verified Specialist:** repeated accepted work + settled/banked evidence.
- **L3 — Tool-backed Field Specialist:** domain worker can independently use required tools/sources and produce the deliverable.
- **L2 — Deterministic Specialist:** bounded domain transformation is implemented and tested locally.
- **L1 — Governed Production Route:** task class is recognized, qualified and can be routed through controlled artifact production + DoneCheck.
- **L0 — Catalog Only:** capability is named but has no executable route.

## Current truth

The canonical capability catalog contains low-risk work across QA, DATA, RESEARCH, CONTENT, CODE, MONITOR, ARTIFACT, AGENT_NATIVE and MICRO_SERVICE categories.

Current repository-native executable workers are:

1. **Production Worker** — controlled artifact materialization.
2. **QA / DoneCheck Worker** — measurable artifact verification.
3. **Settlement Collector** — external settlement evidence collection.
4. **Research & Verification Specialist Adapter™ v1** — invokes an approved research-tool contract, accepts only approved HTTPS source URLs, cross-checks verification terms, emits structured source evidence and hands the artifact to DoneCheck.

The Field Execution Bridge now separates **task capability** from **runtime capability**. A catalog task such as `docs-fix` is preserved in evidence while the current executable runtime route is `produce_artifact`. Unknown task capabilities fail closed.

## Specialist coverage judgment

### L1 — PASS
All current low-risk catalog capabilities can be represented as governed task classes and carried through the controlled production route when a valid deliverable has already been produced upstream.

### L2 — PARTIAL
Some transformations can already be deterministic through existing code paths and artifact handling, but there is not yet one dedicated deterministic executor for every catalog capability.

### L3 — PARTIAL / RESEARCH IMPLEMENTED
Research now has a dedicated tool-backed specialist adapter and end-to-end adapter → structured evidence → DoneCheck tests. Live L3 commissioning remains HOLD until one approved real research-tool provider is bound and the same path is proven on real public sources. Code, full Data, browser QA, Monitor and Machine Product specialist executors remain outside the current scope.

### L4 — HOLD
No specialist class may claim economically verified expertise before accepted external runs and banked evidence exist.

## Six-swarm readiness

| Swarm | Governed routing | Dedicated specialist executor | Field-economic proof |
|---|---|---|---|
| Code | PASS | HOLD | HOLD |
| Research | PASS | PASS (adapter) / HOLD (live tool binding) | HOLD |
| Data | PASS | PARTIAL | HOLD |
| QA | PASS | PARTIAL | HOLD |
| Monitor | PASS | HOLD | HOLD |
| Machine Product | PASS | HOLD | HOLD |

## Required field discipline

A task may enter internal execution only when:

`catalog capability → qualification PASS → specialist/deliverable evidence → produce_artifact → DoneCheck → authority gate → permitted delivery`

The generic Production Worker must never be described as the domain expert that created the content. It only materializes a deliverable already produced by a specialist/model/tool layer.

## Final pre-field conclusion

Core orchestration, queueing, capability governance, production materialization, verification, settlement evidence and economic finality are suitable for field commissioning.

The remaining expertise gap is **specialist synthesis/tool adapters**, not the economic control plane. The first field run should therefore select a task that can be completed with an already available specialist/tool surface and keep the adapter explicit in evidence.


## Research & Verification Specialist Adapter™ v1 — Locked scope

Canonical path:

`approved public-source set → research tool → source evidence → cross-source term verification → structured JSON artifact → SHA-256 evidence → DoneCheck`

Fail-closed boundaries:
- only approved HTTPS source URLs are accepted by the adapter contract;
- a tool-returned source outside the approved source set is BLOCKED;
- missing confirmations remain HOLD;
- tool invocation failure is bounded RETRY_WAIT;
- output remains inside the controlled runtime workspace;
- adapter completion is not economic acceptance or payment proof.

**Engineering judgment:** PASS.

**Live L3 judgment:** HOLD until one real approved research provider completes the same path against live public sources. This is a commissioning gate, not a new specialist-development program.

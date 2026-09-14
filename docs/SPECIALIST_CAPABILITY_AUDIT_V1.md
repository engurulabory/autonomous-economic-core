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

The Field Execution Bridge now separates **task capability** from **runtime capability**. A catalog task such as `docs-fix` is preserved in evidence while the current executable runtime route is `produce_artifact`. Unknown task capabilities fail closed.

## Specialist coverage judgment

### L1 — PASS
All current low-risk catalog capabilities can be represented as governed task classes and carried through the controlled production route when a valid deliverable has already been produced upstream.

### L2 — PARTIAL
Some transformations can already be deterministic through existing code paths and artifact handling, but there is not yet one dedicated deterministic executor for every catalog capability.

### L3 — HOLD
Dedicated tool-backed specialists for Code, Research, Data, QA browser execution, Monitor and Machine Product production are not yet all implemented as autonomous domain executors inside this repository.

### L4 — HOLD
No specialist class may claim economically verified expertise before accepted external runs and banked evidence exist.

## Six-swarm readiness

| Swarm | Governed routing | Dedicated specialist executor | Field-economic proof |
|---|---|---|---|
| Code | PASS | HOLD | HOLD |
| Research | PASS | HOLD | HOLD |
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

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Mapping


class GateState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


ARCHITECTURE_GATES = (
    "governance_discipline",
    "authority_identity_separation",
    "qualification_before_execution",
    "exact_action_zero_capital_fail_closed",
    "critical_unknowns_hold",
    "credential_exfiltration_rejected",
    "idempotency",
    "distributed_leases",
    "human_threshold",
    "capability_matching",
    "bounded_retry_dead_letter",
    "durable_hash_chained_evidence",
    "anti_fake_economy",
    "receipt_fact_separation",
    "positive_reconciled_net_required",
)

ORCHESTRATOR_GATES = (
    "twenty_door_registry",
    "five_live_discovery_adapters",
    "provider_failure_isolation",
    "persistent_job_queue",
    "worker_registry",
    "capability_matching",
    "assignment",
    "execution",
    "verification",
    "retry",
    "human_threshold_hold_release",
    "evidence_ledger",
    "idempotency_reservation",
    "lease_acquire_release",
    "worker_heartbeat",
    "dead_letter_queue",
    "tamper_evident_audit_chain",
    "production_worker",
    "qa_donecheck_worker",
    "settlement_collector",
    "exact_main_ci_pass",
    "controlled_qualified_job_traversal",
)

PERSISTENT_24_7_GATES = (
    "device_independent_schedule",
    "state_survives_runner_termination",
    "scheduled_backend_health_probe",
    "secret_managed_auth",
    "https_only",
    "duplicate_prevention",
    "heartbeat_stall_detection",
    "bounded_retry_dead_letter",
    "secret_safe_status_artifacts",
    "twenty_four_consecutive_hourly_pass_cycles",
    "cross_invocation_queued_job_survival",
    "failure_recovery_demonstrated",
)


@dataclass(frozen=True)
class DomainScore:
    domain: str
    passed: int
    total: int
    score: Decimal
    state: GateState
    missing: tuple[str, ...]
    blocked: tuple[str, ...]

    @property
    def score_text(self) -> str:
        return f"{self.score:.1f}/100"


@dataclass(frozen=True)
class V11TechnicalScorecard:
    architecture_governance: DomainScore
    orchestrator_worker_runtime: DomainScore
    persistent_24_7_execution: DomainScore

    def all_pass(self) -> bool:
        return all(
            domain.state is GateState.PASS
            for domain in (
                self.architecture_governance,
                self.orchestrator_worker_runtime,
                self.persistent_24_7_execution,
            )
        )


def score_domain(domain: str, required: tuple[str, ...], evidence: Mapping[str, bool | None | str]) -> DomainScore:
    if not required or len(required) != len(set(required)):
        raise ValueError("required gate names must be non-empty and unique")

    passed = 0
    missing: list[str] = []
    blocked: list[str] = []
    for gate in required:
        value = evidence.get(gate)
        if value is True or value == "PASS":
            passed += 1
        elif value is False or value == "BLOCKED":
            blocked.append(gate)
        elif value is None or value == "HOLD" or gate not in evidence:
            missing.append(gate)
        else:
            raise ValueError(f"invalid gate evidence for {gate}: {value!r}")

    score = (Decimal(passed) * Decimal(100) / Decimal(len(required))).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    if blocked:
        state = GateState.BLOCKED
    elif passed == len(required):
        state = GateState.PASS
    else:
        state = GateState.HOLD
    return DomainScore(domain, passed, len(required), score, state, tuple(missing), tuple(blocked))


def score_v11(
    *,
    architecture: Mapping[str, bool | None | str],
    orchestrator: Mapping[str, bool | None | str],
    persistent_24_7: Mapping[str, bool | None | str],
) -> V11TechnicalScorecard:
    return V11TechnicalScorecard(
        architecture_governance=score_domain("architecture_governance", ARCHITECTURE_GATES, architecture),
        orchestrator_worker_runtime=score_domain("orchestrator_worker_runtime", ORCHESTRATOR_GATES, orchestrator),
        persistent_24_7_execution=score_domain("persistent_24_7_execution", PERSISTENT_24_7_GATES, persistent_24_7),
    )

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from aec.economic_execution import production_job_payload, qualify_candidate
from aec.economic_learning_core import capability_by_id
from aec.execution_pipeline import QualifiedExecutionRequest
from aec.orchestrator import RevenueCandidate


class SubmissionHandoffState(str, Enum):
    READY_INTERNAL = "READY_INTERNAL"
    HOLD_HUMAN_THRESHOLD = "HOLD_HUMAN_THRESHOLD"
    READY_FOR_PERMITTED_SUBMISSION = "READY_FOR_PERMITTED_SUBMISSION"


@dataclass(frozen=True)
class DoneCheckContract:
    acceptance_criteria: tuple[str, ...]
    verification_instruction: str

    def __post_init__(self) -> None:
        if not self.acceptance_criteria or any(not item.strip() for item in self.acceptance_criteria):
            raise ValueError("at least one measurable acceptance criterion is required")
        if not self.verification_instruction.strip():
            raise ValueError("verification_instruction is required")


@dataclass(frozen=True)
class HumanThresholdEnvelope:
    required: bool
    reason: str
    permitted_submission_route: str
    authority_evidence_ref: str | None = None

    @property
    def released(self) -> bool:
        return not self.required or bool(self.authority_evidence_ref and self.authority_evidence_ref.strip())


@dataclass(frozen=True)
class FieldExecutionBridge:
    candidate: RevenueCandidate
    internal_request: QualifiedExecutionRequest
    donecheck: DoneCheckContract
    human_threshold: HumanThresholdEnvelope
    state: SubmissionHandoffState


def build_field_execution_bridge(
    candidate: RevenueCandidate,
    *,
    qualification_evidence_id: str,
    capability: str,
    output_path: str,
    content: str,
    acceptance_criteria: tuple[str, ...],
    verification_instruction: str,
    permitted_submission_route: str,
    authority_evidence_ref: str | None = None,
    extra_payload: dict[str, Any] | None = None,
) -> FieldExecutionBridge:
    """Bridge PASS-qualified economic work into production, DoneCheck and submission handoff.

    The requested task capability describes the domain work (for example docs-fix
    or research-mini). The runtime capability describes which executable worker
    can carry the already-prepared deliverable through the controlled queue.
    Current field production is intentionally routed through produce_artifact;
    specialist synthesis/tool use remains a separate, explicit upstream adapter.
    """
    decision = qualify_candidate(candidate)
    if not decision.can_enqueue_internal_work:
        raise ValueError(f"candidate is not PASS-qualified: {decision.state.value}: {decision.reason}")
    if not qualification_evidence_id.strip():
        raise ValueError("qualification_evidence_id is required")
    if not capability.strip():
        raise ValueError("capability is required")
    task_capability = capability_by_id(capability)
    if task_capability is None:
        raise ValueError("capability is not present in the canonical AEC capability catalog")
    if not task_capability.low_risk_digital or not task_capability.measurable_acceptance:
        raise ValueError("capability is outside the current low-risk measurable field boundary")
    if not permitted_submission_route.strip():
        raise ValueError("permitted_submission_route is required")

    payload = production_job_payload(candidate, output_path=output_path, content=content)
    payload["task_capability"] = capability
    payload["task_category"] = task_capability.category
    payload["specialist_synthesis_upstream"] = True
    if extra_payload:
        payload.update(extra_payload)

    internal = QualifiedExecutionRequest(
        capability="produce_artifact",
        payload=payload,
        qualification_state="QUALIFIED",
        qualification_evidence_id=qualification_evidence_id,
        # Keep internal materialization runnable. Authority is enforced at the
        # external handoff envelope below, not by blocking production itself.
        human_threshold_required=False,
    )
    donecheck = DoneCheckContract(acceptance_criteria, verification_instruction)
    envelope = HumanThresholdEnvelope(
        required=decision.human_threshold_required,
        reason=(
            "external authority required before submission/signing"
            if decision.human_threshold_required
            else "submission route may proceed only within verified platform policy"
        ),
        permitted_submission_route=permitted_submission_route,
        authority_evidence_ref=authority_evidence_ref,
    )
    if envelope.released:
        state = SubmissionHandoffState.READY_FOR_PERMITTED_SUBMISSION
    elif envelope.required:
        state = SubmissionHandoffState.HOLD_HUMAN_THRESHOLD
    else:
        state = SubmissionHandoffState.READY_INTERNAL

    return FieldExecutionBridge(candidate, internal, donecheck, envelope, state)

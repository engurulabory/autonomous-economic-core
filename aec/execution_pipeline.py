from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aec.worker_runtime import Job, SQLiteJobQueue


@dataclass(frozen=True)
class QualifiedExecutionRequest:
    capability: str
    payload: dict[str, Any]
    qualification_state: str
    qualification_evidence_id: str
    human_threshold_required: bool = False
    max_attempts: int = 3

    def __post_init__(self) -> None:
        if not self.capability.strip():
            raise ValueError("capability is required")
        if self.qualification_state != "QUALIFIED":
            raise ValueError("execution request requires QUALIFIED market/policy state")
        if not self.qualification_evidence_id.strip():
            raise ValueError("qualification evidence id is required")


def enqueue_execution(queue: SQLiteJobQueue, request: QualifiedExecutionRequest) -> Job:
    """Bridge verified qualification into the persistent worker queue.

    Discovery candidates cannot call this path without an explicit QUALIFIED state
    and evidence identifier. Human Threshold jobs enter HOLD, not execution.
    """
    payload = dict(request.payload)
    payload["qualification_evidence_id"] = request.qualification_evidence_id
    return queue.enqueue(
        request.capability,
        payload,
        max_attempts=request.max_attempts,
        human_threshold_required=request.human_threshold_required,
    )

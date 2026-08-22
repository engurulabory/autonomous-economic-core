from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from aec.worker_runtime import Job, JobState, WorkerOutcome, WorkerSpec


@dataclass(frozen=True)
class ProductionWorker:
    spec: WorkerSpec = WorkerSpec(
        worker_id="production-worker",
        capabilities=frozenset({"produce_artifact"}),
        autonomous=True,
    )

    def execute(self, job: Job) -> WorkerOutcome:
        payload = job.payload
        output_path = Path(str(payload.get("output_path", "")))
        content = payload.get("content")
        if not str(output_path).strip() or content is None:
            return WorkerOutcome(
                next_state=JobState.BLOCKED,
                reason="production payload missing output_path/content",
                evidence={},
            )
        if output_path.is_absolute() or ".." in output_path.parts:
            return WorkerOutcome(
                next_state=JobState.BLOCKED,
                reason="production output_path must stay inside runtime workspace",
                evidence={"output_path": str(output_path)},
            )

        resolved = Path("runtime/work") / output_path
        resolved.parent.mkdir(parents=True, exist_ok=True)
        data = content if isinstance(content, str) else json.dumps(content, sort_keys=True, indent=2)
        resolved.write_text(data, encoding="utf-8")
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        return WorkerOutcome(
            next_state=JobState.COMPLETED,
            reason="artifact produced in controlled runtime workspace",
            evidence={"artifact_path": str(resolved), "sha256": digest, "bytes": len(data.encode("utf-8"))},
        )


@dataclass(frozen=True)
class QADoneCheckWorker:
    spec: WorkerSpec = WorkerSpec(
        worker_id="qa-donecheck-worker",
        capabilities=frozenset({"verify_artifact"}),
        autonomous=True,
    )

    def execute(self, job: Job) -> WorkerOutcome:
        payload = job.payload
        artifact_path = Path(str(payload.get("artifact_path", "")))
        if not str(artifact_path).strip() or not artifact_path.exists() or not artifact_path.is_file():
            return WorkerOutcome(
                next_state=JobState.RETRY_WAIT,
                reason="artifact is not yet available for verification",
                evidence={"artifact_path": str(artifact_path)},
            )

        data = artifact_path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        failures: list[str] = []

        min_bytes = int(payload.get("min_bytes", 1))
        max_bytes = int(payload.get("max_bytes", 10_000_000))
        if len(data) < min_bytes:
            failures.append(f"artifact below min_bytes ({len(data)} < {min_bytes})")
        if len(data) > max_bytes:
            failures.append(f"artifact above max_bytes ({len(data)} > {max_bytes})")

        for required in payload.get("contains", []):
            if str(required) not in text:
                failures.append(f"missing required text: {required}")

        for forbidden in payload.get("forbidden", []):
            if str(forbidden) in text:
                failures.append(f"forbidden text present: {forbidden}")

        expected_sha256 = payload.get("sha256")
        digest = hashlib.sha256(data).hexdigest()
        if expected_sha256 and str(expected_sha256) != digest:
            failures.append("sha256 mismatch")

        if failures:
            return WorkerOutcome(
                next_state=JobState.BLOCKED,
                reason="DoneCheck verification failed",
                evidence={"failures": failures, "sha256": digest, "bytes": len(data)},
            )

        return WorkerOutcome(
            next_state=JobState.COMPLETED,
            reason="DoneCheck verification passed",
            evidence={"sha256": digest, "bytes": len(data), "checks": "PASS"},
        )


@dataclass(frozen=True)
class SettlementCollector:
    spec: WorkerSpec = WorkerSpec(
        worker_id="settlement-collector",
        capabilities=frozenset({"collect_settlement"}),
        autonomous=True,
    )

    def execute(self, job: Job) -> WorkerOutcome:
        payload: dict[str, Any] = job.payload
        if not bool(payload.get("external_counterparty")):
            return WorkerOutcome(
                next_state=JobState.BLOCKED,
                reason="settlement cannot count without an independent external counterparty",
                evidence={},
            )

        settled = bool(payload.get("settled"))
        settlement_id = str(payload.get("settlement_id", "")).strip()
        currency = str(payload.get("currency", "")).strip()
        amount = Decimal(str(payload.get("amount", "0")))
        direct_cost = Decimal(str(payload.get("direct_cost", "0")))

        if amount < 0 or direct_cost < 0:
            return WorkerOutcome(
                next_state=JobState.BLOCKED,
                reason="negative settlement values are invalid",
                evidence={},
            )

        if not settled:
            return WorkerOutcome(
                next_state=JobState.RETRY_WAIT,
                reason="settlement not yet final",
                evidence={"settled": False},
            )

        if not settlement_id or not currency or amount <= 0:
            return WorkerOutcome(
                next_state=JobState.HOLD,
                reason="settlement evidence incomplete",
                evidence={"settlement_id": settlement_id, "currency": currency, "amount": str(amount)},
            )

        vnev = amount - direct_cost
        evidence = {
            "settlement_id": settlement_id,
            "currency": currency,
            "settled_amount": str(amount),
            "direct_cost": str(direct_cost),
            "vnev": str(vnev),
            "wallet_receipt_verified": bool(payload.get("wallet_receipt_verified")),
            "bank_receipt_verified": bool(payload.get("bank_receipt_verified")),
        }

        # Settlement evidence can be complete while bank finality is still pending.
        return WorkerOutcome(
            next_state=JobState.COMPLETED,
            reason="external settlement evidence collected; bank finality remains a separate gate",
            evidence=evidence,
        )


DEFAULT_EXECUTION_WORKERS = (
    ProductionWorker(),
    QADoneCheckWorker(),
    SettlementCollector(),
)

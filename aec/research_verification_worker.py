from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from aec.worker_runtime import Job, JobState, WorkerOutcome, WorkerSpec


@dataclass(frozen=True)
class ResearchSource:
    url: str
    title: str
    extracted_text: str
    retrieved_at: str
    provider: str


class ResearchTool(Protocol):
    def research(self, *, question: str, source_urls: Sequence[str]) -> Sequence[ResearchSource]: ...


@dataclass(frozen=True)
class ResearchVerificationWorker:
    tool: ResearchTool
    spec: WorkerSpec = WorkerSpec(
        worker_id="research-verification-specialist-v1",
        capabilities=frozenset({"research_verify"}),
        autonomous=True,
    )

    def execute(self, job: Job) -> WorkerOutcome:
        payload = job.payload
        question = str(payload.get("question", "")).strip()
        source_urls = payload.get("source_urls")
        terms = payload.get("verification_terms")
        output_path = Path(str(payload.get("output_path", "")))

        if not question:
            return WorkerOutcome(JobState.BLOCKED, {}, "research question is required")
        if not isinstance(source_urls, list) or not source_urls or len(source_urls) > 8:
            return WorkerOutcome(JobState.BLOCKED, {}, "research requires 1-8 approved source URLs")
        if any(not isinstance(url, str) or not url.startswith("https://") for url in source_urls):
            return WorkerOutcome(JobState.BLOCKED, {}, "approved sources must use HTTPS")
        if not isinstance(terms, list) or not terms or len(terms) > 20:
            return WorkerOutcome(JobState.BLOCKED, {}, "research requires 1-20 verification terms")
        if any(not isinstance(term, str) or not term.strip() for term in terms):
            return WorkerOutcome(JobState.BLOCKED, {}, "verification terms must be non-empty strings")
        if not str(output_path).strip() or output_path.is_absolute() or ".." in output_path.parts:
            return WorkerOutcome(JobState.BLOCKED, {}, "research output_path must stay inside runtime workspace")

        try:
            sources = tuple(self.tool.research(question=question, source_urls=tuple(source_urls)))
        except Exception as exc:
            return WorkerOutcome(
                JobState.RETRY_WAIT,
                {"exception_type": type(exc).__name__},
                "research tool invocation failed",
            )

        approved = set(source_urls)
        normalized: list[dict[str, object]] = []
        confirmations: dict[str, set[str]] = {term: set() for term in terms}

        for source in sources:
            if source.url not in approved:
                return WorkerOutcome(
                    JobState.BLOCKED,
                    {"unexpected_source": source.url},
                    "research tool returned a source outside the approved source set",
                )
            text = " ".join(source.extracted_text.split())
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            matches: dict[str, str] = {}
            folded = text.casefold()
            for term in terms:
                index = folded.find(term.casefold())
                if index >= 0:
                    start = max(0, index - 120)
                    end = min(len(text), index + len(term) + 120)
                    matches[term] = text[start:end]
                    confirmations[term].add(source.url)
            normalized.append(
                {
                    "url": source.url,
                    "title": source.title,
                    "retrieved_at": source.retrieved_at,
                    "provider": source.provider,
                    "text_sha256": digest,
                    "matched_terms": matches,
                }
            )

        minimum_sources = int(payload.get("minimum_successful_sources", 1))
        minimum_confirmations = int(payload.get("minimum_confirmations_per_term", 1))
        unverified = [
            term for term in terms if len(confirmations[term]) < minimum_confirmations
        ]

        report = {
            "kind": "AEC_RESEARCH_VERIFICATION_V1",
            "question": question,
            "approved_source_urls": source_urls,
            "successful_sources": len(normalized),
            "minimum_confirmations_per_term": minimum_confirmations,
            "verified_terms": [term for term in terms if term not in unverified],
            "unverified_terms": unverified,
            "sources": normalized,
        }

        resolved = Path("runtime/work") / output_path
        resolved.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
        resolved.write_text(encoded, encoding="utf-8")
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        evidence = {
            "artifact_path": str(resolved),
            "sha256": digest,
            "successful_sources": len(normalized),
            "verified_terms": report["verified_terms"],
            "unverified_terms": unverified,
        }

        if len(normalized) < minimum_sources:
            return WorkerOutcome(JobState.HOLD, evidence, "insufficient verified research sources")
        if unverified:
            return WorkerOutcome(JobState.HOLD, evidence, "verification terms lack required independent confirmation")
        return WorkerOutcome(
            JobState.COMPLETED,
            evidence,
            "research tool evidence verified and structured output completed",
        )

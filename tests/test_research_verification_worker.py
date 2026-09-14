from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from aec.research_verification_worker import ResearchSource, ResearchVerificationWorker
from aec.worker_runtime import JobState, SQLiteJobQueue, run_worker_once


class FakeResearchTool:
    def research(self, *, question, source_urls):
        rows = {
            "https://a.example/fact": ResearchSource(
                "https://a.example/fact", "Source A",
                "Alpha price is 10 EUR. Beta is present.",
                "2026-09-14T10:00:00Z", "fake-tool",
            ),
            "https://b.example/fact": ResearchSource(
                "https://b.example/fact", "Source B",
                "Independent source confirms Alpha price is 10 EUR.",
                "2026-09-14T10:01:00Z", "fake-tool",
            ),
        }
        return tuple(rows[url] for url in source_urls)


class UnexpectedSourceTool:
    def research(self, *, question, source_urls):
        return (
            ResearchSource(
                "https://unexpected.example/fact", "Unexpected",
                "Alpha price is 10 EUR.", "2026-09-14T10:00:00Z", "fake-tool"
            ),
        )


class ResearchVerificationWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.tempdir.name)
        self.queue = SQLiteJobQueue("runtime/test.db")

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.tempdir.cleanup()

    def test_cross_source_verification_produces_structured_artifact(self):
        job = self.queue.enqueue(
            "research_verify",
            {
                "question": "What is the Alpha price?",
                "source_urls": ["https://a.example/fact", "https://b.example/fact"],
                "verification_terms": ["Alpha", "10 EUR"],
                "minimum_successful_sources": 2,
                "minimum_confirmations_per_term": 2,
                "output_path": "research/alpha.json",
            },
        )
        result = run_worker_once(self.queue, ResearchVerificationWorker(FakeResearchTool()))
        self.assertEqual(result.state, JobState.COMPLETED)
        self.assertTrue(Path("runtime/work/research/alpha.json").exists())
        evidence = self.queue.events(job.job_id)[-1].detail["evidence"]
        self.assertEqual(evidence["successful_sources"], 2)
        self.assertEqual(evidence["unverified_terms"], [])

    def test_unverified_term_holds_fail_closed(self):
        self.queue.enqueue(
            "research_verify",
            {
                "question": "Verify Gamma",
                "source_urls": ["https://a.example/fact", "https://b.example/fact"],
                "verification_terms": ["Gamma"],
                "output_path": "research/gamma.json",
            },
        )
        result = run_worker_once(self.queue, ResearchVerificationWorker(FakeResearchTool()))
        self.assertEqual(result.state, JobState.HOLD)

    def test_unapproved_source_blocks(self):
        self.queue.enqueue(
            "research_verify",
            {
                "question": "Verify Alpha",
                "source_urls": ["https://a.example/fact"],
                "verification_terms": ["Alpha"],
                "output_path": "research/alpha.json",
            },
        )
        result = run_worker_once(self.queue, ResearchVerificationWorker(UnexpectedSourceTool()))
        self.assertEqual(result.state, JobState.BLOCKED)

    def test_path_escape_blocks(self):
        self.queue.enqueue(
            "research_verify",
            {
                "question": "Verify Alpha",
                "source_urls": ["https://a.example/fact"],
                "verification_terms": ["Alpha"],
                "output_path": "../escape.json",
            },
        )
        result = run_worker_once(self.queue, ResearchVerificationWorker(FakeResearchTool()))
        self.assertEqual(result.state, JobState.BLOCKED)


if __name__ == "__main__":
    unittest.main()

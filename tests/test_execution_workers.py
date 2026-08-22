from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from aec.execution_workers import ProductionWorker, QADoneCheckWorker, SettlementCollector
from aec.worker_runtime import JobState, SQLiteJobQueue, run_worker_once


class ExecutionWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.tempdir.name)
        self.queue = SQLiteJobQueue("runtime/test.db")

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.tempdir.cleanup()

    def test_production_worker_creates_controlled_artifact(self):
        job = self.queue.enqueue(
            "produce_artifact",
            {"output_path": "demo/result.txt", "content": "hello economic world"},
        )
        result = run_worker_once(self.queue, ProductionWorker())
        self.assertEqual(result.state, JobState.COMPLETED)
        self.assertEqual(Path("runtime/work/demo/result.txt").read_text(), "hello economic world")
        evidence = self.queue.events(job.job_id)[-1].detail["evidence"]
        self.assertEqual(evidence["bytes"], len("hello economic world".encode()))

    def test_production_worker_rejects_path_escape(self):
        self.queue.enqueue("produce_artifact", {"output_path": "../escape.txt", "content": "x"})
        result = run_worker_once(self.queue, ProductionWorker())
        self.assertEqual(result.state, JobState.BLOCKED)

    def test_qa_worker_passes_measurable_acceptance(self):
        artifact = Path("artifact.html")
        artifact.write_text("<html>ISBN-10 validator</html>", encoding="utf-8")
        self.queue.enqueue(
            "verify_artifact",
            {
                "artifact_path": str(artifact),
                "contains": ["ISBN-10", "validator"],
                "forbidden": ["SECRET"],
                "min_bytes": 5,
            },
        )
        result = run_worker_once(self.queue, QADoneCheckWorker())
        self.assertEqual(result.state, JobState.COMPLETED)

    def test_qa_worker_blocks_failed_acceptance(self):
        artifact = Path("artifact.txt")
        artifact.write_text("hello", encoding="utf-8")
        self.queue.enqueue("verify_artifact", {"artifact_path": str(artifact), "contains": ["missing"]})
        result = run_worker_once(self.queue, QADoneCheckWorker())
        self.assertEqual(result.state, JobState.BLOCKED)

    def test_settlement_collector_records_external_settlement(self):
        job = self.queue.enqueue(
            "collect_settlement",
            {
                "external_counterparty": True,
                "settled": True,
                "settlement_id": "tx_123",
                "currency": "EUR",
                "amount": "1.00",
                "direct_cost": "0.10",
                "wallet_receipt_verified": True,
                "bank_receipt_verified": False,
            },
        )
        result = run_worker_once(self.queue, SettlementCollector())
        self.assertEqual(result.state, JobState.COMPLETED)
        evidence = self.queue.events(job.job_id)[-1].detail["evidence"]
        self.assertEqual(evidence["vnev"], "0.90")
        self.assertFalse(evidence["bank_receipt_verified"])

    def test_settlement_collector_retries_until_settled(self):
        self.queue.enqueue(
            "collect_settlement",
            {"external_counterparty": True, "settled": False, "amount": "1", "direct_cost": "0"},
            max_attempts=2,
        )
        result = run_worker_once(self.queue, SettlementCollector())
        self.assertEqual(result.state, JobState.RETRY_WAIT)

    def test_settlement_collector_rejects_self_economy(self):
        self.queue.enqueue(
            "collect_settlement",
            {"external_counterparty": False, "settled": True, "amount": "10", "direct_cost": "0"},
        )
        result = run_worker_once(self.queue, SettlementCollector())
        self.assertEqual(result.state, JobState.BLOCKED)


if __name__ == "__main__":
    unittest.main()

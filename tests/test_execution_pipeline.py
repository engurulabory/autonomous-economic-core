from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aec.execution_pipeline import QualifiedExecutionRequest, enqueue_execution
from aec.worker_runtime import JobState, SQLiteJobQueue


class ExecutionPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.queue = SQLiteJobQueue(Path(self.tempdir.name) / "worker.db")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_only_qualified_request_can_enter_execution_queue(self):
        with self.assertRaises(ValueError):
            QualifiedExecutionRequest(
                capability="produce_artifact",
                payload={},
                qualification_state="HOLD",
                qualification_evidence_id="ev-1",
            )

    def test_qualified_request_preserves_evidence_id(self):
        request = QualifiedExecutionRequest(
            capability="produce_artifact",
            payload={"output_path": "x.txt", "content": "x"},
            qualification_state="QUALIFIED",
            qualification_evidence_id="ev-42",
        )
        job = enqueue_execution(self.queue, request)
        self.assertEqual(job.state, JobState.QUEUED)
        self.assertEqual(job.payload["qualification_evidence_id"], "ev-42")

    def test_human_threshold_enters_hold_not_execution(self):
        request = QualifiedExecutionRequest(
            capability="collect_settlement",
            payload={"external_counterparty": True},
            qualification_state="QUALIFIED",
            qualification_evidence_id="ev-99",
            human_threshold_required=True,
        )
        job = enqueue_execution(self.queue, request)
        self.assertEqual(job.state, JobState.HOLD)
        self.assertTrue(job.human_threshold_required)


if __name__ == "__main__":
    unittest.main()

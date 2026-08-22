from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from aec.worker_runtime import (
    JobState,
    SQLiteJobQueue,
    WorkerOutcome,
    WorkerRegistry,
    WorkerSpec,
    run_registry_cycle,
    run_worker_once,
)


@dataclass(frozen=True)
class EchoWorker:
    spec: WorkerSpec = WorkerSpec("echo", frozenset({"echo"}))

    def execute(self, job):
        return WorkerOutcome(JobState.COMPLETED, {"value": job.payload["value"]}, "echo complete")


@dataclass(frozen=True)
class FailingWorker:
    spec: WorkerSpec = WorkerSpec("fail", frozenset({"fail"}))

    def execute(self, job):
        raise RuntimeError("temporary provider failure")


class WorkerRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = Path(self.tempdir.name) / "worker.db"
        self.queue = SQLiteJobQueue(self.db)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_enqueue_assign_execute_and_evidence(self):
        job = self.queue.enqueue("echo", {"value": 7})
        self.assertEqual(job.state, JobState.QUEUED)
        result = run_worker_once(self.queue, EchoWorker())
        self.assertIsNotNone(result)
        self.assertEqual(result.state, JobState.COMPLETED)
        events = self.queue.events(job.job_id)
        self.assertEqual([event.event for event in events], ["ENQUEUED", "ASSIGNED", "STARTED", "OUTCOME"])
        self.assertEqual(events[-1].detail["evidence"]["value"], 7)

    def test_capability_matching_does_not_steal_other_jobs(self):
        self.queue.enqueue("other", {"value": 1})
        self.assertIsNone(run_worker_once(self.queue, EchoWorker()))

    def test_human_threshold_holds_until_released(self):
        job = self.queue.enqueue("echo", {"value": 2}, human_threshold_required=True)
        self.assertEqual(job.state, JobState.HOLD)
        self.assertIsNone(run_worker_once(self.queue, EchoWorker()))
        released = self.queue.release_human_threshold(
            job.job_id, actor="human-authority", evidence={"approval": "yes"}
        )
        self.assertEqual(released.state, JobState.QUEUED)
        self.assertEqual(run_worker_once(self.queue, EchoWorker()).state, JobState.COMPLETED)

    def test_retry_budget_exhausts_fail_closed(self):
        job = self.queue.enqueue("fail", {}, max_attempts=2)
        first = run_worker_once(self.queue, FailingWorker())
        self.assertEqual(first.state, JobState.RETRY_WAIT)
        second = run_worker_once(self.queue, FailingWorker())
        self.assertEqual(second.state, JobState.BLOCKED)
        self.assertEqual(self.queue.get(job.job_id).attempts, 2)

    def test_registry_requires_unique_ids(self):
        with self.assertRaises(ValueError):
            WorkerRegistry((EchoWorker(), EchoWorker()))

    def test_registry_cycle_runs_each_capable_worker_once(self):
        self.queue.enqueue("echo", {"value": 3})
        registry = WorkerRegistry((EchoWorker(),))
        results = run_registry_cycle(self.queue, registry)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].state, JobState.COMPLETED)


if __name__ == "__main__":
    unittest.main()

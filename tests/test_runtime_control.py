from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aec.runtime_control import RuntimeControlPlane


class RuntimeControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.control = RuntimeControlPlane(Path(self.tempdir.name) / "control.db")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_idempotency_key_is_single_use(self):
        self.assertTrue(self.control.reserve_idempotency("door:1:submit", "job-1"))
        self.assertFalse(self.control.reserve_idempotency("door:1:submit", "job-2"))

    def test_lease_has_exclusive_owner_until_release(self):
        first = self.control.acquire_lease("job-1", "worker-a", ttl_seconds=30)
        self.assertIsNotNone(first)
        self.assertIsNone(self.control.acquire_lease("job-1", "worker-b", ttl_seconds=30))
        self.assertTrue(self.control.release_lease(first))
        second = self.control.acquire_lease("job-1", "worker-b", ttl_seconds=30)
        self.assertIsNotNone(second)

    def test_hash_chained_audit_verifies(self):
        self.control.append_audit("worker-a", "START", {"job": "1"})
        self.control.append_audit("worker-a", "DONE", {"job": "1"})
        self.assertTrue(self.control.verify_audit_chain())

    def test_dead_letter_is_audited(self):
        dead_id = self.control.dead_letter("job-9", "exhausted", {"x": 1})
        self.assertTrue(dead_id.startswith("dead_"))
        self.assertTrue(self.control.verify_audit_chain())


if __name__ == "__main__":
    unittest.main()

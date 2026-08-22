from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from aec.remote_state import RemoteStateClient, RemoteStateError


class _Response:
    def __init__(self, payload: dict) -> None:
        self._data = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._data


class RemoteStateClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = RemoteStateClient("https://state.example.test", "secret-token")

    def test_rejects_non_https_or_embedded_credentials(self):
        with self.assertRaises(ValueError):
            RemoteStateClient("http://state.example.test", "x")
        with self.assertRaises(ValueError):
            RemoteStateClient("https://user:pass@state.example.test", "x")

    @patch("aec.remote_state.urlopen")
    def test_health_is_unauthenticated(self, mocked):
        mocked.return_value = _Response({"ok": True, "version": "1.1"})
        result = self.client.health()
        self.assertTrue(result["ok"])
        request = mocked.call_args.args[0]
        self.assertIsNone(request.get_header("Authorization"))

    @patch("aec.remote_state.urlopen")
    def test_enqueue_qualified_job_sends_bearer_auth(self, mocked):
        mocked.return_value = _Response({
            "job": {
                "job_id": "job_1",
                "capability": "produce_artifact",
                "payload": {"qualification_evidence_id": "ev_1"},
                "state": "QUEUED",
                "attempts": 0,
                "max_attempts": 3,
                "assigned_worker": None,
                "human_threshold_required": False,
                "created_at": "2026-08-22T00:00:00+00:00",
                "updated_at": "2026-08-22T00:00:00+00:00",
            }
        })
        job = self.client.enqueue_job(
            job_id="job_1",
            capability="produce_artifact",
            payload={"content": "x"},
            qualification_evidence_id="ev_1",
            idempotency_key="idem_1",
        )
        self.assertEqual(job.state, "QUEUED")
        request = mocked.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-token")
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["qualification_state"], "QUALIFIED")
        self.assertEqual(body["idempotency_key"], "idem_1")

    @patch("aec.remote_state.urlopen")
    def test_artifact_roundtrip_verifies_hash(self, mocked):
        import base64
        import hashlib
        content = b"hello"
        mocked.return_value = _Response({
            "artifact": {
                "artifact_id": "a1",
                "job_id": "j1",
                "media_type": "text/plain",
                "content_base64": base64.b64encode(content).decode(),
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "created_at": "2026-08-22T00:00:00+00:00",
            }
        })
        artifact = self.client.get_artifact("a1")
        self.assertEqual(artifact.content, content)

    @patch("aec.remote_state.urlopen")
    def test_artifact_integrity_failure_is_blocking(self, mocked):
        import base64
        mocked.return_value = _Response({
            "artifact": {
                "artifact_id": "a1", "job_id": "j1", "media_type": "text/plain",
                "content_base64": base64.b64encode(b"hello").decode(),
                "sha256": "0" * 64, "bytes": 5, "created_at": "x",
            }
        })
        with self.assertRaises(RemoteStateError):
            self.client.get_artifact("a1")

    @patch("aec.remote_state.urlopen")
    def test_http_error_keeps_status_without_leaking_token(self, mocked):
        body = io.BytesIO(b'{"error":"qualification_required"}')
        mocked.side_effect = HTTPError(
            "https://state.example.test/jobs/enqueue", 409, "Conflict", {}, body
        )
        with self.assertRaises(RemoteStateError) as caught:
            self.client.reserve_idempotency("x", "y")
        self.assertEqual(caught.exception.status, 409)
        self.assertNotIn("secret-token", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

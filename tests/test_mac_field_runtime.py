from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_field_runtime.py"
SPEC = importlib.util.spec_from_file_location("run_field_runtime", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MacFieldRuntimeTests(unittest.TestCase):
    def test_run_python_includes_repository_root_in_pythonpath(self):
        completed = type(
            "Completed",
            (),
            {"returncode": 0, "stdout": "", "stderr": ""},
        )()
        with patch.object(MODULE.subprocess, "run", return_value=completed) as run:
            result = MODULE.run_python(MODULE.FIELD_CYCLE)
        self.assertEqual(result["returncode"], 0)
        env = run.call_args.kwargs["env"]
        self.assertIn(str(MODULE.REPO_ROOT), env["PYTHONPATH"].split(MODULE.os.pathsep))
        self.assertEqual(run.call_args.kwargs["cwd"], MODULE.REPO_ROOT)

    def test_repository_truth_requires_main_and_clean_before_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            status = Path(tmp) / "status.json"
            with (
                patch.object(MODULE, "STATUS", status),
                patch.object(MODULE, "repository_truth", return_value={"branch": "feature/x", "sha": "abc", "dirty": False}),
                patch.object(MODULE, "run_python") as run_python,
            ):
                self.assertEqual(MODULE.main(), 3)
                run_python.assert_not_called()
                payload = json.loads(status.read_text())
                self.assertEqual(payload["state"], "HOLD")

    def test_dirty_tree_holds_before_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            status = Path(tmp) / "status.json"
            with (
                patch.object(MODULE, "STATUS", status),
                patch.object(MODULE, "repository_truth", return_value={"branch": "main", "sha": "abc", "dirty": True}),
                patch.object(MODULE, "run_python") as run_python,
            ):
                self.assertEqual(MODULE.main(), 4)
                run_python.assert_not_called()

    def test_clean_main_runs_discovery_and_workers(self):
        with tempfile.TemporaryDirectory() as tmp:
            status = Path(tmp) / "status.json"
            results = [
                {"script": "scripts/run_field_cycle.py", "started_at": "a", "finished_at": "b", "returncode": 0, "stdout": "{}", "stderr": ""},
                {"script": "scripts/run_workers.py", "started_at": "a", "finished_at": "b", "returncode": 0, "stdout": "ok", "stderr": ""},
            ]
            with (
                patch.object(MODULE, "STATUS", status),
                patch.object(MODULE, "repository_truth", return_value={"branch": "main", "sha": "abc", "dirty": False}),
                patch.object(MODULE, "run_python", side_effect=results),
            ):
                self.assertEqual(MODULE.main(), 0)
                payload = json.loads(status.read_text())
                self.assertEqual(payload["state"], "PASS")
                self.assertFalse(payload["authority_boundary"]["submit"])
                self.assertFalse(payload["authority_boundary"]["money_movement"])


if __name__ == "__main__":
    unittest.main()

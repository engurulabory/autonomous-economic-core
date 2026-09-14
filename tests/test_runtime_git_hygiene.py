from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class RuntimeGitHygieneTests(unittest.TestCase):
    def test_runtime_directory_is_ignored(self):
        result = subprocess.run(
            ["git", "check-ignore", "-q", "runtime/field-runtime-latest.json"],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_runtime_outputs_do_not_dirty_repository(self):
        before = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        runtime = REPO_ROOT / "runtime"
        runtime.mkdir(exist_ok=True)
        probe = runtime / "git-hygiene-probe.tmp"
        probe.write_text("local runtime state\n", encoding="utf-8")
        try:
            after = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        finally:
            probe.unlink(missing_ok=True)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()

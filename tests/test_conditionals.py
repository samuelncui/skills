"""Run the standalone conditional examples from an isolated installation."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ConditionalSkillInstallation(unittest.TestCase):
    def test_isolated_standard_library_examples(self):
        with tempfile.TemporaryDirectory() as temp:
            installed = Path(temp) / "write-if-statements"
            shutil.copytree(
                ROOT / "skills/write-if-statements", installed,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            self.assertEqual((installed / "LICENSE").read_bytes(),
                             (ROOT / "LICENSE").read_bytes())
            env = dict(os.environ)
            env.pop("PYTHONPATH", None)
            result = subprocess.run(
                [sys.executable, "-I", "-B", "-m", "unittest", "discover",
                 "-s", "examples", "-p", "test_conditionals.py", "-v"],
                cwd=installed, env=env, text=True, capture_output=True,
                timeout=30, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Ran 7 tests", result.stderr)


if __name__ == "__main__":
    unittest.main()

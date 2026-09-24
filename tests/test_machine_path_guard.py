"""Test machine path guard (GH-259)."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_machine_paths_clean():
    cmd = [sys.executable, str(REPO_ROOT / "utils" / "pdda" / "check_machine_paths.py"), "--check"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, f"check_machine_paths failed: {res.stdout}\n{res.stderr}"
    assert "clean" in res.stdout

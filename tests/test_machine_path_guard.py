"""Test machine path guard with positive assertions, negative controls, and pragmas (GH-259)."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_machine_paths_clean():
    cmd = [sys.executable, str(REPO_ROOT / "utils" / "pdda" / "check_machine_paths.py"), "--check"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, f"check_machine_paths failed: {res.stdout}\n{res.stderr}"
    assert "clean" in res.stdout


def test_machine_paths_negative_control(tmp_path: Path):
    """Assert that check_machine_paths --check fails when a machine path is committed."""
    # Init a mock git repository
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True, capture_output=True)

    # Add a file with a hardcoded machine path
    bad_file = tmp_path / "script.py"
    bad_file.write_text('path = "/Users/alice/projects/test.py"\n', encoding="utf-8")
    subprocess.run(["git", "add", "script.py"], cwd=str(tmp_path), check=True, capture_output=True)

    cmd = [
        sys.executable,
        str(REPO_ROOT / "utils" / "pdda" / "check_machine_paths.py"),
        "--check",
        "--root",
        str(tmp_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp_path))
    assert res.returncode == 1, f"Expected non-zero exit on machine path violation, got {res.returncode}"
    assert "machine-local path found" in res.stdout
    assert "script.py:1" in res.stdout


def test_machine_paths_pragma_exemption(tmp_path: Path):
    """Assert that MACHINE-LOCAL-OK pragma exempts the line from failing."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True, capture_output=True)

    good_file = tmp_path / "script.py"
    good_file.write_text('path = "/Users/alice/projects/test.py"  # MACHINE-LOCAL-OK: tested\n', encoding="utf-8")
    subprocess.run(["git", "add", "script.py"], cwd=str(tmp_path), check=True, capture_output=True)

    cmd = [
        sys.executable,
        str(REPO_ROOT / "utils" / "pdda" / "check_machine_paths.py"),
        "--check",
        "--root",
        str(tmp_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp_path))
    assert res.returncode == 0, f"Expected exit 0 with pragma, got {res.returncode}: {res.stdout}"
    assert "clean" in res.stdout

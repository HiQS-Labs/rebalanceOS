"""Test that named CI ratchets run and pass cleanly (GH-260)."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_script_inventory_ratchet_passes():
    cmd = [sys.executable, str(REPO_ROOT / "utils" / "pdda" / "check_script_inventory.py"), "--check"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, f"check_script_inventory failed: {res.stdout}\n{res.stderr}"
    assert "clean" in res.stdout


def test_read_layer_ratchet_passes():
    cmd = [sys.executable, str(REPO_ROOT / "utils" / "pdda" / "check_read_layer.py"), "--check"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, f"check_read_layer failed: {res.stdout}\n{res.stderr}"
    assert "clean" in res.stdout


def test_near_duplicates_ratchet_passes():
    cmd = [sys.executable, str(REPO_ROOT / "utils" / "pdda" / "check_near_duplicates.py"), "--check"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, f"check_near_duplicates failed: {res.stdout}\n{res.stderr}"
    assert "clean" in res.stdout


def test_ci_workflow_has_named_ratchet_steps():
    ci_yaml = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "check_machine_paths.py --check" in ci_yaml
    assert "check_read_layer.py --check" in ci_yaml
    assert "check_near_duplicates.py --check" in ci_yaml

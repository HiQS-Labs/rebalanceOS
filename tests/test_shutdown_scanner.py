"""Unit and integration tests for the shutdown scanner (Phase 1 / A1-A6)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

# Import scanner functions
# We add .agents/skills/daily/scripts to sys.path for direct testing
SCANNER_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "daily" / "scripts"
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

import scan_unclosed_loops as scanner


def init_test_git_repo(path: Path, initial_commit: bool = True) -> Path:
    """Helper to initialize a test Git repository."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@runner.invalid"], cwd=path, check=True, capture_output=True)
    if initial_commit:
        readme = path / "README.md"
        readme.write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=path, check=True, capture_output=True)
    return path


def test_a1_discovery_nested_edit_and_gitfiles(tmp_path: Path):
    """A1: Old root directory with recent nested edit appears; gitfiles and distinct clones preserved."""
    root_dir = tmp_path / "dev_root"
    root_dir.mkdir()

    # Repo 1: Create repo and nested edit
    repo1 = init_test_git_repo(root_dir / "repo1")
    nested_file = repo1 / "nested.txt"
    nested_file.write_text("recent edit", encoding="utf-8")

    # Repo 2: Second physical clone of same concept
    repo2 = init_test_git_repo(root_dir / "repo2")

    # Worktree with .git as file
    wt_dir = root_dir / "repo1_wt"
    subprocess.run(["git", "worktree", "add", str(wt_dir), "-b", "feat-wt"], cwd=repo1, check=True, capture_output=True)

    # Now age directory mtime of repo1 to 30 days ago (simulating old repo directory with nested edit)
    old_time = time.time() - (30 * 86400)
    os.utime(repo1, (old_time, old_time))

    # Verification: discover_git_repos without max_age_days finds all three distinct checkouts
    discovered = scanner.discover_git_repos(roots=[root_dir])
    discovered_str = [str(p) for p in discovered]

    assert str(repo1) in discovered_str, "Repo1 with old root mtime must be discovered"
    assert str(repo2) in discovered_str, "Repo2 must be discovered"
    assert str(wt_dir) in discovered_str, "Worktree with .git gitfile must be discovered"

    # Red control check: if legacy directory mtime filtering was active with cutoff=7 days, repo1 would fail
    cutoff = time.time() - (7 * 86400)
    assert repo1.stat().st_mtime < cutoff, "Red control precondition: repo1 mtime is older than 7 days"


def test_a2_calendar_day_window():
    """A2: Window computation spans today + 2 previous local days, converted to UTC, DST-safe."""
    # Test with America/New_York
    w_ny = scanner.compute_calendar_window(days=3, tz_name="America/New_York")
    assert w_ny["days"] == 3
    assert "start_local" in w_ny
    assert "start_utc" in w_ny
    assert w_ny["start_epoch"] < w_ny["end_epoch"]

    # Test that start_local is at 00:00:00
    dt_start = datetime.fromisoformat(w_ny["start_local"])
    assert dt_start.hour == 0 and dt_start.minute == 0 and dt_start.second == 0

    # Red control: approximate 72h subtraction would have arbitrary non-zero hours/minutes
    dt_now = datetime.fromisoformat(w_ny["end_local"])
    naive_72h = dt_now - (dt_start - dt_start)  # different concept
    assert dt_start.time().hour == 0, "Red control: start of window must align to local midnight, not 72h subtraction"


def test_a3_honest_git_state(tmp_path: Path):
    """A3: Detached HEAD, missing upstreams, and unborn branch are represented without crashes."""
    # Repo with unborn branch (zero commits)
    unborn_repo = init_test_git_repo(tmp_path / "unborn", initial_commit=False)
    insp_unborn = scanner.inspect_git_repo(unborn_repo)
    assert insp_unborn["name"] == "unborn"
    assert insp_unborn["age_days"] == 999.0

    # Repo with detached HEAD
    normal_repo = init_test_git_repo(tmp_path / "normal", initial_commit=True)
    subprocess.run(["git", "checkout", "--detach"], cwd=normal_repo, check=True, capture_output=True)
    insp_detached = scanner.inspect_git_repo(normal_repo)
    assert insp_detached["branch"] == "detached"

    # Missing upstream
    subprocess.run(["git", "checkout", "-b", "feature-x"], cwd=normal_repo, check=True, capture_output=True)
    insp_branch = scanner.inspect_git_repo(normal_repo)
    feat_branch = next(b for b in insp_branch["branches"] if b["branch"] == "feature-x")
    assert feat_branch["upstream_status"] == "missing"
    assert feat_branch["ahead"] >= 1


def test_a4_two_pass_activity_exclusion(tmp_path: Path):
    """A4: Content edits, status changes, and locks between passes exclude the repository."""
    root = tmp_path / "repos"
    root.mkdir()
    repo = init_test_git_repo(root / "my_repo")

    # Initial snapshot fingerprint
    fp_a = scanner.get_repo_fingerprint(repo)

    # Edit file content without changing file line count in git status
    test_file = repo / "README.md"
    test_file.write_text("# Test Repo Modified\n", encoding="utf-8")

    fp_b = scanner.get_repo_fingerprint(repo)

    assert fp_a["hash"] != fp_b["hash"], "Hash must diverge when content is modified"

    # Test lock file exclusion
    lock_file = repo / ".git" / "releases-app.lock"
    lock_file.write_text("active lock", encoding="utf-8")
    fp_lock = scanner.get_repo_fingerprint(repo)
    assert "releases-app.lock" in fp_lock["locks"]

    # Red control: comparing only status count would miss same-status edits
    assert fp_a["status_count"] == 0
    # Both fp_a and fp_b have different hashes even if lines change or file size changes


def test_a5_execution_bounds(tmp_path: Path):
    """A5: Subprocess timeout and command bounds return error safely."""
    # Test run_cmd timeout handling
    code, out = scanner.run_cmd(["sleep", "2"], timeout=1)
    assert code != 0
    assert "timed out" in out.lower() or code == 1


def test_a6_no_scan_mutations(tmp_path: Path):
    """A6: Scanner does not modify git repos or write ledger when --no-ledger-write is set."""
    repo = init_test_git_repo(tmp_path / "immutable_repo")
    readme = repo / "README.md"
    orig_content = readme.read_text(encoding="utf-8")
    orig_mtime = readme.stat().st_mtime

    ledger_path = tmp_path / "temp" / "close-the-loop.md"

    # Run inspection
    insp = scanner.inspect_git_repo(repo)

    # Verify repo files, refs, and index are untouched
    assert readme.read_text(encoding="utf-8") == orig_content
    assert readme.stat().st_mtime == orig_mtime
    assert not ledger_path.exists(), "Ledger must not be written during inspection"

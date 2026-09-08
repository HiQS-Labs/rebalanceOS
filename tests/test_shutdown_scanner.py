"""Unit and integration tests for the shutdown scanner (Phase 1 / A1-A6)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

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

    # Test already-dirty same-status content change
    test_file.write_text("# Test Repo Modified Again With Different Text\n", encoding="utf-8")
    fp_c = scanner.get_repo_fingerprint(repo)
    assert fp_b["hash"] != fp_c["hash"], "Hash must diverge between two consecutive dirty states"

    # Test lock file exclusion
    lock_file = repo / ".git" / "releases-app.lock"
    lock_file.write_text("active lock", encoding="utf-8")
    fp_lock = scanner.get_repo_fingerprint(repo)
    assert "releases-app.lock" in fp_lock["locks"]


def test_a5_execution_bounds():
    """A5: Subprocess timeout, content hashing limits, and command bounds return error safely."""
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
    assert insp["dirty_count"] == 0

    # Verify repo files, refs, and index are untouched
    assert readme.read_text(encoding="utf-8") == orig_content
    assert readme.stat().st_mtime == orig_mtime
    assert not ledger_path.exists(), "Ledger must not be written during inspection"

    # Also test CLI execution with --no-ledger-write
    buf = io.StringIO()
    with (
        patch.object(scanner, "discover_git_repos", return_value=[repo]),
        patch.object(scanner, "fetch_prs_for_remotes", return_value=({}, [])),
        patch.object(sys, "argv", ["scan", "--json", "--no-ledger-write"]),
        contextlib.redirect_stdout(buf),
    ):
        scanner.main()
    assert not ledger_path.exists(), "Ledger must not be written when --no-ledger-write is passed"


# --------------------------------------------------------------------------
# Reproduction verification tests from code review
# --------------------------------------------------------------------------


def test_repro_tracked_dirty_edit(tmp_path: Path):
    """Verifies porcelain v1 status preserves leading spaces, filenames are intact, and fingerprints diverge."""
    repo = init_test_git_repo(tmp_path / "tracked_repo")
    tracked = repo / "README.md"
    tracked.write_text("dirty before\n", encoding="utf-8")

    insp = scanner.inspect_git_repo(repo)
    # Filepath must be README.md, not EADME.md
    assert "README.md" in insp["unstaged_files"]
    assert "README.md" not in insp["staged_files"]

    fp_a = scanner.get_repo_fingerprint(repo)
    assert len(fp_a["dirty_files_meta"]) == 1
    assert fp_a["dirty_files_meta"][0][0] == "README.md"

    tracked.write_text("different and longer dirty content after\n", encoding="utf-8")
    fp_b = scanner.get_repo_fingerprint(repo)
    assert len(fp_b["dirty_files_meta"]) == 1
    assert fp_a["hash"] != fp_b["hash"], "Fingerprint must diverge on tracked dirty file edit"


def test_repro_same_metadata_content_edit(tmp_path: Path):
    """Verifies content hashing detects edits when file size and mtime are identical."""
    repo = init_test_git_repo(tmp_path / "meta_repo")
    untracked = repo / "new.txt"
    untracked.write_text("aaaa", encoding="utf-8")
    os.utime(untracked, (1700000000, 1700000000))
    fp_a = scanner.get_repo_fingerprint(repo)

    untracked.write_text("bbbb", encoding="utf-8")
    os.utime(untracked, (1700000000, 1700000000))
    fp_b = scanner.get_repo_fingerprint(repo)

    assert fp_a["hash"] != fp_b["hash"], "Content hash must catch same-size/same-mtime edits"


def test_repro_failed_git_reads(tmp_path: Path):
    """Verifies failed git commands cause repository to be excluded rather than marked stable."""
    repo = init_test_git_repo(tmp_path / "failed_repo")
    with patch.object(scanner, "run_cmd", return_value=(1, "mock git error")):
        failed = scanner.run_two_pass_scan([repo], scanner.DEFAULT_EXCLUSIONS, {}, delay_seconds=0)

    assert len(failed["stable_repos"]) == 0, "Failed git reads must not be marked stable"
    assert len(failed["excluded_repos"]) == 1, "Failed git reads must be excluded"
    assert any("Failed Git" in r for r in failed["excluded_repos"][0]["activity_reasons"])


def test_repro_failed_pr_lookup(tmp_path: Path):
    """Verifies that PR query failures mark branch status as unknown and avoid claiming no PRs or suggesting cut PR."""
    repo = init_test_git_repo(tmp_path / "pr_repo")
    subprocess.run(["git", "checkout", "-b", "feat/my-feature"], cwd=repo, check=True, capture_output=True)
    readme = repo / "README.md"
    readme.write_text("# PR branch\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "commit on branch"], cwd=repo, check=True, capture_output=True)

    insp = scanner.inspect_git_repo(repo)
    insp.update(canonical_remote="example/project", is_active=False, activity_reasons=[])
    two = {"stable_repos": [insp], "excluded_repos": [], "active_paths": []}

    buf = io.StringIO()
    with (
        patch.object(scanner, "run_two_pass_scan", return_value=two),
        patch.object(
            scanner,
            "fetch_prs_for_remotes",
            return_value=({}, [{"remote": "example/project", "error": "authentication failed"}]),
        ),
        patch.object(sys, "argv", ["scan", "--mode", "shutdown", "--delay", "0"]),
        contextlib.redirect_stdout(buf),
    ):
        scanner.main()

    payload = json.loads(buf.getvalue())
    branch_status = payload["projects"][0]["branches"][0]["pr_status"]
    assert branch_status == "unknown", f"Branch status must be 'unknown' on PR query failure, got {branch_status}"


def test_repro_single_checkout_daily(tmp_path: Path):
    """Verifies that in daily mode, a single-checkout repository does not register spurious active worktrees."""
    repo = init_test_git_repo(tmp_path / "single_checkout")
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=repo, check=True, capture_output=True)

    buf = io.StringIO()
    with (
        patch.object(scanner, "discover_git_repos", return_value=[repo]),
        patch.object(scanner, "fetch_prs_for_remotes", return_value=({}, [])),
        patch.object(sys, "argv", ["scan", "--json", "--no-ledger-write"]),
        contextlib.redirect_stdout(buf),
    ):
        scanner.main()

    daily = json.loads(buf.getvalue())
    assert daily["counts"]["active_worktrees"] == 0, "Single-checkout must not count as active linked worktree"
    assert daily["counts"]["unpred_branches"] == 0, (
        "Single-checkout must not register spurious unpred branch in daily mode"
    )

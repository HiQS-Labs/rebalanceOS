"""Tests for GH-201: Git Remote Peeker & Commit Walk Gating."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from rebalance.ingest.config import get_enable_remote_peeking, set_enable_remote_peeking
from rebalance.ingest.db import db_connection, ensure_github_schema, ensure_schema
from rebalance.ingest.github_commit_backfill import (
    BackfillResult,
    backfill_commits,
    is_commit_walk_cached,
    is_shallow_clone,
    record_commit_coverage_checkpoint,
)
from rebalance.lib.git_ops import (
    canonical_github_url,
    compute_origin_ref_digest,
    peek_remote_refs,
    run_git,
)

REPO = "Hypercart-Dev-Tools/rebalance-OS"


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def _write(path: Path, rel: str, body: str = "x") -> None:
    target = path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body)


class _RepoWithRemoteFixture:
    """A real local git clone wired to a real local bare remote."""

    def __init__(self, root: Path):
        self.bare = root / "remote.git"
        self.bare.mkdir()
        _git(self.bare, "init", "--bare", "-q")

        self.path = root / "clone"
        self.path.mkdir()
        _git(self.path, "init", "-q", "-b", "development")
        _git(self.path, "config", "user.email", "tester@example.com")
        _git(self.path, "config", "user.name", "Tester")
        _git(self.path, "remote", "add", "origin", str(self.bare))

        _write(self.path, "README.md", "init")
        _git(self.path, "add", "-A")
        _git(self.path, "commit", "-q", "-m", "chore: initial commit")
        _git(self.path, "push", "-q", "-u", "origin", "development")
        self.init_sha = _git(self.path, "rev-parse", "HEAD")


class GitCommitPeekerTests(unittest.TestCase):
    def setUp(self):
        self._orig_enable_peeking = get_enable_remote_peeking()
        set_enable_remote_peeking(True)
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.db = root / "test.db"
        with db_connection(self.db, ensure_schema):
            pass
        with db_connection(self.db, ensure_github_schema):
            pass
        self.fx = _RepoWithRemoteFixture(root)

    def tearDown(self):
        set_enable_remote_peeking(self._orig_enable_peeking)
        self._tmp.cleanup()

    def test_peek_remote_refs_real_repo(self):
        """peek_remote_refs discovers origin branch heads on a real bare remote."""
        ref_map = peek_remote_refs(self.fx.path, remote="origin")
        self.assertIsNotNone(ref_map)
        self.assertIn("refs/heads/development", ref_map)
        self.assertEqual(ref_map["refs/heads/development"], self.fx.init_sha)

    def test_compute_origin_ref_digest(self):
        """Digest covers origin branches (refs/heads/*) and ignores unrelated refs."""
        base_map = {
            "refs/heads/development": "aaa111",
            "refs/heads/main": "bbb222",
            "HEAD": "aaa111",
        }
        digest1 = compute_origin_ref_digest(base_map)

        # Adding a pull ref or tag does not change the origin branch digest
        with_pull = dict(base_map, **{"refs/pull/1/head": "ccc333", "refs/tags/v1.0": "ddd444"})
        digest2 = compute_origin_ref_digest(with_pull)
        self.assertEqual(digest1, digest2)

        # Changing an origin branch DOES change the digest
        changed_map = dict(base_map, **{"refs/heads/development": "aaa999"})
        digest3 = compute_origin_ref_digest(changed_map)
        self.assertNotEqual(digest1, digest3)

    def test_backfill_commits_caches_and_skips_subsequent_run(self):
        """First walk records checkpoint; second walk skips redundant commit history walk."""
        # First walk: populates commits and publishes checkpoint
        res1 = backfill_commits(self.db, REPO, clone_path=self.fx.path)
        self.assertEqual(res1.state, "ok")
        self.assertFalse(res1.skipped_cache)
        self.assertEqual(res1.commits_inserted, 1)

        # Verify checkpoint row in DB
        with db_connection(self.db) as conn:
            row = conn.execute("SELECT canonical_remote_url, ref_digest FROM github_remote_peeks").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], canonical_github_url(REPO))

        # Second walk: remote refs unchanged -> short-circuits via cache
        res2 = backfill_commits(self.db, REPO, clone_path=self.fx.path)
        self.assertEqual(res2.state, "ok")
        self.assertTrue(res2.skipped_cache)
        self.assertEqual(res2.commits_seen, 0)
        self.assertEqual(res2.commits_inserted, 0)

    def test_backfill_commits_invalidated_by_branch_movement(self):
        """When remote branch moves, cache-hit is rejected and new commit ingested."""
        # Initial walk
        backfill_commits(self.db, REPO, clone_path=self.fx.path)

        # Push a new commit to origin
        _write(self.fx.path, "file2.txt", "content 2")
        _git(self.fx.path, "add", "-A")
        _git(self.fx.path, "commit", "-q", "-m", "feat: second commit")
        _git(self.fx.path, "push", "-q", "origin", "development")

        # Next walk: cache must be invalidated
        res = backfill_commits(self.db, REPO, clone_path=self.fx.path)
        self.assertFalse(res.skipped_cache)
        self.assertEqual(res.commits_inserted, 1)

    def test_backfill_commits_invalidated_by_secondary_branch(self):
        """When a secondary branch moves while trunk is unchanged, cache is invalidated."""
        backfill_commits(self.db, REPO, clone_path=self.fx.path)

        # Create and push a secondary feature branch
        _git(self.fx.path, "checkout", "-q", "-b", "feature-x")
        _write(self.fx.path, "feature.txt", "feat content")
        _git(self.fx.path, "add", "-A")
        _git(self.fx.path, "commit", "-q", "-m", "feat: branch commit")
        _git(self.fx.path, "push", "-q", "origin", "feature-x")
        _git(self.fx.path, "checkout", "-q", "development")

        res = backfill_commits(self.db, REPO, clone_path=self.fx.path)
        self.assertFalse(res.skipped_cache)
        self.assertEqual(res.commits_inserted, 1)

    def test_backfill_commits_invalidated_on_widened_since(self):
        """Requesting a wider history window than recorded checkpoint forces full walk (Codex R2)."""
        # Seed checkpoint covering since 2026-08-01
        backfill_commits(self.db, REPO, clone_path=self.fx.path, since="2026-08-01T00:00:00Z")

        # Walk with since 2026-08-15 (narrower) hits cache
        res_narrow = backfill_commits(self.db, REPO, clone_path=self.fx.path, since="2026-08-15T00:00:00Z")
        self.assertTrue(res_narrow.skipped_cache)

        # Walk with since 2026-07-01 (wider) misses cache
        res_wide = backfill_commits(self.db, REPO, clone_path=self.fx.path, since="2026-07-01T00:00:00Z")
        self.assertFalse(res_wide.skipped_cache)

        # Walk with since=None (unbounded history) misses bounded cache
        res_unbounded = backfill_commits(self.db, REPO, clone_path=self.fx.path, since=None)
        self.assertFalse(res_unbounded.skipped_cache)

    def test_force_refresh_bypasses_cache(self):
        """Passing force_refresh=True unconditionally runs commit walk."""
        backfill_commits(self.db, REPO, clone_path=self.fx.path)

        res = backfill_commits(self.db, REPO, clone_path=self.fx.path, force_refresh=True)
        self.assertFalse(res.skipped_cache)

    def test_branch_limited_walk_refuses_checkpoint(self):
        """Branch-limited walk (branch='development') never publishes an all-branch checkpoint (Codex R1)."""
        # Create a secondary branch on remote
        _git(self.fx.path, "checkout", "-q", "-b", "feature-branch")
        (self.fx.path / "feat.txt").write_text("feature content\n")
        _git(self.fx.path, "add", "feat.txt")
        _git(self.fx.path, "commit", "-q", "-m", "feature commit")
        _git(self.fx.path, "push", "-q", "origin", "feature-branch")
        _git(self.fx.path, "checkout", "-q", "development")

        # Branch-limited walk on 'development'
        res_branch = backfill_commits(self.db, REPO, clone_path=self.fx.path, branch="development")
        self.assertEqual(res_branch.state, "ok")

        # Must NOT have published a checkpoint because walk was branch-limited
        with db_connection(self.db) as conn:
            chk = conn.execute("SELECT * FROM github_remote_peeks").fetchone()
            self.assertIsNone(chk, "Branch-limited walk must not publish an all-branch checkpoint")

        # Full walk (branch=None) walks all origin branches and publishes checkpoint
        res_full = backfill_commits(self.db, REPO, clone_path=self.fx.path, branch=None)
        self.assertEqual(res_full.state, "ok")
        with db_connection(self.db) as conn:
            chk2 = conn.execute("SELECT * FROM github_remote_peeks").fetchone()
            self.assertIsNotNone(chk2, "Full-repo walk with matching origin branches must publish checkpoint")

    def test_ref_mismatch_between_peek_and_fetch_refuses_checkpoint(self):
        """Mismatch between peek snapshot and local origin refs refuses checkpoint publication (Codex R1)."""
        # Simulate peek returning extra remote branch that wasn't fetched locally
        stale_peek = {
            "refs/heads/development": "sha_dev",
            "refs/heads/ghost_branch": "sha_ghost",
        }
        with patch("rebalance.ingest.github_commit_backfill.peek_remote_refs", return_value=stale_peek):
            res = backfill_commits(self.db, REPO, clone_path=self.fx.path)
            self.assertEqual(res.state, "ok")

        # Assert no checkpoint was published due to mismatch
        with db_connection(self.db) as conn:
            chk = conn.execute("SELECT * FROM github_remote_peeks").fetchone()
            self.assertIsNone(chk, "Ref mismatch between peek and local origin refs must refuse checkpoint")

    def test_failed_file_read_marks_retryable_and_refuses_checkpoint(self):
        """git show failure on commit files marks row 'failed' and refuses checkpoint."""
        with patch("rebalance.ingest.github_commit_backfill._changed_paths", return_value=None):
            res = backfill_commits(self.db, REPO, clone_path=self.fx.path)
            self.assertEqual(res.state, "ok")

        # Check commit path_coverage is 'failed', not 'complete'
        with db_connection(self.db) as conn:
            row = conn.execute("SELECT path_coverage FROM github_direct_commits WHERE repo_full_name = ?", (REPO,)).fetchone()
            self.assertEqual(row[0], "failed")

            # Checkpoint table must NOT have recorded a checkpoint
            chk = conn.execute("SELECT * FROM github_remote_peeks").fetchone()
            self.assertIsNone(chk)

        # Subsequent walk with healthy git show succeeds and upgrades row
        res2 = backfill_commits(self.db, REPO, clone_path=self.fx.path)
        self.assertFalse(res2.skipped_cache)
        self.assertEqual(res2.commits_updated, 1)

        with db_connection(self.db) as conn:
            row2 = conn.execute("SELECT path_coverage FROM github_direct_commits WHERE repo_full_name = ?", (REPO,)).fetchone()
            self.assertEqual(row2[0], "complete")
            # Now checkpoint is established
            chk2 = conn.execute("SELECT * FROM github_remote_peeks").fetchone()
            self.assertIsNotNone(chk2)

    def test_probe_setup_failure_falls_back_to_authoritative_sync(self):
        """Probe setup failure (TimeoutExpired/OSError) cleanly falls back without raising (Codex R3 & R6)."""
        def fail_on_remote_get_url(path, *args, **kwargs):
            if len(args) >= 2 and args[0] == "remote" and args[1] == "get-url":
                raise subprocess.TimeoutExpired(cmd="git remote get-url", timeout=1.0)
            return run_git(path, *args, **kwargs)

        with db_connection(self.db) as conn:
            conn.execute("DELETE FROM github_remote_peeks")
            conn.commit()

        with patch("rebalance.ingest.github_commit_backfill.run_git", side_effect=fail_on_remote_get_url), \
             patch("rebalance.ingest.github_commit_backfill.peek_remote_refs", return_value=None):
            res = backfill_commits(self.db, REPO, clone_path=self.fx.path, force_refresh=False)
            self.assertEqual(res.state, "ok")
            self.assertFalse(res.skipped_cache)

        with db_connection(self.db) as conn:
            conn.execute("DELETE FROM github_remote_peeks")
            conn.commit()

        def oserror_on_remote_get_url(path, *args, **kwargs):
            if len(args) >= 2 and args[0] == "remote" and args[1] == "get-url":
                raise OSError("git executable not found")
            return run_git(path, *args, **kwargs)

        with patch("rebalance.ingest.github_commit_backfill.run_git", side_effect=oserror_on_remote_get_url), \
             patch("rebalance.ingest.github_commit_backfill.peek_remote_refs", return_value=None):
            res = backfill_commits(self.db, REPO, clone_path=self.fx.path, force_refresh=False)
            self.assertEqual(res.state, "ok")
            self.assertFalse(res.skipped_cache)

    def test_backfill_repos_isolates_failures_and_probe_budget(self):
        """backfill_repos isolates per-repo exceptions and enforces whole-run probe budget (Codex R3 & R9)."""
        from rebalance.ingest.github_commit_backfill import backfill_repos

        # 1. Failure isolation: one failing repo does not abort other repos
        with patch("rebalance.ingest.github_commit_backfill.backfill_commits") as mock_backfill:
            mock_backfill.side_effect = [RuntimeError("disk read error"), BackfillResult(repo=REPO, state="ok")]
            results = backfill_repos(self.db, ["failing/repo", REPO])
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].state, "uncoverable")
            self.assertIn("disk read error", results[0].reason)
            self.assertEqual(results[1].state, "ok")

        # 2. Probe budget exhaustion: when deadline is passed, peeking is skipped but walk runs
        with patch("rebalance.ingest.github_commit_backfill.resolve_clone", return_value=self.fx.path):
            res_budget = backfill_repos(self.db, [REPO], probe_budget_seconds=0.0)
            self.assertEqual(len(res_budget), 1)
            self.assertEqual(res_budget[0].state, "ok")

    def test_peek_remote_refs_parser_hardening(self):
        """peek_remote_refs strictly rejects malformed output, empty output, and invalid SHAs (Codex R4)."""
        from rebalance.lib.git_ops import peek_remote_refs

        # Non-zero returncode -> None
        with patch("rebalance.lib.git_ops.run_git") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=128, stdout="", stderr="")
            self.assertIsNone(peek_remote_refs(self.fx.path))

            # Empty output -> None
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="\n\n", stderr="")
            self.assertIsNone(peek_remote_refs(self.fx.path))

            # Malformed line (no ref) -> None
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="just_a_string\n", stderr="")
            self.assertIsNone(peek_remote_refs(self.fx.path))

            # Invalid hex SHA -> None
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="not_a_hex_sha refs/heads/development\n", stderr=""
            )
            self.assertIsNone(peek_remote_refs(self.fx.path))

            # Output with no refs/heads/ -> None
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="a" * 40 + " refs/tags/v1.0\n", stderr=""
            )
            self.assertIsNone(peek_remote_refs(self.fx.path))

    def test_atomic_first_writer_concurrent_upsert(self):
        """Two concurrent connections recording initial checkpoint do not raise IntegrityError (Codex R6 & R7)."""
        canonical_url = "https://github.com/HiQS-Labs/rebalanceOS.git"
        ref_map_1 = {"refs/heads/development": "sha1"}
        ref_map_2 = {"refs/heads/development": "sha2"}

        barrier = threading.Barrier(2)
        errors = []

        def worker(ref_map, t):
            try:
                conn = sqlite3.connect(self.db, timeout=10.0)
                conn.execute("PRAGMA busy_timeout = 10000")
                barrier.wait()
                ok = record_commit_coverage_checkpoint(conn, canonical_url, ref_map, None, t, t)
                conn.commit()
                conn.close()
                if not ok:
                    errors.append("checkpoint rejected")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=worker, args=(ref_map_1, "2026-09-08T12:00:00Z"))
        t2 = threading.Thread(target=worker, args=(ref_map_2, "2026-09-08T12:00:00Z"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(errors, [], f"Expected 0 concurrency errors, got: {errors}")
        with db_connection(self.db) as conn:
            cur = conn.execute(
                "SELECT verified_at, ref_digest FROM github_remote_peeks WHERE canonical_remote_url = ?",
                (canonical_url,),
            ).fetchone()
            self.assertIsNotNone(cur)

    def test_branch_name_with_slash_preserved(self):
        """_default_branch preserves branch names with slashes (Codex R10)."""
        from rebalance.ingest.github_commit_backfill import _default_branch

        with patch("rebalance.ingest.github_commit_backfill._git") as mock_git:
            mock_git.return_value = (0, "refs/remotes/origin/release/stable\n", "")
            self.assertEqual(_default_branch(self.fx.path), "release/stable")

            mock_git.return_value = (0, "refs/remotes/origin/feature/user-auth\n", "")
            self.assertEqual(_default_branch(self.fx.path), "feature/user-auth")

    def test_stale_clone_health_integration_with_remote_peeks(self):
        """check_repo_coverage stays healthy when github_remote_peeks has recent verification (Codex R6 & R10)."""
        from rebalance.ingest.github_coverage import check_repo_coverage

        frozen_now = datetime(2026, 9, 8, 19, 0, 0, tzinfo=timezone.utc)
        canonical_url = f"https://github.com/{REPO.lower()}.git"

        # 1. Healthy recent verification matching clone origin tip
        with db_connection(self.db) as conn:
            record_commit_coverage_checkpoint(
                conn,
                canonical_url,
                {"refs/heads/development": self.fx.init_sha},
                None,
                "2026-09-08T18:00:00Z",
                "2026-09-08T18:00:00Z",
            )
            conn.commit()

        with patch("rebalance.ingest.github_coverage.now_utc", return_value=frozen_now), \
             patch("rebalance.ingest.github_coverage._fetch_age_hours", return_value=None):
            cov = check_repo_coverage(self.db, REPO, clone_path=self.fx.path, check_remote=False)
            self.assertNotEqual(cov.state, "stale", "Recent verified remote peek must prevent stale state even if FETCH_HEAD is absent")

        # 2. SSH vs HTTPS identity equivalence
        ssh_url = f"git@github.com:{REPO}.git"
        self.assertEqual(canonical_github_url(ssh_url), canonical_url)

        # 3. Divergent clone: origin tip not in verified proof reports stale
        with tempfile.TemporaryDirectory() as other_root:
            other_path = Path(other_root) / "other_clone"
            other_path.mkdir()
            _git(other_path, "init", "-q", "-b", "development")
            _write(other_path, "divergent.txt", "divergent")
            _git(other_path, "add", "-A")
            _git(other_path, "commit", "-q", "-m", "divergent commit")
            _git(other_path, "remote", "add", "origin", str(self.fx.bare))

            with patch("rebalance.ingest.github_coverage.now_utc", return_value=frozen_now), \
                 patch("rebalance.ingest.github_coverage._fetch_age_hours", return_value=None):
                cov_divergent = check_repo_coverage(self.db, REPO, clone_path=other_path, check_remote=False)
                self.assertEqual(cov_divergent.state, "stale", "Divergent clone tip not in verified proof must report stale")

        # 3b. Clone missing secondary branch: origin has development + feature, clone only has development
        _git(self.fx.path, "checkout", "-q", "-b", "feature-branch")
        _write(self.fx.path, "feat.txt", "feature content")
        _git(self.fx.path, "add", "-A")
        _git(self.fx.path, "commit", "-q", "-m", "feature commit")
        _git(self.fx.path, "push", "-q", "origin", "feature-branch")
        feat_sha = _git(self.fx.path, "rev-parse", "HEAD")
        _git(self.fx.path, "checkout", "-q", "development")

        # Checkpoint proof has both branches:
        with db_connection(self.db) as conn:
            record_commit_coverage_checkpoint(
                conn,
                canonical_url,
                {"refs/heads/development": self.fx.init_sha, "refs/heads/feature-branch": feat_sha},
                None,
                "2026-09-08T18:00:00Z",
                "2026-09-08T18:00:00Z",
            )
            conn.commit()

        with tempfile.TemporaryDirectory() as partial_root:
            partial_path = Path(partial_root) / "partial_clone"
            partial_path.mkdir()
            _git(partial_path, "init", "-q", "-b", "development")
            _write(partial_path, "README.md", "init")
            _git(partial_path, "add", "-A")
            _git(partial_path, "commit", "-q", "-m", "chore: initial commit")
            _git(partial_path, "remote", "add", "origin", str(self.fx.bare))
            _git(partial_path, "fetch", "-q", "origin", "development")

            with patch("rebalance.ingest.github_coverage.now_utc", return_value=frozen_now), \
                 patch("rebalance.ingest.github_coverage._fetch_age_hours", return_value=None):
                cov_partial = check_repo_coverage(self.db, REPO, clone_path=partial_path, check_remote=False)
                self.assertEqual(cov_partial.state, "stale", "Clone missing secondary branch from origin ref map must report stale")

        # 4. Cache hit renewal across 48-hour threshold
        with db_connection(self.db) as conn:
            conn.execute("DELETE FROM github_remote_peeks")
            time_t0 = "2026-09-01T12:00:00Z"
            record_commit_coverage_checkpoint(
                conn,
                canonical_url,
                {"refs/heads/development": self.fx.init_sha, "refs/heads/feature-branch": feat_sha},
                None,
                time_t0,
                time_t0,
            )
            conn.commit()

        time_t1 = datetime(2026, 9, 8, 12, 0, 0, tzinfo=timezone.utc)
        with patch("rebalance.lib.time_ops.now_utc", return_value=time_t1), \
             patch("rebalance.ingest.github_commit_backfill.now_utc", return_value=time_t1):
            res_renew = backfill_commits(self.db, REPO, clone_path=self.fx.path)
            self.assertTrue(res_renew.skipped_cache)

        with db_connection(self.db) as conn:
            row = conn.execute("SELECT verified_at FROM github_remote_peeks WHERE canonical_remote_url = ?", (canonical_url,)).fetchone()
            self.assertEqual(row[0], time_t1.isoformat())

        # Monotonic non-regression check: an older timestamp cannot regress verified_at
        time_older = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)
        with patch("rebalance.lib.time_ops.now_utc", return_value=time_older), \
             patch("rebalance.ingest.github_commit_backfill.now_utc", return_value=time_older):
            res_older = backfill_commits(self.db, REPO, clone_path=self.fx.path)
            self.assertTrue(res_older.skipped_cache)

        with db_connection(self.db) as conn:
            row2 = conn.execute("SELECT verified_at FROM github_remote_peeks WHERE canonical_remote_url = ?", (canonical_url,)).fetchone()
            self.assertEqual(row2[0], time_t1.isoformat(), "verified_at must remain monotonic and not regress")

    def test_shallow_clone_refuses_unbounded_checkpoint(self):
        """Shallow clone with truncated history must never publish a checkpoint (Codex R1)."""
        # 1. Multi-commit clone with .git/shallow
        _write(self.fx.path, "doc2.txt", "second commit")
        _git(self.fx.path, "add", "doc2.txt")
        _git(self.fx.path, "commit", "-q", "-m", "second commit")
        _git(self.fx.path, "push", "-q", "origin", "development")
        second_sha = _git(self.fx.path, "rev-parse", "HEAD")

        shallow_file = self.fx.path / ".git" / "shallow"
        shallow_file.write_text(f"{second_sha}\n")
        try:
            self.assertTrue(is_shallow_clone(self.fx.path))
            res = backfill_commits(self.db, REPO, clone_path=self.fx.path)
            self.assertEqual(res.state, "ok")
            with db_connection(self.db) as conn:
                chk = conn.execute("SELECT * FROM github_remote_peeks").fetchone()
                self.assertIsNone(chk, "Shallow clone must never publish a commit coverage checkpoint")
        finally:
            if shallow_file.exists():
                shallow_file.unlink()

        # 2. Linked worktree inheriting shallow status from git common dir
        wt_path = self.fx.path.parent / "wt_clone"
        _git(self.fx.path, "worktree", "add", "-q", "--detach", str(wt_path))
        shallow_file.write_text(f"{second_sha}\n")
        try:
            self.assertTrue(is_shallow_clone(wt_path), "Linked worktree must detect shallow from git common dir")
        finally:
            if shallow_file.exists():
                shallow_file.unlink()
            _git(self.fx.path, "worktree", "remove", "--force", str(wt_path))

        # 3. Injected nonzero exit / timeout fails safe to shallow=True
        with patch("rebalance.ingest.github_commit_backfill.run_git") as mock_git:
            mock_git.return_value = subprocess.CompletedProcess(args=[], returncode=128, stdout="", stderr="error")
            self.assertTrue(is_shallow_clone(self.fx.path), "Nonzero rev-parse exit must fail-safe to shallow=True")

        with patch("rebalance.ingest.github_commit_backfill.run_git", side_effect=subprocess.TimeoutExpired(cmd="rev-parse", timeout=1.0)):
            self.assertTrue(is_shallow_clone(self.fx.path), "Timeout on rev-parse must fail-safe to shallow=True")

    def test_concurrent_ref_change_during_walk_refuses_checkpoint(self):
        """Ref movement during history walk refuses checkpoint publication (Codex R1)."""
        import rebalance.ingest.github_commit_backfill as bfill
        original_git = bfill._git

        post_walk_called = False

        def fake_git(repo_path, *args):
            nonlocal post_walk_called
            if args and args[0] == "for-each-ref" and "refs/remotes/origin" in args:
                if not post_walk_called:
                    post_walk_called = True
                    return (0, f"refs/remotes/origin/development {self.fx.init_sha}\n", "")
                else:
                    return (0, "refs/remotes/origin/development deadbeef00000000000000000000000000000000\n", "")
            return original_git(repo_path, *args)

        with patch("rebalance.ingest.github_commit_backfill._git", side_effect=fake_git):
            res = backfill_commits(self.db, REPO, clone_path=self.fx.path)
            self.assertEqual(res.state, "ok")
            with db_connection(self.db) as conn:
                chk = conn.execute("SELECT * FROM github_remote_peeks").fetchone()
                self.assertIsNone(chk, "Ref change during walk must refuse checkpoint publication")

    def test_probe_budget_fake_clock_multi_repo(self):
        """When probe budget expires, subsequent repos skip optional calls while continuing walk (Codex R9)."""
        from rebalance.ingest.github_commit_backfill import backfill_repos
        import rebalance.ingest.github_commit_backfill as bfill

        call_counts = {"remote_get_url": 0, "peek_remote_refs": 0}
        original_run_git = bfill.run_git

        def tracking_run_git(path, *args, **kwargs):
            if len(args) >= 2 and args[0] == "remote" and args[1] == "get-url":
                call_counts["remote_get_url"] += 1
            return original_run_git(path, *args, **kwargs)

        def tracking_peek(path, **kwargs):
            call_counts["peek_remote_refs"] += 1
            return {"refs/heads/development": self.fx.init_sha}

        # Mock monotonic clock: advances beyond 15.0s during first repo
        fake_times = [100.0, 100.1, 100.2, 100.3, 120.0, 120.1, 120.2]

        def mock_monotonic():
            if fake_times:
                return fake_times.pop(0)
            return 200.0

        with patch("time.monotonic", side_effect=mock_monotonic), \
             patch("rebalance.ingest.github_commit_backfill.run_git", side_effect=tracking_run_git), \
             patch("rebalance.ingest.github_commit_backfill.peek_remote_refs", side_effect=tracking_peek), \
             patch("rebalance.ingest.github_commit_backfill.resolve_clone", return_value=self.fx.path):

            results = backfill_repos(
                self.db,
                [REPO, "HiQS-Labs/rebalanceOS"],
                probe_budget_seconds=15.0,
            )
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].state, "ok")
            self.assertEqual(results[1].state, "ok")

            # First repo probed; second repo skipped optional probe calls because budget expired
            self.assertEqual(call_counts["remote_get_url"], 1)
            self.assertEqual(call_counts["peek_remote_refs"], 1)

    def test_build_hardened_ssh_command_conflicting_options(self):
        """build_hardened_ssh_command neutralizes conflicting options and honors core.sshCommand (Codex R4)."""
        from rebalance.lib.git_ops import build_hardened_ssh_command

        # 1. Neutralizes conflicting BatchMode=no
        with patch.dict(os.environ, {"GIT_SSH_COMMAND": "ssh -o BatchMode=no -i /id_rsa"}):
            cmd = build_hardened_ssh_command()
            self.assertIn("-o BatchMode=yes", cmd)
            self.assertNotIn("BatchMode=no", cmd)
            self.assertIn("-i /id_rsa", cmd)

        # 2. Honors core.sshCommand when GIT_SSH_COMMAND is unset
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GIT_SSH_COMMAND", None)
            with patch("rebalance.lib.git_ops.run_git") as mock_git:
                mock_git.return_value = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="custom-ssh -i /path/key\n", stderr=""
                )
                cmd2 = build_hardened_ssh_command(repo_path=self.fx.path)
                self.assertTrue(cmd2.startswith("custom-ssh -o BatchMode=yes -o ConnectTimeout=5"))
                self.assertIn("-i /path/key", cmd2)

    def test_stale_scheduler_overlap_rejected(self):
        """Stale snapshot from overlapping scheduler run cannot overwrite newer checkpoint."""
        canonical_url = "https://github.com/HiQS-Labs/rebalanceOS.git"
        ref_map = {"refs/heads/development": "sha1"}

        with db_connection(self.db) as conn:
            # Fast run T1 (12:30) publishes checkpoint
            t1 = "2026-09-08T12:30:00Z"
            ok = record_commit_coverage_checkpoint(
                conn, canonical_url, ref_map, "2026-08-01T00:00:00Z", verified_at_utc=t1, snapshot_time_utc=t1
            )
            self.assertTrue(ok)

            # Slower overlapping run that took snapshot at T0 (12:00) finishes now at T2 (12:45)
            t_snap_old = "2026-09-08T12:00:00Z"
            t_finish_now = "2026-09-08T12:45:00Z"
            stale_ok = record_commit_coverage_checkpoint(
                conn, canonical_url, ref_map, "2026-08-01T00:00:00Z", verified_at_utc=t_finish_now, snapshot_time_utc=t_snap_old
            )
            self.assertFalse(stale_ok)

            # Assert database still has T1 verified_at
            cur_ver = conn.execute("SELECT verified_at FROM github_remote_peeks WHERE canonical_remote_url = ?", (canonical_url,)).fetchone()[0]
            self.assertEqual(cur_ver, t1)

    def test_sync_github_repo_metadata_authoritative_fixture(self):
        """Metadata polling (issues, PRs, comments) remains authoritative and updates changed existing issues (Codex R1 & R6)."""
        from rebalance.ingest.github_knowledge import sync_github_repo

        # Establish commit cache hit
        backfill_commits(self.db, REPO, clone_path=self.fx.path)
        res_cached = backfill_commits(self.db, REPO, clone_path=self.fx.path)
        self.assertTrue(res_cached.skipped_cache)

        # Mock API returning a new issue AND a new PR
        def mock_api(url: str, **kwargs):
            if "/issues?" in url:
                return [
                    {
                        "number": 42,
                        "title": "Fresh issue opened without commit movement",
                        "body": "Issue details",
                        "state": "open",
                        "updated_at": "2026-09-08T18:00:00Z",
                        "created_at": "2026-09-08T18:00:00Z",
                        "labels": [],
                        "user": {"login": "tester"},
                    }
                ]
            if "/pulls?" in url:
                return [
                    {
                        "number": 101,
                        "title": "Fresh PR opened without commit movement",
                        "updated_at": "2026-09-08T18:00:00Z",
                    }
                ]
            if url.endswith("/pulls/101"):
                return {
                    "number": 101,
                    "title": "Fresh PR opened without commit movement",
                    "body": "PR description",
                    "state": "open",
                    "draft": False,
                    "merged_at": None,
                    "closed_at": None,
                    "created_at": "2026-09-08T18:00:00Z",
                    "updated_at": "2026-09-08T18:00:00Z",
                    "user": {"login": "pr_author"},
                    "base": {"ref": "development"},
                    "head": {"ref": "feature-pr", "sha": "headsha101"},
                    "labels": [],
                }
            if "/commits/headsha101/check-runs" in url:
                return {"check_runs": []}
            if url.endswith(f"/repos/{REPO}"):
                return {
                    "default_branch": "development",
                    "pushed_at": "2026-09-08T12:00:00Z",
                    "updated_at": "2026-09-08T12:00:00Z",
                    "open_issues_count": 1,
                    "has_issues": True,
                    "has_projects": False,
                }
            return []

        # Run 1: initial metadata sync
        sync_res = sync_github_repo(
            database_path=self.db,
            repo_full_name=REPO,
            token="ghp_test",
            since_days=7,
            api_get_json=mock_api,
        )
        self.assertEqual(sync_res.issues_synced, 1)
        self.assertEqual(sync_res.prs_synced, 1)

        # Run 2: Changed existing issue control (Codex R6)
        def mock_api_changed(url: str, **kwargs):
            if "/issues?" in url:
                return [
                    {
                        "number": 42,
                        "title": "Updated Title via Metadata Sync",
                        "body": "Updated body",
                        "state": "open",
                        "updated_at": "2026-09-08T19:00:00Z",
                        "created_at": "2026-09-08T18:00:00Z",
                        "labels": [],
                        "user": {"login": "tester"},
                    }
                ]
            return mock_api(url, **kwargs)

        sync_res_2 = sync_github_repo(
            database_path=self.db,
            repo_full_name=REPO,
            token="ghp_test",
            since_days=7,
            api_get_json=mock_api_changed,
        )
        self.assertEqual(sync_res_2.issues_synced, 1)

        with db_connection(self.db) as conn:
            issue_row = conn.execute("SELECT number, title FROM github_items WHERE number = 42").fetchone()
            self.assertIsNotNone(issue_row)
            self.assertEqual(issue_row[1], "Updated Title via Metadata Sync")

    def test_remote_peeking_disabled_by_default_rollout_gate(self):
        """When enable_remote_peeking is False, remote probes are bypassed completely (Rollout Gate)."""
        set_enable_remote_peeking(False)
        with patch("rebalance.ingest.github_commit_backfill.peek_remote_refs") as mock_peek:
            res = backfill_commits(self.db, REPO, clone_path=self.fx.path)
            self.assertEqual(res.state, "ok")
            mock_peek.assert_not_called()


if __name__ == "__main__":
    unittest.main()

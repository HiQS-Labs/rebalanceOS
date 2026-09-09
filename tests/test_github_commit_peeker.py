"""Tests for GH-201: Git Remote Peeker & Commit Walk Gating."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rebalance.ingest.db import db_connection, ensure_github_schema, ensure_schema
from rebalance.ingest.github_commit_backfill import (
    BackfillResult,
    backfill_commits,
    is_commit_walk_cached,
    record_commit_coverage_checkpoint,
)
from rebalance.lib.git_ops import (
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
        _git(self.path, "push", "-q", "origin", "development")
        self.init_sha = _git(self.path, "rev-parse", "HEAD")


class GitCommitPeekerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.db = root / "test.db"
        with db_connection(self.db, ensure_schema):
            pass
        with db_connection(self.db, ensure_github_schema):
            pass
        self.fx = _RepoWithRemoteFixture(root)

    def tearDown(self):
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
            self.assertEqual(row[0], str(self.fx.bare))

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
        """Requesting a wider history window than recorded checkpoint forces full walk."""
        # Seed checkpoint covering since 2026-08-01
        backfill_commits(self.db, REPO, clone_path=self.fx.path, since="2026-08-01T00:00:00Z")

        # Walk with since 2026-08-15 (narrower) hits cache
        res_narrow = backfill_commits(self.db, REPO, clone_path=self.fx.path, since="2026-08-15T00:00:00Z")
        self.assertTrue(res_narrow.skipped_cache)

        # Walk with since 2026-07-01 (wider) misses cache
        res_wide = backfill_commits(self.db, REPO, clone_path=self.fx.path, since="2026-07-01T00:00:00Z")
        self.assertFalse(res_wide.skipped_cache)

    def test_force_refresh_bypasses_cache(self):
        """Passing force_refresh=True unconditionally runs commit walk."""
        backfill_commits(self.db, REPO, clone_path=self.fx.path)

        res = backfill_commits(self.db, REPO, clone_path=self.fx.path, force_refresh=True)
        self.assertFalse(res.skipped_cache)

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
        """Metadata polling (issues, PRs, comments) remains authoritative and unaffected by commit gating (Codex R1)."""
        from rebalance.ingest.github_knowledge import sync_github_repo

        # Establish commit cache hit
        backfill_commits(self.db, REPO, clone_path=self.fx.path)
        res_cached = backfill_commits(self.db, REPO, clone_path=self.fx.path)
        self.assertTrue(res_cached.skipped_cache)

        # Mock API returning a new issue and PR even though git commit SHAs did NOT move
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

        # Run sync_github_repo
        sync_res = sync_github_repo(
            database_path=self.db,
            repo_full_name=REPO,
            token="ghp_test",
            since_days=7,
            api_get_json=mock_api,
        )

        # Verify metadata sync processed the issue despite commit cache-hit
        self.assertEqual(sync_res.issues_synced, 1)
        with db_connection(self.db) as conn:
            issue_row = conn.execute("SELECT number, title FROM github_items WHERE number = 42").fetchone()
            self.assertIsNotNone(issue_row)
            self.assertEqual(issue_row[1], "Fresh issue opened without commit movement")


if __name__ == "__main__":
    unittest.main()

"""Tests for GH-204: Focus 5 full clone detection and grouping."""

from __future__ import annotations

import unittest
from dataclasses import asdict

from rebalance.ingest.focus5_scan import (
    RepoSignals,
    detect_repo_parent_key,
    pick_parent_checkout,
    roll_up_parent_signals,
    rank_repos,
    summarize_focus5,
    _build_roster_card,
)
from rebalance.ingest.db import db_connection, run_migrations


def _make_sig(
    name: str,
    path: str,
    repo_full_name: str | None = None,
    branch: str = "main",
    my_local_commit_ts: int | None = None,
    is_dirty: bool = False,
    ahead: int = 0,
    modified_count: int = 0,
    untracked_count: int = 0,
) -> RepoSignals:
    return RepoSignals(
        device_id="dev",
        local_path=path,
        repo_name=name,
        repo_full_name=repo_full_name,
        branch=branch,
        upstream=None,
        has_upstream=False,
        ahead=ahead,
        behind=0,
        modified_count=modified_count,
        untracked_count=untracked_count,
        is_dirty=is_dirty,
        last_commit_at=None,
        last_commit_ts=my_local_commit_ts,
        my_last_commit_ts=my_local_commit_ts,
        my_local_commit_ts=my_local_commit_ts,
        recency_basis="local_reflog" if my_local_commit_ts else "none",
        head_reflog_ts=None,
        index_mtime_ts=None,
        remote_url=f"https://github.com/{repo_full_name}.git" if repo_full_name else None,
        probed_at="2026-09-10T12:00:00Z",
    )


class CloneDetectionTests(unittest.TestCase):
    def test_detect_repo_parent_key_with_full_name(self) -> None:
        s1 = _make_sig("XYZ-forge", "/repos/XYZ-forge", repo_full_name="Hypercart-Dev-Tools/XYZ-forge")
        s2 = _make_sig("XYZ-forge-gh365", "/repos/XYZ-forge-gh365", repo_full_name="Hypercart-Dev-Tools/XYZ-forge")
        self.assertEqual(detect_repo_parent_key(s1), "hypercart-dev-tools/xyz-forge")
        self.assertEqual(detect_repo_parent_key(s2), "hypercart-dev-tools/xyz-forge")

    def test_detect_repo_parent_key_fallback_strip_suffix(self) -> None:
        s1 = _make_sig("XYZ-forge", "/repos/XYZ-forge")
        s2 = _make_sig("XYZ-forge-gh365", "/repos/XYZ-forge-gh365")
        s3 = _make_sig("XYZ-forge-qual3", "/repos/XYZ-forge-qual3")
        self.assertEqual(detect_repo_parent_key(s1), "/repos/XYZ-forge")
        self.assertEqual(detect_repo_parent_key(s2), "xyz-forge")
        self.assertEqual(detect_repo_parent_key(s3), "xyz-forge")

    def test_pick_parent_checkout_exact_name_match_wins(self) -> None:
        parent = _make_sig("XYZ-forge", "/repos/XYZ-forge", repo_full_name="Hypercart-Dev-Tools/XYZ-forge", branch="development")
        clone1 = _make_sig("XYZ-forge-gh365", "/repos/XYZ-forge-gh365", repo_full_name="Hypercart-Dev-Tools/XYZ-forge", branch="feat/gh365")
        clone2 = _make_sig("XYZ-forge-gh384", "/repos/XYZ-forge-gh384", repo_full_name="Hypercart-Dev-Tools/XYZ-forge", branch="feat/gh384")
        chosen = pick_parent_checkout([clone1, parent, clone2])
        self.assertEqual(chosen.repo_name, "XYZ-forge")
        self.assertEqual(chosen.local_path, "/repos/XYZ-forge")

    def test_pick_parent_checkout_main_branch_wins_when_names_similar(self) -> None:
        c1 = _make_sig("my-repo-task", "/repos/my-repo-task", branch="feat/foo")
        c2 = _make_sig("my-repo", "/repos/my-repo", branch="main")
        chosen = pick_parent_checkout([c1, c2])
        self.assertEqual(chosen.repo_name, "my-repo")

    def test_roll_up_parent_signals_inherits_newest_commit_and_dirty_state(self) -> None:
        parent = _make_sig("XYZ-forge", "/repos/XYZ-forge", my_local_commit_ts=1000, is_dirty=False)
        clone1 = _make_sig("XYZ-forge-gh365", "/repos/XYZ-forge-gh365", my_local_commit_ts=5000, is_dirty=True)
        clone2 = _make_sig("XYZ-forge-gh384", "/repos/XYZ-forge-gh384", my_local_commit_ts=3000, is_dirty=False)

        rolled = roll_up_parent_signals(parent, [clone1, clone2])
        self.assertEqual(rolled.my_local_commit_ts, 5000)
        self.assertTrue(rolled.is_dirty)
        self.assertEqual(rolled.local_path, "/repos/XYZ-forge")

    def test_rank_repos_groups_clones_into_single_slot(self) -> None:
        now = 10000
        xyz_main = _make_sig("XYZ-forge", "/repos/XYZ-forge", repo_full_name="Hypercart-Dev-Tools/XYZ-forge", my_local_commit_ts=1000)
        xyz_clone1 = _make_sig("XYZ-forge-gh365", "/repos/XYZ-forge-gh365", repo_full_name="Hypercart-Dev-Tools/XYZ-forge", my_local_commit_ts=9900)
        xyz_clone2 = _make_sig("XYZ-forge-gh384", "/repos/XYZ-forge-gh384", repo_full_name="Hypercart-Dev-Tools/XYZ-forge", my_local_commit_ts=9800)

        rb_main = _make_sig("rebalanceOS", "/repos/rebalanceOS", repo_full_name="HiQS-Labs/rebalanceOS", my_local_commit_ts=2000)
        rb_clone = _make_sig("rebalanceOS-gh144", "/repos/rebalanceOS-gh144", repo_full_name="HiQS-Labs/rebalanceOS", my_local_commit_ts=9500)

        repo3 = _make_sig("LTVera-Pandas", "/repos/LTVera-Pandas", repo_full_name="BinoidCBD/LTVera-Pandas", my_local_commit_ts=9000)
        repo4 = _make_sig("AI-DDTK", "/repos/AI-DDTK", repo_full_name="Org/AI-DDTK", my_local_commit_ts=8000)
        repo5 = _make_sig("ask-self", "/repos/ask-self", repo_full_name="Org/ask-self", my_local_commit_ts=7000)

        all_signals = [xyz_clone1, xyz_clone2, rb_clone, xyz_main, rb_main, repo3, repo4, repo5]
        ranked = rank_repos(all_signals, mode="recent_activity", now_ts=now, limit=5)

        self.assertEqual(len(ranked), 5)
        self.assertEqual(ranked[0].signals.repo_name, "XYZ-forge")
        self.assertEqual(ranked[0].position, 1)
        self.assertEqual(len(ranked[0].clones), 2)
        clone_names = {c.repo_name for c in ranked[0].clones}
        self.assertEqual(clone_names, {"XYZ-forge-gh365", "XYZ-forge-gh384"})

        self.assertEqual(ranked[1].signals.repo_name, "rebalanceOS")
        self.assertEqual(ranked[1].position, 2)
        self.assertEqual(len(ranked[1].clones), 1)
        self.assertEqual(ranked[1].clones[0].repo_name, "rebalanceOS-gh144")

        self.assertEqual(ranked[2].signals.repo_name, "LTVera-Pandas")
        self.assertEqual(ranked[3].signals.repo_name, "AI-DDTK")
        self.assertEqual(ranked[4].signals.repo_name, "ask-self")

    def test_build_roster_card_attaches_clone_info(self) -> None:
        parent = _make_sig("XYZ-forge", "/repos/XYZ-forge", repo_full_name="Hypercart-Dev-Tools/XYZ-forge", my_local_commit_ts=1000)
        clone = _make_sig(
            "XYZ-forge-gh365",
            "/repos/XYZ-forge-gh365",
            repo_full_name="Hypercart-Dev-Tools/XYZ-forge",
            branch="feat/gh365",
            my_local_commit_ts=5000,
            is_dirty=True,
            modified_count=2,
            untracked_count=1,
        )
        base = {
            **asdict(parent),
            "position": 1,
            "rank_reason": "your commit just now",
            "ranking_mode": "recent_activity",
            "computed_at": "2026-09-10T12:00:00Z",
            "clones": [clone],
        }
        card = _build_roster_card(None, base, with_activity=False, with_live_health=False)
        self.assertIn("clones", card)
        self.assertEqual(len(card["clones"]), 1)
        c0 = card["clones"][0]
        self.assertEqual(c0["repo_name"], "XYZ-forge-gh365")
        self.assertEqual(c0["branch"], "feat/gh365")
        self.assertTrue(c0["is_dirty"])
        self.assertTrue(card["any_clone_dirty"])
        self.assertEqual(card["clones_dirty_count"], 1)

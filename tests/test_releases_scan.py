"""Tests for the GH-310 opt-in, read-only RELEASES ledger scan."""

import hashlib
import json
import sqlite3
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from typer.testing import CliRunner

from rebalance.cli import app
from rebalance.ingest.db import db_connection, ensure_github_schema
from rebalance.ingest.github_readiness import infer_close_loop_flags
from rebalance.ingest.releases_scan import discover_ledgers, scan_releases

REPO = "Acme/widget"
NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
STAMP = "2026-10-01T00:00:00Z"


def _clone(path: Path, origin: str | None = "https://github.com/Acme/widget.git", branch: str = "development") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True)
    if origin:
        subprocess.run(["git", "-C", str(path), "remote", "add", "origin", origin], check=True)
    return path


def _ledger(root: Path, rows, repos=((1, "widget"),), *, wal: bool = False) -> Path:
    db = root / "releases.db"
    conn = sqlite3.connect(db)
    if wal:
        conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE repos (id INTEGER PRIMARY KEY, global_id TEXT, slug TEXT, updated_at TEXT)")
    conn.execute(
        "CREATE TABLE roadmap_items (id INTEGER PRIMARY KEY, global_id TEXT, repo_id INTEGER, gh_number INTEGER,"
        " title TEXT, section TEXT, status_marker TEXT, rating_pri INTEGER, rating_sev INTEGER,"
        " rating_appeal INTEGER, rating_effort INTEGER, issue_url TEXT, doc_path TEXT, updated_at TEXT)"
    )
    conn.executemany("INSERT INTO repos (id, slug) VALUES (?, ?)", repos)
    for gid, repo_id, number, section, updated in rows:
        conn.execute(
            "INSERT INTO roadmap_items (global_id, repo_id, gh_number, title, section, status_marker, rating_pri,"
            " rating_sev, rating_appeal, rating_effort, updated_at) VALUES (?, ?, ?, ?, ?, NULL, 60, 30, 50, 70, ?)",
            (gid, repo_id, number, f"task {gid}", section, updated),
        )
    conn.commit()
    conn.close()
    return db


def _fingerprint(base: Path) -> dict[str, tuple[str, int]]:
    out = {}
    for path in sorted(base.rglob("releases.db*")):
        out[str(path)] = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
    return out


class ReleasesScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name) / "GitHub"
        self.base.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_discovery_depth_prune_and_non_repo(self) -> None:
        _ledger(_clone(self.base / "a"), [])
        _ledger(_clone(self.base / "d1" / "d2" / "d3"), [])  # depth 3: found
        _ledger(_clone(self.base / "e1" / "e2" / "e3" / "e4"), [])  # depth 4: not found
        _ledger(_clone(self.base / "x" / "node_modules" / "pkg"), [])  # pruned
        plain = self.base / "plain"
        plain.mkdir()
        _ledger(plain, [])  # no .git: skipped
        found = discover_ledgers([str(self.base)])
        names = sorted(p.relative_to(self.base).as_posix() for p in found["roots"])
        self.assertEqual(names, ["a", "d1/d2/d3"])
        self.assertEqual(found["skipped_non_repo"], 1)
        self.assertFalse(found["truncated"])

    def test_tasks_conflicts_multi_repo_and_errors_without_writes(self) -> None:
        first = _clone(self.base / "widget")
        _ledger(
            first,
            [
                ("R-1", 1, 5, "In progress", "2026-10-01T00:00:00Z"),
                ("R-2", 1, 6, "Queue / parked intake", "2026-09-01T00:00:00Z"),
                ("R-3", 1, 7, "Completed", "2026-09-01T00:00:00Z"),
                ("R-9", 2, 9, "In progress", "2026-09-01T00:00:00Z"),  # other repo in the same ledger
            ],
            repos=((1, "widget"), (2, "Acme/other")),
        )
        second = _clone(self.base / "widget-gh5", branch="feat/gh5")
        _ledger(
            second,
            [
                ("R-1", 1, 5, "Queue / parked intake", "2026-09-15T00:00:00Z"),
                ("R-2", 1, 6, "Queue / parked intake", "2026-09-01T00:00:00Z"),
            ],
        )
        (_clone(self.base / "widget-corrupt") / "releases.db").write_bytes(b"not a sqlite file at all" * 10)
        sqlite3.connect(_clone(self.base / "widget-empty") / "releases.db").close()
        _ledger(_clone(self.base / "widget-wal"), [("R-4", 1, 4, "In progress", STAMP)], wal=True)
        _ledger(_clone(self.base / "widget-noorigin", origin=None), [("R-8", 1, 8, "In progress", STAMP)])
        _ledger(
            _clone(self.base / "elsewhere", origin="https://github.com/Other/thing.git"),
            [("O-1", 1, 1, "In progress", STAMP)],
            repos=((1, "thing"),),
        )

        before = _fingerprint(self.base)
        result = scan_releases([str(self.base)], REPO)
        self.assertEqual(before, _fingerprint(self.base))  # red control: bytes + mtime, no new sidecars

        by_number = {t["gh_number"]: t for t in result["tasks"]}
        self.assertEqual(sorted(by_number), [5, 6])  # completed and other-repo rows excluded
        self.assertEqual(by_number[5]["status"], "in-progress")
        self.assertEqual(by_number[5]["clone_path"], str(first))  # newest wins
        self.assertEqual(by_number[5]["clones"], 2)
        self.assertEqual(by_number[5]["rating"], "60/30/50/70")
        self.assertEqual(by_number[6]["status"], "parked")
        self.assertFalse(by_number[6]["conflict"])
        self.assertEqual([c["key"] for c in result["conflicts"]], ["#5"])
        errors = {Path(e["clone_path"]).name: e["error"] for e in result["ledgers"]}
        self.assertEqual(errors["widget-corrupt"], "unreadable")
        self.assertEqual(errors["widget-empty"], "missing-table")
        self.assertEqual(errors["widget-wal"], "wal-mode")
        self.assertEqual(errors["widget-noorigin"], "identity-unresolved")
        self.assertNotIn("elsewhere", errors)
        self.assertEqual(result["other_repo_ledgers"], 1)
        self.assertEqual(result["ledgers_found"], 7)
        self.assertEqual(result["counts"]["ledger_errors"], 4)

    def test_recorded_status_label_is_kept_and_compared(self) -> None:
        for name, label in (("widget", "in-progress"), ("widget-gh5", "blocked")):
            db = _ledger(_clone(self.base / name), [("R-1", 1, 5, "In progress", STAMP)])
            conn = sqlite3.connect(db)  # fixture setup only; the scan itself never writes
            conn.execute("ALTER TABLE roadmap_items ADD COLUMN status_label TEXT")
            conn.execute("UPDATE roadmap_items SET status_label = ?", (label,))
            conn.commit()
            conn.close()
        result = scan_releases([str(self.base)], REPO)
        self.assertEqual(result["tasks"][0]["status"], "in-progress")
        self.assertIn(result["tasks"][0]["status_label"], {"in-progress", "blocked"})
        self.assertEqual([c["key"] for c in result["conflicts"]], ["#5"])
        self.assertEqual(
            sorted(v["status_label"] for v in result["conflicts"][0]["values"]), ["blocked", "in-progress"]
        )


def _seed_corpus(db_path: Path) -> None:
    with db_connection(db_path, ensure_github_schema) as conn:
        conn.execute(
            "INSERT INTO github_repo_meta (repo_full_name, default_branch, fetched_at) VALUES (?, 'development', ?)",
            (REPO, STAMP),
        )
        for item_type, number, state, merged in [
            ("issue", 5, "closed", 0),
            ("issue", 6, "open", 0),
            ("issue", 7, "open", 0),
            ("pull_request", 60, "closed", 1),
        ]:
            conn.execute(
                "INSERT INTO github_items (repo_full_name, item_type, number, title, state, is_merged, html_url,"
                " created_at, updated_at, closed_at, fetched_at) VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?)",
                (
                    REPO,
                    item_type,
                    number,
                    f"{item_type} {number}",
                    state,
                    merged,
                    STAMP,
                    STAMP,
                    STAMP if state == "closed" else None,
                    STAMP,
                ),
            )
        conn.execute(
            "INSERT INTO github_links (repo_full_name, source_type, source_number, target_type, target_number,"
            " link_kind) VALUES (?, 'pull_request', 60, 'issue', 6, 'closes')",
            (REPO,),
        )
        conn.commit()


class CloseLoopReleasesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.db_path = tmp / "rebalance.db"
        self.base = tmp / "GitHub"
        _ledger(
            _clone(self.base / "widget"),
            [
                ("R-5", 1, 5, "In progress", STAMP),
                ("R-6", 1, 6, "In progress", STAMP),
                ("R-7", 1, 7, "In progress", STAMP),
            ],
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_drift_positives_and_negative_twin(self) -> None:
        _seed_corpus(self.db_path)
        report = infer_close_loop_flags(self.db_path, REPO, now=NOW, releases_scan_dirs=[str(self.base)])
        drift = {d["gh_number"]: d["kind"] for d in report["releases"]["drift"]}
        self.assertEqual(drift, {5: "issue_closed", 6: "pr_merged"})  # #7 open, no PR: no drift
        self.assertEqual(report["releases"]["counts"]["drift"], 2)
        json.dumps(report)

    def test_no_local_data_still_reports_ledger_tasks(self) -> None:
        report = infer_close_loop_flags(self.db_path, REPO, now=NOW, releases_scan_dirs=[str(self.base)])
        self.assertEqual(report["status"], "no_local_data")
        self.assertEqual(report["releases"]["counts"]["tasks"], 3)

    def test_default_off_has_no_releases_block(self) -> None:
        _seed_corpus(self.db_path)
        report = infer_close_loop_flags(self.db_path, REPO, now=NOW)
        self.assertNotIn("releases", report)
        runner = CliRunner()
        args = ["github-close-loop", "--repo", REPO, "--database", str(self.db_path), "--output", "json"]
        off = json.loads(runner.invoke(app, args).output)
        on = json.loads(runner.invoke(app, [*args, "--releases-scan", str(self.base)]).output)
        self.assertNotIn("releases", off)
        self.assertEqual(set(on) - set(off), {"releases"})
        self.assertEqual(
            {k: v for k, v in on.items() if k not in ("releases", "as_of")},
            {k: v for k, v in off.items() if k != "as_of"},
        )


if __name__ == "__main__":
    unittest.main()

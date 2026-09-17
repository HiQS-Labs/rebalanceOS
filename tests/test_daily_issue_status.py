"""Nonempty, offline status fixtures: no operator data, writers or paid calls."""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.ingest.db.queries import fetch_issue_status_evidence

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("daily_status_test", ROOT / "utils/daily_work_synthesis.py")
dws = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dws)
NOW = datetime(2026, 9, 17, 20, tzinfo=timezone.utc)
AT = NOW.isoformat()
OLD = (NOW - timedelta(days=7)).isoformat()
EVIDENCE = {"supported": True, "read_at": AT, "roots_complete": True,
            "status_label": "in-progress", "start": {"at": OLD, "event": "in_flight", "freshness": "stale"},
            "lifecycle": {"at": OLD, "event": "in_flight"}}
NATIVE = {"native_identity_valid": True, "state": "open", "labels": ["in-progress"], "fetched_at": AT}


def native_database(path, *, closed=False):
    cx = sqlite3.connect(path)
    cx.executescript("""CREATE TABLE github_items(repo_full_name TEXT,item_type TEXT,number INTEGER,state TEXT,
        html_url TEXT,updated_at TEXT,fetched_at TEXT,created_at TEXT,labels_json TEXT,state_reason TEXT,title TEXT);""")
    cx.execute("INSERT INTO github_items VALUES(?,?,?,?,?,?,?,?,?,?,?)", (
        "Example/Project", "issue", 7, "closed" if closed else "open",
        "https://github.com/Example/Project/issues/7", OLD, AT, OLD,
        '["in-progress"]', "completed" if closed else None,
        "PRIVATE-TITLE /Users/private/account token=private-token"))
    cx.commit(); cx.close()


def trusted_fixture(tmp_path, report):
    harness = tmp_path / "trusted"
    script = harness / "utils/py/releases_app.py"
    script.parent.mkdir(parents=True)
    script.write_text(f"def load_work_evidence(path,as_of=None): return {report!r}\n"
                      "def main(): raise AssertionError('CLI/writer forbidden')\n"
                      "if __name__=='__main__': main()\n")
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    (ledger / "releases.db").write_bytes(b"populated read-only sentinel")
    return harness, ledger


def report():
    return {"schema_ready": True, "status_label_supported": True, "generation": 7,
            "raw_payload": "PRIVATE-PAYLOAD", "cursor": "PRIVATE-CURSOR",
            "issues": [{"identity_valid": True, "repo": "Example/Project", "number": 7,
                        "status_label_supported": True, "status_label": "in-progress",
                        "recent_start": EVIDENCE["start"], "latest_lifecycle": EVIDENCE["lifecycle"]}]}


def test_status_agreement_preserves_quiet_multiday_work():
    assert dws.issue_status(NATIVE, [EVIDENCE], NOW)["kind"] == "in-progress"
    assert "execution unverified" in dws.issue_status(NATIVE, [EVIDENCE], NOW)["reason"]


@pytest.mark.parametrize("reason,label", [("completed", "Completed"), ("not_planned", "Cancelled"), (None, "Closed")])
def test_fresh_closure_precedes_stale_conflicting_or_stopped_ledger(reason, label):
    closed = NATIVE | {"state": "closed", "state_reason": reason}
    bad = EVIDENCE | {"supported": False, "roots_complete": False, "start": None}
    result = dws.issue_status(closed, [bad], NOW)
    assert result["label"] == label
    assert "cleanup pending" in result["reason"]


@pytest.mark.parametrize("override", [
    {"fetched_at": (NOW - timedelta(seconds=7201)).isoformat()},
    {"fetched_at": (NOW + timedelta(seconds=1)).isoformat()},
    {"fetched_at": "2026-09-17T20:00:00"}, {"native_identity_valid": False}, {"labels": None},
])
def test_invalid_or_stale_native_is_not_current_work(override):
    assert dws.issue_status(NATIVE | override, [EVIDENCE], NOW)["kind"] == "unknown"


@pytest.mark.parametrize("override", [
    {"supported": False}, {"roots_complete": False}, {"error": "timeout"}, {"start": None},
    {"read_at": (NOW - timedelta(seconds=301)).isoformat()},
])
def test_incomplete_or_unestablished_ledger_is_not_current_work(override):
    assert dws.issue_status(NATIVE, [EVIDENCE | override], NOW)["kind"] == "unknown"


def test_null_label_does_not_mean_completion_and_roots_conflict_independently_of_order():
    quiet = EVIDENCE | {"status_label": None, "start": None}
    assert dws.issue_status(NATIVE | {"labels": []}, [quiet], NOW)["kind"] == "context"
    assert dws.issue_status(NATIVE, [quiet], NOW)["kind"] == "conflict"
    assert dws.issue_status(NATIVE, [EVIDENCE, quiet], NOW) == dws.issue_status(NATIVE, [quiet, EVIDENCE], NOW)


def test_default_unconfigured_does_not_launch_helper(tmp_path, monkeypatch):
    monkeypatch.setattr(dws, "resolve_xyz_work_sources", lambda *_: (None, ()))
    monkeypatch.setattr(dws.importlib.util, "spec_from_file_location", lambda *_: pytest.fail("helper import forbidden"))
    assert dws.collect_issue_statuses(tmp_path / "missing.db", NOW, dws.default_config()) is None


def test_populated_collector_is_readonly_and_egress_is_whitelisted(tmp_path, monkeypatch):
    db = tmp_path / "rebalance.db"
    native_database(db)
    harness, ledger = trusted_fixture(tmp_path, report())
    monkeypatch.setattr(dws, "resolve_xyz_work_sources", lambda *_: (harness, (ledger,)))
    before = db.read_bytes(), (ledger / "releases.db").read_bytes()
    result = dws.collect_issue_statuses(db, NOW, dws.default_config())
    assert result["facts"][0]["kind"] == "in-progress"
    assert result["facts"][0]["sources"][0]["generation"] == 7
    assert not result["partial"]
    encoded = json.dumps(result)
    for forbidden in ("PRIVATE", "private-token", "/Users/", str(tmp_path), "cursor", "raw_payload"):
        assert forbidden not in encoded
    assert before == (db.read_bytes(), (ledger / "releases.db").read_bytes())
    assert not any(path.exists() for path in (Path(str(db) + "-wal"), Path(str(db) + "-shm")))


def test_failed_second_root_is_visible_uncertainty_not_confirmed_work(tmp_path, monkeypatch):
    db = tmp_path / "rebalance.db"
    native_database(db)
    harness, ledger = trusted_fixture(tmp_path, report())
    for roots in ((ledger, tmp_path / "missing"), (tmp_path / "missing", ledger)):
        monkeypatch.setattr(dws, "resolve_xyz_work_sources", lambda *_: (harness, roots))
        result = dws.collect_issue_statuses(db, NOW, dws.default_config())
        assert result["facts"][0]["kind"] == "unknown"
        assert result["partial"]


def test_newest_case_variant_and_strict_url_validation(tmp_path, monkeypatch):
    from rebalance.ingest.db import queries
    monkeypatch.setattr(queries, "_get_alias_map", lambda: {})
    db = tmp_path / "rebalance.db"
    native_database(db)
    cx = sqlite3.connect(db)
    cx.execute("INSERT INTO github_items SELECT upper(repo_full_name),item_type,number,'closed',html_url,?,?,created_at,labels_json,'completed',title FROM github_items", (AT, AT))
    cx.commit(); cx.close()
    for url, valid in (("https://github.com/Example/Project/issues/7", True),
                       ("https://evil.test/Example/Project/issues/7", False),
                       ("https://github.com/Other/Project/issues/7", False),
                       ("https://github.com/Example/Project/pull/7", False),
                       ("https://github.com/Example/Project/issues/8", False)):
        cx = sqlite3.connect(db)
        cx.execute("UPDATE github_items SET html_url=?", (url,)); cx.commit(); cx.close()
        with db_connection_readonly(db) as conn:
            native = fetch_issue_status_evidence(conn, [("example/project", 7)], time.monotonic() + 1)
        assert native[("example/project", 7)]["state"] == "closed"
        assert native[("example/project", 7)]["native_identity_valid"] is valid


def test_native_sql_lock_is_bounded(tmp_path, monkeypatch):
    from rebalance.ingest.db import queries
    monkeypatch.setattr(queries, "_get_alias_map", lambda: {})
    db = tmp_path / "rebalance.db"
    native_database(db)
    cx = sqlite3.connect(db)
    cx.execute("BEGIN EXCLUSIVE")
    began = time.monotonic()
    try:
        with db_connection_readonly(db) as conn, pytest.raises(sqlite3.OperationalError):
            fetch_issue_status_evidence(conn, [("example/project", 7)], began + 0.15)
        assert time.monotonic() - began < 0.5
    finally:
        cx.rollback(); cx.close()


def test_model_prose_cannot_replace_authoritative_rendered_status():
    packet = {"unclosed_loops": {}, "cpu_health": {}, "issue_statuses": {
        "facts": [{"id": "issue-status:example/project#7", "repo": "example/project", "number": 7,
                   "label": "In progress", "reason": "Explicit start and cached GitHub agree",
                   "native_at": AT, "established_at": OLD}], "partial": False, "errors": [], "shown": 1, "total_known": 1}}
    result = {"focus": "All work is complete (adversarial model claim)", "trajectory": ["done", "done"],
              "velocity": "Nominal", "operational_horizon": "done", "coaching_nudge": "done", "coaching_trigger": "test"}
    output = dws.render(result, packet, NOW, 1, {}, 0, 0, dws.default_config())
    assert "Model interpretation" in output
    authoritative = output.split("Recorded issue status — authoritative read facts")[1]
    assert "#7: In progress" in authoritative
    assert "All work is complete" not in authoritative


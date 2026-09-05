"""SOP.md §6 — one real-world entity contributes to a metric exactly once.

Deterministic and configuration-agnostic. Every org and repo name here is synthetic
(``oldorg`` / ``NewOrg``), the alias map is injected rather than read from any operator's
``rbos.config``, and the database is a fresh temp file. Nothing in this module depends on
which orgs this checkout's owner happens to have renamed.

What it pins, in the order the defect actually unfolded:

1. ``canonical_github_repo_name`` collapses an aliased owner and leaves everything else alone.
2. A stored-duplicate detector finds one entity written under two spellings for the same day.
3. The reconciliation rule for a snapshot table is *latest wins*, never *sum*.
4. The duplicate fixture is non-zero — the meta-check, because the original guard for this
   defect inserted the duplicate with every metric set to ``0`` and could never fail.

Background: a GitHub org rename put one repository in ``github_activity`` under two spellings
on the same ``scan_date``. Read paths summed them, so a day with 48 commits and 13 PRs
reported 86 and 26 in every ranking built on that table. No error was raised.
"""

import sqlite3

import pytest

from rebalance.ingest import config as config_mod
from rebalance.ingest.db.schema import ensure_github_schema, ensure_schema

# Synthetic identities. `oldorg` is the retired spelling; `NewOrg` is canonical.
OLD_ORG = "oldorg"
NEW_ORG = "NewOrg"
REPO = "widget-service"
LOGIN = "someuser"
DAY = "2026-01-15"

# The duplicate's metrics. Deliberately non-zero and deliberately DIFFERENT from the
# canonical row's, so that neither summing nor picking-the-wrong-row can pass silently.
EARLY = {"commits": 38, "prs_opened": 13, "scanned_at": "2026-01-15T19:45:00+00:00"}
LATE = {"commits": 48, "prs_opened": 13, "scanned_at": "2026-01-15T23:45:00+00:00"}


@pytest.fixture
def aliases(monkeypatch):
    """Inject a synthetic alias map so this never reads the operator's config."""
    monkeypatch.setattr(config_mod, "get_github_org_aliases", lambda: {OLD_ORG: NEW_ORG})
    return {OLD_ORG: NEW_ORG}


@pytest.fixture
def db(tmp_path):
    """A real schema on a throwaway file, holding the same entity under two spellings."""
    path = tmp_path / "dedup.db"
    with sqlite3.connect(path) as conn:
        ensure_schema(conn)
        ensure_github_schema(conn)
        for org, m in ((OLD_ORG, EARLY), (NEW_ORG, LATE)):
            conn.execute(
                """
                INSERT INTO github_activity
                    (login, repo_full_name, scan_date, commits, pushes, prs_opened,
                     prs_merged, issues_opened, issue_comments, reviews,
                     last_active_at, scanned_at)
                VALUES (?, ?, ?, ?, 0, ?, 0, 0, 0, 0, ?, ?)
                """,
                (LOGIN, f"{org}/{REPO}", DAY, m["commits"], m["prs_opened"], m["scanned_at"], m["scanned_at"]),
            )
        conn.commit()
    return path


def _canonical_key(conn, canonicalise):
    """Group rows by (login, canonical repo, day) and return groups holding >1 row."""
    groups: dict[tuple[str, str, str], list[sqlite3.Row]] = {}
    conn.row_factory = sqlite3.Row
    for row in conn.execute("SELECT * FROM github_activity"):
        key = (row["login"], canonicalise(row["repo_full_name"]).lower(), row["scan_date"])
        groups.setdefault(key, []).append(row)
    return {k: v for k, v in groups.items() if len(v) > 1}


def test_canonicalisation_collapses_an_aliased_owner_only(aliases):
    """The owner is rewritten; repo casing, and any unaliased owner, are untouched."""
    canon = config_mod.canonical_github_repo_name
    assert canon(f"{OLD_ORG}/{REPO}") == f"{NEW_ORG}/{REPO}"
    assert canon(f"{OLD_ORG.upper()}/{REPO}") == f"{NEW_ORG}/{REPO}"  # casing variant merges
    assert canon(f"{NEW_ORG}/{REPO}") == f"{NEW_ORG}/{REPO}"
    # A fork of the same repo under a DIFFERENT owner must never be collapsed.
    assert canon(f"someone-else/{REPO}") == f"someone-else/{REPO}"
    # Malformed input is returned unchanged rather than raising.
    assert canon("") == ""
    assert canon("no-slash") == "no-slash"


def test_the_store_holds_one_entity_under_two_spellings(db, aliases):
    """The detector that would have caught the live defect."""
    with sqlite3.connect(db) as conn:
        dupes = _canonical_key(conn, config_mod.canonical_github_repo_name)
    assert len(dupes) == 1, "expected exactly one aliased duplicate group"
    ((key,),) = [tuple(dupes)]
    assert key == (LOGIN, f"{NEW_ORG}/{REPO}".lower(), DAY)
    assert len(dupes[key]) == 2


def test_a_snapshot_table_reconciles_by_latest_not_by_sum(db, aliases):
    """SOP.md §6 rule 1: ON CONFLICT REPLACE means one row wins. Summing is always wrong."""
    with sqlite3.connect(db) as conn:
        dupes = _canonical_key(conn, config_mod.canonical_github_repo_name)
        rows = next(iter(dupes.values()))

    winner = max(rows, key=lambda r: r["scanned_at"])
    assert winner["commits"] == LATE["commits"] == 48
    assert winner["prs_opened"] == LATE["prs_opened"] == 13

    summed = sum(r["commits"] for r in rows)
    assert summed == 86, "fixture sanity: the two rows do sum to the wrong answer"
    assert winner["commits"] != summed, "latest-wins must not agree with summing here"


def test_github_activity_is_a_snapshot_table(db):
    """The schema is what decides latest-wins over summing — pin it, don't assume it."""
    with sqlite3.connect(db) as conn:
        ddl = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='github_activity'").fetchone()[0]
    assert "UNIQUE(login, repo_full_name, scan_date)" in ddl.replace("\n", " ")
    assert "ON CONFLICT REPLACE" in ddl


def test_the_duplicate_fixture_is_not_inert():
    """Meta-check. The original guard for this defect used zeros and could never fail.

    If someone reduces these to zero, summing and latest-wins agree and every assertion
    above passes while testing nothing. That regression is what this pins.
    """
    assert EARLY["commits"] > 0 and LATE["commits"] > 0
    assert EARLY["commits"] != LATE["commits"]
    assert EARLY["scanned_at"] < LATE["scanned_at"]

"""GH-5 Phase 4.2 — exit-code pin tests, written BEFORE the 4.3 reroute.

The plan's safety property: at no point may a binary exit code exist that
cannot be diagnosed. These pins freeze three things ahead of rerouting the CLI
exit through ``health.compute_health_status()``:

(a) the blast radius — every constructor in ``doctor.py`` that can produce a
    ``WARN``-status / ``ERROR``-severity check (exits 0 today, will exit 1
    after 4.3), **derived from source by AST**, not hand-counted. The plan's
    own hand count of five missed a sixth site (``_check_pulse_collectors``,
    whose severity flows dynamically from ``_PULSE_STATE_TO_CHECK``) — found
    by writing this very test, which is the argument for its existence.
(b) the onboarding policy (decided 2026-08-16): fresh install with nothing
    configured exits 0; a *configured* source with no data is an error. Gmail's
    mcp-mode wrinkle is pinned explicitly, not left implicit.
(c) the status-unavailable path: a missing index-status snapshot disables
    suppression (nothing reconciles away) but never crashes and never hides.
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import rebalance.doctor as doctor_mod
from rebalance.doctor import (
    ERROR,
    FAIL,
    OK,
    WARN,
    _COLLECTOR_FRESHNESS,
    _PULSE_STATE_TO_CHECK,
    Check,
    DoctorReport,
    _check_collector_freshness,
)
from rebalance.health import compute_health_status
from rebalance.ingest.db import db_connection, ensure_baseline_schema, run_migrations

NOW = datetime(2026, 8, 16, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# (a) Blast radius, derived from source
# ---------------------------------------------------------------------------


def _warn_check_constructors() -> list[tuple[str, str | None]]:
    """(enclosing function, severity-expression) for every ``Check`` call in
    doctor.py whose status argument is ``WARN`` — literal or dynamic."""
    source = Path(doctor_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    stack: list[str] = []
    found: list[tuple[str, str | None]] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            stack.append(node.name)
            self.generic_visit(node)
            stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and node.func.id == "Check":
                status = (
                    ast.unparse(node.args[1])
                    if len(node.args) >= 2
                    else next(
                        (ast.unparse(k.value) for k in node.keywords if k.arg == "status"),
                        None,
                    )
                )
                severity = next(
                    (ast.unparse(k.value) for k in node.keywords if k.arg == "severity"),
                    None,
                )
                if status is not None and "WARN" in status and status != "WARNING":
                    found.append((stack[-1] if stack else "<module>", severity))
            self.generic_visit(node)

    Visitor().visit(tree)
    return found


class BlastRadiusEnumerationTests(unittest.TestCase):
    """A hand-counted list is not a control. These sets are derived from the
    AST at test time; adding a seventh WARN+ERROR site without updating the pin
    fails loudly instead of silently widening the post-4.3 exit-1 surface."""

    # Every constructor that emits WARN status with LITERAL ERROR severity.
    # _check_collector_freshness appears twice: table-not-present and
    # empty-source (the latter now behind the onboarding gate).
    # _check_sleuth LEFT this set in GH-5 Phase F (operator directive,
    # 2026-08-16): the publisher-staleness check demoted to WARNING — the
    # publisher is a timer on another machine, and every other stale-data
    # check already grades WARNING; device-first health grades the local
    # verdict on local state.
    LITERAL_WARN_ERROR = Counter(
        {
            "_check_collector_freshness": 2,
            "_check_auth_failures": 1,
            "_check_three_eyes_supervision": 1,
        }
    )

    # Constructors whose severity is a VARIABLE that can hold ERROR at
    # runtime. The plan's hand count missed this bucket entirely.
    DYNAMIC_SEVERITY_WARN_CAPABLE = {"_check_pulse_collectors"}

    def test_literal_warn_error_sites_match_the_pin(self) -> None:
        actual = Counter(fn for fn, severity in _warn_check_constructors() if severity == "ERROR")
        self.assertEqual(self.LITERAL_WARN_ERROR, actual)

    def test_dynamic_severity_sites_match_the_pin(self) -> None:
        named = {"ERROR", "WARNING", "NOTICE", "None"}
        actual = {fn for fn, severity in _warn_check_constructors() if severity is not None and severity not in named}
        self.assertEqual(self.DYNAMIC_SEVERITY_WARN_CAPABLE, actual)

    def test_pulse_state_table_error_states_are_the_known_three(self) -> None:
        """The sixth site's actual blast radius: which pulse states produce a
        WARN+ERROR check through _check_pulse_collectors."""
        warn_error_states = {
            state
            for state, (status, severity, _) in _PULSE_STATE_TO_CHECK.items()
            if status == WARN and severity == ERROR
        }
        self.assertEqual({"ALERT", "DEGRADED", "NO PUSHES"}, warn_error_states)


# ---------------------------------------------------------------------------
# (b) Onboarding policy — the decided behaviour table, executed
# ---------------------------------------------------------------------------


def _empty_db(tmp: str) -> Path:
    db = Path(tmp) / "rebalance.db"
    with db_connection(db, ensure_baseline_schema) as conn:
        run_migrations(conn)
    return db


def _freshness_entry(name: str) -> dict:
    entry = next(e for e in _COLLECTOR_FRESHNESS if e["name"] == name)
    self_check = dict(entry)
    return self_check


class OnboardingPolicyTests(unittest.TestCase):
    def test_every_freshness_source_declares_a_configured_probe(self) -> None:
        for entry in _COLLECTOR_FRESHNESS:
            self.assertIn("configured", entry, entry["name"])

    def test_unconfigured_empty_source_is_a_clean_skip(self) -> None:
        """Fresh install, source never opted into: OK, figma's exact posture."""
        with tempfile.TemporaryDirectory() as tmp:
            entry = _freshness_entry("github data")
            entry["configured"] = lambda: False
            check = _check_collector_freshness(_empty_db(tmp), **entry)
        self.assertEqual(OK, check.status)
        self.assertEqual("not configured (optional integration)", check.detail)

    def test_configured_empty_source_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry = _freshness_entry("github data")
            entry["configured"] = lambda: True
            check = _check_collector_freshness(_empty_db(tmp), **entry)
        self.assertEqual(WARN, check.status)
        self.assertEqual(ERROR, check.severity)
        self.assertIn("no github data ingested", check.detail)

    def test_broken_configured_probe_fails_toward_surfacing(self) -> None:
        """A probe exception must never silently downgrade a real empty-source
        error into a skip."""

        def boom() -> bool:
            raise RuntimeError("keyring unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            entry = _freshness_entry("sleuth data")
            entry["configured"] = boom
            check = _check_collector_freshness(_empty_db(tmp), **entry)
        self.assertEqual(WARN, check.status)
        self.assertEqual(ERROR, check.severity)

    def test_missing_table_on_unconfigured_source_is_also_a_skip(self) -> None:
        """Some collector tables (sleuth_reminders) are created by the first
        sync, not by migrations — writing this suite surfaced that a genuine
        fresh install hits the table-not-present branch, not the empty branch.
        Both must be gated or fresh installs still exit 1 through sleuth."""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "rebalance.db"
            with db_connection(db, ensure_baseline_schema):
                pass  # baseline only — no collector tables at all
            entry = _freshness_entry("sleuth data")
            entry["configured"] = lambda: False
            check = _check_collector_freshness(db, **entry)
        self.assertEqual(OK, check.status)

    def test_missing_table_on_configured_source_stays_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "rebalance.db"
            with db_connection(db, ensure_baseline_schema):
                pass
            entry = _freshness_entry("sleuth data")
            entry["configured"] = lambda: True
            check = _check_collector_freshness(db, **entry)
        self.assertEqual(WARN, check.status)
        self.assertEqual(ERROR, check.severity)

    def test_fresh_install_black_box_exits_zero(self) -> None:
        """The decided top-line behaviour: nothing configured, empty DB →
        every freshness check skips → reconciled verdict ok → exit 0. This is
        the exact code path 4.3 will wire the exit to, asserted through the
        real registry with all four probes forced unconfigured at the
        config-resolver level (not by stubbing the probes themselves)."""
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch("rebalance.ingest.config.get_github_token", return_value=None),
            patch(
                "rebalance.ingest.config.get_sleuth_credentials",
                side_effect=FileNotFoundError,
            ),
            patch(
                "rebalance.ingest.config.get_calendar_oauth_token_json",
                return_value=None,
            ),
            patch(
                "rebalance.ingest.config.get_gmail_ingest_method",
                return_value="oauth",
            ),
            patch(
                "rebalance.ingest.config.get_gmail_oauth_token_json",
                return_value=None,
            ),
            patch.object(doctor_mod, "_google_oauth_source", return_value=None),
        ):
            db = _empty_db(tmp)
            checks = [_check_collector_freshness(db, **entry) for entry in _COLLECTOR_FRESHNESS]
            health = compute_health_status(checks, {}, NOW, notice_patterns=[])
        self.assertEqual([OK] * len(_COLLECTOR_FRESHNESS), [c.status for c in checks])
        self.assertEqual(OK, health.verdict)
        # 4.3 derives the exit from the verdict: ok → 0. Pinned here so the
        # reroute cannot regress onboarding.
        self.assertEqual([], health.problems)

    def test_gmail_mcp_mode_selected_but_empty_is_an_error(self) -> None:
        """The pinned mcp-mode reading: selecting mcp is an explicit opt-in
        (the config default is oauth), so mcp-selected + zero rows reads as
        configured-and-empty → ERROR. NOT a skip."""
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(
                "rebalance.ingest.config.get_gmail_ingest_method",
                return_value="mcp",
            ),
        ):
            entry = _freshness_entry("email data")
            check = _check_collector_freshness(_empty_db(tmp), **entry)
        self.assertEqual(WARN, check.status)
        self.assertEqual(ERROR, check.severity)

    def test_gmail_oauth_default_unconnected_is_a_skip(self) -> None:
        """The other half of the wrinkle: the oauth default with no token ever
        connected is NOT an opt-in — permanently exit 0, per the decision."""
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(
                "rebalance.ingest.config.get_gmail_ingest_method",
                return_value="oauth",
            ),
            patch(
                "rebalance.ingest.config.get_gmail_oauth_token_json",
                return_value=None,
            ),
            patch.object(doctor_mod, "_google_oauth_source", return_value=None),
        ):
            entry = _freshness_entry("email data")
            check = _check_collector_freshness(_empty_db(tmp), **entry)
        self.assertEqual(OK, check.status)


class FleetDemotionTests(unittest.TestCase):
    """GH-5 Phase F: the sleuth publisher-staleness finding is fleet state (the
    publisher is a timer on another machine) — WARNING, never ERROR. The
    per-device collector cap is pinned in test_doctor_pulse_severity.py."""

    def test_stale_publisher_export_is_a_warning_not_an_error(self) -> None:
        from datetime import timedelta

        from rebalance.doctor import WARNING, _check_sleuth
        from rebalance.ingest import config as config_mod

        stale_beat = datetime.now(timezone.utc) - timedelta(hours=30)
        with (
            patch.object(config_mod, "get_sleuth_credentials", return_value=None),
            patch.object(config_mod, "_keyring_get", return_value=None),
            patch(
                "rebalance.ingest.sleuth_reminders.get_export_generated_at",
                return_value=stale_beat,
            ),
        ):
            check = _check_sleuth(Path("/nonexistent-for-this-test.db"))
        self.assertEqual(WARN, check.status)
        self.assertEqual(WARNING, check.severity)
        self.assertIn("another machine", check.detail)
        # Distinct name: "sleuth" WARNs are suppressed by a recent local sync
        # timestamp — which bumps even while rereading a DEAD export. Under the
        # shared name this warning vanished on that false evidence.
        self.assertEqual("sleuth export", check.name)

    def test_sleuth_export_staleness_is_not_suppressible_by_local_reread(self) -> None:
        """The reconciler must not hide publisher staleness just because the
        local sync loop recently re-read the stale file."""
        from datetime import timedelta

        from rebalance.doctor import WARNING
        from rebalance.health import compute_health_status

        recent = (NOW - timedelta(hours=1)).isoformat()
        status = {"sources": {"sleuth": {"last_synced_at": recent}}}
        checks = [Check("sleuth export", WARN, "publisher export is stale", severity=WARNING)]
        health = compute_health_status(checks, status, NOW, notice_patterns=[])
        self.assertEqual(["sleuth export"], [c.name for c in health.problems])


# ---------------------------------------------------------------------------
# (c) Status-unavailable path
# ---------------------------------------------------------------------------


class StatusUnavailableTests(unittest.TestCase):
    def test_empty_status_disables_suppression_without_hiding(self) -> None:
        """No snapshot → no recovery evidence → a WARN stays a problem. The
        degraded direction must be toward visibility, never toward ok."""
        checks = [Check("sleuth", WARN, "credential warning")]
        health = compute_health_status(checks, {}, NOW, notice_patterns=[])
        self.assertEqual(WARN, health.verdict)
        self.assertEqual(["sleuth"], [c.name for c in health.problems])

    def test_malformed_status_never_crashes_the_verdict(self) -> None:
        malformed: dict = {"sources": {"sleuth": {"last_synced_at": "not-a-date"}}}
        checks = [Check("sleuth", WARN, "credential warning")]
        health = compute_health_status(checks, malformed, NOW, notice_patterns=[])
        self.assertEqual(WARN, health.verdict)

    def test_fail_check_still_fails_without_status(self) -> None:
        report = DoctorReport(checks=[Check("db", FAIL, "gone", severity=ERROR)])
        health = compute_health_status(report.checks, {}, NOW, notice_patterns=[])
        self.assertEqual(FAIL, health.verdict)


if __name__ == "__main__":
    unittest.main()

"""GH-5 Phase 4.1 — `rebalance doctor --json` emits the reconciled verdict.

The requirement (Codex Q4, pinned in the plan): raw checks cannot explain *why*
something was suppressed or demoted — that decision lives in the reconciler
(`health.compute_health_status`). So the JSON must carry each check's
*disposition* (problem / notice / suppressed / ok), not merely the raw list;
otherwise a binary exit code stays undiagnosable in exactly the cases the
reconciler acts on. This is the prerequisite for the 4.3 collapse, not a
follow-up.
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from typer.testing import CliRunner

from rebalance.cli import app
from rebalance.doctor import ERROR, FAIL, NOTICE, OK, WARN, WARNING, Check, DoctorReport
from rebalance.paths import DatabaseNotFoundError
from rebalance.health import check_dispositions, compute_health_status

runner = CliRunner()

NOW = datetime(2026, 8, 16, 12, 0, 0, tzinfo=timezone.utc)


def _recent_sleuth_status() -> dict:
    """Index-status snapshot showing sleuth synced an hour ago — inside its
    48h suppression window, so a sleuth WARN must reconcile away."""
    return {"sources": {"sleuth": {"last_synced_at": (NOW - timedelta(hours=1)).isoformat()}}}


class CheckDispositionTests(unittest.TestCase):
    def _dispositions(self, checks, status=None, now=NOW):
        health = compute_health_status(checks, status or {}, now, notice_patterns=[])
        return {c.name: d for c, d in check_dispositions(checks, health)}

    def test_every_check_gets_exactly_one_disposition_in_input_order(self) -> None:
        checks = [Check("a", OK, ""), Check("b", WARN, ""), Check("c", FAIL, "")]
        health = compute_health_status(checks, {}, NOW, notice_patterns=[])
        result = check_dispositions(checks, health)
        self.assertEqual([c.name for c, _ in result], ["a", "b", "c"])

    def test_ok_problem_and_notice(self) -> None:
        checks = [
            Check("clean", OK, ""),
            Check("broken", FAIL, "", severity=ERROR),
            Check("fyi", OK, "", severity=NOTICE),
        ]
        d = self._dispositions(checks)
        self.assertEqual("ok", d["clean"])
        self.assertEqual("problem", d["broken"])
        self.assertEqual("notice", d["fyi"])

    def test_recovered_warn_is_suppressed_not_silently_ok(self) -> None:
        """The disposition the whole flag exists for: the reconciler hid a WARN
        because the source synced recently — the JSON must say so."""
        checks = [Check("sleuth", WARN, "credential warning", severity=WARNING)]
        d = self._dispositions(checks, status=_recent_sleuth_status())
        self.assertEqual("suppressed", d["sleuth"])

    def test_unsuppressed_warn_is_a_problem(self) -> None:
        checks = [Check("sleuth", WARN, "credential warning", severity=WARNING)]
        self.assertEqual("problem", self._dispositions(checks, status={})["sleuth"])

    def test_configured_notice_pattern_demotes_to_notice(self) -> None:
        checks = [Check("launchd: com.x.optional", WARN, "", severity=WARNING)]
        health = compute_health_status(checks, {}, NOW, notice_patterns=["com.x.optional"])
        d = {c.name: disp for c, disp in check_dispositions(checks, health)}
        self.assertEqual("notice", d["launchd: com.x.optional"])

    def test_equal_but_distinct_checks_classify_independently(self) -> None:
        """Membership is by object identity — two value-equal checks must both
        appear, once each, with the right disposition."""
        checks = [Check("dup", WARN, "same"), Check("dup", WARN, "same")]
        health = compute_health_status(checks, {}, NOW, notice_patterns=[])
        result = check_dispositions(checks, health)
        self.assertEqual(2, len(result))
        self.assertEqual({"problem"}, {d for _, d in result})


class DoctorJsonCliTests(unittest.TestCase):
    def _invoke(self, report: DoctorReport, status: dict | None = None):
        # The clock has to be pinned, not just the fixture timestamps. `NOW` is a fixed date and
        # the suppression window is 48h wide, so with the CLI reading the real clock these tests
        # passed for exactly two days after `NOW` was written and then failed permanently — which
        # is what happened on 2026-08-18, when "synced an hour ago" quietly became 52 hours ago.
        with (
            patch("rebalance.cli.now_utc", return_value=NOW),
            patch("rebalance.doctor.run_doctor", return_value=report),
            patch(
                "rebalance.ingest.index_ops.get_index_status",
                return_value=status or {},
            ),
            patch("rebalance.cli.resolve_database_path", return_value="/dev/null"),
        ):
            return runner.invoke(app, ["doctor", "--json"])

    def test_stdout_is_valid_json_with_verdict_and_dispositions(self) -> None:
        report = DoctorReport(checks=[Check("db", OK, "fine"), Check("token", WARN, "stale")])
        result = self._invoke(report)
        payload = json.loads(result.stdout)
        self.assertEqual(WARN, payload["verdict"])
        self.assertEqual(
            {"db": "ok", "token": "problem"},
            {c["name"]: c["disposition"] for c in payload["checks"]},
        )
        for c in payload["checks"]:
            self.assertEqual(
                {"name", "status", "severity", "disposition", "detail", "hint"},
                set(c),
            )
        self.assertEqual(0, payload["exit_code"])

    def test_suppressed_warn_yields_ok_verdict_but_stays_diagnosable(self) -> None:
        """A binary OK with a hidden WARN is exactly the case that must not be
        opaque: verdict ok — and since 4.3 exit 0 derives from it — but the
        check is present, labelled suppressed."""
        report = DoctorReport(checks=[Check("sleuth", WARN, "credential warning")])
        result = self._invoke(report, status=_recent_sleuth_status())
        payload = json.loads(result.stdout)
        self.assertEqual(OK, payload["verdict"])
        self.assertEqual("suppressed", payload["checks"][0]["disposition"])
        self.assertEqual(0, payload["exit_code"])
        self.assertEqual(0, result.exit_code)

    def test_exit_code_derives_from_the_reconciled_verdict(self) -> None:
        """GH-5 Phase 4.3: one verdict path. FAIL verdict → exit 1; WARN → 0."""
        failed = DoctorReport(checks=[Check("db", FAIL, "gone", severity=ERROR)])
        result = self._invoke(failed)
        self.assertEqual(1, result.exit_code)
        payload = json.loads(result.stdout)
        self.assertEqual(FAIL, payload["verdict"])
        self.assertEqual(1, payload["exit_code"])

        warned = DoctorReport(checks=[Check("token", WARN, "stale")])
        self.assertEqual(0, self._invoke(warned).exit_code)

    def test_warn_status_error_severity_now_fails_the_exit(self) -> None:
        """The 4.2-pinned blast radius, activated: a WARN-status ERROR-severity
        check (dashboard shows an error, old CLI exited 0) now exits 1 —
        the CLI/dashboard disagreement this phase exists to close."""
        report = DoctorReport(checks=[Check("github data", WARN, "no github data ingested", severity=ERROR)])
        result = self._invoke(report)
        self.assertEqual(1, result.exit_code)
        self.assertEqual(FAIL, json.loads(result.stdout)["verdict"])

    def test_missing_database_still_emits_json(self) -> None:
        report = DoctorReport(checks=[Check("db", OK, "fine")])
        with (
            patch("rebalance.doctor.run_doctor", return_value=report),
            patch(
                "rebalance.cli.resolve_database_path",
                side_effect=DatabaseNotFoundError([]),
            ),
        ):
            result = runner.invoke(app, ["doctor", "--json"])
        payload = json.loads(result.stdout)
        self.assertEqual(OK, payload["verdict"])
        self.assertEqual(0, result.exit_code)


if __name__ == "__main__":
    unittest.main()

"""GH-59 Phase 2 — a scheduled job that failed must grade FAIL, not WARN.

The outage this pins: `github-sync` and `pulse-sync` both sat at launchctl exit
1 for a full day and nothing reported it. Every mechanism downstream was already
correct and already wired up —

  * `_check_launchd` DID detect both (`doctor.py`, "WARN only on a positive
    non-zero exit with no PID");
  * `cli/__init__.py` DOES `raise typer.Exit(1)` when the verdict is FAIL;
  * `health_issue_reporter.py` DOES file GitHub issues, for `error` by default.

— and none of them fired, because the grade was WARN. WARN does not move the
verdict, a verdict that is not FAIL does not exit non-zero, and a check that is
not `error` is not filed. One wrong constant made three working mechanisms
silent, so these tests pin the constant rather than the plumbing.

The companion invariant is that a FAIL is never suppressed by a recent
successful sync. That is already true — `visible_problem_checks` gates
suppression on `status == WARN` — but it was inherited rather than decided, and
an hourly job that crashes after a recent success is exactly the case where
losing it would recreate this outage somewhere new.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from rebalance.doctor import (
    ERROR,
    FAIL,
    NOTICE,
    OK,
    WARN,
    Check,
    _check_launchd,
    _check_pulse,
    _check_scheduler_liveness,
)
from rebalance.health import compute_health_status, visible_problem_checks

NOW = datetime(2026, 8, 17, 21, 0, tzinfo=timezone.utc)
POLICY = "| Job (label suffix) |\n|---|---|\n| `github-sync` |\n| `health-check` |\n"


class LaunchdGradingTests(unittest.TestCase):
    def test_the_exact_observed_outage_now_fails(self):
        """`-\t1\tcom.rebalance-os.github-sync` — the literal launchctl row."""
        checks = _check_launchd(
            "-\t1\tcom.rebalance-os.github-sync\n-\t1\tcom.rebalance-os.pulse-sync\n",
            log_dir=Path("/nonexistent"),
            now=NOW,
        )
        self.assertEqual(len(checks), 2)
        for check in checks:
            self.assertEqual(check.status, FAIL, check.name)
            self.assertEqual(check.severity, ERROR, check.name)

    def test_healthy_jobs_are_untouched(self):
        """The promotion must not turn idle or running jobs into failures."""
        checks = _check_launchd(
            "-\t0\tcom.rebalance-os.vault-sync\n"
            "4242\t0\tcom.rebalance-os.pulse-server\n"
            "-\t-15\tcom.rebalance-os.pulse-web-sync\n",
            log_dir=Path("/nonexistent"),
            now=NOW,
        )
        self.assertEqual([c.status for c in checks], [OK, OK, OK])
        self.assertTrue(all(c.severity == NOTICE for c in checks))


class SchedulerLivenessTests(unittest.TestCase):
    """Absent from launchd is two different situations (GH-59).

    The signal separating them is the plist file itself — written by
    rb_install_launchd_job, removed by `stack.sh purge` — which doctor already
    treats as the device-local install record in _check_scheduled_stack_checkout
    (GH-36). No new state was introduced for this.
    """

    def setUp(self):
        self._tmp = __import__("tempfile").TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.policy = self.root / "SCHEDULER.md"
        self.policy.write_text(POLICY, encoding="utf-8")
        self.agents = self.root / "LaunchAgents"
        self.agents.mkdir()
        self.addCleanup(self._tmp.cleanup)

    def _checks(self, launchctl_output: str):
        return _check_scheduler_liveness(
            policy_path=self.policy,
            launchctl_output=launchctl_output,
            agents_dir=self.agents,
        )

    def test_installed_but_unloaded_is_a_failure(self):
        """The health-check case: its plist was on disk and it was never loaded,
        so the hourly job that would have reported everything else was itself
        among the things nothing was watching."""
        (self.agents / "com.rebalance-os.health-check.plist").write_text("x", encoding="utf-8")
        checks = self._checks("-\t0\tcom.rebalance-os.github-sync\n")

        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].name, "scheduler:health-check")
        self.assertEqual(checks[0].status, FAIL)
        self.assertEqual(checks[0].severity, ERROR)
        self.assertIn("NOT loaded", checks[0].detail)

    def test_never_installed_stays_a_muted_notice(self):
        """A fresh clone has run no installers, and most machines deliberately
        run only part of the fleet. Hard-failing that would make `doctor` exit 1
        on a correct checkout."""
        checks = self._checks("-\t0\tcom.rebalance-os.github-sync\n")

        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].name, "scheduler:health-check")
        self.assertEqual(checks[0].status, WARN)
        self.assertEqual(checks[0].severity, NOTICE)
        self.assertIn("install it with", checks[0].hint)

    def test_loaded_jobs_produce_no_check_either_way(self):
        (self.agents / "com.rebalance-os.health-check.plist").write_text("x", encoding="utf-8")
        checks = self._checks(
            "-\t0\tcom.rebalance-os.github-sync\n-\t0\tcom.rebalance-os.health-check\n"
        )
        self.assertEqual(checks, [])

    def test_purging_a_plist_downgrades_the_failure(self):
        """Rollback semantics come free: removing the plist is `stack.sh purge`,
        and the check returns to a muted notice rather than staying FAIL."""
        plist = self.agents / "com.rebalance-os.health-check.plist"
        plist.write_text("x", encoding="utf-8")
        self.assertEqual(self._checks("")[1].status, FAIL)

        plist.unlink()
        after = [c for c in self._checks("") if c.name == "scheduler:health-check"]
        self.assertEqual(after[0].status, WARN)
        self.assertEqual(after[0].severity, NOTICE)


class PulseConfigGradingTests(unittest.TestCase):
    def _pulse(self, cfg):
        with patch("rebalance.ingest.config.get_pulse_config", return_value=cfg):
            return _check_pulse()

    def test_configured_but_missing_target_fails(self):
        """The literal pulse-sync outage: pulse_target_path named a directory
        that had been archived away."""
        check = self._pulse(
            {"github_login": "noelsaw1", "pulse_target_path": "/nonexistent/git-pulse-sync"}
        )
        self.assertEqual(check.status, FAIL)
        self.assertEqual(check.severity, ERROR)

    def test_configured_but_not_a_git_repo_fails(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            check = self._pulse({"github_login": "x", "pulse_target_path": tmp})
        self.assertEqual(check.status, FAIL)

    def test_unconfigured_stays_a_warning(self):
        """A fresh clone has never set these keys. Same line the collector
        freshness registry draws with its `configured=` probes: not configured
        is not broken."""
        check = self._pulse({})
        self.assertEqual(check.status, WARN)
        self.assertIn("missing keys", check.detail)

    def test_healthy_config_is_ok(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".git").mkdir()
            check = self._pulse({"github_login": "x", "pulse_target_path": tmp})
        self.assertEqual(check.status, OK)


class SuppressionInvariantTests(unittest.TestCase):
    """A recent successful sync may hide a WARN. It must never hide a FAIL."""

    def _status(self, ago: timedelta):
        stamp = (NOW - ago).isoformat()
        return {"sources": {"sleuth": {"last_synced_at": stamp}}}

    def test_a_recent_success_suppresses_a_warning(self):
        """Control: without this passing, the FAIL test below proves nothing —
        it would be asserting against a suppression path that never fires."""
        warn = Check("sleuth", WARN, "stale")
        visible = visible_problem_checks([warn], self._status(timedelta(minutes=5)), NOW)
        self.assertEqual(visible, [])

    def test_a_recent_success_never_suppresses_a_failure(self):
        """An hourly job that succeeded at :00 and crashed at :45 is exactly the
        case that would otherwise recreate the GH-59 outage in a new place."""
        fail = Check("sleuth", FAIL, "collector crashed")
        visible = visible_problem_checks([fail], self._status(timedelta(minutes=5)), NOW)
        self.assertEqual([c.status for c in visible], [FAIL])

    def test_a_real_failing_job_reaches_a_FAIL_verdict(self):
        """End to end, from the launchctl row to the verdict `doctor` exits on.

        The tests above use synthetic Checks to isolate the reconciler. That is
        the right unit boundary, but it cannot catch a regression that stops
        `_check_launchd` producing FAIL in the first place — the two halves
        would each pass while the machine went quiet again. This asserts the
        whole path on the literal row the outage produced.
        """
        checks = _check_launchd(
            "-\t1\tcom.rebalance-os.github-sync\n",
            log_dir=Path("/nonexistent"),
            now=NOW,
        )
        health = compute_health_status(checks, {}, NOW, notice_patterns=[])

        self.assertEqual(health.verdict, FAIL)
        self.assertIn(
            "launchd:github-sync",
            [c.name for c in health.problems],
            "a failing job must be a problem, not a demoted notice",
        )


if __name__ == "__main__":
    unittest.main()

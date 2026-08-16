"""GH-5 Phase 6 — doctor consumes 3-Eyes' supervision verdict (#4).

#4's root cause was not a code defect: `collect.sh` already has `set -euo
pipefail` and a `self_heal_sync_repo()` recovery path. The collector went dead
for days because `com.user.git-pulse`'s launchd job stopped being *loaded* and
nothing watched for that. 3-Eyes already tracks loaded-state; doctor was never
told. This is that wiring, plus the failure contract it needs to be trustworthy.

The contract matters more than the happy path. `three_eyes.health.scan()` does
NOT raise when it cannot read launchd — it returns a structured report with
`launchctl_available: False` and every row "unknown". A check that only guards
against exceptions reads `failing == 0` off that and reports the fleet healthy
when nothing was observed at all.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from rebalance import three_eyes_bridge
from rebalance.doctor import (
    ERROR,
    NOTICE,
    OK,
    WARN,
    WARNING,
    _check_three_eyes_supervision,
)


def _report(**overrides) -> dict:
    base = {
        "ok": 3,
        "failing": 0,
        "not_loaded": 0,
        "unknown": 0,
        "launchctl_available": True,
        "probe_error": "",
        "rows": [
            {"label": "com.rebalance-os.a", "health": "ok"},
            {"label": "com.rebalance-os.b", "health": "ok"},
            {"label": "com.user.git-pulse", "health": "ok"},
        ],
    }
    base.update(overrides)
    return base


def _checks(scan_result=None, scan_exc=None):
    target = "rebalance.three_eyes_bridge.health_scan"
    if scan_exc is not None:
        with patch(target, side_effect=scan_exc):
            return _check_three_eyes_supervision()
    with patch(target, return_value=scan_result):
        return _check_three_eyes_supervision()


class InactiveSentinelTests(unittest.TestCase):
    """Case 1 of the contract: 3-Eyes not active here -> emit nothing."""

    def test_inactive_emits_no_check_at_all(self) -> None:
        self.assertEqual([], _checks(scan_result=None))


class UnavailableTests(unittest.TestCase):
    """Case 2: the import or the scan raised. Must warn — never silently ok."""

    def test_import_or_scan_failure_emits_a_warning(self) -> None:
        checks = _checks(scan_exc=three_eyes_bridge.ThreeEyesUnavailable("boom"))
        self.assertEqual(1, len(checks))
        self.assertEqual(WARN, checks[0].status)
        self.assertEqual(WARNING, checks[0].severity)

    def test_failure_reason_is_surfaced_not_swallowed(self) -> None:
        checks = _checks(scan_exc=three_eyes_bridge.ThreeEyesUnavailable("no module three_eyes"))
        self.assertIn("no module three_eyes", checks[0].detail)

    def test_failure_never_reports_ok(self) -> None:
        checks = _checks(scan_exc=three_eyes_bridge.ThreeEyesUnavailable("boom"))
        self.assertNotEqual(OK, checks[0].status)
        self.assertNotEqual(NOTICE, checks[0].severity)


class ProbeUnavailableTests(unittest.TestCase):
    """Case 3 — the subtle one. scan() succeeded but could not read launchd, so
    every row is "unknown" and the counters are all zero. `failing == 0` here
    means "nothing was observed", not "nothing is wrong"."""

    def _unreadable(self) -> dict:
        return _report(
            ok=0,
            failing=0,
            not_loaded=0,
            unknown=3,
            launchctl_available=False,
            probe_error="launchctl: Operation not permitted",
            rows=[{"label": "com.user.git-pulse", "health": "unknown"}],
        )

    def test_unreadable_launchctl_warns_rather_than_reporting_healthy(self) -> None:
        checks = _checks(scan_result=self._unreadable())
        self.assertEqual(1, len(checks))
        self.assertEqual(WARN, checks[0].status)
        self.assertEqual(WARNING, checks[0].severity)

    def test_probe_error_is_surfaced_to_the_operator(self) -> None:
        checks = _checks(scan_result=self._unreadable())
        self.assertIn("Operation not permitted", checks[0].detail)

    def test_zero_failing_is_not_mistaken_for_a_clean_fleet(self) -> None:
        detail = _checks(scan_result=self._unreadable())[0].detail.lower()
        self.assertIn("unknown", detail)
        self.assertNotIn("healthy", detail)

    def test_bridge_helper_reports_the_reason(self) -> None:
        self.assertEqual(
            "launchctl: Operation not permitted",
            three_eyes_bridge.probe_unavailable_reason(self._unreadable()),
        )
        self.assertEqual("", three_eyes_bridge.probe_unavailable_reason(_report()))


class FleetStateTests(unittest.TestCase):
    def test_clean_fleet_reports_ok_at_notice_severity(self) -> None:
        checks = _checks(scan_result=_report())
        self.assertEqual(1, len(checks))
        self.assertEqual(OK, checks[0].status)
        self.assertEqual(NOTICE, checks[0].severity)

    def test_unloaded_job_is_an_error(self) -> None:
        """This is #4's actual incident shape: the job simply stopped being loaded."""
        report = _report(
            ok=2,
            not_loaded=1,
            rows=[
                {"label": "com.rebalance-os.a", "health": "ok"},
                {"label": "com.rebalance-os.b", "health": "ok"},
                {"label": "com.user.git-pulse", "health": "not-loaded"},
            ],
        )
        checks = _checks(scan_result=report)
        self.assertEqual(WARN, checks[0].status)
        self.assertEqual(ERROR, checks[0].severity)
        self.assertIn("com.user.git-pulse", checks[0].detail)
        self.assertIn("not loaded", checks[0].detail)

    def test_failing_job_is_an_error(self) -> None:
        report = _report(
            ok=2,
            failing=1,
            rows=[
                {"label": "com.rebalance-os.a", "health": "ok"},
                {"label": "com.rebalance-os.b", "health": "ok"},
                {"label": "com.rebalance-os.c", "health": "FAIL(exit 1)"},
            ],
        )
        checks = _checks(scan_result=report)
        self.assertEqual(ERROR, checks[0].severity)
        self.assertIn("com.rebalance-os.c", checks[0].detail)

    def test_unknown_rows_never_read_as_a_clean_fleet(self) -> None:
        """Forward-compatibility, not a live bug.

        Today `unknown > 0` only occurs when launchctl_available is False, which
        the probe_error branch catches first — so this fall-through is
        unreachable through the real scan(). Codex confirmed agy's Blocker was
        overstated on exactly that ground. But the code read `unknown` only to
        build `total` and would then report OK, contradicting _map_pulse_state's
        own refusal to treat an unrecognised state as healthy. A synthetic or
        future report must not read as clean.
        """
        report = _report(
            ok=2,
            unknown=1,
            launchctl_available=True,  # deliberately inconsistent — the synthetic case
            probe_error="",
            rows=[
                {"label": "com.rebalance-os.a", "health": "ok"},
                {"label": "com.rebalance-os.b", "health": "ok"},
                {"label": "com.user.git-pulse", "health": "unknown"},
            ],
        )
        checks = _checks(scan_result=report)
        self.assertEqual(1, len(checks))
        self.assertNotEqual(OK, checks[0].status)
        self.assertNotEqual(NOTICE, checks[0].severity)
        self.assertIn("unknown", checks[0].detail)
        self.assertIn("com.user.git-pulse", checks[0].detail)

    def test_long_problem_lists_are_truncated_with_a_count(self) -> None:
        rows = [{"label": f"com.x.{i}", "health": "not-loaded"} for i in range(9)]
        checks = _checks(scan_result=_report(ok=0, not_loaded=9, rows=rows))
        self.assertIn("+5 more", checks[0].detail)


class CrashLoopDetectionRetainedTests(unittest.TestCase):
    """Codex's round-2 finding, pinned: 3-Eyes' scan() is a single snapshot with
    no persisted history, so it CANNOT distinguish a one-off crash from a
    KeepAlive job launchd is respawning in a loop. Doctor's own
    launchd_crash_state.json must survive this phase, not be deprecated by it."""

    def test_doctor_still_persists_launchd_crash_state(self) -> None:
        from pathlib import Path

        import rebalance.doctor as doctor_mod

        source = Path(doctor_mod.__file__).read_text(encoding="utf-8")
        self.assertIn("launchd_crash_state.json", source)
        self.assertIn("_save_launchd_crash_state", source)
        self.assertTrue(hasattr(doctor_mod, "_load_launchd_crash_state"))

    def test_three_eyes_scan_has_no_persisted_history_to_replace_it(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        source = (root / "utils" / "3-eyes" / "three_eyes" / "health.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("crash_state", source)


class DependencyDirectionTests(unittest.TestCase):
    """3-Eyes must stay standalone: rebalance reaches in, 3-Eyes never reaches out.
    In particular it keeps its own package-relative root resolver rather than
    adopting rebalance.paths — the coupling Codex's round-1 finding rejected."""

    def test_three_eyes_does_not_import_rebalance_anywhere(self) -> None:
        """Asserts on *imports*, not on the string "rebalance" — 3-Eyes mentions
        the repo by name in paths and prose (`REPO_ROOT`, its state dir) and
        always has. What must never appear is a runtime dependency."""
        import ast
        from pathlib import Path

        pkg = Path(__file__).resolve().parents[1] / "utils" / "3-eyes" / "three_eyes"
        offenders: list[str] = []
        for path in sorted(pkg.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                if any(n == "rebalance" or n.startswith("rebalance.") for n in names):
                    offenders.append(f"{path.name}:{node.lineno}")
        self.assertEqual([], offenders, "3-Eyes gained a runtime dependency on rebalance")

    def test_three_eyes_keeps_its_own_root_resolver(self) -> None:
        """Codex round-1 finding: replacing this with `rebalance.paths` would break
        3-Eyes exactly in the degraded conditions it is designed to survive."""
        from pathlib import Path

        source = (
            Path(__file__).resolve().parents[1]
            / "utils" / "3-eyes" / "three_eyes" / "config.py"
        ).read_text(encoding="utf-8")
        self.assertIn("ROOT.parent.parent", source)

    def test_bridge_is_importable_without_fastapi_web_module(self) -> None:
        """doctor.py must not have to import web.py (and FastAPI) to reach 3-Eyes."""
        from pathlib import Path

        import rebalance.doctor as doctor_mod

        source = Path(doctor_mod.__file__).read_text(encoding="utf-8")
        self.assertIn("three_eyes_bridge", source)
        self.assertNotIn("from rebalance.web import", source)


if __name__ == "__main__":
    unittest.main()

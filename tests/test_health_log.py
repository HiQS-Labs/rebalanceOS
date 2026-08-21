"""Health-check transitions reaching the unified system log (GH-101).

The durability constraint is the interesting part. ``auth_log`` is append-only
with no rotation, and every read parses the whole file before slicing off the
last N rows — so cost grows with total history, not with what is displayed.
Writing every check on every hourly run (~20 checks) would add ~175k lines a year
and make each dashboard load parse all of them.

Writing only transitions keeps volume proportional to how often things actually
break. ``test_a_steady_state_writes_nothing_at_all`` is the test that holds that
line: if it ever goes green-by-accident, the file starts growing with time rather
than with change, and the format stops being viable.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from rebalance.doctor import Check, FAIL, OK, WARN
from rebalance.ingest import auth_log, health_log


def _check(name: str, status: str, detail: str = "d", hint: str = "") -> dict:
    return {"name": name, "status": status, "detail": detail, "hint": hint}


class HealthTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        patcher = mock.patch.object(auth_log, "_log_dir", return_value=self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _events(self) -> list[dict]:
        path = self.dir / "auth_activity.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_a_first_failure_is_logged(self) -> None:
        health_log.log_health_transitions([_check("vault", FAIL, "no vault path", hint="set vault_path")])
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["source"], "health")
        self.assertEqual(events[0]["event"], "check_failed")
        self.assertEqual(events[0]["detail"]["check"], "vault")
        self.assertEqual(events[0]["detail"]["from"], "unseen")
        self.assertEqual(events[0]["detail"]["hint"], "set vault_path")

    def test_a_steady_state_writes_nothing_at_all(self) -> None:
        """THE PIN — the whole durability argument rests on this.

        Three identical runs must leave exactly one event. If a repeat ever
        writes, the log grows with elapsed time instead of with change, and the
        no-rotation, parse-the-whole-file format stops being viable.
        """
        checks = [_check("vault", FAIL)]
        for _ in range(3):
            health_log.log_health_transitions(checks)
        self.assertEqual(len(self._events()), 1)

    def test_a_first_sighting_that_is_healthy_is_not_news(self) -> None:
        """Baseline, not an event. Otherwise the first run writes ~20 rows saying
        nothing happened, and the log opens with noise."""
        health_log.log_health_transitions([_check("vault", OK)])
        self.assertEqual(self._events(), [])

    def test_recovery_is_logged(self) -> None:
        health_log.log_health_transitions([_check("vault", FAIL)])
        health_log.log_health_transitions([_check("vault", OK)])
        events = self._events()
        self.assertEqual([e["event"] for e in events], ["check_failed", "check_recovered"])
        self.assertEqual(events[1]["detail"]["from"], FAIL)

    def test_escalation_and_de_escalation_are_both_transitions(self) -> None:
        for status in (WARN, FAIL, WARN):
            health_log.log_health_transitions([_check("gmail", status)])
        self.assertEqual(
            [e["event"] for e in self._events()],
            ["check_degraded", "check_failed", "check_degraded"],
        )

    def test_a_failing_check_that_stops_being_reported_is_not_silence(self) -> None:
        """Losing sight of a broken thing is not the same as it being fixed.

        Dropping it from state quietly would let a failing check disappear with
        no record — the silent-success shape this project keeps hitting. It takes
        TWO absences, because one is not proof (see the flapping tests below).
        """
        health_log.log_health_transitions([_check("gmail", FAIL), _check("vault", OK)])
        health_log.log_health_transitions([_check("vault", OK)])
        health_log.log_health_transitions([_check("vault", OK)])
        events = self._events()
        self.assertEqual([e["event"] for e in events], ["check_failed", "check_vanished"])
        self.assertEqual(events[1]["detail"]["to"], "unseen")
        self.assertEqual(events[1]["detail"]["absent_runs"], 2)

    def test_a_healthy_check_that_stops_being_reported_is_silence(self) -> None:
        """The mirror case: nothing was wrong, so nothing is lost."""
        health_log.log_health_transitions([_check("gmail", FAIL)])
        health_log.log_health_transitions([_check("gmail", OK)])
        before = len(self._events())
        health_log.log_health_transitions([_check("vault", OK)])
        health_log.log_health_transitions([_check("vault", OK)])
        self.assertEqual(len(self._events()), before)


class SubsetAndFlapTests(unittest.TestCase):
    """`run_doctor` returns a SUBSET in normal operation.

    Its schema and project checks are gated on the database existing
    (``doctor.py``, ``if db_path:``), so losing the database drops several checks
    at once. A one-absence vanish rule would log each as vanished and then, on
    the next healthy run, log each again as a fresh failure — flapping instead of
    reporting.
    """

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        patcher = mock.patch.object(auth_log, "_log_dir", return_value=self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _events(self) -> list[dict]:
        path = self.dir / "auth_activity.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_a_check_missing_for_one_run_then_back_produces_no_events(self) -> None:
        """THE PIN for flapping. A blip must cost nothing."""
        health_log.log_health_transitions([_check("schema", FAIL), _check("vault", OK)])
        before = len(self._events())
        health_log.log_health_transitions([_check("vault", OK)])  # database gone
        health_log.log_health_transitions([_check("schema", FAIL), _check("vault", OK)])  # back
        self.assertEqual(len(self._events()), before, "a one-run blip must not log anything")

    def test_an_empty_run_is_a_failed_run_not_a_healed_world(self) -> None:
        """Zero usable checks means doctor broke, not that everything recovered.

        Sweeping would mark every check vanished; persisting the empty result
        would erase state so the next healthy run re-reported every failure.
        """
        health_log.log_health_transitions([_check("gmail", FAIL)])
        before = len(self._events())
        health_log.log_health_transitions([])
        health_log.log_health_transitions([])
        self.assertEqual(len(self._events()), before)

        # State survived: the check coming back unchanged is still a no-op.
        health_log.log_health_transitions([_check("gmail", FAIL)])
        self.assertEqual(len(self._events()), before)


class StatePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        patcher = mock.patch.object(auth_log, "_log_dir", return_value=self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _events(self) -> list[dict]:
        path = self.dir / "auth_activity.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_a_failed_state_write_is_loud(self) -> None:
        """The flooding case: state never advances, so every run re-reports.

        It cannot be prevented without somewhere to write — but it must not be
        silent, or the log fills up with no explanation anywhere.
        """
        with mock.patch.object(health_log.Path, "write_text", side_effect=OSError("read-only")):
            with self.assertLogs("rebalance.ingest.health_log", level="WARNING") as captured:
                ok = health_log._save_state({"vault": FAIL}, {})
        self.assertFalse(ok)
        self.assertTrue(any("re-report" in line for line in captured.output))

    def test_the_state_file_is_replaced_atomically(self) -> None:
        """A half-written sidecar reads as corrupt, which sends the next run down
        the re-report-everything path. Concurrent runs must cost a duplicate
        event at worst, never a broken file."""
        health_log._save_state({"vault": FAIL}, {"gmail": 1})
        leftovers = list(self.dir.glob("health_state.json.*.tmp"))
        self.assertEqual(leftovers, [], "temp file left behind")
        data = json.loads((self.dir / "health_state.json").read_text())
        self.assertEqual(data["checks"], {"vault": FAIL})
        self.assertEqual(data["absent"], {"gmail": 1})

    def test_the_pre_absence_counter_state_format_still_loads(self) -> None:
        """Discarding it on upgrade would re-report every failing check once."""
        (self.dir / "health_state.json").write_text(json.dumps({"vault": FAIL}), encoding="utf-8")
        checks, absent = health_log._load_state()
        self.assertEqual(checks, {"vault": FAIL})
        self.assertEqual(absent, {})

        health_log.log_health_transitions([_check("vault", FAIL)])
        self.assertEqual(self._events(), [], "an unchanged check must stay silent across the format upgrade")

    def test_accepts_doctor_check_objects_as_well_as_dicts(self) -> None:
        health_log.log_health_transitions([Check("database", FAIL, "missing")])
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["detail"]["check"], "database")

    def test_a_corrupt_state_file_does_not_stop_logging(self) -> None:
        (self.dir / "health_state.json").write_text("{not json", encoding="utf-8")
        health_log.log_health_transitions([_check("vault", FAIL)])
        self.assertEqual(len(self._events()), 1)

    def test_the_state_sidecar_follows_the_log_directory_seam(self) -> None:
        """It must not be left pointing at the real log dir under test.

        `health_log` originally did `from auth_log import _log_dir`, which binds
        at import time and silently escapes the patch: events went to the temp
        dir while state went to the developer's real one, leaking between cases.
        """
        health_log.log_health_transitions([_check("vault", FAIL)])
        self.assertTrue((self.dir / "health_state.json").exists())


class StateVocabularyTests(unittest.TestCase):
    """THE PIN for a bug that shipped past its own tests.

    doctor's constants are named FAIL/WARN but their VALUES are "error" and
    "warning". Keyed on the names, `_EVENT_FOR_STATE` matched only "ok" — so the
    module logged recoveries and nothing else, and the first fixtures used the
    same wrong strings, so the tests agreed with the bug.

    Asserting against the real constants is the only version of this that can
    fail.
    """

    def test_state_vocabulary_matches_doctor(self) -> None:
        self.assertEqual(set(health_log._EVENT_FOR_STATE), {FAIL, WARN, OK})

    def test_each_doctor_status_maps_to_a_distinct_event(self) -> None:
        events = [health_log._EVENT_FOR_STATE[s] for s in (FAIL, WARN, OK)]
        self.assertEqual(len(set(events)), 3)

    def test_every_emitted_event_has_a_badge_on_the_system_log(self) -> None:
        """An event with no badge renders as a bare, unstyled string."""
        from rebalance import web

        for event in list(health_log._EVENT_FOR_STATE.values()) + [health_log._VANISHED_EVENT]:
            with self.subTest(event=event):
                self.assertIn(event, web._EVENT_BADGE)


if __name__ == "__main__":
    unittest.main()

"""GH-5 Phase 4 — severity vocabulary alignment at the pulse_health→doctor boundary.

Closes #3 (a fourth severity word leaking into user-facing text) and a second,
separately-confirmed bug found while adjudicating the fix: the severity
assignment was inverted, so a *healthy* collector was reported at WARNING.

`pulse_health.py` is deliberately NOT touched. Its 5-state model has other
consumers and its own test suite; collapsing its granularity to serve one
caller's presentation would be scope creep. The mapping lives at the
consumption boundary in `doctor.py`.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from rebalance.doctor import (
    ERROR,
    NOTICE,
    OK,
    WARN,
    WARNING,
    _check_pulse_collectors,
    _map_pulse_state,
)
from rebalance.ingest.pulse_health import CollectorHealth

RAW_STATE_WORDS = ("ALIVE", "STALE", "ALERT", "DEGRADED", "NO PUSHES")


def _health(
    name: str,
    state: str,
    *,
    age_hours: float | None = 1.0,
    failures: int = 0,
    scan_status: str = "ok",
) -> CollectorHealth:
    health = CollectorHealth(
        device_id=name,
        device_name=name,
        last_scan_utc=None,
        scan_status=scan_status,
        repo_scan_failures=failures,
    )
    health.state = state
    health.age_hours = age_hours
    return health


def _checks_for(devices: list[CollectorHealth]):
    with patch(
        "rebalance.ingest.pulse_health.read_collector_health", return_value=devices
    ):
        return {c.name: c for c in _check_pulse_collectors(current_device_id=None)}


class RawStateWordDoesNotLeakTests(unittest.TestCase):
    """#3's ready acceptance test, as posted on the issue. Confirmed red against
    the pre-change code, where detail was literally
    `'ALERT — last scan 2026-08-15 4:10 AM · 1d ago'`."""

    def test_detail_leads_with_canonical_severity_not_raw_pulse_state(self) -> None:
        devices = [
            _health("Stale", "ALERT", age_hours=30.0),
            _health("Broken", "DEGRADED", age_hours=0.3, failures=1),
        ]
        by = _checks_for(devices)
        for check_name in ("pulse collector:Stale", "pulse collector:Broken"):
            detail = by[check_name].detail
            self.assertFalse(
                detail.startswith(RAW_STATE_WORDS),
                f"{check_name} still leads with a raw pulse state: {detail!r}",
            )

    def test_no_raw_state_word_appears_anywhere_in_user_facing_text(self) -> None:
        devices = [_health(state.title(), state) for state in RAW_STATE_WORDS]
        by = _checks_for(devices)
        for check in by.values():
            for word in RAW_STATE_WORDS:
                self.assertNotIn(
                    word,
                    check.detail,
                    f"raw pulse state {word!r} leaked into detail: {check.detail!r}",
                )


class SeverityInversionTests(unittest.TestCase):
    """The second bug: `severity=WARNING if health.healthy else ERROR` reported a
    healthy collector at WARNING severity — backwards from intent."""

    def test_healthy_collector_is_not_reported_at_warning_severity(self) -> None:
        by = _checks_for([_health("Good", "ALIVE")])
        check = by["pulse collector:Good"]
        self.assertEqual(OK, check.status)
        self.assertEqual(NOTICE, check.severity)
        self.assertNotEqual(WARNING, check.severity)

    def test_unhealthy_collectors_carry_error_severity(self) -> None:
        for state in ("ALERT", "DEGRADED", "NO PUSHES"):
            with self.subTest(state=state):
                by = _checks_for([_health("D", state)])
                self.assertEqual(ERROR, by["pulse collector:D"].severity)

    def test_stale_is_a_warning_not_an_error(self) -> None:
        by = _checks_for([_health("D", "STALE")])
        self.assertEqual(WARNING, by["pulse collector:D"].severity)
        self.assertEqual(WARN, by["pulse collector:D"].status)


class MappingContractTests(unittest.TestCase):
    def test_every_pulse_state_maps_to_a_canonical_severity(self) -> None:
        for state in RAW_STATE_WORDS:
            with self.subTest(state=state):
                status, severity, phrase = _map_pulse_state(state)
                self.assertIn(status, {OK, WARN})
                self.assertIn(severity, {NOTICE, WARNING, ERROR})
                self.assertTrue(phrase)
                self.assertNotIn(state, phrase)

    def test_unknown_state_is_not_assumed_healthy(self) -> None:
        """Doctor must never report a state it does not understand as fine."""
        status, severity, _phrase = _map_pulse_state("SOMETHING_NEW")
        self.assertEqual(WARN, status)
        self.assertEqual(WARNING, severity)

    def test_qualified_state_classifies_on_its_leading_word(self) -> None:
        status, severity, _ = _map_pulse_state("ALIVE (intermittent-device window 18h)")
        self.assertEqual(OK, status)
        self.assertEqual(NOTICE, severity)

    def test_qualifier_is_preserved_in_detail_text(self) -> None:
        """The intermittent-device window is operator-useful context — mapping the
        state word must not throw it away."""
        _, _, phrase = _map_pulse_state("ALIVE (intermittent-device window 18h)")
        self.assertNotIn("18h", phrase)  # phrase itself is the canonical word

        by = _checks_for([_health("Laptop", "ALIVE (intermittent-device window 18h)")])
        detail = by["pulse collector:Laptop"].detail
        self.assertIn("intermittent-device window 18h", detail)
        self.assertNotIn("ALIVE", detail)


class PulseHealthLeftUntouchedTests(unittest.TestCase):
    def test_pulse_health_still_owns_its_five_state_model(self) -> None:
        """Pinned: the fix is at the boundary, not by collapsing the source model."""
        from rebalance.ingest import pulse_health

        source = __import__("pathlib").Path(pulse_health.__file__).read_text(encoding="utf-8")
        for state in RAW_STATE_WORDS:
            self.assertIn(f'"{state}"', source)


if __name__ == "__main__":
    unittest.main()

"""GH-5 Phase 3 — absorbing dashboard._ago into time_ops.format_relative.

`_ago` was NOT a drop-in for `format_relative`. The two disagreed on three
display behaviors, and swapping one for the other would have silently changed
what six dashboard call sites render:

    input                     _ago (TUI)     format_relative (web)
    None / unparseable        "—"            ""
    45 seconds ago            "45s ago"      "just now"
    5 minutes in the future   "in 5m"        "just now"

Rather than pick a winner and change a live surface as a side effect of a
consolidation, the divergences became explicit options. This file is the gate:
the web default must be byte-identical to before, and `_ago` must render
byte-identical to its old implementation.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from rebalance.lib.time_ops import format_relative

NOW = datetime(2026, 8, 16, 12, 0, 0, tzinfo=timezone.utc)


def _legacy_ago(value, now=None):
    """`scripts/dashboard.py:_ago` exactly as it stood before GH-5 Phase 3.

    Kept verbatim as the oracle. If the new implementation ever diverges, the
    equivalence test below fails rather than the dashboard quietly changing.
    """
    if value is None:
        return "—"
    dt = value
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    n = now or datetime.now(timezone.utc)
    delta = n - dt
    secs = int(delta.total_seconds())
    if secs < 0:
        secs = -secs
        future = True
    else:
        future = False
    if secs < 60:
        s = f"{secs}s"
    elif secs < 3600:
        s = f"{secs // 60}m"
    elif secs < 86400:
        s = f"{secs // 3600}h"
    else:
        s = f"{secs // 86400}d"
    return f"in {s}" if future else f"{s} ago"


OFFSETS = [
    timedelta(seconds=0),
    timedelta(seconds=1),
    timedelta(seconds=45),
    timedelta(seconds=59),
    timedelta(minutes=1),
    timedelta(minutes=5),
    timedelta(minutes=59),
    timedelta(hours=1),
    timedelta(hours=3),
    timedelta(hours=23),
    timedelta(days=1),
    timedelta(days=2),
    timedelta(days=400),
]


class DashboardAgoEquivalenceTests(unittest.TestCase):
    """The gate: TUI output is unchanged by the consolidation."""

    def _new_ago(self, value, now=None):
        return format_relative(value, now=now, empty="—", allow_future=True, sub_minute=True)

    def test_past_timestamps_match_legacy_exactly(self) -> None:
        for offset in OFFSETS:
            value = NOW - offset
            with self.subTest(offset=str(offset)):
                self.assertEqual(_legacy_ago(value, now=NOW), self._new_ago(value, now=NOW))

    def test_future_timestamps_match_legacy_exactly(self) -> None:
        for offset in OFFSETS:
            if not offset:
                continue
            value = NOW + offset
            with self.subTest(offset=str(offset)):
                self.assertEqual(_legacy_ago(value, now=NOW), self._new_ago(value, now=NOW))

    def test_none_renders_the_tui_empty_marker(self) -> None:
        self.assertEqual("—", self._new_ago(None, now=NOW))

    def test_unparseable_string_renders_the_tui_empty_marker(self) -> None:
        self.assertEqual("—", self._new_ago("not a timestamp", now=NOW))

    def test_naive_input_treated_as_utc(self) -> None:
        naive = datetime(2026, 8, 16, 9, 0, 0)  # no tzinfo
        self.assertEqual("3h ago", self._new_ago(naive, now=NOW))


class WebDefaultsUnchangedTests(unittest.TestCase):
    """The other half of the gate: adding options must not shift the default,
    which every web surface already renders through."""

    def test_defaults_clamp_future_to_just_now(self) -> None:
        self.assertEqual("just now", format_relative(NOW + timedelta(minutes=5), now=NOW))

    def test_defaults_collapse_sub_minute_to_just_now(self) -> None:
        self.assertEqual("just now", format_relative(NOW - timedelta(seconds=45), now=NOW))
        self.assertEqual("just now", format_relative(NOW, now=NOW))

    def test_defaults_return_empty_string_for_none(self) -> None:
        self.assertEqual("", format_relative(None, now=NOW))

    def test_defaults_return_empty_string_for_unparseable(self) -> None:
        self.assertEqual("", format_relative("nonsense", now=NOW))

    def test_standard_buckets_unchanged(self) -> None:
        cases = [
            (timedelta(minutes=5), "5m ago"),
            (timedelta(hours=3), "3h ago"),
            (timedelta(days=2), "2d ago"),
            (timedelta(days=400), "400d ago"),
        ]
        for offset, expected in cases:
            with self.subTest(offset=str(offset)):
                self.assertEqual(expected, format_relative(NOW - offset, now=NOW))

    def test_iso_string_input_still_parsed(self) -> None:
        self.assertEqual("3h ago", format_relative("2026-08-16T09:00:00+00:00", now=NOW))


class RetiredShimTests(unittest.TestCase):
    """`rebalance.tz_utils` was deleted in GH-5 PR2 — the separately announced
    removal the old shim-pin test was holding the door open for. Everything it
    re-exported lives in `rebalance.lib.time_ops`."""

    def test_shim_is_gone(self) -> None:
        with self.assertRaises(ModuleNotFoundError):
            import rebalance.tz_utils  # noqa: F401

    def test_no_code_references_the_shim(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        offenders = []
        for directory in ("src", "scripts"):
            for path in (root / directory).rglob("*.py"):
                if "rebalance.tz_utils" in path.read_text(encoding="utf-8"):
                    offenders.append(str(path.relative_to(root)))
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()

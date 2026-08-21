"""Health banner layout + collapse caret.

The banner's shell changed from a two-column grid to a single flex column: the
lead was in an ``auto`` column beside the problems, so it held dead space for the
banner's full height while the problems were squeezed into the other half. The
problem rows also lost their 999px pill radius, which bowed inward around copy
that wraps to three lines.

This banner has broken twice from render changes that no test could see — once
when GH-100 deleted the element ``pulse_warning_watch.py`` scrapes (the suite
stayed green because its fixtures were hand-typed HTML), and once when JS strings
kept stale wording an HTML-asserting guard could not reach. So these tests assert
against the REAL render, and cover the scraper contract explicitly rather than
trusting that a CSS-only change cannot reach it.
"""

from __future__ import annotations

import re
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from rebalance.doctor import Check, ERROR, FAIL, OK, WARN, WARNING
from rebalance.health import HealthStatus

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pulse_web  # noqa: E402

NOW = datetime(2026, 8, 21, 15, 0, tzinfo=timezone.utc)
INGEST = "2026-08-21T14:30:00Z"


def _render(health: HealthStatus) -> str:
    return pulse_web.render_status_bar(health, NOW, INGEST)


def _healthy() -> HealthStatus:
    return HealthStatus(verdict=OK, problems=[])


def _degraded() -> HealthStatus:
    return HealthStatus(
        verdict=FAIL,
        problems=[
            Check("database", FAIL, "missing", "create it", ERROR),
            Check("gmail", WARN, "ADC missing", "reauth", WARNING),
        ],
    )


class CaretPresenceTests(unittest.TestCase):
    def test_the_healthy_state_has_no_caret(self) -> None:
        """A control that hides nothing is a control that lies about having
        content. The healthy bar renders no problem rows, so it renders no
        toggle."""
        markup = _render(_healthy())
        self.assertNotIn("health-banner-toggle", markup)
        self.assertNotIn("health-banner-items", markup)

    def test_a_banner_with_problems_has_a_caret(self) -> None:
        markup = _render(_degraded())
        self.assertIn("health-banner-toggle", markup)
        self.assertIn("health-banner-items", markup)

    def test_the_caret_points_at_the_panel_it_controls(self) -> None:
        """A mismatched ``aria-controls`` is invisible to sighted review and
        breaks the control entirely for a screen reader."""
        markup = _render(_degraded())
        controls = re.search(r'aria-controls="([^"]+)"', markup)
        self.assertIsNotNone(controls, "toggle has no aria-controls")
        assert controls is not None
        self.assertIn(f'id="{controls.group(1)}"', markup)

    def test_the_caret_starts_expanded(self) -> None:
        """The server renders the expanded state; the client collapses it from
        localStorage after load. Rendering collapsed here would hide the panel
        for anyone with JS disabled, permanently."""
        self.assertIn('aria-expanded="true"', _render(_degraded()))


class LayoutRegressionTests(unittest.TestCase):
    def test_the_banner_shell_is_not_a_two_column_grid(self) -> None:
        """THE PIN for the reported layout bug. The lead sat in an ``auto``
        column beside the problems and held dead space for the banner's whole
        height."""
        shell = _rule(_banner_css(), ".health-banner")
        self.assertNotIn("grid-template-columns", shell)
        self.assertIn("flex-direction: column", shell)

    def test_problem_rows_do_not_use_a_pill_radius(self) -> None:
        """999px on a box whose text wraps to three lines bows the edges in
        around the copy — the "text overflowing the pill" symptom."""
        rule = _rule(_banner_css(), ".health-banner-item")
        self.assertNotIn("999px", rule)

    def test_no_rule_still_targets_the_removed_grid(self) -> None:
        """The narrow-window media query kept a ``grid-template-columns``
        override for a grid that no longer exists — dead CSS that reads as
        intent."""
        self.assertNotIn(".health-banner { grid-template-columns", _banner_css())


class ScraperContractTests(unittest.TestCase):
    """``pulse_warning_watch.py`` parses this markup. GH-100 broke it by
    deleting the element it read, and the launchd job reported ``unknown`` in
    every state while exiting 0."""

    def test_the_scraped_section_and_badge_survive(self) -> None:
        for name, health in (("healthy", _healthy()), ("degraded", _degraded())):
            with self.subTest(state=name):
                markup = _render(health)
                self.assertRegex(markup, r'class="health-banner health-banner-(ok|warn|danger)"')
                self.assertIn("health-banner-badge", markup)

    def test_the_live_watcher_still_reads_a_tone_from_the_real_render(self) -> None:
        """Asserting on the class name is not enough — the watcher has its own
        parser, and the fixtures that were supposed to catch this last time had
        drifted from the real markup by two renames."""
        import pulse_warning_watch

        parser = pulse_warning_watch._PulseHTMLParser()
        parser.feed(_render(_degraded()))
        self.assertEqual(parser.sync_tone, "danger")


def _banner_css() -> str:
    """The stylesheet text, however pulse_web happens to expose it."""
    import inspect

    return inspect.getsource(pulse_web)


def _rule(css: str, selector: str) -> str:
    """The body of the FIRST rule whose selector is exactly *selector*."""
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    if match is None:  # pragma: no cover - a missing rule is a test failure below
        return ""
    return match.group(1)


if __name__ == "__main__":
    unittest.main()

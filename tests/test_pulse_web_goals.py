"""Tests for the pulse web goals parser and hero rendering."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from rebalance.doctor import Check, FAIL, WARN
from rebalance.health import compute_health_status
from rebalance.web_components import render_sidebar


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pulse_web  # noqa: E402


class PulseWebGoalTests(unittest.TestCase):
    def test_parse_goals_keeps_uppermost_open_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_path = Path(tmpdir) / "0. Goals.md"
            goals_path.write_text(
                "\n".join(
                    [
                        "- [x] Completed item",
                        *[f"- [ ] Open item {i}" for i in range(1, 11)],
                    ]
                ),
                encoding="utf-8",
            )

            goals = pulse_web.parse_goals(goals_path, limit=9)

        self.assertEqual([goal["title"] for goal in goals], [f"Open item {i}" for i in range(1, 10)])

    def test_parse_goals_exposes_source_line_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            goals_path = Path(tmpdir) / "0. Goals.md"
            goals_path.write_text(
                "\n".join(
                    [
                        "# Header",
                        "- [ ] First open",
                        "  details",
                        "- [x] Done",
                        "- [ ] Second open",
                    ]
                ),
                encoding="utf-8",
            )

            goals = pulse_web.parse_goals(goals_path, limit=None)

        self.assertEqual([goal["line_index"] for goal in goals], [1, 4])
        self.assertEqual(goals[0]["description"], "details")

    def test_render_hero_shows_secondary_todo_column(self) -> None:
        all_goals = [{"done": False, "title": f"Open item {i}", "description": ""} for i in range(1, 10)]

        html = pulse_web.render_hero(
            all_goals[:3],
            "0. Goals.md",
            datetime(2026, 5, 14, tzinfo=timezone.utc),
            None,
            [],
            secondary_todos=all_goals[3:],
        )

        self.assertIn("Next open todos", html)
        self.assertIn("Open item 4", html)
        self.assertIn("Open item 9", html)
        self.assertIn("<b>9</b> in progress", html)
        self.assertEqual(html.count('class="goal goal-compact"'), 6)

    def test_render_status_bar_prioritizes_failures(self) -> None:
        checks = [
            Check("launchd:github-sync", WARN, "last run exited with status 1"),
            Check("gmail", WARN, "ADC token is missing the Gmail readonly scope"),
            Check("github token", FAIL, "no GitHub token configured"),
            Check("vault", FAIL, "no vault path configured"),
            Check("sleuth", WARN, "no Sleuth Web API env file"),
        ]

        now = datetime(2026, 5, 28, 18, 0, tzinfo=timezone.utc)
        health = compute_health_status(checks, {"sources": {}}, now)
        html = pulse_web.render_status_bar(
            health,
            now,
            "2026-05-28T17:55:00+00:00",
        )

        self.assertIn("2 errors", html)
        self.assertIn("github token", html)
        self.assertIn("vault", html)
        self.assertIn("health-banner-copy-btn", html)
        self.assertIn("data-copy-text=", html)
        self.assertNotIn('launchd:github-sync</span><span class="health-banner-detail"', html)

    def test_overflow_says_what_was_hidden(self) -> None:
        """GH-100: "+1 more" did not say more WHAT. A silent cap reads as
        "that's everything"; the count must name what it is counting."""
        checks = [Check(f"check-{i}", FAIL, "broken") for i in range(6)]
        now = datetime(2026, 5, 28, 18, 0, tzinfo=timezone.utc)
        health = compute_health_status(checks, {"sources": {}}, now)
        html = pulse_web.render_status_bar(health, now, "2026-05-28T17:55:00+00:00")

        self.assertIn("2 more problems not shown", html)

    def test_the_hint_is_never_truncated(self) -> None:
        """THE PIN (GH-100): the remedy survives intact.

        The old bar trimmed the hint to 120 chars, which on a live screen
        rendered "→ inspect tem…" — the complaint kept, the fix cut. Detail may
        still be shortened: a shortened symptom is still a usable symptom.
        """
        long_hint = (
            "inspect temp/logs/health-check.err for the failing step, then re-run "
            "`rebalance doctor --verbose` and confirm the launchd job is bootstrapped "
            "with `launchctl print gui/$UID/com.rebalance.health-check`"
        )
        self.assertGreater(len(long_hint), 120, "the fixture must exceed the old cap to prove anything")
        checks = [Check("launchd:health-check", FAIL, "last run exited with status 1", hint=long_hint)]
        now = datetime(2026, 5, 28, 18, 0, tzinfo=timezone.utc)
        health = compute_health_status(checks, {"sources": {}}, now)
        html = pulse_web.render_status_bar(health, now, "2026-05-28T17:55:00+00:00")

        self.assertIn(long_hint, html)
        self.assertNotIn("…", html.split('class="health-banner-fix"')[1][: len(long_hint) + 40])

    def test_the_bar_renders_when_healthy(self) -> None:
        """One element in every state — that is what retires the sync chip.

        The chip existed only to have somewhere to say "last ingest" when
        nothing was wrong. If the bar disappeared on a healthy system, the chip
        would have to come back.
        """
        now = datetime(2026, 5, 28, 18, 0, tzinfo=timezone.utc)
        health = compute_health_status([], {"sources": {}}, now)
        html = pulse_web.render_status_bar(health, now, "2026-05-28T17:55:00+00:00")

        self.assertIn("health-banner-ok", html)
        self.assertIn("healthy", html)
        self.assertIn("Last data ingest", html)

    def test_notices_do_not_inflate_the_headline(self) -> None:
        """GH-100: the badge counts what is actionable.

        Notices are checks the operator already marked intentional. Counting 18
        of them beside one real error told the operator 19 things needed
        attention when one did.
        """
        from rebalance.doctor import NOTICE

        checks = [
            Check("github token", FAIL, "no GitHub token configured"),
            *[Check(f"launchd:job-{i}", WARN, "not loaded", severity=NOTICE) for i in range(18)],
        ]
        now = datetime(2026, 5, 28, 18, 0, tzinfo=timezone.utc)
        health = compute_health_status(checks, {"sources": {}}, now)
        self.assertEqual(len(health.notices), 18)

        html = pulse_web.render_status_bar(health, now, "2026-05-28T17:55:00+00:00")
        badge = html.split('class="health-banner-badge">')[1].split("</span>")[0]
        self.assertEqual(badge, "1 error")
        self.assertNotIn("notice", badge)

    def test_the_copy_button_still_carries_the_complete_picture(self) -> None:
        """The bar is a summary; the clipboard is the whole story.

        Excluding notices from the HEADLINE must not delete them from the thing
        the operator pastes into an issue.
        """
        from rebalance.doctor import NOTICE

        checks = [
            Check("github token", FAIL, "no GitHub token configured"),
            Check("launchd:job", WARN, "not loaded", severity=NOTICE),
        ]
        now = datetime(2026, 5, 28, 18, 0, tzinfo=timezone.utc)
        health = compute_health_status(checks, {"sources": {}}, now)
        html = pulse_web.render_status_bar(health, now, "2026-05-28T17:55:00+00:00")

        copy_text = html.split('data-copy-text="')[1].split('"')[0]
        self.assertIn("1 error", copy_text)
        self.assertIn("1 notice", copy_text)

    def test_the_sync_chip_is_gone(self) -> None:
        """GH-100: two widgets rendering one HealthStatus is the defect itself."""
        self.assertFalse(hasattr(pulse_web, "render_sync_chip"))
        self.assertFalse(hasattr(pulse_web, "render_health_banner"))

    def test_build_stream_rows_includes_email_and_figma(self) -> None:
        rows = pulse_web.build_stream_rows(
            {
                "sources": {
                    "github": {"items": 10},
                    "vault": {"chunks": 6},
                    "calendar": {"events": 6},
                    "sleuth": {"reminders": 6},
                    "email": {"messages": 2},
                    "figma": {"comments": 0},
                    "ask_self": {"repos": 4},
                }
            }
        )

        self.assertEqual(
            [row["name"] for row in rows],
            ["github", "vault", "calendar", "sleuth", "email", "figma"],
        )
        self.assertEqual(
            [row["count"] for row in rows],
            [10, 6, 6, 6, 2, 0],
        )

    def test_render_sidebar_renders_dynamic_stream_rows(self) -> None:
        html = render_sidebar(
            "today",
            {
                "badge": 0,
                "cal_html": "",
                "sleuth_html": "",
                "notices_html": "",
                "streams": [
                    {"name": "github", "label": "GitHub", "kbd": "G", "count": 10},
                    {"name": "email", "label": "Email", "kbd": "E", "count": 2},
                    {"name": "figma", "label": "Figma", "kbd": "F", "count": 0},
                ],
                "drift_total": 0,
                "semantic_total": 0,
            },
        )

        self.assertIn('>Email</span><span class="badge">2</span>', html)
        self.assertIn('>Figma</span><span class="badge">0</span>', html)
        self.assertNotIn('>Sleuth</span><span class="badge">', html)

    def test_render_recent_figma_shows_comments_and_add_form(self) -> None:
        html = pulse_web.render_recent_figma(
            [
                {
                    "message": "Update hero CTA spacing before handoff.",
                    "user_handle": "designer",
                    "file_key": "VoQWc0fhO020JoxOyqeE1P",
                    "created_at": "2026-06-09T04:20:19.496Z",
                    "resolved_at": "",
                    "synced_at": "2026-06-09T04:52:51.992193+00:00",
                }
            ],
            datetime(2026, 6, 9, 5, 0, tzinfo=timezone.utc),
            tz=timezone.utc,
            limit=12,
            stored_total=686,
            configured_keys=["VoQWc0fhO020JoxOyqeE1P"],
            last_synced_at="2026-06-09T04:52:51.992193+00:00",
        )

        self.assertIn("Recent Figma comments", html)
        self.assertIn("Add Figma project ID", html)
        self.assertIn("Update hero CTA spacing before handoff.", html)
        self.assertIn("designer", html)
        self.assertIn("figma-project-form", html)


if __name__ == "__main__":
    unittest.main()

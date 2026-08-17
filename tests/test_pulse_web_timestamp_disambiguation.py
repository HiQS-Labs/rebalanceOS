"""GH-5 Phase 4b — two unrelated timestamps stop reading as one (#2).

The dashboard banner showed, adjacently:

  * "Last collector activity 7:08 PM"  — the newest *general ingestion*
    timestamp (vault / github / calendar / sleuth / email / semantic index)
  * "fleet:noel's Mac Studio — … last scan 9:22 AM"  — a *git-pulse
    per-device* scan age

Both said "collector", so the operator read one as contradicting the other and
had no way to tell they measure different subsystems. The fix is naming, not
arithmetic: the general-ingestion label stops claiming the word.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from rebalance.doctor import WARN, Check
from rebalance.health import compute_health_status

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pulse_web  # noqa: E402

NOW = datetime(2026, 8, 16, 16, 22, tzinfo=timezone.utc)
INGEST_TS = "2026-08-16T16:22:00+00:00"


def _strip_copy_payload(html: str) -> str:
    """Drop the copy button's `data-copy-text="…"` attribute.

    That payload is a serialised copy of the problem list, so it legitimately
    contains check names like "fleet:Mac Studio". Assertions about the
    banner's own *labels* must not trip over it.
    """
    marker = 'data-copy-text="'
    start = html.find(marker)
    if start < 0:
        return html
    end = html.find('"', start + len(marker))
    return html[:start] + html[end + 1:]


def _banner(checks: list[Check]) -> str:
    health = compute_health_status(checks, {"sources": {}}, NOW)
    return pulse_web.render_health_banner(health, NOW, INGEST_TS)


class BannerLeadDisambiguationTests(unittest.TestCase):
    """#2's ready acceptance test, as posted on the issue. Confirmed red against
    the pre-change code: `.health-banner-lead` contained both
    "Last collector activity …" and aria-label="Copy collector warning text"."""

    def test_activity_label_does_not_share_wording_with_a_pulse_collector_pill(self) -> None:
        html = _banner([
            Check(
                "fleet:noel's Mac Studio",
                WARN,
                "not collecting — last scan 2026-08-11 7:08 PM",
            ),
        ])
        lead_start = html.index('class="health-banner-lead"')
        items_start = html.index('class="health-banner-items"')
        lead_html = html[lead_start:items_start]

        # As originally posted on #2 this asserted against the whole lead div.
        # That over-reaches: the lead also carries the copy button's
        # `data-copy-text` payload, which embeds the problem list — and a
        # per-device check named "fleet:…" SHOULD say collector there.
        # The defect was only ever the general-ingestion *label*, so the
        # assertion is scoped to the lead's own visible chrome.
        visible = _strip_copy_payload(lead_html)
        self.assertNotIn("collector", visible.lower())

    def test_lead_still_shows_the_ingest_timestamp(self) -> None:
        """Disambiguating must not remove the information — the timestamp is
        still there, just no longer mislabelled."""
        html = _banner([Check("vault", WARN, "stale")])
        lead_html = html[html.index('class="health-banner-lead"'):html.index('class="health-banner-items"')]
        self.assertIn("Last data ingest", lead_html)
        self.assertIn("2026-08-16", lead_html)

    def test_per_device_collector_items_keep_their_own_wording(self) -> None:
        """Only the general-ingestion label changed. The pulse-collector problem
        items legitimately say "collector" — that IS what they measure."""
        html = _banner([
            Check("fleet:Mac Studio", WARN, "not collecting — last scan earlier"),
        ])
        items_html = html[html.index('class="health-banner-items"'):]
        self.assertIn("fleet:Mac Studio", items_html)


class CopyPayloadMirrorsVisibleTextTests(unittest.TestCase):
    def test_clipboard_text_uses_the_same_disambiguated_label(self) -> None:
        text = pulse_web._health_banner_copy_text(
            [Check("vault", WARN, "stale")],
            status_text="1 warning",
            activity_text="2026-08-16 4:22 PM",
        )
        self.assertIn("Last data ingest:", text)
        self.assertNotIn("collector", text.lower())

    def test_clipboard_text_still_names_per_device_collector_checks(self) -> None:
        """The payload's job is to reproduce the problem list verbatim — a check
        named "fleet:…" must survive into it unchanged."""
        text = pulse_web._health_banner_copy_text(
            [Check("fleet:Mac Studio", WARN, "not collecting")],
            status_text="1 warning",
            activity_text="2026-08-16 4:22 PM",
        )
        self.assertIn("fleet:Mac Studio", text)


class SyncChipDisambiguationTests(unittest.TestCase):
    """The chip renders the same general-ingestion timestamp and had the same
    mislabel."""

    def _chip(self, checks: list[Check]) -> str:
        health = compute_health_status(checks, {"sources": {}}, NOW)
        return pulse_web.render_sync_chip(health, INGEST_TS, NOW)

    def test_chip_does_not_call_the_ingest_timestamp_a_collector(self) -> None:
        for checks in (
            [Check("gmail", WARN, "scope missing")],
            [],
        ):
            with self.subTest(checks=len(checks)):
                self.assertNotIn("collector", self._chip(checks).lower())

    def test_chip_still_reports_the_warning_state(self) -> None:
        chip = self._chip([Check("gmail", WARN, "scope missing")])
        self.assertIn("synced-warn", chip)
        self.assertIn("Sync warnings", chip)


class HelperNameMatchesWhatItMeasuresTests(unittest.TestCase):
    def test_helper_renamed_off_the_ambiguous_word(self) -> None:
        self.assertTrue(hasattr(pulse_web, "_latest_ingest_activity"))
        self.assertFalse(
            hasattr(pulse_web, "_latest_collector_activity"),
            "the old ambiguous name is back — it measures ingestion, not collectors",
        )

    def test_helper_reads_general_ingestion_sources_not_pulse_devices(self) -> None:
        status = {
            "sources": {
                "vault": {"last_ingested_at": "2026-08-16T10:00:00+00:00"},
                "github": {"activity_last_scanned_at": "2026-08-16T16:22:00+00:00"},
            },
            "semantic_index": {"last_embedded_at": "2026-08-16T09:00:00+00:00"},
        }
        self.assertEqual("2026-08-16T16:22:00+00:00", pulse_web._latest_ingest_activity(status))

    def test_helper_returns_none_when_nothing_has_ingested(self) -> None:
        self.assertIsNone(pulse_web._latest_ingest_activity({"sources": {}}))


if __name__ == "__main__":
    unittest.main()

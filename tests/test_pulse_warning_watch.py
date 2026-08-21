"""Tests for the pulse warning watcher's page scraper.

These parse the REAL rendered status bar, not a hand-written fixture.

That is the whole point of this file. The watcher reads the dashboard's HTML,
so its tests used to embed a copy of that HTML — and a copy goes stale silently.
When GH-100 deleted the `<span class="synced">` sync chip the watcher scraped,
every test here kept passing against markup the page no longer emitted, while
the watcher itself would have logged `page_state="unknown"` forever and reported
itself healthy. The fixture had ALREADY drifted before that: it still said
"Collector warnings", wording renamed in GH-5 Phase 4b.

A test that scans a fixture cannot fail when the thing it models changes. So the
input here comes from `pulse_web.render_status_bar` — the same call the page
makes. Break the markup contract and these go red.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# scripts/ is not a package; add it to sys.path so the module imports directly
# (matches the convention in test_pulse_server_figma.py and the other pulse tests).
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pulse_web  # noqa: E402
from pulse_warning_watch import PulseSnapshot, append_log, extract_banner_text  # noqa: E402
from rebalance.doctor import Check, FAIL, WARN  # noqa: E402
from rebalance.health import compute_health_status  # noqa: E402

NOW = datetime(2026, 8, 20, 17, 38, tzinfo=timezone.utc)
INGEST_TS = "2026-08-20T17:16:00+00:00"


def _real_page(checks: list[Check]) -> str:
    """The status bar as the dashboard actually renders it."""
    health = compute_health_status(checks, {"sources": {}}, NOW)
    return "<html><body>" + pulse_web.render_status_bar(health, NOW, INGEST_TS) + "</body></html>"


def test_warning_state_is_read_from_the_real_page() -> None:
    page_state, sync_text, banner_text, sync_tone = extract_banner_text(
        _real_page([Check("gmail", WARN, "token missing", hint="rerun auth")])
    )

    assert page_state == "warning"
    assert sync_tone == "warn"
    assert sync_text == "1 warning"
    assert "gmail: token missing" in banner_text
    assert "Hint: rerun auth" in banner_text


def test_error_state_reads_as_danger() -> None:
    page_state, _sync_text, _banner_text, sync_tone = extract_banner_text(
        _real_page([Check("github token", FAIL, "not configured")])
    )

    assert page_state == "warning"  # the watcher's coarse "needs attention" bucket
    assert sync_tone == "danger"


def test_healthy_state_is_read_from_the_real_page() -> None:
    """THE PIN. The bar renders when healthy too (GH-100), so a healthy page is
    a POSITIVE reading — not the absence of markup it used to be inferred from."""
    page_state, sync_text, banner_text, sync_tone = extract_banner_text(_real_page([]))

    assert page_state == "healthy"
    assert sync_tone == "ok"
    assert sync_text == "healthy"
    assert "Status: healthy" in banner_text


def test_a_page_that_did_not_render_is_unknown_not_healthy() -> None:
    """Missing evidence is not an all-clear.

    Before GH-100 an absent banner meant "nothing wrong". Now the bar always
    renders, so an absent one means the page failed — and calling that healthy
    would be the watcher inventing the very all-clear it exists to disprove.
    """
    page_state, _sync_text, banner_text, sync_tone = extract_banner_text("<html><body>nope</body></html>")

    assert page_state == "unknown"
    assert sync_tone == ""
    assert banner_text == ""


def test_the_scraper_notices_when_the_bar_stops_emitting_a_tone() -> None:
    """A negative control for the drift that started this file's rewrite.

    Strip the tone class the way GH-100 stripped the chip, and the watcher must
    fall back to "unknown" rather than reporting a state it cannot see.
    """
    broken = _real_page([Check("gmail", WARN, "token missing")]).replace("health-banner-warn", "")
    page_state, _sync_text, _banner_text, sync_tone = extract_banner_text(broken)

    assert sync_tone == ""
    assert page_state == "unknown"


def test_append_log_writes_jsonl(tmp_path) -> None:
    log_path = tmp_path / "watch.jsonl"
    snapshot = PulseSnapshot(
        fetched_at="2026-06-03T00:00:00+00:00",
        url="http://127.0.0.1:8767/",
        fetch_ok=True,
        page_state="warning",
        sync_tone="warn",
        sync_text="2 warnings",
        banner_text="Status: 2 warnings",
        fingerprint="abc123",
        changed=True,
    )

    append_log(log_path, snapshot)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["fingerprint"] == "abc123"
    assert payload["page_state"] == "warning"

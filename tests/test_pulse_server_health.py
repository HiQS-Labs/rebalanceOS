from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import pulse_server  # noqa: E402

PACIFIC = ZoneInfo("America/Los_Angeles")


def _health(tmp_path: Path, *, generated_local: datetime, now_local: datetime):
    pulse = tmp_path / "pulse.html"
    pulse.write_text("generated", encoding="utf-8")
    generated_utc = generated_local.astimezone(timezone.utc)
    os.utime(pulse, (generated_utc.timestamp(), generated_utc.timestamp()))
    with (
        patch.object(pulse_server, "PULSE_HTML", pulse),
        patch.object(pulse_server, "now_utc", return_value=now_local.astimezone(timezone.utc)),
        patch.object(pulse_server, "_local_timezone", return_value=PACIFIC),
    ):
        return TestClient(pulse_server.app).get("/api/health")


def test_overnight_artifact_is_healthy_through_0653(tmp_path: Path) -> None:
    generated = datetime(2026, 9, 11, 23, 38, tzinfo=PACIFIC)
    assert (
        _health(
            tmp_path,
            generated_local=generated,
            now_local=datetime(2026, 9, 12, 6, 53, tzinfo=PACIFIC),
        ).status_code
        == 200
    )


def test_overnight_artifact_is_stale_immediately_after_0653(tmp_path: Path) -> None:
    response = _health(
        tmp_path,
        generated_local=datetime(2026, 9, 11, 23, 38, tzinfo=PACIFIC),
        now_local=datetime(2026, 9, 12, 6, 53, 1, tzinfo=PACIFIC),
    )
    assert response.status_code == 503
    assert response.json()["reason"] == "pulse.html stale"


def test_active_artifact_is_healthy_at_90_minutes_and_stale_after(tmp_path: Path) -> None:
    generated = datetime(2026, 9, 12, 8, 0, tzinfo=PACIFIC)
    at_boundary = _health(
        tmp_path,
        generated_local=generated,
        now_local=datetime(2026, 9, 12, 9, 30, tzinfo=PACIFIC),
    )
    after_boundary = _health(
        tmp_path,
        generated_local=generated,
        now_local=datetime(2026, 9, 12, 9, 30, 1, tzinfo=PACIFIC),
    )
    assert at_boundary.status_code == 200
    assert after_boundary.status_code == 503

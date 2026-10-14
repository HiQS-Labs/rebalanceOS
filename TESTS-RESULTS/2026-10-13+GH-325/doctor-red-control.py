"""GH-325 red control: the public doctor report on the same inputs, base vs candidate.

Run from a checkout's root with its own interpreter:
    python TESTS-RESULTS/2026-10-13+GH-325/doctor-red-control.py
Prints one JSON line per scenario with every pulse/fleet row. Temp config only.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from rebalance import doctor
from rebalance.ingest import config as config_module

SCENARIOS = {
    "a_installed_unenrolled": ('device_id="mac-a"\nfleet_mode=true\n', {}),
    "b_fleet_on_collector_missing": (None, {"pulse_fleet_enabled": True, "pulse_device_id": "mac-a"}),
}

for name, (collector, rbos) in SCENARIOS.items():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        gp = root / "gp"
        gp.mkdir()
        clone = root / "clone"
        (clone / ".git").mkdir(parents=True)
        (clone / "devices").mkdir()
        if collector:
            (gp / "config.sh").write_text(collector)
        cfg = root / "rbos.config"
        cfg.write_text(json.dumps({"github_login": "x", "pulse_target_path": str(clone), **rbos}))
        config_module.CONFIG_PATH = cfg
        with (
            patch.dict(os.environ, {"GIT_PULSE_CONFIG_DIR": str(gp)}),
            patch("rebalance.ingest.pulse_health.read_collector_health", return_value=[]),
        ):
            report = doctor.run_doctor(root / "missing.db")
        rows = [
            {"name": c.name, "status": c.status, "detail": c.detail, "hint": c.hint}
            for c in report.checks
            if "pulse" in c.name or "fleet" in c.name
        ]
        print(json.dumps({"scenario": name, "rows": rows}))

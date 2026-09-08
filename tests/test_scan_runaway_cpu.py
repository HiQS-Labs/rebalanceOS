"""GH-194 — scan_runaway_cpu.py: deterministic runaway-CPU classification.

Unit tests over the pure core (parsing, thresholds, persistence, exemptions,
summary format) with synthetic ps rows — no live process table, fully deterministic.
The 2026-09-06 incident profile (XYZ-forge ATE test snippet: 90.7% CPU, 2d20:57:35
elapsed, duty 0.98) is the anchor fixture; the measured legitimate services
(pulse_server at 0.1% duty over 4½ days, the idle mcp_server fleet) are the
false-alarm controls.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "daily" / "scripts" / "scan_runaway_cpu.py"
spec = importlib.util.spec_from_file_location("scan_runaway_cpu", SCRIPT)
scan_runaway_cpu = importlib.util.module_from_spec(spec)
sys.modules["scan_runaway_cpu"] = scan_runaway_cpu
spec.loader.exec_module(scan_runaway_cpu)


def make_proc(
    pid=4377,
    pcpu=90.7,
    etime="02-20:57:35",
    cputime="4056:39.31",
    lstart="Thu Sep  3 23:28:34 2026",
    command="Python -c from utils.py.adaptive_ate import generate_pairwise ...",
):
    return {
        "pid": pid,
        "pcpu": pcpu,
        "elapsed_s": scan_runaway_cpu.parse_ps_duration(etime),
        "cpu_s": scan_runaway_cpu.parse_ps_duration(cputime),
        "lstart": lstart,
        "command": command,
    }


# --- duration parsing -------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("01:05", 65.0),
        ("23:02:14", 23 * 3600 + 2 * 60 + 14),
        ("4056:39.31", 4056 * 60 + 39.31),
        ("02-20:57:35", 2 * 86400 + 20 * 3600 + 57 * 60 + 35),
        ("00:00:00.5", 0.5),
        ("72:00:00", 72 * 3600),
        ("75:00", 75 * 60),
    ],
)
def test_parse_duration_accepts_ps_shapes(text, expected):
    assert scan_runaway_cpu.parse_ps_duration(text) == expected


@pytest.mark.parametrize("text", ["", "x", "1:2:3:4", "99:xx", "-5:00"])
def test_parse_duration_rejects_garbage(text):
    assert scan_runaway_cpu.parse_ps_duration(text) is None


# --- ps line parsing --------------------------------------------------------------


def test_parse_ps_line_splits_lstart_from_command():
    line = (
        "4377  3829 90.7 02-20:57:35 4056:39.31 Thu Sep  3 23:28:34 2026 "
        "/opt/homebrew/Python -c from utils.py.adaptive_ate import generate_pairwise"
    )
    proc = scan_runaway_cpu.parse_ps_line(line)
    assert proc is not None
    assert proc["pid"] == 4377
    assert proc["lstart"] == "Thu Sep 3 23:28:34 2026" or proc["lstart"].startswith("Thu Sep")
    assert "generate_pairwise" in proc["command"]


def test_parse_ps_line_rejects_short_or_garbled_rows():
    assert scan_runaway_cpu.parse_ps_line("4377 3829") is None
    assert scan_runaway_cpu.parse_ps_line("pid x 90 01:00:00 00:30 Thu Sep 3 23:28:34 2026 cmd") is None


# --- the incident profile flags; legitimate services never do ---------------------


def test_incident_profile_flags_on_first_sighting_via_24h_rule():
    eligible, flagged = scan_runaway_cpu.scan([make_proc()], [], [])
    assert len(eligible) == 1
    assert len(flagged) == 1
    assert flagged[0]["cycles"] == 1
    assert flagged[0]["kill_command"] == "kill 4377"


def test_pulse_server_profile_never_flags():
    # Measured 2026-09-06: 4d13h elapsed, 0:47.69 CPU total, 0.1% — duty 0.01%.
    proc = make_proc(
        pid=24823,
        pcpu=0.1,
        etime="04-13:04:09",
        cputime="0:47.69",
        command="Python /Users/noelsaw/rebalance-runtime/scripts/pulse_server.py --port 8767",
    )
    eligible, flagged = scan_runaway_cpu.scan([proc], [], [])
    assert eligible == []
    assert flagged == []


def test_mcp_server_profile_never_flags():
    proc = make_proc(
        pid=53235,
        pcpu=0.0,
        etime="02-08:13:50",
        cputime="0:00.72",
        command="Python -m rebalance.mcp_server",
    )
    eligible, flagged = scan_runaway_cpu.scan([proc], [], [])
    assert eligible == []
    assert flagged == []


def test_short_heavy_build_never_flags():
    # 100% CPU for 10 minutes: duty ~1 but fails the 2h elapsed gate.
    proc = make_proc(pcpu=100.0, etime="00:10:00", cputime="00:09:50")
    eligible, flagged = scan_runaway_cpu.scan([proc], [], [])
    assert eligible == []
    assert flagged == []


def test_service_exemption_holds_even_at_pathological_cpu():
    proc = make_proc(
        pid=999,
        pcpu=92.0,
        etime="03-00:00:00",
        cputime="72:00:00",
        command="Python /Users/noelsaw/rebalance-runtime/scripts/pulse_server.py --port 8767",
    )
    eligible, flagged = scan_runaway_cpu.scan([proc], [], [])
    assert eligible == []
    assert flagged == []


# --- persistence across cycles ----------------------------------------------------


def test_second_sighting_with_growing_cpu_flags_with_cycle_count():
    proc = make_proc(etime="03:00:00", cputime="02:42:00")  # 3h elapsed, duty 0.9, <24h
    prev_eligible = [{**proc, "cpu_s": proc["cpu_s"] - 60, "duty": 0.88}]
    eligible, flagged = scan_runaway_cpu.scan([proc], prev_eligible, [])
    assert len(flagged) == 1
    assert flagged[0]["cycles"] == 1  # first FLAG; persistence was the trigger


def test_flagged_cycles_increment_across_consecutive_flags():
    proc = make_proc(etime="03:00:00", cputime="02:42:00")
    prev_flagged = [{**proc, "cpu_s": proc["cpu_s"] - 30, "duty": 0.9, "cycles": 2}]
    _, flagged = scan_runaway_cpu.scan([proc], [{**proc, "cpu_s": proc["cpu_s"] - 30}], prev_flagged)
    assert flagged[0]["cycles"] == 3


def test_persisted_without_cpu_growth_stays_unflagged_before_24h():
    proc = make_proc(etime="03:00:00", cputime="02:42:00")  # idle-but-alive at high duty
    prev_eligible = [{**proc, "duty": 0.9}]
    eligible, flagged = scan_runaway_cpu.scan([proc], prev_eligible, [])
    assert len(eligible) == 1
    assert flagged == []


def test_restart_counts_as_fresh_process():
    proc = make_proc(etime="03:00:00", cputime="02:42:00", lstart="Sat Sep  6 10:00:00 2026")
    prev_eligible = [{**make_proc(etime="03:00:00", cputime="02:00:00"), "duty": 0.9}]
    _, flagged = scan_runaway_cpu.scan([proc], prev_eligible, [])
    assert flagged == []  # new lstart: no persistence, under 24h


# --- state round-trip -------------------------------------------------------------


def test_load_state_tolerates_missing_and_malformed(tmp_path):
    assert scan_runaway_cpu.load_state(tmp_path / "absent.json") == ([], [])
    bad = tmp_path / "bad.json"
    bad.write_text("not json {", encoding="utf-8")
    assert scan_runaway_cpu.load_state(bad) == ([], [])


def test_state_round_trip_preserves_flagged_cycles(tmp_path):
    state = tmp_path / "cpu-watch.json"
    proc = make_proc()
    scan_runaway_cpu.save_state(state, [proc], [{**proc, "duty": 0.98, "cycles": 2, "kill_command": "kill 4377"}])
    prev_eligible, prev_flagged = scan_runaway_cpu.load_state(state)
    _, flagged = scan_runaway_cpu.scan([proc], prev_eligible, prev_flagged)
    assert flagged[0]["cycles"] == 3


# --- summary format ---------------------------------------------------------------


def test_summary_clean_when_nothing_flagged():
    line = scan_runaway_cpu.format_summary([])
    assert line == "- **Machine CPU Health**: clean (0 runaway CPU candidates)"


def test_summary_names_pid_duty_and_kill_command():
    proc = make_proc()
    _, flagged = scan_runaway_cpu.scan([proc], [], [])
    line = scan_runaway_cpu.format_summary(flagged)
    assert line.startswith("- **Machine CPU Health**: 1 runaway candidate — ")
    assert "PID 4377" in line
    assert "duty 98%" in line
    assert "[kill 4377]" in line
    assert "[Details: temp/daily-log/cpu-watch.json]" in line


def test_two_candidates_pluralize_and_collapse():
    a = make_proc(pid=1)
    b = make_proc(pid=2, command="python other_runaway.py")
    _, flagged = scan_runaway_cpu.scan([a, b], [], [])
    line = scan_runaway_cpu.format_summary(flagged)
    assert line.startswith("- **Machine CPU Health**: 2 runaway candidates — ")
    assert "PID 1" in line and "PID 2" in line


# --- ps snapshot shell ------------------------------------------------------------


def test_snapshot_processes_returns_none_when_ps_missing(monkeypatch):
    def boom(*args, **kwargs):
        raise FileNotFoundError("ps")

    monkeypatch.setattr(scan_runaway_cpu.subprocess, "run", boom)
    assert scan_runaway_cpu.snapshot_processes() is None


def test_json_payload_round_trip_shape(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        scan_runaway_cpu,
        "snapshot_processes",
        lambda: [make_proc()],
    )
    monkeypatch.setattr(scan_runaway_cpu, "DEFAULT_STATE_PATH", tmp_path / "cpu-watch.json", raising=False)
    sys.argv = ["scan_runaway_cpu.py", "--json", "--state-path", str(tmp_path / "cpu-watch.json")]
    assert scan_runaway_cpu.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["eligible_count"] == 1
    assert payload["flagged"][0]["pid"] == 4377
    assert (tmp_path / "cpu-watch.json").exists()

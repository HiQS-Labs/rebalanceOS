"""Tests for the job guard's footprint measurement (GH-219 Lane 4).

These must be deterministic and host-independent. An earlier version passed only
when run from the repo root on the development machine, and failed in an isolated
worktree on three counts: it used the real `~/.cache` lock directory, it depended
on `total_memory_bytes()` probing real hardware, and it relied on host `ps`
visibility. A guard test that only passes on one machine cannot protect anything.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

# `from utils import job_guard` resolves only when the repo root is importable.
# pytest puts `tests/` on sys.path (conftest, no __init__.py), not the root, so
# running from any other cwd fails at collection. Bootstrap it explicitly.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from utils import job_guard  # noqa: E402

GIB = 1024**3
FAKE_TOTAL_RAM = 64 * GIB


@pytest.fixture
def isolated_guard(tmp_path, monkeypatch):
    """Detach the guard from host RAM, the real lock dir, and system memory pressure."""
    monkeypatch.setattr(job_guard, "LOCK_DIR", tmp_path / "locks")
    # Redirect the peak-footprint telemetry log. Without this, `run_guarded` in a
    # test writes to the REAL temp/logs/job_rss.jsonl: a single test session left
    # 30 synthetic records there, including 14 `test-over-ceiling` entries with a
    # mocked 10 GB peak. Lane 7's regression detection replays that file, so those
    # would surface as phantom contract breaches long after the test run.
    monkeypatch.setattr(job_guard, "RSS_LOG_PATH", tmp_path / "job_rss.jsonl")
    monkeypatch.setattr(job_guard, "total_memory_bytes", lambda: FAKE_TOTAL_RAM)
    # A healthy machine by default, so the preflight never masks what a test means
    # to exercise. Individual tests override these.
    monkeypatch.setattr(job_guard, "available_memory_bytes", lambda: 32 * GIB)
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: 1 * GIB)
    # Not paging. A compressor reading above the ceiling only trips when a second
    # signal confirms real distress (#157), so the fixture has to state which
    # machine it is describing rather than leave it to the host sysctl.
    monkeypatch.setattr(job_guard, "swap_used_bytes", lambda: 0)
    # GH-296: the swap bar scales with the swap file, and settings come from the
    # device config. Pin both so no host swap size or real rbos.config leaks in:
    # an unreadable total keeps the legacy 1 GiB bar, and the config file is absent.
    monkeypatch.setattr(job_guard, "swap_total_bytes", lambda: None, raising=False)
    monkeypatch.setenv("REBALANCE_CONFIG", str(tmp_path / "no-rbos.config"))
    for name in ("REBALANCE_JOB_GUARD_MEMORY", "REBALANCE_JOB_GUARD_SWAP_DISTRESS_GB"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv(job_guard.ENV_MAX_COMPRESSOR_GB, raising=False)
    return tmp_path


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def test_over_ceiling_trips_and_child_is_reaped(isolated_guard, monkeypatch):
    """1. A synthetic over-ceiling child trips the guard AND is actually killed.

    Asserting only `code == 4` is insufficient: `run_guarded` also returns 4 when
    the available-memory preflight refuses to start, so the assertion can pass
    without the child ever launching. The preflight is pinned healthy here and the
    child's liveness is checked directly.
    """
    script = isolated_guard / "spin.py"
    script.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")

    captured: dict[str, int] = {}
    real_popen = subprocess.Popen

    def capturing_popen(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        captured["pid"] = proc.pid
        return proc

    monkeypatch.setattr(subprocess, "Popen", capturing_popen)
    # Force the ceiling branch specifically, independent of what the child does.
    monkeypatch.setattr(job_guard, "tree_footprint_bytes", lambda pid: (10 * GIB, False, 0))

    code = job_guard.run_guarded(
        name="test-over-ceiling",
        argv=[sys.executable, str(script)],
        max_footprint_gb=1.0,
        poll_seconds=0.1,
        grace_seconds=0.5,
    )

    assert code == 4
    assert "pid" in captured, "the child never launched — 4 came from the preflight"

    deadline = time.monotonic() + 5
    while _pid_alive(captured["pid"]) and time.monotonic() < deadline:
        time.sleep(0.1)
    assert not _pid_alive(captured["pid"]), "child survived the ceiling trip"


def test_wall_clock_timeout_has_distinct_exit_and_reaps_child(isolated_guard, monkeypatch):
    """GH-211: a deadline expires with 124 and leaves no child behind."""
    script = isolated_guard / "sleep_forever.py"
    script.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")

    captured: dict[str, int] = {}
    real_popen = subprocess.Popen

    def capturing_popen(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        captured["pid"] = proc.pid
        return proc

    monkeypatch.setattr(subprocess, "Popen", capturing_popen)

    code = job_guard.run_guarded(
        name="test-wall-clock-timeout",
        argv=[sys.executable, str(script)],
        max_footprint_gb=8.0,
        max_runtime_seconds=0.2,
        poll_seconds=0.05,
        grace_seconds=0.2,
    )

    assert code == job_guard.EXIT_WALL_CLOCK_TIMEOUT == 124
    assert "pid" in captured
    deadline = time.monotonic() + 5
    while _pid_alive(captured["pid"]) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _pid_alive(captured["pid"]), "timed-out child survived its guard"


def test_scheduled_timeout_records_one_start_and_one_failure(isolated_guard, monkeypatch):
    """The outer guard owns lifecycle for wrapper and Python-direct jobs."""
    script = isolated_guard / "assert_child_env_then_sleep.py"
    script.write_text(
        "import os, time\nassert os.environ['REBALANCE_SCHEDULER_LIFECYCLE_CHILD'] == '1'\ntime.sleep(60)\n",
        encoding="utf-8",
    )
    log_dir = isolated_guard / "auth"
    monkeypatch.setenv("REBALANCE_AUTH_LOG_DIR", str(log_dir))

    code = job_guard.run_guarded(
        name="test-scheduled-timeout",
        argv=[sys.executable, str(script)],
        max_footprint_gb=8.0,
        max_runtime_seconds=0.2,
        grace_seconds=0.2,
        lifecycle_job="fake-scheduled-job",
    )

    rows = [json.loads(line) for line in (log_dir / "auth_activity.jsonl").read_text().splitlines()]
    assert code == 124
    assert [row["event"] for row in rows] == ["job_started", "job_failed"]
    assert rows[1]["detail"]["exit_code"] == 124
    assert rows[1]["detail"]["reason"] == "wall_clock_timeout"


def test_guarded_child_self_report_defers_to_the_guard(isolated_guard, monkeypatch):
    """GH-215: a library-backed self-reporter inside the guarded child must not
    duplicate the pair the guard owns (observed live on daily-synthesis)."""
    script = isolated_guard / "self_report_then_exit.py"
    script.write_text(
        "from rebalance.ingest.auth_log import log_job_completed, log_job_started\n"
        "log_job_started('self-reporting-job')\n"
        "log_job_completed('self-reporting-job', 0.5)\n",
        encoding="utf-8",
    )
    log_dir = isolated_guard / "auth"
    monkeypatch.setenv("REBALANCE_AUTH_LOG_DIR", str(log_dir))
    # The child is a fresh interpreter: point it at this checkout's src even
    # when the host venv has some other rebalance installed.
    monkeypatch.setenv("PYTHONPATH", str(_REPO_ROOT / "src"))

    code = job_guard.run_guarded(
        name="test-self-report-suppressed",
        argv=[sys.executable, str(script)],
        max_footprint_gb=8.0,
        lifecycle_job="fake-scheduled-job",
    )

    rows = [json.loads(line) for line in (log_dir / "auth_activity.jsonl").read_text().splitlines()]
    assert code == 0
    # Exactly the guard's pair — the child's self-report never lands.
    assert [row["event"] for row in rows] == ["job_started", "job_completed"]
    assert all(row["detail"]["job"] == "fake-scheduled-job" for row in rows)


def test_ceiling_trip_records_resource_ceiling_lifecycle(isolated_guard, monkeypatch):
    """GH-215: a resource-ceiling trip records the guard's failed pair, not a silent run."""
    script = isolated_guard / "spin.py"
    script.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    log_dir = isolated_guard / "auth"
    monkeypatch.setenv("REBALANCE_AUTH_LOG_DIR", str(log_dir))
    monkeypatch.setenv("PYTHONPATH", str(_REPO_ROOT / "src"))
    # Force the ceiling branch specifically, independent of what the child does.
    monkeypatch.setattr(job_guard, "tree_footprint_bytes", lambda pid: (10 * GIB, False, 0))

    code = job_guard.run_guarded(
        name="test-ceiling-lifecycle",
        argv=[sys.executable, str(script)],
        max_footprint_gb=1.0,
        poll_seconds=0.1,
        grace_seconds=0.2,
        lifecycle_job="fake-scheduled-job",
    )

    rows = [json.loads(line) for line in (log_dir / "auth_activity.jsonl").read_text().splitlines()]
    assert code == job_guard.EXIT_CEILING_TRIPPED == 4
    assert [row["event"] for row in rows] == ["job_started", "job_failed"]
    assert rows[1]["detail"]["reason"] == "resource_ceiling"


def test_eviction_records_evicted_lifecycle(isolated_guard, monkeypatch):
    """GH-215: a replacing run's SIGTERM (eviction) records reason=evicted."""
    script = isolated_guard / "sleep_forever.py"
    script.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    log_dir = isolated_guard / "auth"
    monkeypatch.setenv("REBALANCE_AUTH_LOG_DIR", str(log_dir))
    monkeypatch.setenv("PYTHONPATH", str(_REPO_ROOT / "src"))

    # The guard installs its own SIGTERM handler before waiting on the child,
    # so a SIGTERM delivered inside that window raises _Evicted there. Fire it
    # well after spawn (handler installed) and well before the child could
    # exit on its own; cancel() is a no-op once fired.
    timer = threading.Timer(0.5, lambda: os.kill(os.getpid(), signal.SIGTERM))
    timer.start()

    try:
        code = job_guard.run_guarded(
            name="test-eviction-lifecycle",
            argv=[sys.executable, str(script)],
            max_footprint_gb=8.0,
            grace_seconds=0.2,
            lifecycle_job="fake-scheduled-job",
        )
    finally:
        timer.cancel()

    rows = [json.loads(line) for line in (log_dir / "auth_activity.jsonl").read_text().splitlines()]
    assert code == 143
    assert [row["event"] for row in rows] == ["job_started", "job_failed"]
    assert rows[1]["detail"]["reason"] == "evicted"


def test_preflight_refusal_has_its_own_exit_code(isolated_guard, monkeypatch):
    """1b. "Refused to start" and "tripped mid-run" must be distinguishable.

    Both were exit 4 until GH-195 P6, which is exactly the ambiguity the test above
    has to work around with a liveness check. A caller could not tell "the machine
    was busy, nothing ran" from "this job blew its budget and was killed" — so a
    supervisor counting non-zero exits as failures quarantined healthy jobs during
    unrelated memory pressure. The preflight now returns EX_TEMPFAIL (75).
    """
    script = isolated_guard / "noop.py"
    script.write_text("pass\n", encoding="utf-8")

    launched: list[int] = []
    real_popen = subprocess.Popen
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **k: (lambda p: (launched.append(p.pid), p)[1])(real_popen(*a, **k)),
    )
    # Starve the machine so the availability preflight refuses.
    monkeypatch.setattr(job_guard, "available_memory_bytes", lambda: 1 * GIB)

    code = job_guard.run_guarded(
        name="test-preflight-refusal",
        argv=[sys.executable, str(script)],
        max_footprint_gb=8.0,
        min_available_gb=16.0,
        poll_seconds=0.1,
    )

    assert code == job_guard.EXIT_REFUSED_TO_START
    assert code != job_guard.EXIT_CEILING_TRIPPED, "refusal must not masquerade as a trip"
    assert not launched, "the child launched despite the preflight refusing"
    assert code in job_guard.DEFERRED_EXIT_CODES


def test_healthy_footprint_does_not_trip(isolated_guard, monkeypatch):
    """2. A process at a healthy footprint does not trip."""
    monkeypatch.setattr(job_guard, "tree_footprint_bytes", lambda pid: (1.4 * GIB, False, 0))
    ceiling = job_guard.MemoryCeiling(max_footprint_bytes=8 * GIB, poll_seconds=0.05)
    ceiling.start()
    time.sleep(0.3)
    ceiling.stop()
    assert ceiling.tripped_reason is None


def test_high_footprint_near_zero_rss(isolated_guard, monkeypatch):
    """3. The 07-27 signature: high phys_footprint with negligible RSS must trip.

    This is the case the RSS-based guard structurally could not see — it ran 233
    jobs on 2026-07-27 without tripping while the machine fell to 0.09 GB free.
    """
    monkeypatch.setattr(job_guard, "tree_footprint_bytes", lambda pid: (10 * GIB, False, 0))
    ceiling = job_guard.MemoryCeiling(max_footprint_bytes=8 * GIB, poll_seconds=0.05)
    ceiling.start()
    time.sleep(0.3)
    ceiling.stop()

    assert ceiling.tripped_reason is not None
    assert "phys_footprint" in ceiling.tripped_reason


def _fake_libc(unreadable_pid: int):
    """A libc whose proc_pid_rusage reports -1 for one pid and a footprint for others."""

    class _ProcPidRusage:
        argtypes = None
        restype = None

        def __call__(self, pid, flavor, buf_ptr):
            if int(pid) == unreadable_pid:
                return -1
            buf_ptr._obj.ri_phys_footprint = 1024 if int(pid) == 1000 else 2048
            return 0

    class _FakeLibc:
        def __init__(self):
            self.proc_pid_rusage = _ProcPidRusage()

    return _FakeLibc()


def test_unreadable_pids_are_skipped_and_counted(isolated_guard, monkeypatch):
    """4. Unreadable pids (rc = -1) are skipped, counted, and never counted as 0.

    Reading a runaway as zero is precisely the blindness this lane exists to
    remove, so an unreadable process must be surfaced rather than absorbed.
    """
    monkeypatch.setattr(sys, "platform", "darwin")

    class _PsOut:
        returncode = 0
        stdout = "1000 1 100\n1001 1000 200\n1002 1000 300\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _PsOut())
    monkeypatch.setattr(ctypes.util, "find_library", lambda name: "fake_c")
    monkeypatch.setattr(ctypes, "CDLL", lambda *a, **k: _fake_libc(unreadable_pid=1001))

    footprint, is_fallback, unreadable = job_guard.tree_footprint_bytes(1000)

    assert not is_fallback
    assert unreadable == 1
    assert footprint == 3072, "an unreadable pid must not silently contribute 0"

    ceiling = job_guard.MemoryCeiling(pid=1000, max_footprint_bytes=1000, poll_seconds=0.1)
    reason = ceiling._check()
    assert reason is not None
    assert "skipped 1 unreadable pids" in reason


def test_rss_fallback_announces_itself(isolated_guard, monkeypatch):
    """5. The RSS fallback works and says so — a degraded metric must never be silent."""
    monkeypatch.setattr(sys, "platform", "linux")

    class _PsOut:
        returncode = 0
        stdout = f"{os.getpid()} 1 2048\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _PsOut())

    footprint, is_fallback, unreadable = job_guard.tree_footprint_bytes(os.getpid())
    assert is_fallback
    assert footprint > 0

    ceiling = job_guard.MemoryCeiling(max_footprint_bytes=1024, poll_seconds=0.1)
    reason = ceiling._check()
    assert reason is not None
    assert "RSS (fallback)" in reason


def test_footprint_env_var_is_read(monkeypatch):
    """6a. The footprint-named setting actually applies."""
    monkeypatch.delenv(job_guard.ENV_MAX_FOOTPRINT_GB_DEPRECATED, raising=False)
    monkeypatch.setenv(job_guard.ENV_MAX_FOOTPRINT_GB, "6.5")
    assert job_guard.env_max_footprint_gb(warn=lambda _m: None) == 6.5


def test_deprecated_rss_env_var_still_applies(monkeypatch):
    """6b. The old RSS-named variable keeps working, with a deprecation warning."""
    monkeypatch.delenv(job_guard.ENV_MAX_FOOTPRINT_GB, raising=False)
    monkeypatch.setenv(job_guard.ENV_MAX_FOOTPRINT_GB_DEPRECATED, "42.0")

    warnings: list[str] = []
    assert job_guard.env_max_footprint_gb(warn=warnings.append) == 42.0
    assert any("deprecated" in w for w in warnings)


def test_footprint_env_var_wins_over_deprecated_alias(monkeypatch):
    """6c. With both set, the footprint-named variable takes precedence."""
    monkeypatch.setenv(job_guard.ENV_MAX_FOOTPRINT_GB, "3.0")
    monkeypatch.setenv(job_guard.ENV_MAX_FOOTPRINT_GB_DEPRECATED, "42.0")
    assert job_guard.env_max_footprint_gb(warn=lambda _m: None) == 3.0


def test_non_numeric_env_var_is_ignored_not_fatal(monkeypatch):
    """6d. A typo must not crash the job the guard exists to protect."""
    monkeypatch.setenv(job_guard.ENV_MAX_FOOTPRINT_GB, "eight")
    monkeypatch.delenv(job_guard.ENV_MAX_FOOTPRINT_GB_DEPRECATED, raising=False)

    warnings: list[str] = []
    assert job_guard.env_max_footprint_gb(warn=warnings.append) is None
    assert any("non-numeric" in w for w in warnings)


def test_max_rss_bytes_still_maps_to_the_footprint_ceiling():
    """The bridge still passes max_rss_gb; that path must keep working."""
    ceiling = job_guard.MemoryCeiling(max_rss_bytes=12345)
    assert ceiling.max_footprint == 12345


def test_deprecated_env_var_reaches_the_actual_ceiling(isolated_guard, monkeypatch):
    """The RSS-named alias must reach the GUARD, not merely parse.

    Codex R3: asserting `env_max_footprint_gb()` returns 42.0 proves the helper
    works, not that anything consumes it. This drives run_guarded and inspects the
    ceiling the MemoryCeiling was actually constructed with.
    """
    monkeypatch.delenv(job_guard.ENV_MAX_FOOTPRINT_GB, raising=False)
    monkeypatch.setenv(job_guard.ENV_MAX_FOOTPRINT_GB_DEPRECATED, "7.0")

    seen: dict[str, int | None] = {}
    real_ceiling_cls = job_guard.MemoryCeiling

    class _Recording(real_ceiling_cls):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            seen["max_footprint"] = self.max_footprint

    monkeypatch.setattr(job_guard, "MemoryCeiling", _Recording)
    script = isolated_guard / "noop.py"
    script.write_text("pass\n", encoding="utf-8")

    job_guard.run_guarded(
        name="test-deprecated-alias",
        argv=[sys.executable, str(script)],
        poll_seconds=0.05,
        grace_seconds=0.2,
    )

    assert seen.get("max_footprint") == int(7.0 * GIB), "the deprecated alias parsed but never reached the ceiling"


def test_compressor_pressure_refuses_to_start(isolated_guard, monkeypatch):
    """Compressor saturation must block a new job even when memory looks available.

    This is the 2026-07-27 condition and the reason the availability question is
    settled rather than deferred: reclaimable pages can look plentiful while the
    kernel is already paying CPU to avoid swapping. Recorded data shows compressor
    at 25-35 GB during the crisis versus a 0.65-0.96 GB median when healthy.

    The machine is paging, which is what distinguishes this from ambient pressure
    (#157) — a compressor that is merely large has ABSORBED pressure; one that is
    large while swap is in use has run out of room to absorb it.
    """
    monkeypatch.setattr(job_guard, "available_memory_bytes", lambda: 32 * GIB)
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: 30 * GIB)
    monkeypatch.setattr(job_guard, "swap_used_bytes", lambda: 6 * GIB)

    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    with pytest.raises(job_guard.MemoryCeilingExceeded) as exc:
        ceiling.preflight()
    assert "compressor" in str(exc.value)
    assert "swap in use" in str(exc.value), "the refusal must name what confirmed it"


def test_compressor_pressure_alone_does_not_refuse_a_healthy_machine(isolated_guard, monkeypatch):
    """GH-157: 179 refusals in 9 days for a 1.9 GB job on a machine that was fine.

    Ambient compressor pressure from unrelated software sat at 17-23 GB against a
    16 GB ceiling while ``memory_pressure`` reported 64% free and ``vm.swapusage``
    0.00M used. The job peaked at 1.86 GB and moved the compressor by 0.23 GB, so
    it neither caused the reading nor added to it — and the gate had no path back
    to healthy, it just waited for other software to release memory.
    """
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: 19 * GIB)  # over the 16 GB ceiling
    monkeypatch.setattr(job_guard, "available_memory_bytes", lambda: 40 * GIB)
    monkeypatch.setattr(job_guard, "swap_used_bytes", lambda: 0)

    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    ceiling.preflight()  # must not raise
    assert ceiling._compressor_trip() is None, "the mid-run check must agree with preflight"


def test_a_high_compressor_still_trips_when_availability_is_gone(isolated_guard, monkeypatch):
    """The second corroborating signal: the availability floor, not just swap."""
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: 30 * GIB)
    monkeypatch.setattr(job_guard, "swap_used_bytes", lambda: 0)
    monkeypatch.setattr(job_guard, "available_memory_bytes", lambda: 1 * GIB)

    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    with pytest.raises(job_guard.MemoryCeilingExceeded) as exc:
        ceiling.preflight()
    assert "below floor" in str(exc.value)


def _laptop_14in(monkeypatch, *, swap_used=1.2 * GIB, swap_total=2 * GIB):
    """The MacBook Pro 14\" measured on 2026-09-27 (GH-296): 24 GB RAM, 2 GB swap file.

    ~50% free, swap flat at ~1.2 GB for hours (residual, not growing), compressor
    9.3 GB against a 6.0 GB ceiling. Every guarded job was refused on this state.
    """
    monkeypatch.setattr(job_guard, "total_memory_bytes", lambda: 24 * GIB)
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: int(9.3 * GIB))
    monkeypatch.setattr(job_guard, "available_memory_bytes", lambda: 6 * GIB)
    monkeypatch.setattr(job_guard, "swap_used_bytes", lambda: int(swap_used))
    monkeypatch.setattr(job_guard, "swap_total_bytes", lambda: int(swap_total), raising=False)


def test_residual_swap_on_a_small_swap_file_is_not_distress(isolated_guard, monkeypatch):
    """GH-296: the absolute 1 GiB swap bar is always true on a 2 GB swap file.

    1.2 GB of static residual swap "confirmed" a compressor reading that the machine
    had absorbed, so preflight refused and the mid-run check would kill. The bar now
    scales with the swap file: 1.2 of 2.0 GB is below 75% and is not distress.
    """
    _laptop_14in(monkeypatch)
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    ceiling.preflight()  # must not raise
    assert ceiling._compressor_trip() is None, "the mid-run check must agree with preflight"


def test_a_nearly_full_swap_file_still_confirms_distress(isolated_guard, monkeypatch):
    """The scaled bar still refuses when the swap file is actually filling up."""
    _laptop_14in(monkeypatch, swap_used=1.8 * GIB)  # 90% of a 2 GB file
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    with pytest.raises(job_guard.MemoryCeilingExceeded) as exc:
        ceiling.preflight()
    assert "swap in use" in str(exc.value)


def test_unreadable_swap_total_keeps_the_legacy_bar(isolated_guard, monkeypatch):
    """#156: an unreadable swap total must not loosen the rule — 1 GiB still applies."""
    _laptop_14in(monkeypatch)
    monkeypatch.setattr(job_guard, "swap_total_bytes", lambda: None, raising=False)
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    with pytest.raises(job_guard.MemoryCeilingExceeded):
        ceiling.preflight()


def test_unreadable_corroboration_fails_closed(isolated_guard, monkeypatch):
    """A blind probe must never be the thing that grants permission (#156)."""
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: 30 * GIB)
    monkeypatch.setattr(job_guard, "swap_used_bytes", lambda: None)
    monkeypatch.setattr(job_guard, "available_memory_bytes", lambda: 0)  # unreadable

    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    with pytest.raises(job_guard.MemoryCeilingExceeded) as exc:
        ceiling.preflight()
    assert "failing closed" in str(exc.value)


def test_an_unreadable_ram_probe_refuses_instead_of_disabling_the_ceiling(isolated_guard, monkeypatch):
    """GH-156: the guard used to fail OPEN when it could not read physical RAM.

    With total == 0 every ceiling is None and the watchdog disables itself, so a run
    that "passed" only because the sysctl was blocked was indistinguishable from a
    genuinely well-behaved one. That also makes any measurement OF the guard
    unreliable, which is why #157's acceptance depends on this.
    """
    monkeypatch.setattr(job_guard, "total_memory_bytes", lambda: 0)

    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    with pytest.raises(job_guard.MemoryCeilingExceeded) as exc:
        ceiling.preflight()
    assert "cannot determine physical RAM" in str(exc.value)


def test_swap_usage_is_parsed_with_its_unit(monkeypatch):
    """sysctl reports a unit alongside the number and it is not always M."""

    class _Out:
        returncode = 0
        stdout = "total = 4096.00M  used = 2.50G  free = 1.00M  (encrypted)"

    monkeypatch.setattr(job_guard.subprocess, "run", lambda *a, **k: _Out())
    monkeypatch.setattr(job_guard.sys, "platform", "darwin")
    assert job_guard.swap_used_bytes() == int(2.5 * GIB)


def test_compressor_below_ceiling_does_not_block(isolated_guard, monkeypatch):
    """A healthy compressor must not refuse work — the free-only mistake, avoided."""
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: 1 * GIB)
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    ceiling.preflight()  # must not raise


def test_compressor_ceiling_is_env_overridable(isolated_guard, monkeypatch):
    """An operator must be able to loosen the compressor ceiling without a code change."""
    monkeypatch.setenv(job_guard.ENV_MAX_COMPRESSOR_GB, "40")
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: 30 * GIB)
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    assert ceiling.max_compressor == int(40 * GIB)
    ceiling.preflight()  # 30 GB is now under the raised ceiling


def test_available_memory_counts_reclaimable_pages_not_just_free(monkeypatch):
    """A healthy Mac with little FREE but lots of INACTIVE must not read as starved.

    Regression test for the defect this lane briefly shipped: `available_memory_bytes`
    was narrowed to free-only without re-tuning the floor that consumes it. On a
    healthy machine (free 1.59 GB, inactive 21.46 GB, speculative 0.93 GB) that
    reported 1.58 GB against a 7.68 GB floor, so the preflight refused EVERY guarded
    job. macOS keeps cache in inactive by design, so free alone is not availability.

    Nothing caught it because every other test pins this function to a healthy
    constant for determinism — correct in itself, but it left the real
    implementation with no coverage at all.
    """
    monkeypatch.setattr(sys, "platform", "darwin")

    # Real vm_stat shape, 16 KiB pages: the healthy-machine numbers above.
    class _VmStatOut:
        returncode = 0
        stdout = (
            "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
            "Pages free:                              104000.\n"
            "Pages active:                            874626.\n"
            "Pages inactive:                         1406000.\n"
            "Pages speculative:                        61000.\n"
        )

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _VmStatOut())

    available = job_guard.available_memory_bytes()
    free_only = 104000 * 16384

    assert available > free_only, "inactive/speculative must count as reclaimable"
    assert available == (104000 + 1406000 + 61000) * 16384

    # And the consequence that actually matters: this machine must clear the floor.
    floor = max(
        int(FAKE_TOTAL_RAM * job_guard.DEFAULT_MIN_AVAILABLE_FRACTION),
        job_guard.MIN_AVAILABLE_FLOOR,
    )
    assert available > floor, (
        f"a healthy machine reads as starved: {available / GIB:.2f} GB < "
        f"{floor / GIB:.2f} GB floor — the guard would refuse every job"
    )


# --------------------------------------------------------------------------- #
# GH-296: per-device settings (memory checks only; lock and timeout always on)
# --------------------------------------------------------------------------- #


def _write_device_config(tmp_path, monkeypatch, section) -> Path:
    path = tmp_path / "rbos.config"
    path.write_text(json.dumps({"vault_path": "/x", "job_guard": section}), encoding="utf-8")
    monkeypatch.setenv("REBALANCE_CONFIG", str(path))
    return path


def _starved(monkeypatch):
    """A machine every memory check would refuse: paging hard, nothing available."""
    monkeypatch.setattr(job_guard, "compressor_bytes", lambda: 30 * GIB)
    monkeypatch.setattr(job_guard, "swap_used_bytes", lambda: 20 * GIB)
    monkeypatch.setattr(job_guard, "available_memory_bytes", lambda: 1 * GIB)


def test_settings_default_to_on_with_no_overrides(isolated_guard):
    settings = job_guard.guard_settings()
    assert settings["memory_guard"] == {"value": True, "source": "default"}
    assert all(settings[k]["value"] is None for k in ("max_compressor_gb", "swap_distress_gb", "min_available_gb"))


def test_memory_guard_off_skips_memory_checks_and_says_so(isolated_guard, monkeypatch):
    _write_device_config(isolated_guard, monkeypatch, {"memory_guard": "off"})
    _starved(monkeypatch)
    lines: list[str] = []
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05, log=lines.append)
    ceiling.preflight()  # must not raise
    assert ceiling._check() is None, "no mid-run trip either"
    assert any("memory checks disabled by device config" in m and "lock and timeout still active" in m for m in lines)


def test_memory_guard_off_keeps_the_single_instance_lock(isolated_guard, monkeypatch):
    """The lock is the GH-172 defence; turning memory checks off must not touch it."""
    _write_device_config(isolated_guard, monkeypatch, {"memory_guard": "off"})
    with job_guard.guard("gh296-lock", poll_seconds=0.05, log=lambda m: None):
        with pytest.raises(job_guard.InstanceConflict):
            with job_guard.guard("gh296-lock", poll_seconds=0.05, log=lambda m: None):
                pass


def test_memory_guard_off_keeps_the_wall_clock_timeout_and_logs_off(isolated_guard, monkeypatch):
    _write_device_config(isolated_guard, monkeypatch, {"memory_guard": "off"})
    _starved(monkeypatch)
    code = job_guard.run_guarded(
        "gh296-timeout",
        [sys.executable, "-c", "import time; time.sleep(30)"],
        poll_seconds=0.05,
        grace_seconds=0.2,
        max_runtime_seconds=0.5,
    )
    assert code == job_guard.EXIT_WALL_CLOCK_TIMEOUT
    rows = [json.loads(line) for line in (isolated_guard / "job_rss.jsonl").read_text().splitlines()]
    assert rows[-1]["memory_guard"] == "off", "job_rss.jsonl must record that the run was unguarded"


def test_device_swap_distress_override_applies(isolated_guard, monkeypatch):
    """An explicit per-device swap bar replaces the scaled one."""
    _laptop_14in(monkeypatch)  # 1.2 GB used of 2 GB: passes the scaled bar
    _write_device_config(isolated_guard, monkeypatch, {"swap_distress_gb": 1.0})
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    with pytest.raises(job_guard.RefusedToStart):
        ceiling.preflight()


def test_env_wins_over_device_config(isolated_guard, monkeypatch):
    _write_device_config(isolated_guard, monkeypatch, {"memory_guard": "off", "max_compressor_gb": 3})
    monkeypatch.setenv("REBALANCE_JOB_GUARD_MEMORY", "on")
    monkeypatch.setenv(job_guard.ENV_MAX_COMPRESSOR_GB, "7")
    settings = job_guard.guard_settings()
    assert settings["memory_guard"] == {"value": True, "source": "env REBALANCE_JOB_GUARD_MEMORY"}
    assert settings["max_compressor_gb"]["value"] == 7.0
    assert settings["max_compressor_gb"]["source"].startswith("env ")


@pytest.mark.parametrize(
    "section, key",
    [
        ({"memory_guard": "sometimes"}, "memory_guard"),
        ({"swap_distress_gb": "lots"}, "swap_distress_gb"),
        ({"min_available_gb": -2}, "min_available_gb"),
        ({"max_compressor_gb": True}, "max_compressor_gb"),
    ],
)
def test_invalid_values_fall_back_to_default_loudly(isolated_guard, monkeypatch, section, key):
    _write_device_config(isolated_guard, monkeypatch, section)
    warnings: list[str] = []
    settings = job_guard.guard_settings(warn=warnings.append)
    assert settings[key]["source"] == "default"
    assert settings["memory_guard"]["value"] is True, "an invalid value must never switch checks off"
    assert any(key in w and "using default" in w for w in warnings)


def test_a_non_object_section_is_ignored_loudly(isolated_guard, monkeypatch):
    _write_device_config(isolated_guard, monkeypatch, "off")
    warnings: list[str] = []
    settings = job_guard.guard_settings(warn=warnings.append)
    assert settings["memory_guard"]["value"] is True
    assert any("expected an object" in w for w in warnings)


def test_device_config_path_is_the_guards_own_checkout_by_default(monkeypatch):
    """Not cwd-based: agent-spawned runs from any directory resolve the same file."""
    monkeypatch.delenv("REBALANCE_CONFIG", raising=False)
    monkeypatch.chdir("/")
    assert job_guard.device_config_path() == _REPO_ROOT / "temp" / "rbos.config"


def test_ambient_pressure_is_logged_once_per_run_not_every_poll(isolated_guard, monkeypatch):
    """GH-296: a 194 s run on the 14\" wrote the same "not in distress" line 39 times."""
    _laptop_14in(monkeypatch)
    lines: list[str] = []
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05, log=lines.append)
    ceiling.preflight()
    for _ in range(5):
        assert ceiling._check() is None
    assert sum("not in distress" in line for line in lines) == 1


@pytest.mark.parametrize("via_env", [True, False])
@pytest.mark.parametrize("raw", ["nan", "inf", "-inf", "1e308"])
def test_non_finite_or_huge_values_fall_back_instead_of_crashing(isolated_guard, monkeypatch, via_env, raw):
    """GH-296 final QA F1: a bad number must warn and use the default, never crash the job."""
    if via_env:
        monkeypatch.setenv("REBALANCE_JOB_GUARD_SWAP_DISTRESS_GB", raw)
        section = {"min_available_gb": raw}
    else:
        section = {"swap_distress_gb": raw, "min_available_gb": raw, "max_compressor_gb": raw}
    _write_device_config(isolated_guard, monkeypatch, section)
    warnings: list[str] = []
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05, log=warnings.append)  # must not raise
    assert ceiling.swap_distress_override is None
    assert ceiling.min_available == max(int(FAKE_TOTAL_RAM * 0.12), job_guard.MIN_AVAILABLE_FLOOR)
    assert any("using default" in w for w in warnings)


def test_a_valid_finite_override_still_applies(isolated_guard, monkeypatch):
    _write_device_config(isolated_guard, monkeypatch, {"swap_distress_gb": 1.5, "min_available_gb": 2})
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05)
    assert ceiling.swap_distress_override == int(1.5 * GIB)
    assert ceiling.min_available == 2 * GIB


@pytest.mark.parametrize(
    "raw, expected",
    [(False, False), (True, True), (0, False), (1, True), (None, True), ("OFF", False), ("on", True)],
)
def test_memory_guard_accepts_json_bool_int_and_null(isolated_guard, monkeypatch, raw, expected):
    """JSON false/0/"off" switch the checks off; true/1/"on" on; null means unset (default on)."""
    _write_device_config(isolated_guard, monkeypatch, {"memory_guard": raw})
    assert job_guard.guard_settings()["memory_guard"]["value"] is expected


@pytest.mark.parametrize("key", ["swap_distress_gb", "min_available_gb", "max_compressor_gb"])
@pytest.mark.parametrize("memory_guard", ["on", "off"])
def test_an_overflowing_json_integer_falls_back_instead_of_crashing(isolated_guard, monkeypatch, key, memory_guard):
    """GH-296 final QA r3 F1: a valid JSON integer too large for a float must not crash."""
    path = isolated_guard / "rbos.config"
    path.write_text(json.dumps({"job_guard": {key: 10**400, "memory_guard": memory_guard}}), encoding="utf-8")
    monkeypatch.setenv("REBALANCE_CONFIG", str(path))
    warnings: list[str] = []
    ceiling = job_guard.MemoryCeiling(poll_seconds=0.05, log=warnings.append)  # must not raise
    assert ceiling.settings[key] == {"value": None, "source": "default"}
    assert any(key in w and "using default" in w for w in warnings)
    report, _ = job_guard.settings_report()
    assert report

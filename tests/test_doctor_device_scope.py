"""Regression coverage for device-owned doctor checks."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from rebalance.doctor import (
    ERROR,
    FAIL,
    OK,
    WARN,
    WARNING,
    _DeviceScope,
    _DEVICE_SCOPE_REGISTRY,
    _check_pulse_collectors,
    _check_scheduler_liveness,
)
from rebalance.ingest.pulse_health import CollectorHealth


def _health(device_id: str, *, age_hours: float | None, state: str = "STALE") -> CollectorHealth:
    health = CollectorHealth(
        device_id=device_id,
        device_name=device_id,
        last_scan_utc=None,
    )
    health.age_hours = age_hours
    health.state = state
    return health


def _write_policy(directory: Path, jobs: list[str]) -> Path:
    rows = "\n".join(f"| `{job}` | hourly | `scripts/{job}.sh` | work | — | output |" for job in jobs)
    policy = directory / "SCHEDULER.md"
    policy.write_text(
        "\n".join(
            [
                "# Scheduler Policy",
                "",
                "| Job (label suffix) | Cadence | Wrapper | Work | Prerequisites | Outputs |",
                "|---|---|---|---|---|---|",
                rows,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return policy


def test_foreign_pulse_collector_is_informational_not_a_warning() -> None:
    health = _health("noels-mbp-16-m1-pro", age_hours=48, state="ALERT")
    with patch("rebalance.ingest.pulse_health.read_collector_health", return_value=[health]):
        checks = _check_pulse_collectors(current_device_id="noels-mac-studio")

    assert checks[0].status == OK  # the foreign-device assertion
    assert "not applicable" in checks[0].detail


def test_stale_collector_still_warns_on_its_own_device() -> None:
    health = _health("noels-mbp-16-m1-pro", age_hours=25, state="ALERT")
    with patch("rebalance.ingest.pulse_health.read_collector_health", return_value=[health]):
        checks = _check_pulse_collectors(current_device_id="noels-mbp-16-m1-pro")

    assert checks[0].status == WARN


def test_intermittent_laptop_window_differs_from_always_on_collector() -> None:
    laptop = _health("noels-macbook-pro-14", age_hours=7)
    workstation = _health("noels-mac-studio", age_hours=7)
    with patch(
        "rebalance.ingest.pulse_health.read_collector_health",
        return_value=[laptop, workstation],
    ):
        laptop_check = _check_pulse_collectors(current_device_id="noels-macbook-pro-14")[0]
        workstation_check = _check_pulse_collectors(current_device_id="noels-mac-studio")[1]

    assert laptop_check.status == OK
    assert "intermittent-device window 24h" in laptop_check.detail
    assert workstation_check.status == WARN


def _collector_checks(devices: list[CollectorHealth], current: str, patterns: list[str] | None = None):
    with (
        patch("rebalance.ingest.pulse_health.read_collector_health", return_value=devices),
        patch("rebalance.ingest.config.get_health_notice_patterns", return_value=patterns or []),
    ):
        return _check_pulse_collectors(current_device_id=current)


# GH-338: a device silent past 72h is a FAIL on every other Mac, so the
# health-check reporter (which files raw status `error` only) files it.


def test_scoped_foreign_collector_silent_past_72h_fails_from_another_mac() -> None:
    import shlex

    health = _health("noels-mbp-16-m1-pro", age_hours=80, state="ALERT")
    health.device_name = "Noel's MBP 16\" M1 Pro"
    check = _collector_checks([health], "noels-mac-studio")[0]

    assert check.status == FAIL
    assert check.severity == ERROR
    assert "silent >72h — reported from noels-mac-studio" in check.detail
    command = check.hint.split("acknowledge with: ", 1)[1]
    assert shlex.split(command) == ["rebalance", "config", "add-health-notice", check.name]


def test_foreign_silence_bound_is_strictly_greater_than_72h() -> None:
    at_bound = _collector_checks([_health("noels-mbp-16-m1-pro", age_hours=72.0, state="ALERT")], "noels-mac-studio")
    past = _collector_checks([_health("noels-mbp-16-m1-pro", age_hours=72.1, state="ALERT")], "noels-mac-studio")

    assert at_bound[0].status == OK
    assert "not applicable" in at_bound[0].detail
    assert past[0].status == FAIL


def test_unscoped_foreign_collector_silent_past_72h_is_not_capped() -> None:
    capped = _collector_checks([_health("mini", age_hours=30, state="ALERT")], "noels-mac-studio")[0]
    silent = _collector_checks([_health("mini", age_hours=80, state="ALERT")], "noels-mac-studio")[0]

    assert (capped.status, capped.severity) == (WARN, WARNING)  # GH-5 Phase F cap, unchanged
    assert (silent.status, silent.severity) == (FAIL, ERROR)


def test_acknowledged_silent_foreign_collector_is_demoted_to_a_notice() -> None:
    from datetime import datetime, timezone

    from rebalance.health import compute_health_status

    health = _health("noels-mbp-16-m1-pro", age_hours=80, state="ALERT")
    check = _collector_checks([health], "noels-mac-studio", patterns=["fleet:noels-mbp"])[0]

    assert (check.status, check.severity) == (WARN, WARNING)
    verdict = compute_health_status([check], {}, datetime.now(timezone.utc), notice_patterns=["fleet:noels-mbp"])
    assert check in verdict.notices
    assert check not in verdict.problems


def test_own_device_and_never_pushed_foreign_rows_are_unchanged() -> None:
    own = _collector_checks([_health("noels-mac-studio", age_hours=80, state="ALERT")], "noels-mac-studio")[0]
    never = _collector_checks([_health("noels-mbp-16-m1-pro", age_hours=None, state="NO PUSHES")], "noels-mac-studio")[
        0
    ]

    assert (own.status, own.severity) == (WARN, ERROR)
    assert "silent >" not in own.detail
    assert never.status == OK
    assert "not applicable" in never.detail


def test_device_scoped_job_stays_informational_even_with_a_stale_plist() -> None:
    """GH-59: a laptop that does not own a job must not go red over a leftover plist.

    A device-scoped job. Phase 2 made "plist present but not loaded" a FAIL,
    using the plist as this machine's install record — so a plist left behind
    by a repo move or a restored backup on a NON-owner device is exactly the
    case that could turn that laptop's doctor gate red for a job it was never
    supposed to run. The device-scope branch must win, and it must win
    *before* the local-plist branch is reached.

    GH-74: the production job this originally exercised (git-pulse-daily-
    synthesis) was merged into the unscoped daily-synthesis and no longer
    carries a _DEVICE_SCOPE_REGISTRY entry, so this test injects a synthetic
    one via patch.dict — the mechanism itself still needs live coverage even
    though the real job that used to demonstrate it is gone.
    """
    example_scope = {("scheduler", "example-scoped-job"): _DeviceScope(frozenset({"noels-mbp-16-m1-pro"}))}
    with TemporaryDirectory() as tmp, patch.dict(_DEVICE_SCOPE_REGISTRY, example_scope):
        root = Path(tmp)
        policy = _write_policy(root, ["example-scoped-job"])
        agents = root / "LaunchAgents"
        agents.mkdir()
        # The stale plist: present on disk, absent from launchctl.
        (agents / "com.rebalance-os.example-scoped-job.plist").write_text("x", encoding="utf-8")

        checks = _check_scheduler_liveness(
            policy,
            "",
            current_device_id="noels-mac-studio",  # NOT the owner
            agents_dir=agents,
        )

    assert len(checks) == 1
    assert checks[0].status == OK, "a non-owner device must not fail on someone else's job"
    assert checks[0].severity != ERROR, "must not escalate the verdict on a non-owner device"


def test_device_scoped_job_with_a_stale_plist_still_fails_on_its_OWNER() -> None:
    """The other half: on the machine that DOES own the job, the same stale
    plist is a real failure. Without this, the test above could pass simply
    because the plist signal never fires."""
    example_scope = {("scheduler", "example-scoped-job"): _DeviceScope(frozenset({"noels-mbp-16-m1-pro"}))}
    with TemporaryDirectory() as tmp, patch.dict(_DEVICE_SCOPE_REGISTRY, example_scope):
        root = Path(tmp)
        policy = _write_policy(root, ["example-scoped-job"])
        agents = root / "LaunchAgents"
        agents.mkdir()
        (agents / "com.rebalance-os.example-scoped-job.plist").write_text("x", encoding="utf-8")

        checks = _check_scheduler_liveness(
            policy,
            "",
            current_device_id="noels-mbp-16-m1-pro",  # the owner
            agents_dir=agents,
        )

    assert len(checks) == 1
    assert checks[0].status == FAIL


def test_unscoped_scheduler_job_keeps_existing_missing_job_warning() -> None:
    with TemporaryDirectory() as tmp:
        policy = _write_policy(Path(tmp), ["future-job"])
        checks = _check_scheduler_liveness(
            policy,
            "",
            current_device_id="noels-mac-studio",
        )

    assert checks[0].status == WARN

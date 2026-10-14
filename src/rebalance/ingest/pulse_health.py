"""First-class read of git-pulse collector health.

Promotes the *health-read* path out of ``experimental/git-pulse/health-check.py``
so ``doctor`` (and any other consumer) can answer "did a collector break?"
without shelling out to the experimental CLI or parsing its text output. This
is what lets a *broken* collector (a degraded/stale git-pulse scan) show up in
``rebalance doctor`` right next to a *de-authorized* one — both in one place.

Source of truth: the per-device YAML the git-pulse collector writes to
``{sync_repo_dir}/devices/<device_id>.yaml`` (fields ``last_scan_utc``,
``scan_status``, ``repo_scan_failures``, ``scan_failure_examples``). We resolve
``{sync_repo_dir}`` from rebalance's own ``pulse_target_path`` first (the
configured git-pulse-sync working tree), then fall back to the git-pulse
``config.sh``. Legacy reading is pure flat YAML. Opted-in fleet publishers additionally verify delivered status/page with bounded local Git object reads.

Scope note: this is a *targeted* promotion of the health-read path only. The
full git-pulse migration (collect.sh, recap, launchd jobs) remains Phase 9. The
canonical ``classify()`` + device-read logic now lives here; the experimental
``health-check.py`` should import from this module when that migration happens.
The ``classify`` thresholds and states mirror that script exactly.
"""

from __future__ import annotations

import hashlib
import json

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from rebalance.lib import time_ops
from rebalance.lib.time_ops import parse_utc_iso

# Mirror experimental/git-pulse/health-check.py defaults.
WARN_HOURS = 3.0
ALERT_HOURS = 24.0


# 23:00 -> 06:00 gap (7h), fall-back DST (1h), producer budget (0.5h),
# collector cadence (1h) and network/stagger grace (0.5h). Explicit failures
# and queued output remain immediately visible; this is only silent-job aging.
MAX_SCHEDULED_RENDER_AGE_HOURS = 10.0


@dataclass
class CollectorHealth:
    """One device's git-pulse collector health, post-classification."""

    device_id: str
    device_name: str
    last_scan_utc: datetime | None
    scan_status: str = "ok"
    repo_scan_failures: int = 0
    scan_failure_examples: str = ""
    fleet_mode: bool = False
    last_pulse_publish_utc: datetime | None = None
    last_pulse_exit: int | None = None
    pulse_delivery_pending: bool = False
    pulse_delivery_reason: str = ""
    # Filled by classify():
    state: str = ""  # ALIVE | ALIVE_NOT_PUBLISHING | STALE | ALERT | DEGRADED | NO PUSHES
    priority: int = 3  # lower = worse (sorts first)
    age_hours: float | None = None

    @property
    def healthy(self) -> bool:
        return self.state == "ALIVE"


# ---------------------------------------------------------------------------
# Flat-YAML helpers (ported from health-check.py — no pyyaml dependency)
# ---------------------------------------------------------------------------


def _yaml_value(path: Path, key: str) -> str:
    prefix = f"{key}: "
    for raw_line in path.read_text().splitlines():
        if not raw_line.startswith(prefix):
            continue
        value = raw_line[len(prefix) :].strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        return value.replace('\\"', '"').replace("\\\\", "\\")
    return ""


def _int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Sync-repo resolution
# ---------------------------------------------------------------------------


def resolve_sync_repo_dir() -> Path | None:
    """Locate the git-pulse sync repo (the dir containing ``devices/``).

    Prefers rebalance's own ``pulse_target_path`` (clean, no experimental
    coupling); falls back to the git-pulse ``config.sh``. Returns the repo dir
    only when its ``devices/`` subdir exists, else None.
    """
    # 1. rebalance config — the configured git-pulse-sync working tree.
    try:
        from rebalance.ingest.config import get_pulse_config

        target = (get_pulse_config() or {}).get("pulse_target_path")
        if target:
            cand = Path(target).expanduser()
            if (cand / "devices").is_dir():
                return cand
    except Exception:  # noqa: BLE001 — config unreadable; try the fallback
        pass

    # 2. git-pulse config.sh — `sync_repo_dir=...`, default `$CONFIG_DIR/repo`.
    config_dir = Path(
        os.environ.get("GIT_PULSE_CONFIG_DIR")
        or os.environ.get("GIT_HISTORY_CONFIG_DIR")
        or (Path.home() / ".config" / "git-pulse")
    )
    config_file = config_dir / "config.sh"
    if config_file.is_file():
        try:
            for line in config_file.read_text().splitlines():
                match = re.match(r"\s*(?:export\s+)?sync_repo_dir=(.+)", line)
                if not match:
                    continue
                val = match.group(1).strip().strip('"').strip("'")
                val = val.replace("${CONFIG_DIR}", str(config_dir)).replace("$CONFIG_DIR", str(config_dir))
                cand = Path(os.path.expanduser(os.path.expandvars(val)))
                if (cand / "devices").is_dir():
                    return cand
        except Exception:  # noqa: BLE001
            pass
        default = config_dir / "repo"
        if (default / "devices").is_dir():
            return default
    return None


# ---------------------------------------------------------------------------
# Classification + read
# ---------------------------------------------------------------------------


def classify(
    health: CollectorHealth,
    now: datetime,
    warn_hours: float = WARN_HOURS,
    alert_hours: float = ALERT_HOURS,
) -> CollectorHealth:
    """Set ``state`` / ``priority`` / ``age_hours`` in place and return it.

    Mirrors experimental/git-pulse/health-check.py:classify — lower priority is
    worse. DEGRADED (repo scan failures) and ALERT (past alert window) are the
    worst tier (1); STALE is 2; ALIVE is 3; never-pushed is 0.
    """
    last = health.last_scan_utc
    if last is None:
        health.state, health.priority, health.age_hours = "NO PUSHES", 0, None
        return health
    hours = (now - last).total_seconds() / 3600
    health.age_hours = hours
    if health.repo_scan_failures > 0 or health.scan_status == "degraded":
        health.state, health.priority = "DEGRADED", 1
    elif hours > alert_hours:
        health.state, health.priority = "ALERT", 1
    elif hours > warn_hours:
        health.state, health.priority = "STALE", 2
    elif health.fleet_mode and (
        health.pulse_delivery_pending
        or health.last_pulse_exit != 0
        or health.last_pulse_publish_utc is None
        or not -1 / 60 <= (now - health.last_pulse_publish_utc).total_seconds() / 3600 <= MAX_SCHEDULED_RENDER_AGE_HOURS
    ):
        health.state, health.priority = "ALIVE_NOT_PUBLISHING", 2
        if health.last_pulse_exit not in (None, 0):
            health.pulse_delivery_reason = f"render failed (exit {health.last_pulse_exit})"
            if health.pulse_delivery_pending:
                health.pulse_delivery_reason += "; awaiting collector delivery"
        elif not health.pulse_delivery_reason:
            if health.last_pulse_publish_utc is None:
                health.pulse_delivery_reason = "no verified delivered status"
            elif health.pulse_delivery_pending:
                health.pulse_delivery_reason = "queued, awaiting collector"
            else:
                age = (now - health.last_pulse_publish_utc).total_seconds() / 3600
                health.pulse_delivery_reason = f"delivered render {age:.1f}h old; outside scheduled freshness bound"
    else:
        health.state, health.priority = "ALIVE", 3
    return health


def read_collector_health(
    sync_repo_dir: Path | None = None,
    now: datetime | None = None,
    *,
    warn_hours: float = WARN_HOURS,
    alert_hours: float = ALERT_HOURS,
) -> list[CollectorHealth]:
    """Read + classify every device under ``{sync_repo_dir}/devices/*.yaml``.

    Returns ``[]`` when git-pulse is not configured or has no device YAMLs —
    callers treat that as "nothing to report". Sorted worst-first.
    """
    now = now or time_ops.now_utc()
    sync_repo_dir = sync_repo_dir or resolve_sync_repo_dir()
    if sync_repo_dir is None:
        return []
    devices_dir = Path(sync_repo_dir) / "devices"
    if not devices_dir.is_dir():
        return []

    out: list[CollectorHealth] = []
    for yaml_path in sorted(devices_dir.glob("*.yaml")):
        device_id = _yaml_value(yaml_path, "device_id") or yaml_path.stem
        health = CollectorHealth(
            device_id=device_id,
            device_name=_yaml_value(yaml_path, "device_name") or device_id,
            last_scan_utc=parse_utc_iso(_yaml_value(yaml_path, "last_scan_utc")),
            scan_status=_yaml_value(yaml_path, "scan_status") or "ok",
            repo_scan_failures=_int(_yaml_value(yaml_path, "repo_scan_failures")),
            scan_failure_examples=_yaml_value(yaml_path, "scan_failure_examples"),
        )
        health.fleet_mode = _yaml_value(yaml_path, "fleet_mode") == "true"
        if health.fleet_mode:
            # Only local Git object reads, each bounded to five seconds. Upstream
            # evidence cannot be replaced by a dirty/queued local success.
            from rebalance.lib.git_ops import run_git

            relative = f"devices/{device_id}/status/pulse-sync.json"
            try:
                if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", device_id):
                    raise ValueError("unsafe fleet device identity")
                delivered = run_git(Path(sync_repo_dir), "show", f"@{{u}}:{relative}", timeout=5)
                if delivered.returncode or len(delivered.stdout) > 65536:
                    raise ValueError("upstream status unavailable")
                status = json.loads(delivered.stdout)
                if (
                    status.get("device_id") != device_id
                    or status.get("job") != "pulse-sync"
                    or status.get("schema_version") != 1
                    or type(status.get("last_exit")) is not int
                ):
                    raise ValueError("invalid delivered status")
                health.last_pulse_exit = status["last_exit"]
                health.last_pulse_publish_utc = parse_utc_iso(status.get("last_render_success_utc"))
                payload_path = f"devices/{device_id}/live-pulse.md"
                if status.get("payload_path") != payload_path:
                    raise ValueError("invalid delivered payload path")
                payload = run_git(Path(sync_repo_dir), "show", f"@{{u}}:{payload_path}", timeout=5)
                if payload.returncode or hashlib.sha256(payload.stdout.encode()).hexdigest() != status.get(
                    "payload_sha256"
                ):
                    raise ValueError("delivered page and status do not match")
                local = Path(sync_repo_dir) / relative
                if local.is_symlink():
                    raise ValueError("symlinked status")
                if local.exists():
                    local_status = json.loads(local.read_text())
                    if (
                        not isinstance(local_status, dict)
                        or local_status.get("device_id") != device_id
                        or local_status.get("job") != "pulse-sync"
                        or type(local_status.get("last_exit")) is not int
                    ):
                        raise ValueError("invalid local status")
                    health.pulse_delivery_pending = local_status != status
                    if health.pulse_delivery_pending:
                        health.last_pulse_exit = local_status["last_exit"]
            except Exception:  # doctor remains conservative on unreadable fleet evidence
                # Conservative for opted-in publishers: unverifiable is not ALIVE.
                health.pulse_delivery_pending = True
                health.pulse_delivery_reason = "delivery evidence unavailable"
        classify(health, now, warn_hours, alert_hours)
        out.append(health)

    out.sort(key=lambda h: (h.priority, h.device_name.lower()))
    return out

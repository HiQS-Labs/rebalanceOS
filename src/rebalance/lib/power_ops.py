"""Power source monitoring and battery-aware throttling (GH-201).

Adopts GitCanary's PowerMonitor posture: on macOS portable hardware, detect
whether the system is operating on battery power to defer intensive ML/embedding
workloads until AC power is restored, preventing thermal throttling and battery
depletion.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Literal

PowerSource = Literal["battery", "ac", "unknown"]


def get_power_source() -> PowerSource:
    """Detect current system power source ('battery', 'ac', or 'unknown').

    Environment variable overrides (useful for testing and containerized sandboxes):
      - REBALANCE_FORCE_BATTERY=1 -> returns 'battery'
      - REBALANCE_FORCE_AC=1 -> returns 'ac'
      - REBALANCE_POWER_SOURCE='battery'|'ac'|'unknown' -> returns normalized value

    On macOS (darwin), queries `pmset -g batt`. If non-macOS, command fails,
    or output is indeterminate, returns 'unknown'.
    """
    env_source = os.environ.get("REBALANCE_POWER_SOURCE", "").strip().lower()
    if env_source in ("battery", "batt"):
        return "battery"
    if env_source in ("ac", "charger", "plugged"):
        return "ac"
    if env_source == "unknown":
        return "unknown"

    if os.environ.get("REBALANCE_FORCE_BATTERY") == "1":
        return "battery"
    if os.environ.get("REBALANCE_FORCE_AC") == "1":
        return "ac"

    if sys.platform != "darwin":
        return "unknown"

    try:
        proc = subprocess.run(
            ["pmset", "-g", "batt"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if proc.returncode != 0:
            return "unknown"
        stdout = proc.stdout.lower()
        if "battery power" in stdout or "'battery power'" in stdout:
            return "battery"
        if "ac power" in stdout or "'ac power'" in stdout:
            return "ac"
    except (OSError, subprocess.SubprocessError):
        return "unknown"

    return "unknown"


def is_on_battery() -> bool:
    """Return True if the machine is verified to be running on battery power.

    Returns False for AC power, non-macOS platforms, or unknown/errored states
    (safe default to AC behavior).
    """
    return get_power_source() == "battery"


def power_source_name() -> str:
    """Return human-readable power source description for status reports."""
    src = get_power_source()
    if src == "battery":
        return "Battery Power"
    if src == "ac":
        return "AC Power"
    return "Unknown"


def should_defer_embeddings() -> bool:
    """Return True if embeddings should be deferred under current power conditions.

    Evaluates:
      1. Config `defer_embeddings_on_battery` (defaults to True)
      2. Current power source via `is_on_battery()`
    Unknown power, disabled config, or AC power return False.
    """
    try:
        from rebalance.ingest.config import get_defer_embeddings_on_battery

        if not get_defer_embeddings_on_battery():
            return False
    except Exception:
        # If config is unavailable, default to True (enabled)
        pass

    return is_on_battery()

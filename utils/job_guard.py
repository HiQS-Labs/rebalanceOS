#!/usr/bin/env python3
"""Single-instance + memory-ceiling guard for long-running local jobs (GH-172).

Context — on 2026-07-19 the Mac Studio hard kernel-panicked (AppleARMWatchdogTimer,
90s watchdogd starvation) because three unbounded Python embedding runs stacked to
~90 GB resident on a 68.7 GB machine. Nothing in either embedding stack prevented
concurrent invocation, and nothing aborted before the VM compressor saturated.

This module supplies the two missing primitives, independent of any one job:

  1. SingleInstanceLock — an advisory ``flock`` on a named lockfile. A second run
     either REFUSES (default) or REPLACES the incumbent. Stale locks left by a
     killed process are reclaimed automatically.
  2. MemoryCeiling — a watchdog thread that samples the guarded process tree's
     ``phys_footprint``, the system-available memory, *and* the memory compressor,
     and aborts the job CLEANLY (SIGTERM, then SIGKILL after a grace period)
     before the machine starts thrashing.

     The metric is footprint, NOT RSS (GH-219 Lane 4). RSS cannot see Metal/GPU
     buffers, which are charged to phys_footprint as ``iokit``: on 2026-07-27 the
     offending processes held ~46.9 GB of footprint while reporting ~0.08 GB RSS,
     so an RSS-based guard ran 233 jobs and tripped zero times while the machine
     fell to 0.09 GB free. Do not reintroduce RSS semantics here; RSS survives
     only as a fallback where phys_footprint is unavailable, and says so when used.

Deliberately stdlib-only (no psutil): this has to run under the system python3,
inside launchd jobs, and inside the rebalance venv without an install step.

Two usage modes.

In-process — wrap the body of a Python job::

    from job_guard import guard

    with guard("ask-self-ingest", max_rss_gb=24):
        run_the_ingest()

Wrapper — guard any command, including non-Python ones. The ceiling then covers
the whole child process tree::

    python3 utils/job_guard.py --name ask-self-ingest --max-rss-gb 24 -- \
        python3 ask_self/ask_self_ingest.py --repo .

Exit codes in wrapper mode:
    0    child exited 0
    3    another instance holds the lock (``--on-conflict refuse``)
    4    memory ceiling tripped MID-RUN; the child launched and was terminated
    75   refused to start: the machine was already starved (child NEVER launched)
    143  evicted by a later ``--on-conflict replace`` run (child tree reaped)
    else the child's own exit status

3 and 75 both mean *deferred* — nothing ran and nothing is broken, so a supervisor
must not count them as job failures. 4 means the job actually misbehaved. These
were both 4 until GH-195 P6, which made them indistinguishable to a caller: three
"machine was busy" refusals silently latched a 3-Eyes circuit breaker and killed a
healthy job for a day. 75 is ``EX_TEMPFAIL`` from ``sysexits.h`` — "temporary
failure, the user is invited to retry" — chosen over a low number because it is far
less likely to collide with a real child's exit status.

Installed on the embedding path as of GH-172. #174 landed this module with zero
callers; the wiring followed once attribution was resolved. The 45 GB belonged to
the **HiQS signal / activity RAG** (``src/rebalance/ingest/embedder.py``,
Qwen3-Embedding-0.6B via MLX) — NOT the ask_self codebase index, which is Gemini
and was ruled out. ``rebalance.ingest._job_guard`` loads this module by path and
applies :func:`guard` to ``embed_chunks`` and ``embed_pending``.

Guard the *leaves*, never the facades: ``embed_vault_chunks`` and
``embed_semantic_pending`` delegate to those leaves, and guarding both layers
would take the same ``flock`` twice in one process and self-deadlock.

Operator reference: UPGRADE.md § "Embedding job guard (GH-172)".
"""

from __future__ import annotations

import argparse
import math
import ctypes
import ctypes.util
import errno
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

GIB = 1024**3

#: Where lockfiles live. Kept out of the repo so worktrees share one namespace —
#: two clones of rebalance-OS running the same job must still collide.
LOCK_DIR = Path(os.environ.get("JOB_GUARD_LOCK_DIR", Path.home() / ".cache" / "rebalance-os" / "locks"))

#: Fraction of physical RAM a single guarded job may hold before it is aborted.
#: The project contract specifies <= 8 GB peak phys_footprint per process, and
#: <= 16 GB aggregate concurrent footprint. On a 64 GB machine, 8 GB is 12.5%.
#: We size the default to 12.5% (0.125) to align with the per-process contract.
DEFAULT_MAX_FOOTPRINT_FRACTION = 0.125

#: Abort if system-available memory falls below this fraction of physical RAM,
#: regardless of how well-behaved *this* job is. This is the defence against
#: stacked runs: the newcomer notices the machine is already starved and bails.
DEFAULT_MIN_AVAILABLE_FRACTION = 0.12

#: Never let the available-memory floor drop below this absolute value.
MIN_AVAILABLE_FLOOR = 4 * GIB

#: Compressor size, as a fraction of RAM, above which the machine is treated as
#: under real memory pressure regardless of how much memory looks "available".
#:
#: This is the signal that CONCLUDES the availability question for GH-219 Lane 4.
#: Reclaimable-pages accounting (free+inactive+speculative) is retained as the
#: availability numerator, because free-only accounting refuses jobs on a healthy
#: Mac — but on its own it can look survivable while the compressor is saturating,
#: which is the 2026-07-27 condition. The compressor is the direct measurement of
#: that state and needs no inference.
#:
#: Sized from the recorded sampler data (sysmem-sys-*.csv, 07-26 and 07-27, 1602
#: samples). The distribution is strongly BIMODAL — median 0.65–0.96 GB when
#: healthy, 25–35 GB when in distress, with almost nothing between: the fraction
#: of samples above 8 GB and above 24 GB is nearly identical (22.2% vs 21.6% on
#: 07-26; 16.7% vs 14.8% on 07-27). That gap makes the exact threshold
#: uncritical — any value in the empty middle classifies the same way — so 25% of
#: RAM (16 GB on this machine) is chosen to sit as far from both modes as
#: possible. Robustness here is a property of the data, not a lucky constant.
#:
#: GH-157 AMENDMENT (2026-09-03) — the constant is UNCHANGED; what changed is that
#: crossing it is now a SUSPICION, not a verdict. The "almost nothing between" the
#: two modes is exactly what stopped holding: this machine spent 9 days sitting at
#: 17-23 GB of ambient compressor — squarely inside the supposedly-empty middle —
#: and refused ``obsidian-vault-embeddings`` **179 times**, 36 times in a single day
#: on four separate days, i.e. every scheduled run. A full run measured on
#: 2026-09-03 peaked at 1.86 GB and moved the compressor by 0.23 GB (17.71 -> 17.94,
#: 59 samples, exit 0): the job neither causes the pressure nor meaningfully adds to
#: it, and with ambient pressure from other software the gate had no path back to
#: healthy. See :meth:`MemoryCeiling._compressor_trip` for the corroboration rule
#: that replaces the bare threshold. Raising this number was explicitly rejected —
#: it would weaken the check for every guarded job. (The "14.32 GiB Qwen" run once
#: cited here was an unbounded-chunk bug in a one-off HiQS evaluation, fixed in
#: 0.68.4 — peak 2.16 GiB after — not a scheduled job; measured scheduled-job peaks
#: are <= 1.85 GB, GH-296.) The fix is a better predicate, not a looser one.
DEFAULT_MAX_COMPRESSOR_FRACTION = 0.25

#: Swap actually in use, above which a high compressor reading is CONFIRMED as real
#: distress. This is the signal the compressor alone stopped providing: a compressor
#: that is merely large has absorbed pressure, while a machine that is *swapping* has
#: run out of room to absorb it. A healthy Mac routinely carries a few hundred MB of
#: residual swap from earlier peaks, so the bar is 1 GiB rather than "nonzero".
#: Measured on 2026-09-03 during a refusal: compressor 19.25 GB, ``vm.swapusage``
#: 0.00M used, 64% of memory free, no paging — the refusal had no distress behind it.
SWAP_DISTRESS_BYTES = 1 * GIB

#: GH-296: the absolute bar above is ALWAYS true on a Mac whose swap file is small.
#: Measured on a MacBook Pro 14" (24 GB RAM, 2 GB swap file) on 2026-09-27: ~1.2 GB
#: of static residual swap for hours at ~50% free, so every compressor reading over
#: the ceiling became a refusal — 5 of 5 small jobs refused, one killed mid-run.
#: Swap now confirms distress only when it ALSO fills this fraction of the swap
#: file. An unreadable total keeps the absolute bar: a blind probe never loosens
#: the rule (#156). macOS grows swap files on demand, so on a machine that is
#: genuinely paging the available-memory floor remains the second corroborator.
SWAP_DISTRESS_FRACTION = 0.75

#: Override for the compressor pressure ceiling, in GB.
ENV_MAX_COMPRESSOR_GB = "REBALANCE_JOB_GUARD_MAX_COMPRESSOR_GB"

#: GH-296 per-device settings. They switch or tune the MEMORY checks only; the
#: single-instance lock and the wall-clock timeout are never configurable, since
#: the lock is the direct defence against the GH-172 stacked-run kernel panic.
ENV_MEMORY_GUARD = "REBALANCE_JOB_GUARD_MEMORY"
ENV_SWAP_DISTRESS_GB = "REBALANCE_JOB_GUARD_SWAP_DISTRESS_GB"
CONFIG_SECTION = "job_guard"
_ON_WORDS = {"on", "1", "true", "yes"}
_OFF_WORDS = {"off", "0", "false", "no"}


def _valid_gb(value: float) -> bool:
    """At least one byte, finite and at most 1 PB (GH-296 final QA F1/F7).

    nan, inf or 1e308 would otherwise crash the GB-to-bytes conversion inside the
    very job the setting was meant to protect.
    """
    return math.isfinite(value) and 1 / GIB <= value <= 1_000_000


def device_config_path() -> Path:
    """The per-device config file the guard reads (GH-296).

    ``$REBALANCE_CONFIG`` when set (the same variable ``rebalance.ingest.config``
    honours), else ``temp/rbos.config`` in the checkout this file lives in. It is
    deliberately neither cwd-based nor handed down by :func:`run_guarded`: the
    in-process embedding guard loads this same module, so launchd, CLI, MCP and
    agent-spawned runs all resolve one file. #281 moves the location; this is the
    one place to change it.
    """
    override = os.environ.get("REBALANCE_CONFIG", "").strip()
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parents[1] / "temp" / "rbos.config"


def guard_settings(warn=None) -> dict:
    """Effective memory-check settings, each as ``{"value": ..., "source": ...}``.

    Precedence: environment variable > device config ``job_guard`` section >
    built-in default. Explicit CLI flags and call arguments still win over all of
    these where they exist. An invalid value is reported in one warning line and
    falls back to the default — it never crashes the job it was meant to protect.

    Keys: ``memory_guard`` (bool), ``max_compressor_gb``, ``swap_distress_gb``,
    ``min_available_gb`` (positive float or ``None`` for "use the default").
    """
    warn = warn or (lambda msg: print(f"[job-guard] {msg}", file=sys.stderr))
    path = device_config_path()
    section: dict = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                warn(f"ignoring config in {path}: expected an object; using defaults")
                data = {}
            raw_section = data.get(CONFIG_SECTION, {})
            if isinstance(raw_section, dict):
                section = raw_section
            else:
                warn(f"ignoring {CONFIG_SECTION!r} in {path}: expected an object; using defaults")
        except (OSError, ValueError) as exc:
            warn(f"could not read {path} ({exc}); job guard using defaults")

    def _pick(key: str, env_name: str | None):
        raw = os.environ.get(env_name, "").strip() if env_name else ""
        if raw:
            return raw, f"env {env_name}"
        if section.get(key) is not None:
            return section[key], f"device config {path}"
        return None, "default"

    settings: dict = {}
    raw, source = _pick("memory_guard", ENV_MEMORY_GUARD)
    word = str(raw).strip().lower() if raw is not None else ""
    if raw is None:
        settings["memory_guard"] = {"value": True, "source": "default"}
    elif raw is True or raw is False:
        settings["memory_guard"] = {"value": raw, "source": source}
    elif word in _ON_WORDS | _OFF_WORDS:
        settings["memory_guard"] = {"value": word in _ON_WORDS, "source": source}
    else:
        warn(f"invalid memory_guard {raw!r} from {source}; expected on/off, using default (on)")
        settings["memory_guard"] = {"value": True, "source": "default"}

    for key, env_name in (
        ("max_compressor_gb", ENV_MAX_COMPRESSOR_GB),
        ("swap_distress_gb", ENV_SWAP_DISTRESS_GB),
        ("min_available_gb", None),
    ):
        raw, source = _pick(key, env_name)
        value = None
        if raw is not None:
            try:
                value = float(raw)
            except (TypeError, ValueError, OverflowError):  # JSON 1e400-sized ints overflow
                value = None
            if value is None or isinstance(raw, bool) or not _valid_gb(value):
                warn(f"invalid {key} {raw!r} from {source}; expected a positive number of GB, using default")
                value, source = None, "default"
        settings[key] = {"value": value, "source": source}
    return settings


#: Wrapper-mode exit codes. Named so a supervisor can branch on *why* a run did
#: not succeed instead of pattern-matching integers. The distinction that matters:
#: CONFLICT and REFUSED are **deferred** (nothing ran, nothing is broken, retry
#: later is correct), while CEILING is a real failure (the job launched and blew
#: its budget). Conflating the two is GH-195 P6's root cause.
EXIT_INSTANCE_CONFLICT = 3
EXIT_CEILING_TRIPPED = 4
EXIT_REFUSED_TO_START = 75  # EX_TEMPFAIL
EXIT_WALL_CLOCK_TIMEOUT = 124  # conventional timeout(1) status
# The child-env flag lives in auth_log (GH-215): the lifecycle writers there
# defer to the guard when it is set. Imported lazily alongside log_job_started.

#: The codes that mean "did not run; not the job's fault". Supervisors should
#: leave their failure counters untouched for these. Contract: a guarded job's
#: own payload must not exit 3 or 75, because launchd records only the final
#: status — the wrapper and doctor read these codes as the guard's (GH-296).
DEFERRED_EXIT_CODES = frozenset({EXIT_INSTANCE_CONFLICT, EXIT_REFUSED_TO_START})

#: Per-process ceiling override, in GB. The guard measures ``phys_footprint``
#: (GH-219 Lane 4), so the setting is named for the metric it actually applies to.
ENV_MAX_FOOTPRINT_GB = "REBALANCE_JOB_GUARD_MAX_FOOTPRINT_GB"

#: Deprecated alias, kept working so existing plists and docs do not silently
#: stop applying when the metric was renamed RSS -> phys_footprint. Honoured with
#: a warning; the footprint-named variable wins when both are set.
ENV_MAX_FOOTPRINT_GB_DEPRECATED = "REBALANCE_JOB_GUARD_MAX_RSS_GB"


def env_max_footprint_gb(warn=None) -> float | None:
    """Resolve the per-process ceiling from the environment, or ``None``.

    Prefers :data:`ENV_MAX_FOOTPRINT_GB`; falls back to the deprecated
    RSS-named alias. A non-numeric value is reported and ignored rather than
    crashing the job it was meant to protect.
    """
    warn = warn or (lambda msg: print(f"[job-guard] {msg}", file=sys.stderr))

    for name, deprecated in (
        (ENV_MAX_FOOTPRINT_GB, False),
        (ENV_MAX_FOOTPRINT_GB_DEPRECATED, True),
    ):
        raw = os.environ.get(name, "").strip()
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            warn(f"ignoring non-numeric {name}={raw!r}")
            continue
        if not _valid_gb(value):
            warn(f"ignoring {name}={raw!r}: expected a positive finite number of GB")
            continue
        if deprecated:
            warn(f"{name} is deprecated (the guard measures phys_footprint, not RSS); use {ENV_MAX_FOOTPRINT_GB}")
        return value
    return None


DEFAULT_POLL_SECONDS = 5.0
DEFAULT_GRACE_SECONDS = 20.0

#: Append-only record of every guarded run's peak memory (GH-175 remediation 4).
#: GH-172 could not be attributed because jetsam records only the process name
#: ``Python`` — three processes at 45.9/35.8/9.2 GB with no way to tell which
#: code path held them. This file makes the NEXT incident attributable to a job.
RSS_LOG_PATH = Path(
    os.environ.get(
        "JOB_GUARD_RSS_LOG",
        Path(__file__).resolve().parents[1] / "temp" / "logs" / "job_rss.jsonl",
    )
)


class GuardError(RuntimeError):
    """Base class for guard failures."""


class InstanceConflict(GuardError):
    """Another instance of this job already holds the lock."""


class MemoryCeilingExceeded(GuardError):
    """The job tripped the footprint ceiling, the available floor, or compressor pressure."""


class RefusedToStart(MemoryCeilingExceeded):
    """Preflight refused before any work ran — deferred, not failed (GH-296).

    A subclass so every existing ``except MemoryCeilingExceeded`` still catches it,
    while a caller that must tell "never started" from "tripped mid-run" (the ingest
    orchestrator classifying a scope as deferred) can do so without parsing text.
    """


class _Evicted(BaseException):
    """Raised in the wrapper's main thread when a replacing run SIGTERMs it.

    BaseException, not Exception: it must not be swallowed by a broad
    ``except Exception`` between the handler and the teardown.
    """


# --------------------------------------------------------------------------- #
# Memory probing
# --------------------------------------------------------------------------- #


def _sysctl(name: str) -> str | None:
    try:
        out = subprocess.run(["sysctl", "-n", name], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def total_memory_bytes() -> int:
    """Physical RAM. Returns 0 when it cannot be determined."""
    if sys.platform == "darwin":
        raw = _sysctl("hw.memsize")
        return int(raw) if raw and raw.isdigit() else 0

    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    return 0


def available_memory_bytes() -> int:
    """Memory the OS could hand out without swapping. 0 when undeterminable.

    On macOS this counts free + inactive + speculative pages, all of which the
    kernel can reclaim without swapping. Compressed pages are excluded.

    A healthy Mac routinely runs with very little *free* memory — the OS uses RAM
    for cache and lists it as inactive — so free alone is not a usable proxy for
    availability here. See the comment in the implementation for the measurement
    that settled this, and for why compressor/swap are the better pressure signal.
    """
    if sys.platform == "darwin":
        try:
            out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return 0
        if out.returncode != 0:
            return 0

        page_size = 4096
        header = re.search(r"page size of (\d+) bytes", out.stdout)
        if header:
            page_size = int(header.group(1))

        pages = 0
        # GH-219 Lane 4: free-ONLY accounting was tried here and REVERTED, measured.
        # The theory (counting inactive/speculative masks pressure until the
        # compressor saturates) is reasonable, but the implementation made the guard
        # refuse to start on a perfectly healthy machine: with free=1.59 GB,
        # inactive=21.46 GB, speculative=0.93 GB — i.e. ~24 GB genuinely reclaimable —
        # free-only reported 1.58 GB against a 7.68 GB floor, so EVERY guarded job
        # was refused. A safety mechanism that blocks legitimate work is one that
        # gets switched off.
        #
        # Changing this numerator requires re-tuning DEFAULT_MIN_AVAILABLE_FRACTION
        # in the same edit; the two are one decision, not two.
        #
        # DECISION (GH-219 Lane 4, concluded — not deferred): reclaimable-pages
        # accounting is RETAINED here, and the gap it leaves is covered by a separate,
        # direct pressure signal rather than by tightening this numerator.
        #
        # Rationale. This definition can look survivable while the machine is dying,
        # which is the real objection to it. But narrowing it to free-only is strictly
        # worse (it refuses every job on a healthy Mac), and it cannot be validated
        # against history: sysmem-sys-*.csv never recorded inactive/speculative, so
        # the 07-27 crisis cannot be replayed against any variant of this number.
        # Rather than tune a metric that cannot be checked, the guard now also reads
        # the memory compressor (see DEFAULT_MAX_COMPRESSOR_FRACTION), which IS
        # recorded, IS strongly bimodal between healthy and crisis, and measures the
        # dying-machine state directly instead of inferring it.
        wanted = ("Pages free:", "Pages inactive:", "Pages speculative:")
        for line in out.stdout.splitlines():
            for key in wanted:
                if line.startswith(key):
                    pages += int(line.split(":")[1].strip().rstrip("."))
        return pages * page_size

    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    return 0


class _RusageInfoV2(ctypes.Structure):
    _fields_ = [
        ("ri_uuid", ctypes.c_uint8 * 16),
        ("ri_user_time", ctypes.c_uint64),
        ("ri_system_time", ctypes.c_uint64),
        ("ri_pkg_idle_wkups", ctypes.c_uint64),
        ("ri_interrupt_wkups", ctypes.c_uint64),
        ("ri_pageins", ctypes.c_uint64),
        ("ri_wired_size", ctypes.c_uint64),
        ("ri_resident_size", ctypes.c_uint64),
        ("ri_phys_footprint", ctypes.c_uint64),
        ("ri_proc_start_abstime", ctypes.c_uint64),
        ("ri_proc_exit_abstime", ctypes.c_uint64),
        ("ri_child_user_time", ctypes.c_uint64),
        ("ri_child_system_time", ctypes.c_uint64),
        ("ri_child_pkg_idle_wkups", ctypes.c_uint64),
        ("ri_child_interrupt_wkups", ctypes.c_uint64),
        ("ri_child_pageins", ctypes.c_uint64),
        ("ri_child_elapsed_abstime", ctypes.c_uint64),
        ("ri_diskio_bytesread", ctypes.c_uint64),
        ("ri_diskio_byteswritten", ctypes.c_uint64),
    ]


def compressor_bytes() -> int:
    """Bytes held by the macOS memory compressor. 0 when undeterminable.

    A saturating compressor is the most direct evidence that the machine is in
    real trouble: it means the kernel is already paying CPU to avoid swapping.
    Unlike "available" memory, it cannot look healthy while the machine dies.
    """
    if sys.platform != "darwin":
        return 0
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return 0
    if out.returncode != 0 or not out.stdout.strip():
        return 0

    header = re.search(r"page size of (\d+) bytes", out.stdout)
    page_size = int(header.group(1)) if header else 4096
    for line in out.stdout.splitlines():
        if line.startswith("Pages occupied by compressor:"):
            digits = line.split(":", 1)[1].strip().rstrip(".")
            if digits.isdigit():
                return int(digits) * page_size
    return 0


def swap_used_bytes() -> int | None:
    """Bytes of swap currently in use, or ``None`` when undeterminable (GH-157).

    ``None`` and ``0`` mean different things here and must not be collapsed: ``0`` is
    positive evidence that the machine is NOT paging, while ``None`` is no evidence at
    all. The compressor corroboration rule treats them differently — an unreadable
    probe falls back to the old refuse-on-threshold behaviour rather than quietly
    granting permission, because a guard that stops constraining when a probe fails is
    #156's defect class.
    """
    return _swapusage_field("used")


def swap_total_bytes() -> int | None:
    """Size of the swap file(s) in bytes, or ``None`` when undeterminable (GH-296).

    Same ``None``-is-no-evidence contract as :func:`swap_used_bytes`: an unreadable
    total keeps the absolute :data:`SWAP_DISTRESS_BYTES` bar rather than loosening it.
    """
    return _swapusage_field("total")


def _swapusage_field(field: str) -> int | None:
    if sys.platform != "darwin":
        return None
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    # "total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)" — the unit travels with
    # the number and is not always M, so parse both rather than assuming megabytes.
    match = re.search(field + r"\s*=\s*([\d.]+)([KMGT])", out.stdout)
    if not match:
        return None
    scale = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}[match.group(2)]
    return int(float(match.group(1)) * scale)


def tree_footprint_bytes(pid: int) -> tuple[int, bool, int]:
    """Resident memory (or phys_footprint on macOS) of ``pid`` plus every descendant.

    Returns: (total_bytes, is_fallback, unreadable_count)
    """
    try:
        out = subprocess.run(["ps", "-eo", "pid=,ppid=,rss="], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return 0, True, 0
    if out.returncode != 0:
        return 0, True, 0

    children: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        try:
            this_pid, ppid, kb = (int(p) for p in parts)
        except ValueError:
            continue
        rss[this_pid] = kb * 1024
        children.setdefault(ppid, []).append(this_pid)

    stack = [pid]
    seen: set[int] = set()
    tree_pids = []
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        tree_pids.append(current)
        stack.extend(children.get(current, ()))

    is_fallback = True
    total = 0
    unreadable_count = 0

    if sys.platform == "darwin":
        try:
            libc = ctypes.CDLL(ctypes.util.find_library("c"))
            proc_pid_rusage = libc.proc_pid_rusage
            proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
            proc_pid_rusage.restype = ctypes.c_int
            is_fallback = False
        except Exception:
            pass

        if not is_fallback:
            for p in tree_pids:
                buf = _RusageInfoV2()
                rc = proc_pid_rusage(p, 2, ctypes.byref(buf))
                if rc == 0:
                    total += buf.ri_phys_footprint
                else:
                    unreadable_count += 1
            return total, False, unreadable_count

    for p in tree_pids:
        total += rss.get(p, 0)
    return total, True, unreadable_count


def _fmt_gb(value: int) -> str:
    return f"{value / GIB:.1f} GB"


# --------------------------------------------------------------------------- #
# Single-instance lock
# --------------------------------------------------------------------------- #


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError as exc:
        return exc.errno == errno.EPERM
    return True


class SingleInstanceLock:
    """Advisory whole-file ``flock`` keyed by job name.

    ``flock`` is released by the kernel when the holder dies, so a killed job
    never leaves a lock that blocks the next run — the failure mode a bare PID
    file has. The PID written into the file is advisory, for diagnostics and for
    ``on_conflict="replace"``.
    """

    def __init__(self, name: str, lock_dir: Path | None = None) -> None:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("_") or "job"
        self.name = name
        self.path = (lock_dir or LOCK_DIR) / f"{safe}.lock"
        self._fh = None

    def _read_state(self) -> dict:
        """Lockfile contents as a dict. Tolerates a bare-PID legacy file."""
        try:
            raw = self.path.read_text().strip()
        except OSError:
            return {}
        if not raw:
            return {}
        try:
            state = json.loads(raw)
        except ValueError:
            return {"pid": int(raw)} if raw.isdigit() else {}
        return state if isinstance(state, dict) else {}

    def holder_pid(self) -> int | None:
        """PID recorded in the lockfile, if it names a live process."""
        pid = self._read_state().get("pid")
        if not isinstance(pid, int):
            return None
        return pid if _pid_alive(pid) else None

    def acquire(self, on_conflict: str = "refuse", replace_grace: float = 15.0) -> None:
        """Take the lock, or raise :class:`InstanceConflict`.

        on_conflict="refuse"  — raise, leaving the incumbent untouched (default;
                                the safe choice for anything that writes).
        on_conflict="replace" — SIGTERM the incumbent, wait ``replace_grace``
                                seconds, SIGKILL it, then take the lock. This is
                                the "re-running the embeddings" ergonomic the
                                operator expected and did not get.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a+")

        if self._try_flock():
            self._write_state()
            return

        if on_conflict == "replace":
            if self._evict(replace_grace):
                self._write_state()
                return

        pid = self.holder_pid()
        self.release()
        raise InstanceConflict(
            f"job {self.name!r} is already running" + (f" (pid {pid})" if pid else "") + f"; lock: {self.path}"
        )

    def _try_flock(self) -> bool:
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True

    def _write_state(self, **extra) -> None:
        self._fh.seek(0)
        self._fh.truncate()
        self._fh.write(json.dumps({"pid": os.getpid(), **extra}))
        self._fh.flush()

    def record_child_group(self, pgid: int) -> None:
        """Record the guarded child's process group in the lockfile.

        Load-bearing for ``--on-conflict replace``: the child runs in its OWN
        session, so it is unreachable via the wrapper's process group. Without
        this, an evictor that has to SIGKILL an unresponsive wrapper leaves the
        grandchildren resident — the exact stacking GH-172 is about.
        """
        if self._fh is None:
            return
        self._write_state(child_pgid=pgid)

    def _evict(self, grace: float) -> bool:
        """Displace the incumbent and take the lock. True if we now hold it.

        Success is measured by ACQUIRING THE FLOCK, not by the incumbent's PID
        disappearing. PID liveness is the wrong signal: ``kill(pid, 0)`` succeeds
        against a zombie, so a reaped-but-unwaited incumbent reads as alive
        forever, and a bare "SIGKILL then retry once" races the kernel's lock
        release. The flock is the only ground truth about who owns the job.
        """
        state = self._read_state()
        pid = state.get("pid")
        child_pgid = state.get("child_pgid")
        if not isinstance(pid, int) or pid == os.getpid():
            return self._try_flock()

        def _signal_all(sig: int) -> None:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
            # The incumbent's child runs in its OWN session, so it is not
            # reachable via the wrapper's group. A cooperative wrapper reaps it
            # on SIGTERM; a SIGKILLed one never gets the chance. Signal it
            # directly so eviction is total either way.
            if isinstance(child_pgid, int) and child_pgid > 0:
                try:
                    os.killpg(child_pgid, sig)
                except OSError:
                    pass

        for sig in (signal.SIGTERM, signal.SIGKILL):
            _signal_all(sig)
            deadline = time.monotonic() + (grace if sig == signal.SIGTERM else 5.0)
            while time.monotonic() < deadline:
                if self._try_flock():
                    return True
                time.sleep(0.1)
        return self._try_flock()

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            self._fh.close()
        finally:
            self._fh = None

    def __enter__(self) -> "SingleInstanceLock":
        self.acquire()
        return self

    def __exit__(self, *exc) -> None:
        self.release()


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except OSError as exc:
        return exc.errno == errno.EPERM
    return True


def _terminate_group(pgid: int, grace: float) -> None:
    """SIGTERM a process GROUP, escalating to SIGKILL after ``grace`` seconds."""
    try:
        os.killpg(pgid, signal.SIGTERM)
    except OSError:
        return

    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if not _group_alive(pgid):
            return
        time.sleep(0.25)

    try:
        os.killpg(pgid, signal.SIGKILL)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# Memory ceiling
# --------------------------------------------------------------------------- #


class MemoryCeiling:
    """Background watchdog that aborts a process tree before the machine dies.

    Three independent trip conditions, because they catch different failures:

      * ``phys_footprint`` ceiling — this job leaked or accumulated (GH-172
        defects 2 and 3, the ``out = [None] * len(texts)`` accumulation; and
        GH-219's MLX buffer-cache growth, which RSS could not see at all).
      * Available-memory floor — the *machine* is starved, whoever is at fault
        (GH-172 defect 1, stacked concurrent runs).
      * Compressor pressure — the machine is already paying CPU to avoid
        swapping. This catches the case the floor alone misses, where
        reclaimable pages still look plentiful while the compressor saturates
        (GH-219 Lane 4; the 2026-07-27 condition).
    """

    def __init__(
        self,
        pid: int | None = None,
        max_footprint_bytes: int | None = None,
        min_available_bytes: int | None = None,
        poll_seconds: float = DEFAULT_POLL_SECONDS,
        on_trip=None,
        log=None,
        max_rss_bytes: int | None = None,
    ) -> None:
        total = total_memory_bytes()
        self.pid = pid or os.getpid()
        self.total = total
        self.log = log or (lambda msg: print(f"[job-guard] {msg}", file=sys.stderr))

        # GH-296: one resolver for both guard layers (launchd wrapper and the
        # in-process embedding guard). Explicit arguments still win over it.
        self.settings = guard_settings(warn=self.log)
        self.memory_checks = bool(self.settings["memory_guard"]["value"])

        def _gb(key: str) -> int | None:
            value = self.settings[key]["value"]
            return int(value * GIB) if value else None

        ceiling = max_footprint_bytes or max_rss_bytes
        self.max_footprint = ceiling or int(total * DEFAULT_MAX_FOOTPRINT_FRACTION) or None
        self.min_available = (
            min_available_bytes
            or _gb("min_available_gb")
            or max(int(total * DEFAULT_MIN_AVAILABLE_FRACTION), MIN_AVAILABLE_FLOOR if total else 0)
            or None
        )
        self.max_compressor = _gb("max_compressor_gb") or int(total * DEFAULT_MAX_COMPRESSOR_FRACTION) or None
        self.swap_distress_override = _gb("swap_distress_gb")
        self._ambient_logged = False
        self.poll_seconds = poll_seconds
        self.on_trip = on_trip
        self.tripped_reason: str | None = None
        self.peak_footprint = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def swap_distress_bar(self) -> int:
        """Swap in use above which a high compressor counts as real distress (GH-296).

        A device-config/env override wins; otherwise ``max(1 GiB, 75% of the swap
        file)``. An unreadable swap total keeps the 1 GiB bar (#156).
        """
        if self.swap_distress_override:
            return self.swap_distress_override
        total = swap_total_bytes()
        if not total:
            return SWAP_DISTRESS_BYTES
        return max(SWAP_DISTRESS_BYTES, int(total * SWAP_DISTRESS_FRACTION))

    def _compressor_trip(self) -> str | None:
        """The compressor verdict, corroborated. ``None`` means do not trip (GH-157).

        Crossing the compressor ceiling used to be sufficient on its own, on the
        recorded premise that the distribution was bimodal with an empty middle
        (see :data:`DEFAULT_MAX_COMPRESSOR_FRACTION`). That premise stopped holding:
        the machine now idles at 17-23 GB of ambient compressor from unrelated
        software, and the bare threshold refused a 1.9 GB job 179 times in 9 days
        while the machine was demonstrably healthy — 64% free, zero swap, no paging.

        Machine-wide compressor pressure answers *"is this machine in distress?"*.
        It does not answer *"will running this job put it there?"*, and for a job
        whose measured effect on the compressor is 0.23 GB those are different
        questions. So a reading above the ceiling now has to be CONFIRMED by a
        signal that only genuine distress produces:

          * swap actually in use above :data:`SWAP_DISTRESS_BYTES` — the machine has
            run out of room to absorb pressure and is paging; or
          * available memory below the floor — the availability gate would refuse
            this run anyway.

        A large compressor with neither is a machine that absorbed pressure
        successfully, which is the compressor doing its job, not evidence against
        starting a small one.

        Fails CLOSED on a blind probe: if neither corroborating signal can be read,
        the old refuse-on-threshold behaviour stands. An unreadable probe must never
        be the thing that grants permission (#156).
        """
        if not self.max_compressor:
            return None
        compressor = compressor_bytes()
        if not compressor or compressor <= self.max_compressor:
            return None

        swap = swap_used_bytes()
        available = available_memory_bytes()
        swap_bar = self.swap_distress_bar()
        if swap is not None and swap > swap_bar:
            corroboration = f"swap in use {_fmt_gb(swap)} (distress bar {_fmt_gb(swap_bar)})"
        elif available and self.min_available and available < self.min_available:
            corroboration = f"available {_fmt_gb(available)} below floor {_fmt_gb(self.min_available)}"
        elif swap is None and not available:
            corroboration = "corroborating signals unreadable; failing closed"
        else:
            # Once per run: the mid-run check repeats this every poll, and on a Mac
            # that idles above the ceiling it was 39 identical lines per job (GH-296).
            if self._ambient_logged:
                return None
            self._ambient_logged = True
            self.log(
                f"memory compressor holds {_fmt_gb(compressor)} (ceiling {_fmt_gb(self.max_compressor)}) "
                f"but the machine is not in distress: swap "
                f"{_fmt_gb(swap) if swap is not None else 'unknown'}, available {_fmt_gb(available)}. "
                f"Proceeding — ambient compressor pressure this job does not cause is not a reason "
                f"to refuse it (#157)."
            )
            return None

        return (
            f"memory compressor holds {_fmt_gb(compressor)}, ceiling is "
            f"{_fmt_gb(self.max_compressor)}, confirmed by {corroboration}"
        )

    def preflight(self) -> None:
        """Refuse to even start when the machine is already starved.

        Cheaper than starting a 40-minute job that will be killed at minute two,
        and it is the check that turns a stacked run into a clean error instead
        of a kernel panic.
        """
        # The guard must never silently stop guarding. Without physical RAM every
        # ceiling below is None and the watchdog disables itself, so a run that only
        # "passed" because the sysctl was blocked would be indistinguishable from a
        # genuinely well-behaved one — and #157's measurements would be unreliable
        # for exactly that reason. Refuse instead: EX_TEMPFAIL is deferred, so a
        # supervisor retries rather than counting it as a job failure (#156).
        if not self.memory_checks:
            # GH-296: an unguarded run must never look like a guarded one, so say
            # so on every run. The lock and the wall-clock timeout are unaffected.
            self.log(
                f"memory checks disabled by {self.settings['memory_guard']['source']} (lock and timeout still active)"
            )
            return
        if not self.total:
            raise RefusedToStart(
                "refusing to start: cannot determine physical RAM, so no memory ceiling "
                "can be enforced (an unguarded run must not masquerade as a guarded one)"
            )

        # Compressor pressure first: it stays honest when "available" does not.
        reason = self._compressor_trip()
        if reason:
            raise RefusedToStart(f"refusing to start: {reason}")

        if not self.min_available:
            return
        available = available_memory_bytes()
        if available and available < self.min_available:
            raise RefusedToStart(
                f"refusing to start: only {_fmt_gb(available)} available, floor is {_fmt_gb(self.min_available)}"
            )

    def start(self) -> None:
        if self.total == 0:
            self.log("could not determine physical RAM; memory ceiling disabled")
            return
        self._thread = threading.Thread(target=self._run, name="job-guard", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.wait(self.poll_seconds):
            reason = self._check()
            if reason:
                self.tripped_reason = reason
                self.log(f"MEMORY CEILING TRIPPED: {reason}")
                if self.on_trip:
                    self.on_trip(reason)
                return

    def _check(self) -> str | None:
        footprint, is_fallback, unreadable = tree_footprint_bytes(self.pid)
        self.peak_footprint = max(self.peak_footprint, footprint)
        if not self.memory_checks:
            return None  # GH-296: still measured for job_rss.jsonl, never enforced
        metric = "RSS (fallback)" if is_fallback else "phys_footprint"
        unr_msg = f" (skipped {unreadable} unreadable pids)" if unreadable else ""

        if self.max_footprint and footprint > self.max_footprint:
            return (
                f"process tree holds {_fmt_gb(footprint)} {metric}, ceiling is {_fmt_gb(self.max_footprint)}{unr_msg}"
            )

        # Same corroboration rule as preflight (#157). A long run that started on a
        # healthy machine must not be killed at minute forty because unrelated
        # software filled the compressor; only real distress ends it.
        reason = self._compressor_trip()
        if reason:
            return f"{reason} (this job {metric}: {_fmt_gb(footprint)}{unr_msg})"

        available = available_memory_bytes()
        if self.min_available and available and available < self.min_available:
            return (
                f"system available memory {_fmt_gb(available)} fell below "
                f"floor {_fmt_gb(self.min_available)} (this job {metric}: {_fmt_gb(footprint)}{unr_msg})"
            )
        return None

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.poll_seconds + 1)
            self._thread = None


def settings_report() -> tuple[str, list[str]]:
    """One line of effective memory-check settings with their sources, plus warnings.

    Shared by ``job_guard.py --status`` and ``rebalance doctor`` (GH-296) so the two
    can never describe the guard differently.
    """
    warnings: list[str] = []
    # Resolve the footprint ceiling exactly as run_guarded does, so the report
    # matches what the launchd wrapper enforces (GH-296 final QA F3).
    env_footprint = env_max_footprint_gb(warn=warnings.append)
    ceiling = MemoryCeiling(
        max_footprint_bytes=int(env_footprint * GIB) if env_footprint else None,
        log=warnings.append,
    )
    settings = ceiling.settings
    swap_total = swap_total_bytes()

    def _src(key: str) -> str:
        return settings[key]["source"]

    swap_src = (
        _src("swap_distress_gb")
        if ceiling.swap_distress_override
        else f"default: max(1 GB, {SWAP_DISTRESS_FRACTION:.0%} of {_fmt_gb(swap_total) if swap_total else 'unreadable'} swap)"
    )
    text = (
        f"memory checks {'on' if ceiling.memory_checks else 'OFF'} ({_src('memory_guard')}); "
        f"compressor ceiling {_fmt_gb(ceiling.max_compressor or 0)} ({_src('max_compressor_gb')}), "
        f"swap distress bar {_fmt_gb(ceiling.swap_distress_bar())} ({swap_src}), "
        f"available floor {_fmt_gb(ceiling.min_available or 0)} ({_src('min_available_gb')}), "
        f"per-job footprint ceiling (wrapper and embedding; mid-run on main thread only) {_fmt_gb(ceiling.max_footprint or 0)} "
        f"({'env' if env_footprint else f'default: {DEFAULT_MAX_FOOTPRINT_FRACTION:.1%} of RAM'})"
    )
    if not ceiling.memory_checks:
        text += "; thresholds not enforced; lock and timeout still active"
    return text, warnings


# --------------------------------------------------------------------------- #
# In-process entry point
# --------------------------------------------------------------------------- #


def record_peak_footprint(
    name: str,
    ceiling: "MemoryCeiling",
    *,
    started: float | None = None,
    exit_code: int | None = None,
    path: Path | None = None,
) -> None:
    """Append one JSONL row describing a guarded run's peak memory.

    Best-effort by construction: a logging failure must never take down the job
    it was only observing. Every exception is swallowed deliberately.
    """
    target = path or RSS_LOG_PATH
    try:
        row = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "job": name,
            "pid": os.getpid(),
            "peak_footprint_bytes": int(ceiling.peak_footprint or 0),
            "peak_footprint_gb": round((ceiling.peak_footprint or 0) / GIB, 3),
            "total_memory_gb": round((ceiling.total or 0) / GIB, 1),
            "max_footprint_gb": round((ceiling.max_footprint or 0) / GIB, 3) if ceiling.max_footprint else None,
            "tripped_reason": ceiling.tripped_reason,
            "memory_guard": "on" if getattr(ceiling, "memory_checks", True) else "off",
            "exit_code": exit_code,
            "duration_s": round(time.monotonic() - started, 1) if started else None,
        }
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a") as fh:
            fh.write(json.dumps(row) + "\n")
    except Exception:  # pragma: no cover - observability must never break the job
        pass


@contextmanager
def guard(
    name: str,
    max_footprint_gb: float | None = None,
    min_available_gb: float | None = None,
    on_conflict: str = "refuse",
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    log=None,
    max_rss_gb: float | None = None,
):
    """Guard the calling process: single-instance lock + memory ceiling.

    On trip the watchdog raises :class:`MemoryCeilingExceeded` in the MAIN
    thread via ``signal.SIGTERM`` -> handler, so ``finally`` blocks still run and
    partial work is flushed. If the main thread is wedged inside a C extension
    and ignores it, the process is SIGKILLed after the grace period.

    Off the main thread (GH-296 final QA F8 — e.g. the terminal dashboard's
    background GitHub refresh) Python cannot install a signal handler, and a
    SIGTERM would hit the host process, not the work. There the lock and the
    preflight still apply in full; the watchdog still measures and records a
    trip, and the guard raises :class:`MemoryCeilingExceeded` when the body
    returns rather than interrupting it. It never signals the host process.
    """
    lock = SingleInstanceLock(name)
    lock.acquire(on_conflict=on_conflict)

    ceiling = MemoryCeiling(
        max_footprint_bytes=int((max_footprint_gb or max_rss_gb) * GIB) if (max_footprint_gb or max_rss_gb) else None,
        min_available_bytes=int(min_available_gb * GIB) if min_available_gb else None,
        poll_seconds=poll_seconds,
        log=log,
    )
    in_main_thread = threading.current_thread() is threading.main_thread()

    def _on_trip(reason: str) -> None:
        os.kill(os.getpid(), signal.SIGTERM)
        # Backstop: if SIGTERM is swallowed (native extension mid-allocation),
        # take the process down rather than let it reach the compressor cliff.
        time.sleep(DEFAULT_GRACE_SECONDS)
        os.kill(os.getpid(), signal.SIGKILL)

    # Off the main thread: record only (the watchdog logs the trip); raised below.
    ceiling.on_trip = _on_trip if in_main_thread else None

    previous = signal.getsignal(signal.SIGTERM) if in_main_thread else None

    def _handler(signum, frame):
        raise MemoryCeilingExceeded(ceiling.tripped_reason or "terminated by job guard")

    started = time.monotonic()
    try:
        ceiling.preflight()
        if in_main_thread:
            signal.signal(signal.SIGTERM, _handler)
        ceiling.start()
        yield ceiling
        if ceiling.tripped_reason:
            raise MemoryCeilingExceeded(ceiling.tripped_reason)
    finally:
        ceiling.stop()
        if in_main_thread:
            try:
                signal.signal(signal.SIGTERM, previous)
            except (ValueError, TypeError):
                pass
        # Written on EVERY exit path — clean, raised, or ceiling-tripped. The
        # tripped run is precisely the one worth having a record of.
        record_peak_footprint(name, ceiling, started=started)
        lock.release()


# --------------------------------------------------------------------------- #
# Wrapper CLI
# --------------------------------------------------------------------------- #


def run_guarded(
    name: str,
    argv: list[str],
    max_footprint_gb: float | None = None,
    min_available_gb: float | None = None,
    on_conflict: str = "refuse",
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    grace_seconds: float = DEFAULT_GRACE_SECONDS,
    max_rss_gb: float | None = None,
    max_runtime_seconds: float | None = None,
    lifecycle_job: str | None = None,
) -> int:
    """Run ``argv`` as a guarded child process. Returns the exit code."""
    log = lambda msg: print(f"[job-guard] {msg}", file=sys.stderr)  # noqa: E731

    if max_runtime_seconds is not None and max_runtime_seconds <= 0:
        raise ValueError("max_runtime_seconds must be positive")

    lock = SingleInstanceLock(name)
    try:
        lock.acquire(on_conflict=on_conflict, replace_grace=grace_seconds)
    except InstanceConflict as exc:
        log(str(exc))
        return EXIT_INSTANCE_CONFLICT

    started = time.monotonic()
    try:
        # Explicit argument wins; otherwise fall back to the environment so a
        # plist can raise the ceiling without a code change (GH-219 Lane 4).
        effective_gb = max_footprint_gb or max_rss_gb or env_max_footprint_gb(warn=log)
        ceiling = MemoryCeiling(
            max_footprint_bytes=int(effective_gb * GIB) if effective_gb else None,
            min_available_bytes=int(min_available_gb * GIB) if min_available_gb else None,
            poll_seconds=poll_seconds,
            log=log,
        )
        try:
            ceiling.preflight()
        except MemoryCeilingExceeded as exc:
            # Distinct from the mid-run trip below: the child never launched, so
            # this is "come back later", not "this job is broken" (GH-195 P6).
            log(str(exc))
            return EXIT_REFUSED_TO_START

        if ceiling.memory_checks:
            log(
                f"starting {name!r}: footprint ceiling {_fmt_gb(ceiling.max_footprint or 0)}, "
                f"available floor {_fmt_gb(ceiling.min_available or 0)}"
            )
        else:
            log(f"starting {name!r}: memory checks off")

        child_env = None
        if lifecycle_job:
            from rebalance.ingest.auth_log import SCHEDULER_LIFECYCLE_CHILD_ENV, log_job_started

            log_job_started(lifecycle_job)
            child_env = os.environ.copy()
            child_env[SCHEDULER_LIFECYCLE_CHILD_ENV] = "1"

        # Own process group, so the whole tree dies together — a pool's workers
        # outliving their parent is how 90 GB stayed resident in GH-172.
        try:
            child = subprocess.Popen(argv, start_new_session=True, env=child_env)
        except Exception:
            if lifecycle_job:
                from rebalance.ingest.auth_log import log_job_failed

                log_job_failed(lifecycle_job, 1, time.monotonic() - started, reason="launch_failed")
            raise
        lock.record_child_group(child.pid)  # new session => pgid == pid
        ceiling.pid = child.pid
        ceiling.on_trip = lambda reason: _reap_child_tree(child, grace_seconds, log)
        ceiling.start()

        # A replacing run SIGTERMs THIS wrapper. Without a handler the wrapper
        # dies instantly and the child — in its own session — is orphaned, so
        # "replace" would stack processes instead of replacing them.
        def _on_term(signum, frame):
            raise _Evicted()

        previous_term = signal.signal(signal.SIGTERM, _on_term)

        timed_out = False
        try:
            code = child.wait(timeout=max_runtime_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            log(f"wall_clock_timeout: {name!r} exceeded {max_runtime_seconds:g}s; tearing down child tree {child.pid}")
            _reap_child_tree(child, grace_seconds, log)
            code = EXIT_WALL_CLOCK_TIMEOUT
        except _Evicted:
            log("evicted by a replacing run; tearing down child tree")
            _reap_child_tree(child, grace_seconds, log)
            code = 143
        except KeyboardInterrupt:
            _reap_child_tree(child, grace_seconds, log)
            code = 130
        finally:
            ceiling.stop()
            try:
                signal.signal(signal.SIGTERM, previous_term)
            except (ValueError, TypeError):
                pass

        final_code = EXIT_WALL_CLOCK_TIMEOUT if timed_out else EXIT_CEILING_TRIPPED if ceiling.tripped_reason else code
        log(f"{name!r} finished with exit {final_code}; peak tree footprint {_fmt_gb(ceiling.peak_footprint)}")
        record_peak_footprint(name, ceiling, started=started, exit_code=final_code)
        if lifecycle_job:
            from rebalance.ingest.auth_log import log_job_completed, log_job_failed, log_job_skipped

            elapsed = time.monotonic() - started
            if final_code == 0:
                log_job_completed(lifecycle_job, elapsed)
            elif final_code in DEFERRED_EXIT_CODES:
                reason = "instance_conflict" if final_code == EXIT_INSTANCE_CONFLICT else "refused_to_start"
                log_job_skipped(lifecycle_job, final_code, elapsed, reason=reason)
            else:
                if timed_out:
                    reason = "wall_clock_timeout"
                elif ceiling.tripped_reason:
                    reason = "resource_ceiling"
                elif final_code == 143:
                    reason = "evicted"
                elif final_code == 130:
                    reason = "interrupted"
                else:
                    reason = "child_exit"
                log_job_failed(lifecycle_job, final_code, elapsed, reason=reason)
        return final_code
    finally:
        lock.release()


def _reap_child_tree(child: subprocess.Popen, grace: float, log) -> None:
    """Terminate the guarded child's process group and REAP the child.

    The parent must ``waitpid`` rather than poll ``killpg(pgid, 0)``: a zombie
    still answers signal 0, so polling alone would block for the entire grace
    period on a child that has already exited.
    """
    try:
        pgid = os.getpgid(child.pid)
    except OSError:
        pgid = None

    log(f"terminating child tree {child.pid}")
    if pgid is not None:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except OSError:
            pass

    try:
        child.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        log(f"child {child.pid} ignored SIGTERM; sending SIGKILL")
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log(f"child {child.pid} survived SIGKILL")

    # Sweep grandchildren that outlived the direct child (the reaped child no
    # longer confuses the liveness probe, so this poll is now meaningful).
    if pgid is not None and _group_alive(pgid):
        _terminate_group(pgid, min(grace, 5.0))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="job_guard",
        description="Run a long-running local job under a single-instance lock and a memory ceiling (GH-172).",
    )
    parser.add_argument("--name", required=True, help="lock identity; same name = same lock")
    parser.add_argument(
        "--max-footprint-gb",
        type=float,
        default=None,
        help=f"abort above this tree footprint (default: {DEFAULT_MAX_FOOTPRINT_FRACTION:.0%} of RAM)".replace(
            "%", "%%"
        ),
    )
    parser.add_argument(
        "--max-rss-gb",
        type=float,
        default=None,
        help="DEPRECATED alias for --max-footprint-gb",
    )
    parser.add_argument(
        "--min-available-gb",
        type=float,
        default=None,
        help=f"abort below this system-available memory "
        f"(default: max({DEFAULT_MIN_AVAILABLE_FRACTION:.0%} of RAM, 4 GB))".replace("%", "%%"),
    )
    parser.add_argument(
        "--on-conflict",
        choices=("refuse", "replace"),
        default="refuse",
        help="what to do when another instance holds the lock (default: refuse)",
    )
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--grace-seconds", type=float, default=DEFAULT_GRACE_SECONDS)
    parser.add_argument(
        "--max-runtime-seconds",
        type=float,
        default=None,
        help="terminate the child tree after this positive wall-clock duration",
    )
    parser.add_argument(
        "--lifecycle-job",
        default=None,
        help="record exactly one scheduler lifecycle for this job around the guarded child",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="report memory and lock state for --name, then exit",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- command to run")
    args = parser.parse_args(argv)

    if args.status:
        total = total_memory_bytes()
        lock = SingleInstanceLock(args.name)
        holder = lock.holder_pid()
        print(f"job:       {args.name}")
        print(f"lockfile:  {lock.path}")
        print(f"holder:    {holder if holder else 'none'}")
        print(f"total RAM: {_fmt_gb(total)}")
        print(f"available: {_fmt_gb(available_memory_bytes())}")
        report, warnings = settings_report()
        print(f"settings:  {report}")
        for warning in warnings:
            print(f"warning:   {warning}")
        if holder:
            footprint, is_fallback, unr = tree_footprint_bytes(holder)
            metric = "RSS (fallback)" if is_fallback else "phys_footprint"
            unr_msg = f" (skipped {unr} unreadable)" if unr else ""
            print(f"tree {metric}: {_fmt_gb(footprint)}{unr_msg}")
        return 0

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("no command given; pass it after --")

    return run_guarded(
        args.name,
        command,
        max_footprint_gb=args.max_footprint_gb,
        max_rss_gb=args.max_rss_gb,
        min_available_gb=args.min_available_gb,
        on_conflict=args.on_conflict,
        poll_seconds=args.poll_seconds,
        grace_seconds=args.grace_seconds,
        max_runtime_seconds=args.max_runtime_seconds,
        lifecycle_job=args.lifecycle_job,
    )


if __name__ == "__main__":
    sys.exit(main())

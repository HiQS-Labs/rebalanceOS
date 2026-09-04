"""Shared pytest fixtures for the rebalance-OS test suite."""

import importlib.machinery
import os
import sys
import types

import pytest

from rebalance.lib.metal_probe import metal_available

# Register Hypothesis profiles for property-based testing across local and CI environments.
try:
    from hypothesis import HealthCheck, Phase, Verbosity, settings

    settings.register_profile(
        "ci",
        max_examples=50,
        deadline=None,
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink],
        suppress_health_check=[HealthCheck.too_slow],
    )
    settings.register_profile(
        "dev",
        max_examples=100,
        deadline=None,
    )
    settings.register_profile(
        "debug",
        max_examples=10,
        verbosity=Verbosity.verbose,
    )
    settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
except ImportError:
    pass


# GH-225: stand in for MLX when it is not installed, so the MLX tests can run anywhere.
#
# mlx is Apple-Silicon-only and CI runs ubuntu-latest, so `import mlx` there raises
# ModuleNotFoundError — 2 failures and 6 fixture errors across tests/test_mlx_cache_cap.py
# and tests/test_mlx_instrumentation.py. It is equally absent from a local venv built
# without the `embeddings` extra, which is what `pip install -e ".[calendar,server]"` gives.
#
# Those tests do not need MLX to work. Every one of them replaces it with a MagicMock or a
# hand-written double (MockMLXCore / MockMLXCoreForCap); the real `import mlx` exists only to
# obtain the module OBJECT that patch.object() then rebinds. The two test NAMES that read like
# they need a missing MLX -- test_degrades_safely_when_mlx_unavailable,
# test_instrumentation_degrades_when_mlx_absent -- are about MLX's methods RAISING
# (RuntimeError("no Metal device")) and about telemetry not becoming a new crash path. Neither
# is about the package being uninstalled, so skipping them on CI would remove real coverage of
# the degradation paths rather than deferring an environment problem.
#
# `core` is bound as an ATTRIBUTE of the parent, not merely registered in sys.modules. This is
# load-bearing and is documented in test_mlx_instrumentation.py:13-17: `import mlx.core as mx`
# resolves through getattr(mlx, "core"), so a sys.modules-only stub is ignored, real MLX gets
# exercised, and the mock's counters silently stay at zero.
#
# Guarded by ImportError so a machine WITH MLX (this project's target platform) keeps testing
# against the real package; the stub is a fallback, never an override.
# Each stub carries a real `__spec__`. `types.ModuleType` leaves it None, and a
# sys.modules entry with `__spec__ is None` makes `importlib.util.find_spec()`
# raise `ValueError: mlx.__spec__ is None` rather than return None. Nothing
# called find_spec on "mlx" until GH-81 put sentence-transformers in the CI
# install: it pulls `transformers`, whose utils/generic.py runs
# `is_mlx_available()` at import time, which is that exact call. The three
# tests/test_embedder*.py tests died on it. With a spec present, transformers
# proceeds to `importlib.metadata.version("mlx")`, gets PackageNotFoundError,
# and correctly concludes MLX is absent — which is the truth on CI.
try:  # pragma: no cover - depends on the host platform
    import mlx  # noqa: F401
    import mlx.core  # noqa: F401
except ImportError:  # pragma: no cover - the CI / no-extras path
    _mlx_stub = types.ModuleType("mlx")
    _mlx_core_stub = types.ModuleType("mlx.core")
    # submodule_search_locations marks "mlx" as a package, so "mlx.core" is a
    # coherent submodule name rather than an attribute of a plain module.
    _mlx_stub.__spec__ = importlib.machinery.ModuleSpec("mlx", loader=None, is_package=True)
    _mlx_core_stub.__spec__ = importlib.machinery.ModuleSpec("mlx.core", loader=None)
    _mlx_stub.core = _mlx_core_stub
    sys.modules.setdefault("mlx", _mlx_stub)
    sys.modules.setdefault("mlx.core", _mlx_core_stub)

#: GH-178 quarantine. These failed at GH-124's own final commit (536de83,
#: 2026-07-11) and were merged red — nothing caught it because CI did not run on
#: `development` until GH-177. Verified to fail identically on macOS and on clean
#: Ubuntu CI, so they are real product bugs, not environment artifacts.
#:
#: They are quarantined rather than deleted so CI regains signal NOW: a red run
#: means *new* breakage instead of the same 10 forever, which is the state that
#: trains people to ignore CI. This list must shrink to empty — every entry is a
#: real defect in commit-threshold auto-promotion.
#:
#: DO NOT add to this list to make a red build green. Fix the test or the code.
KNOWN_FAILING_GH178 = {
    "tests/test_auto_promote.py::AutoPromoteTests::test_activity_commits_sum_across_scan_dates",
    "tests/test_auto_promote.py::AutoPromoteTests::test_auto_promoted_row_survives_activity_inference_sync",
    "tests/test_auto_promote.py::AutoPromoteTests::test_cloud_agent_commits_count_toward_threshold",
    "tests/test_auto_promote.py::AutoPromoteTests::test_direct_push_commits_count_not_just_pr_commits",
    "tests/test_auto_promote.py::AutoPromoteTests::test_idempotent_rerun_does_not_duplicate",
    "tests/test_auto_promote.py::AutoPromoteTests::test_name_collision_disambiguates_instead_of_overwriting",
    "tests/test_auto_promote.py::AutoPromoteTests::test_operator_push_and_bot_commits_combine",
    "tests/test_auto_promote.py::AutoPromoteTests::test_promotes_repo_at_threshold",
    "tests/test_auto_promote.py::AutoPromoteTests::test_promotion_fires_auth_log_alert",
    "tests/test_project_inference.py::ProjectInferenceTests::test_infers_binoid_from_github_and_ltvera_from_calendar_only",
}


# GH-250 / GH-42: `metal_available()` (probes for a usable Metal device
# OUT OF PROCESS, since MLX aborts rather than raising when none is reachable)
# now lives in rebalance.lib.metal_probe so both this fixture and the
# production embedder (src/rebalance/ingest/embedder.py) share one
# implementation instead of drifting copies. See that module's docstring for
# the full abort-vs-raise explanation.


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_metal: needs a real Metal device. Skipped when MLX cannot "
        "create one — probed out-of-process because MLX aborts rather than "
        "raising, which no in-test guard can catch (GH-250).",
    )


def pytest_collection_modifyitems(config, items):
    """Mark the GH-178 quarantine xfail, non-strict; skip Metal-only tests.

    Non-strict on purpose: if one starts passing the run stays green (XPASS) and
    the entry is simply stale. Strict would turn someone else's unrelated fix
    into a red build, which is the opposite of the point.
    """
    # Probe lazily: only pay for the subprocess if something actually asks.
    metal_skip = None
    for item in items:
        if item.nodeid in KNOWN_FAILING_GH178:
            item.add_marker(
                pytest.mark.xfail(
                    reason="GH-178: known-failing since GH-124 (536de83); quarantined by GH-177",
                    strict=False,
                )
            )
        if item.get_closest_marker("requires_metal") is not None:
            if metal_skip is None:
                metal_skip = (
                    pytest.mark.skip(
                        reason="no usable Metal device (probed out-of-process; "
                        "MLX would abort this run rather than raise) — GH-250"
                    )
                    if not metal_available()
                    else False
                )
            if metal_skip is not False:
                item.add_marker(metal_skip)


@pytest.fixture(autouse=True)
def _disable_job_guard(monkeypatch):
    """Turn off the GH-172 embedding guard for the whole suite.

    The guard takes a real ``flock`` and starts a memory watchdog whose
    ``preflight()`` REFUSES to start when the machine is low on available
    memory. Left on, tests that call ``embed_pending``/``embed_chunks`` would
    fail spuriously on a busy machine and serialise against any real ingest
    running on the same box. Guard behaviour itself is covered explicitly in
    ``tests/test_job_guard_wiring.py``, which re-enables it per-test.
    """
    monkeypatch.setenv("REBALANCE_JOB_GUARD", "0")


@pytest.fixture(autouse=True)
def _isolate_secret_store(tmp_path_factory):
    """Redirect the out-of-repo secret store to a fresh tmp dir for EACH test.

    The GitHub/Figma dual-store helpers (`config.py`) now write/read the
    permission-enforced secret store at `~/.config/rebalance-os/secrets`. Without
    isolation, suite runs pollute the operator's real secret dir and — because
    secret files are last-write-wins (unlike the append-only auth log) — leak
    values across tests. Per-test scope gives every test a clean store.
    `secret_store.secret_store_root()` honors `REBALANCE_SECRET_STORE_DIR`; tests
    that need a specific path override `secret_store.SECRET_STORE_DIR` (module
    seam), which takes precedence.
    """
    store_dir = tmp_path_factory.mktemp("secret_store")
    previous = os.environ.get("REBALANCE_SECRET_STORE_DIR")
    os.environ["REBALANCE_SECRET_STORE_DIR"] = str(store_dir)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("REBALANCE_SECRET_STORE_DIR", None)
        else:
            os.environ["REBALANCE_SECRET_STORE_DIR"] = previous


@pytest.fixture(autouse=True, scope="session")
def _isolate_auth_log(tmp_path_factory):
    """Redirect the unified auth-activity log to a throwaway tmp dir for the
    whole test session.

    Several code paths (gmail/calendar `_load_credentials`, the 403 scope probe,
    etc.) call `auth_log` helpers that append to `temp/logs/auth_activity.jsonl`.
    Without this, running the suite injects fake `token_missing` /
    `scope_insufficient` events into the *real* log, which then shows up as false
    failures in `rebalance doctor`. `auth_log._log_dir()` honors
    `REBALANCE_AUTH_LOG_DIR`, so pointing it at a tmp dir keeps the suite from
    touching the repo's log.
    """
    log_dir = tmp_path_factory.mktemp("auth_log")
    previous = os.environ.get("REBALANCE_AUTH_LOG_DIR")
    os.environ["REBALANCE_AUTH_LOG_DIR"] = str(log_dir)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("REBALANCE_AUTH_LOG_DIR", None)
        else:
            os.environ["REBALANCE_AUTH_LOG_DIR"] = previous


@pytest.fixture(autouse=True, scope="session")
def _disable_keyring():
    """Route every keyring helper to its no-op path for the whole session.

    `config.py` reads credentials with `keyring.get_password(KEYRING_SERVICE, key)`
    (`KEYRING_SERVICE = "rebalance-os"`). On macOS that is the real login Keychain,
    so any test that touches a config getter triggers a Security-framework
    authorization prompt. Keychain ACLs are per-(binary, item), and there is one
    item per credential (github / calendar / gmail / figma / sleuth / gemini), so
    "Always Allow" grants one item to one interpreter and the next request prompts
    again — an unattended `pytest` run stalls on a prompt loop it cannot answer.

    This never surfaced in CI because CI runs on ubuntu-latest, where `keyring` has
    no Keychain backend and `config.py`'s `except Exception  # noqa: BLE001` swallows
    the failure. The suite was therefore only cleanly runnable on Linux, on a project
    that requires macOS.

    `REBALANCE_NO_KEYRING` is the seam `config.py:42` already provides for this. The
    dedicated keyring tests (`test_gmail_keyring.py`, `test_sleuth_keyring.py`,
    `test_calendar_keyring.py`, `test_config_github_token.py`) patch the `keyring`
    module directly, so they are unaffected; tests that want the stricter hermetic
    mode still opt in per-test via `patch.dict` (`test_lifecycle_contract.py:211`).
    """
    previous = os.environ.get("REBALANCE_NO_KEYRING")
    os.environ["REBALANCE_NO_KEYRING"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("REBALANCE_NO_KEYRING", None)
        else:
            os.environ["REBALANCE_NO_KEYRING"] = previous

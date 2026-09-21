"""GH-236: diagnose a broken declared-runtime interpreter once per fleet."""

from __future__ import annotations

import plistlib
import shlex
from pathlib import Path
from unittest.mock import patch

from rebalance import doctor
from rebalance.doctor import FAIL, OK, WARN, _check_scheduler_runtime_interpreter


def _write_plist(agents: Path, name: str, arguments: list[str], *, label: str | None = None) -> None:
    payload = {
        "Label": label or f"com.rebalance-os.{name}",
        "ProgramArguments": arguments,
    }
    with (agents / f"com.rebalance-os.{name}.plist").open("wb") as fh:
        plistlib.dump(payload, fh)


def _runtime(tmp_path: Path) -> tuple[Path, Path, Path]:
    runtime = tmp_path / "declared runtime"
    python = runtime / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    agents = tmp_path / "agents"
    agents.mkdir()
    root_file = tmp_path / "runtime-root"
    root_file.write_text(str(runtime) + "\n", encoding="utf-8")
    return runtime, python, agents


def _check(tmp_path: Path, agents: Path):
    runtime = tmp_path / "declared runtime"
    root_file = tmp_path / "runtime-root"
    root_file.write_text(str(runtime) + "\n", encoding="utf-8")
    with patch.object(doctor, "RUNTIME_ROOT_FILE", root_file):
        return _check_scheduler_runtime_interpreter(agents)


def test_healthy_interpreter_counts_each_installed_job_once(tmp_path: Path) -> None:
    runtime, python, agents = _runtime(tmp_path)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o755)
    _write_plist(agents, "health-check", [str(python), str(python), "job_guard.py"])
    _write_plist(agents, "github-sync", [str(python), "job_guard.py"])

    checks = _check(tmp_path, agents)

    assert len(checks) == 1
    assert checks[0].status == OK
    assert "2 installed job(s)" in checks[0].detail
    assert str(runtime) in checks[0].detail


def test_missing_interpreter_fails_with_declared_root_repair(tmp_path: Path) -> None:
    runtime, python, agents = _runtime(tmp_path)
    _write_plist(agents, "github-sync", [str(python), "job_guard.py"])

    check = _check(tmp_path, agents)[0]

    assert check.status == FAIL
    assert "1 installed job(s)" in check.detail
    assert "missing" in check.detail
    assert f"cd {shlex.quote(str(runtime))}" in check.hint
    assert ".[embeddings,calendar,server,dev]" in check.hint
    assert "bash scripts/stack.sh verify" in check.hint
    assert "bash scripts/stack.sh restart" in check.hint


def test_dangling_symlink_fails_specifically(tmp_path: Path) -> None:
    _, python, agents = _runtime(tmp_path)
    python.symlink_to("python3.14")
    _write_plist(agents, "pulse-sync", [str(python), "job_guard.py"])

    check = _check(tmp_path, agents)[0]

    assert check.status == FAIL
    assert "dangling symlink" in check.detail


def test_cyclic_symlink_fails_without_aborting_doctor(tmp_path: Path) -> None:
    _, python, agents = _runtime(tmp_path)
    peer = python.with_name("python-loop")
    python.symlink_to(peer.name)
    peer.symlink_to(python.name)
    _write_plist(agents, "pulse-sync", [str(python), "job_guard.py"])

    check = _check(tmp_path, agents)[0]

    assert check.status == FAIL
    assert "cannot be resolved" in check.detail


def test_non_executable_file_and_executable_directory_both_fail(tmp_path: Path) -> None:
    _, python, agents = _runtime(tmp_path)
    _write_plist(agents, "pulse-sync", [str(python)])

    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o644)
    assert "not executable" in _check(tmp_path, agents)[0].detail

    python.unlink()
    python.mkdir()
    python.chmod(0o755)
    assert "regular file" in _check(tmp_path, agents)[0].detail


def test_malformed_installed_plist_warns_without_healthy_claim(tmp_path: Path) -> None:
    _, python, agents = _runtime(tmp_path)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o755)
    _write_plist(agents, "github-sync", [str(python)])
    (agents / "com.rebalance-os.bad.plist").write_text("<plist><dict>", encoding="utf-8")

    checks = _check(tmp_path, agents)

    assert len(checks) == 1
    assert checks[0].status == WARN
    assert "could not inspect" in checks[0].detail
    assert "bad" in checks[0].detail


def test_no_matching_interpreter_jobs_emits_no_health_claim(tmp_path: Path) -> None:
    _, _, agents = _runtime(tmp_path)
    _write_plist(agents, "foreign", ["/usr/bin/python3", "/opt/foreign/job.py"])

    assert _check(tmp_path, agents) == []


def test_policy_unmanaged_prefixed_label_is_ignored(tmp_path: Path) -> None:
    _, python, agents = _runtime(tmp_path)
    _write_plist(agents, "foreign-job", [str(python), "foreign.py"])

    assert _check(tmp_path, agents) == []

    _write_plist(agents, "github-sync", [str(python), "job_guard.py"])
    check = _check(tmp_path, agents)[0]
    assert check.status == FAIL
    assert "1 installed job(s)" in check.detail


def test_invalid_declared_root_uses_installer_fallback_checkout(tmp_path: Path) -> None:
    agents = tmp_path / "agents"
    agents.mkdir()
    invalid_root = tmp_path / "missing-runtime"
    root_file = tmp_path / "runtime-root"
    root_file.write_text(str(invalid_root) + "\n", encoding="utf-8")
    checkout_python = Path(doctor.__file__).resolve().parents[2] / ".venv" / "bin" / "python"
    _write_plist(agents, "github-sync", [str(checkout_python), "job_guard.py"])

    with patch.object(doctor, "RUNTIME_ROOT_FILE", root_file):
        check = _check_scheduler_runtime_interpreter(agents)[0]

    assert check.status == FAIL
    assert str(checkout_python) in check.detail
    assert str(invalid_root) not in check.detail


def test_missing_scheduler_policy_warns_without_claiming_health(tmp_path: Path) -> None:
    _, _, agents = _runtime(tmp_path)
    with patch("rebalance.paths.resolve_project_root", return_value=tmp_path / "missing-project"):
        checks = _check(tmp_path, agents)

    assert len(checks) == 1
    assert checks[0].status == WARN
    assert "could not read SCHEDULER.md" in checks[0].detail


def test_duplicate_labels_count_as_one_job_and_foreign_label_is_ignored(tmp_path: Path) -> None:
    _, python, agents = _runtime(tmp_path)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o755)
    _write_plist(agents, "first", [str(python)], label="com.rebalance-os.pulse-sync")
    _write_plist(agents, "second", [str(python)], label="com.rebalance-os.pulse-sync")
    _write_plist(agents, "camouflage", [str(python)], label="com.foreign.job")

    checks = _check(tmp_path, agents)

    assert len(checks) == 1
    assert checks[0].status == OK
    assert "1 installed job(s)" in checks[0].detail

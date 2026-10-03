"""Tests for the .githooks/pre-push static gate (GH-312 Rung 2 Stage 1).

Shell-subprocess style matching test_machine_path_guard.py / test_stack_script.py.
The stage interpreter is pinned through the REBALANCE_GATE_PY seam (GH-289's
RB_PYTHON pattern): stub-driven runs are hermetic in a throwaway git repo; the
one real-green run exercises the actual ruff + ratchet chain against this tree.

The historical full-lane red control (campaign gate-red-run1) went through the
pytest stage this gate deliberately does not have — the binding fail-red
evidence for the SHIPPED static stages is the parameterized controls below.
"""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-push"

REF_LINE = "refs/heads/development {sha} refs/heads/development {sha}\n"

STUB = """#!/bin/bash
# Stub stage interpreter: exits 1 when the full command matches $REBALANCE_STUB_FAIL.
if [[ -n "${REBALANCE_STUB_FAIL:-}" && "$*" == *"$REBALANCE_STUB_FAIL"* ]]; then
    echo "stub: failing on command match '$REBALANCE_STUB_FAIL'" >&2
    exit 1
fi
exit 0
"""


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True)


def _mock_repo(tmp_path: Path) -> Path:
    """A throwaway git repo with a src/ dir and one commit (so HEAD resolves)."""
    _git("init", cwd=tmp_path)
    _git("config", "user.name", "Tester", cwd=tmp_path)
    _git("config", "user.email", "test@example.com", cwd=tmp_path)
    (tmp_path / "src" / "rebalance" / "ingest").mkdir(parents=True)  # both guard search paths exist
    (tmp_path / "src" / ".keep").write_text("")
    _git("add", "src/.keep", cwd=tmp_path)
    _git("commit", "-m", "init", cwd=tmp_path)
    return tmp_path


def _stub_python(tmp_path: Path) -> Path:
    stub = tmp_path / "stubpy.sh"
    stub.write_text(STUB)
    stub.chmod(0o755)
    return stub


# Control variables the gate honors — scrubbed from the inherited environment so a
# hostile ambient value (an always-green REBALANCE_GATE_PY, a set bypass flag, a
# leftover stub-failure match) cannot quietly redirect a test that did not ask for it.
CONTROL_VARS = ("REBALANCE_GATE_PY", "REBALANCE_SKIP_PREPUSH_GATE", "REBALANCE_STUB_FAIL")


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in CONTROL_VARS}


def _run_hook(repo: Path, stdin: str, env_extra: dict[str, str], hook: Path = HOOK):
    env = _clean_env()
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(hook), "origin", "placeholder-url"],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=env,
    )


def _receipts(repo: Path) -> list[dict]:
    receipt = repo / "temp" / "gate-receipts.jsonl"
    assert receipt.exists(), "gate wrote no receipt"
    return [json.loads(line) for line in receipt.read_text().splitlines() if line.strip()]


def test_hook_is_tracked_and_armed():
    """Stage 1 ships executable — mode 755 in git and on disk."""
    mode = HOOK.stat().st_mode
    assert mode & stat.S_IXUSR, "hook must be armed (executable) for opted-in clones"
    out = subprocess.run(
        ["git", "ls-files", "-s", ".githooks/pre-push"], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True
    ).stdout
    assert out.split()[0] == "100755", f"git mode must be 100755, got: {out!r}"


def test_verify_reports_disarmed_state(tmp_path: Path):
    """A 0644 hook INSTALLED at the checked path: git skips it, --verify must say so.

    The hook sits at .githooks/pre-push with hooksPath configured and the
    interpreter present, so the executable-bit check is the isolated failure —
    this control goes red if the check is ever weakened from -x to -f.
    """
    repo = _mock_repo(tmp_path)
    hooks = repo / ".githooks"
    hooks.mkdir()
    hook = hooks / "pre-push"
    shutil.copy(HOOK, hook)
    hook.chmod(0o644)
    _git("config", "core.hooksPath", ".githooks", cwd=repo)
    res = subprocess.run(
        ["bash", str(hook), "--verify"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={**_clean_env(), "REBALANCE_GATE_PY": str(_stub_python(tmp_path))},
    )
    assert res.returncode == 1
    assert "DISARMED" in res.stdout
    assert "core.hooksPath=.githooks" in res.stdout  # only the permission check failed


def test_verify_reports_armed_state(tmp_path: Path):
    repo = _mock_repo(tmp_path)
    hooks = repo / ".githooks"
    hooks.mkdir()
    hook = hooks / "pre-push"
    shutil.copy(HOOK, hook)
    hook.chmod(0o755)
    _git("config", "core.hooksPath", ".githooks", cwd=repo)
    stub = _stub_python(tmp_path)
    res = subprocess.run(
        ["bash", str(hook), "--verify"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={**_clean_env(), "REBALANCE_GATE_PY": str(stub)},
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "armed" in res.stdout and "interpreter present" in res.stdout


def test_noop_on_empty_stdin(tmp_path: Path):
    repo = _mock_repo(tmp_path)
    res = _run_hook(repo, "", {"REBALANCE_GATE_PY": str(_stub_python(tmp_path))})
    assert res.returncode == 0
    rec = _receipts(repo)[-1]
    assert rec["kind"] == "noop"


def test_noop_on_delete_only_push(tmp_path: Path):
    repo = _mock_repo(tmp_path)
    zero = "0" * 40
    res = _run_hook(
        repo, f"refs/heads/x {zero} refs/heads/x {zero}\n", {"REBALANCE_GATE_PY": str(_stub_python(tmp_path))}
    )
    assert res.returncode == 0
    rec = _receipts(repo)[-1]
    assert rec["kind"] == "noop" and "delete-only" in rec["detail"]


def test_bypass_is_logged_with_fixed_detail(tmp_path: Path):
    """P1: logged, never silent — and the bypass VALUE never enters the receipt (R1)."""
    repo = _mock_repo(tmp_path)
    sha = (
        subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
        or "0" * 40
    )
    res = _run_hook(
        repo,
        REF_LINE.format(sha=sha or "0" * 40),
        {"REBALANCE_GATE_PY": str(_stub_python(tmp_path)), "REBALANCE_SKIP_PREPUSH_GATE": 'naughty " value'},
    )
    assert res.returncode == 0
    assert "BYPASSED (logged" in res.stdout
    rec = _receipts(repo)[-1]
    assert rec["kind"] == "bypass"
    assert rec["detail"] == "bypass requested via REBALANCE_SKIP_PREPUSH_GATE"
    assert "naughty" not in json.dumps(rec), "bypass value must not be interpolated into the receipt"


def test_fail_closed_on_missing_interpreter(tmp_path: Path):
    repo = _mock_repo(tmp_path)
    sha = (
        subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
        or "0" * 40
    )
    env = _clean_env()
    res = subprocess.run(
        ["bash", str(HOOK), "origin", "placeholder-url"],
        input=REF_LINE.format(sha=sha or "0" * 40),
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=env,
    )
    assert res.returncode == 1
    assert "FAIL CLOSED" in res.stderr
    rec = _receipts(repo)[-1]
    assert rec["kind"] == "fail-closed" and rec["exit"] == 1


@pytest.mark.parametrize(
    "fail_match,stage",
    [
        ("ruff check", "ruff-check"),
        ("ruff format", "ruff-format"),
        ("check_script_inventory", "ratchet-script-inventory"),
        ("check_near_duplicates", "ratchet-near-duplicates"),
    ],
)
def test_gate_blocks_on_static_stage_failure(tmp_path: Path, fail_match: str, stage: str):
    """The binding red control for the shipped static stages (review R2)."""
    repo = _mock_repo(tmp_path)
    sha = (
        subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
        or "0" * 40
    )
    res = _run_hook(
        repo,
        REF_LINE.format(sha=sha or "0" * 40),
        {
            "REBALANCE_GATE_PY": str(_stub_python(tmp_path)),
            "REBALANCE_STUB_FAIL": fail_match,
        },
    )
    assert res.returncode == 1, f"gate must block, got {res.returncode}: {res.stdout}"
    assert f"FAIL stage={stage}" in res.stderr
    rec = _receipts(repo)[-1]
    assert rec["kind"] == "gate" and rec["exit"] == 1
    assert rec["detail"]["stages"][stage]["exit"] == 1


def test_receipt_write_failure_is_loud_and_never_claims_logged(tmp_path: Path):
    """R1: a regular file at temp/ makes every receipt write fail — say so, loudly."""
    repo = _mock_repo(tmp_path)
    (repo / "temp").write_text("not a directory\n")
    res = _run_hook(repo, "", {"REBALANCE_GATE_PY": str(_stub_python(tmp_path))})
    assert res.returncode == 0  # noop path still functions
    assert "receipt write FAILED" in res.stderr
    assert "NOT logged" in res.stderr or "NOT logged" in res.stdout


def test_receipt_write_failure_bypass_never_claims_logged(tmp_path: Path):
    """The bypass success message must not claim "(logged" when the write failed."""
    repo = _mock_repo(tmp_path)
    (repo / "temp").write_text("not a directory\n")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
    res = _run_hook(
        repo,
        REF_LINE.format(sha=sha),
        {"REBALANCE_GATE_PY": str(_stub_python(tmp_path)), "REBALANCE_SKIP_PREPUSH_GATE": "1"},
    )
    assert res.returncode == 0
    assert "receipt write FAILED" in res.stderr
    assert "BYPASSED (logged" not in res.stdout
    assert "NOT logged" in res.stdout


def test_gate_fails_closed_when_guard_search_errors(tmp_path: Path):
    """A missing searched directory is a guard ERROR, not a silent pass.

    The pre-CR pipelines discarded the search grep's own exit status, so a
    missing src/rebalance/ read as "no match" and the guard passed vacuously.
    """
    repo = _mock_repo(tmp_path)
    shutil.rmtree(repo / "src" / "rebalance")
    sha = (
        subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
        or "0" * 40
    )
    res = _run_hook(repo, REF_LINE.format(sha=sha), {"REBALANCE_GATE_PY": str(_stub_python(tmp_path))})
    assert res.returncode == 1, f"gate must block on guard search error, got {res.returncode}"
    assert "search error" in res.stderr
    assert "guard=raw-datetime" in res.stderr
    rec = _receipts(repo)[-1]
    assert rec["kind"] == "gate" and rec["exit"] == 1
    assert rec["detail"]["stages"]["grep-guards"]["exit"] == 1


def test_gate_green_with_stub(tmp_path: Path):
    repo = _mock_repo(tmp_path)
    sha = (
        subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
        or "0" * 40
    )
    res = _run_hook(repo, REF_LINE.format(sha=sha or "0" * 40), {"REBALANCE_GATE_PY": str(_stub_python(tmp_path))})
    assert res.returncode == 0, res.stdout + res.stderr
    rec = _receipts(repo)[-1]
    assert rec["kind"] == "gate" and rec["exit"] == 0
    assert all(s["exit"] == 0 for s in rec["detail"]["stages"].values())


def test_gate_green_for_real(tmp_path: Path):
    """One real run of the actual chain (ruff + five ratchets + guards) on this tree.

    Skipped where the repo venv lacks ruff (e.g. hosted CI test jobs — the lint
    job there already runs the same checks); stub tests above carry the logic.
    """
    venv_py = REPO_ROOT / ".venv" / "bin" / "python"
    if not (
        venv_py.exists()
        and subprocess.run([str(venv_py), "-m", "ruff", "--version"], capture_output=True).returncode == 0
    ):
        pytest.skip("repo venv with ruff not available")
    receipt = REPO_ROOT / "temp" / "gate-receipts.jsonl"
    before = receipt.read_text().splitlines() if receipt.exists() else []
    res = _run_hook(
        REPO_ROOT,
        REF_LINE.format(
            sha=subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True
            ).stdout.strip()
        ),
        {"REBALANCE_GATE_PY": str(venv_py)},  # explicitly the repo venv, never an ambient override
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "PASS" in res.stdout
    lines = receipt.read_text().splitlines()
    assert len(lines) == len(before) + 1
    rec = json.loads(lines[-1])
    assert rec["kind"] == "gate" and rec["exit"] == 0
    assert set(rec["detail"]["stages"]) == {
        "ruff-check",
        "ruff-format",
        "ratchet-script-inventory",
        "ratchet-machine-paths",
        "ratchet-banned-imports",
        "ratchet-read-layer",
        "ratchet-near-duplicates",
        "grep-guards",
    }

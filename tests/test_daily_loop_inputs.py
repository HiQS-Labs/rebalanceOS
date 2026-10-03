"""GH-310 (c): opt-in /daily scanner inputs — close-loop flags and the RELEASES ledger scan."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "daily" / "scripts"
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

import scan_unclosed_loops as scanner  # noqa: E402

REPO = "Acme/widget"
FIXTURE = {
    "status": "ok",
    "flags": [
        {"flag": "stale_pr", "item_type": "pull_request", "number": 10, "title": "pr 10", "html_url": "u10"},
        {"flag": "pr_needs_refinement", "item_type": "pull_request", "number": 10, "title": "pr 10", "html_url": "u10"},
        {"flag": "forgotten_draft", "item_type": "pull_request", "number": 11, "title": "pr 11", "html_url": "u11"},
        {"flag": "stale_pr", "item_type": "pull_request", "number": 12, "title": "pr 12", "html_url": "u12"},
        {"flag": "started_not_shipped", "item_type": "issue", "number": 20, "title": "issue 20", "html_url": "u20"},
        {"flag": "closed_without_delivery", "item_type": "issue", "number": 30, "title": "issue 30", "html_url": "u30"},
    ],
    "releases": {
        "ledgers_found": 2,
        "tasks": [
            {"status": "in-progress", "gh_number": 20, "global_id": "R-20", "title": "issue 20", "issue_url": "u20"},
            {"status": "in-progress", "gh_number": 21, "global_id": "R-21", "title": "issue 21", "issue_url": "u21"},
            {"status": "parked", "gh_number": 22, "global_id": "R-22", "title": "issue 22", "issue_url": "u22"},
        ],
        "drift": [{"kind": "issue_closed", "gh_number": 21, "title": "issue 21", "evidence": "Ledger marks #21 ..."}],
    },
}
LIVE_PRS = {
    REPO: [
        {"repo": REPO, "number": 10, "state": "OPEN"},
        {"repo": REPO, "number": 11, "state": "MERGED"},
    ]
}


def _fake_cli(tmp_path: Path, payload: dict | None) -> Path:
    data = tmp_path / "payload.json"
    data.write_text(json.dumps(payload) if payload is not None else "")
    script = tmp_path / "rebalance"
    script.write_text(
        f"#!{sys.executable}\nimport sys\n"
        f"text = open({str(data)!r}).read()\n"
        "if '--repo' in sys.argv and sys.argv[sys.argv.index('--repo') + 1] == 'Acme/widget' and text:\n"
        "    print(text)\nelse:\n    sys.exit(1)\n"
    )
    script.chmod(0o755)
    return script


def test_on_mode_dedupes_tags_and_reverifies(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("REBALANCE_BIN", str(_fake_cli(tmp_path, FIXTURE)))
    monkeypatch.setattr(scanner, "_live_open_issue_numbers", lambda repo: {20, 22})
    out = scanner.collect_close_loop_inputs(
        [REPO, "Acme/broken"], LIVE_PRS, set(), close_loop=True, releases_dirs=str(tmp_path)
    )
    loops = {(i["repo"], i["number"]): i["sources"] for i in out["flagged_loops"]}
    assert loops == {
        (REPO, 10): ["close-loop:stale_pr", "close-loop:pr_needs_refinement"],
        (REPO, 20): ["close-loop:started_not_shipped", f"releases:{REPO}#R-20"],
    }  # merged PR 11 and closed issue 21 are not open loops; PR 12 is unverifiable
    assert out["unverified"] == 1
    assert sorted(q["source"] for q in out["questions"]) == [
        "close-loop:closed_without_delivery",
        "releases-drift:issue_closed",
    ]
    assert out["inputs"] == {"close-loop": "ok", "releases": "ok"}
    assert out["failed_repos"] == ["Acme/broken"]  # partial failure is reported, not silent
    assert "input partial (1 of 2 repo(s) failed: Acme/broken)" in capsys.readouterr().err


def test_missing_cli_skips_each_input_with_one_line(monkeypatch, capsys):
    monkeypatch.setenv("REBALANCE_BIN", "")
    monkeypatch.setattr(scanner.shutil, "which", lambda name: None)
    out = scanner.collect_close_loop_inputs([REPO], LIVE_PRS, set(), close_loop=True, releases_dirs="/x")
    assert out["flagged_loops"] == []
    assert out["inputs"] == {
        "close-loop": "skipped: rebalance CLI not found",
        "releases": "skipped: rebalance CLI not found",
    }
    assert capsys.readouterr().err.count("input skipped") == 2


def _run_main(monkeypatch, capsys, argv: list[str]) -> dict:
    monkeypatch.setattr(scanner, "PRIMARY_WATCHED_REPOS", [REPO])
    monkeypatch.setattr(scanner, "discover_git_repos", lambda **kwargs: [])
    monkeypatch.setattr(scanner, "fetch_prs_for_remotes", lambda remotes: (LIVE_PRS, []))
    monkeypatch.setattr(scanner, "_live_open_issue_numbers", lambda repo: {20})
    monkeypatch.setattr(sys, "argv", ["scan_unclosed_loops.py", "--json", "--no-ledger-write", *argv])
    assert scanner.main() == 0
    return json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("env_on", [False, True])
def test_main_off_and_degraded_outputs_are_unchanged(monkeypatch, capsys, env_on):
    monkeypatch.delenv("REBALANCE_DAILY_CLOSE_LOOP", raising=False)
    monkeypatch.delenv("REBALANCE_RELEASES_SCAN_DIRS", raising=False)
    baseline = _run_main(monkeypatch, capsys, [])
    if env_on:  # enabled, but the CLI is missing: degrade to exactly the old output
        monkeypatch.setenv("REBALANCE_BIN", "")
        monkeypatch.setattr(scanner.shutil, "which", lambda name: None)
        degraded = _run_main(monkeypatch, capsys, ["--close-loop"])
        assert degraded == baseline
    assert set(baseline) == {
        "summary_line",
        "counts",
        "unpred_branches",
        "open_prs",
        "unpushed_branches",
        "ledger_path",
    }
    assert "flagged loops" not in baseline["summary_line"]


def test_main_on_adds_fields_and_summary(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("REBALANCE_RELEASES_SCAN_DIRS", raising=False)
    monkeypatch.setenv("REBALANCE_BIN", str(_fake_cli(tmp_path, FIXTURE)))
    payload = _run_main(monkeypatch, capsys, ["--close-loop"])
    assert payload["counts"]["flagged_loops"] == 2  # PR 10 + issue 20 (close-loop source only)
    assert "2 flagged loops (close-loop/releases)" in payload["summary_line"]
    assert payload["inputs"] == {"close-loop": "ok"}

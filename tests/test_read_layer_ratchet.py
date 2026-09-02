"""GH-150: the read-layer ratchets and the near-duplicate canary.

The ratchets in utils/pdda/check_read_layer.py pin today's sprawl (SQL emitters,
LLM clients, day-window helpers) to an exact per-file baseline; the canary in
utils/pdda/check_near_duplicates.py pins cross-file re-typed functions. Additions
fail (new debt), shrinks fail (stale baseline that must be tightened deliberately
via --update-baseline, so a win is recorded and cannot silently regress). These
tests constrain both directions, the pragma exemption, and the fail-closed path —
the same contract tests/test_sqlite_gateway_ratchet.py established for GH-136.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
READ_LAYER_PATH = REPO_ROOT / "utils" / "pdda" / "check_read_layer.py"
NEAR_DUP_PATH = REPO_ROOT / "utils" / "pdda" / "check_near_duplicates.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def read_layer():
    return _load(READ_LAYER_PATH, "check_read_layer_ratchet")


@pytest.fixture()
def near_dup():
    return _load(NEAR_DUP_PATH, "check_near_duplicates_ratchet")


def _make_tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp_path


def test_repo_matches_baseline_exactly(read_layer) -> None:
    """The live tree must equal the committed baseline in all three sections."""
    baseline = json.loads((REPO_ROOT / "utils/pdda/read_layer_baseline.json").read_text())
    actual = read_layer.scan_all(REPO_ROOT)
    assert read_layer.compare_to_baseline(actual, baseline) == []


def test_new_site_fails_and_pragma_exempts(read_layer, tmp_path: Path) -> None:
    root = _make_tree(tmp_path, {"src/reports/new.py": 'q = "SELECT COUNT(*) FROM github_items"\n'})
    baseline: dict = {"sql_emitters": {}, "llm_clients": {}, "day_windows": {}}
    findings = read_layer.compare_to_baseline(read_layer.scan_all(root), baseline)
    assert any("NEW sql_emitters" in f for f in findings)

    _make_tree(tmp_path, {"src/reports/new.py": 'q = "x"  # READ-LAYER-OK: storage-layer probe (ticket)\n'})
    assert read_layer.scan_all(root) == {"sql_emitters": {}, "llm_clients": {}, "day_windows": {}}


def test_pragma_without_reason_fails_closed(read_layer, tmp_path: Path) -> None:
    root = _make_tree(tmp_path, {"src/reports/new.py": 'q = "FROM github_items"  # READ-LAYER-OK:\n'})
    assert read_layer.scan_all(root)["sql_emitters"] == {"src/reports/new.py": 1}


def test_growth_and_shrink_both_fail(read_layer, tmp_path: Path) -> None:
    root = _make_tree(tmp_path, {"src/a.py": "x = 1\ny = 2\n".replace("x = 1", "SELECT 1 FROM github_commits")})
    baseline = {"sql_emitters": {"src/a.py": 1}, "llm_clients": {}, "day_windows": {}}

    _make_tree(root, {"src/a.py": "a = 'SELECT 1 FROM github_commits'\nb = 'SELECT 2 FROM github_items'\n"})
    findings = read_layer.compare_to_baseline(read_layer.scan_all(root), baseline)
    assert any("grew 1 -> 2" in f for f in findings)

    _make_tree(root, {"src/a.py": "clean = True\n"})
    findings = read_layer.compare_to_baseline(read_layer.scan_all(root), baseline)
    assert any("stale baseline — file is now clean" in f for f in findings)


def test_llm_ratchet_ignores_canonical_clients(read_layer, tmp_path: Path) -> None:
    root = _make_tree(
        tmp_path,
        {
            "src/rebalance/ingest/querier.py": "URL = 'https://generativelanguage.googleapis.com/x'\n",
            "src/rebalance/ingest/claude_cloud.py": "URL = 'https://api.anthropic.com/v1/code/sessions'\n",
            "src/rebalance/ingest/other.py": "URL = 'https://generativelanguage.googleapis.com/y'\n",
        },
    )
    counts = read_layer.scan_all(root)["llm_clients"]
    assert counts == {"src/rebalance/ingest/other.py": 1}


def test_near_duplicates_repo_matches_baseline(near_dup) -> None:
    baseline = json.loads((REPO_ROOT / "utils/pdda/near_duplicates_baseline.json").read_text())
    assert near_dup.findings_from(near_dup.scan_functions(REPO_ROOT)) == baseline


def test_near_duplicate_detection_and_resolution(near_dup, tmp_path: Path) -> None:
    body = "def f(a, b):\n    total = 0\n    for item in b:\n        if item > a:\n            total += item\n    return total\n"
    # Pad past the MIN_NODES threshold with structure both copies share.
    pad = "".join(f"    x{i} = a + {i} * 2\n    if x{i} > 3:\n        total += x{i}\n" for i in range(8))
    fn_a = body.replace("return total", pad + "    return total\n")
    fn_b = fn_a.replace("def f(", "def differently_named(")  # rename only: still a match
    root = _make_tree(
        tmp_path,
        {
            "src/rebalance/one.py": fn_a,
            "src/rebalance/two.py": fn_b,
        },
    )
    findings = near_dup.findings_from(near_dup.scan_functions(root))
    assert findings == ["src/rebalance/one.py:f ~ src/rebalance/two.py:differently_named"]

    baseline = list(findings)
    assert near_dup.findings_from(near_dup.scan_functions(root)) == baseline

    # Diverge the second copy structurally: the finding disappears, and the ratchet
    # flags the stale baseline entry so the fix is recorded.
    _make_tree(root, {"src/rebalance/two.py": "def differently_named(a, b):\n    return sum(b)\n"})
    assert near_dup.findings_from(near_dup.scan_functions(root)) == []
    assert baseline  # still present: the shrink is the caller's (main --check) finding


def test_same_file_duplicates_are_not_findings(near_dup, tmp_path: Path) -> None:
    fn = "def f(a):\n    return a + 1\n" * 1
    root = _make_tree(tmp_path, {"src/rebalance/solo.py": fn + "\n\ndef g(a):\n    return a + 1\n"})
    assert near_dup.findings_from(near_dup.scan_functions(root)) == []

"""GH-126: exact-baseline tests for datetime/subprocess import debt."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "utils" / "pdda" / "check_banned_imports.py"
BASELINE_PATH = REPO_ROOT / "utils" / "pdda" / "banned_imports_baseline.json"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_banned_imports_ratchet", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def checker():
    return _load_checker()


def _make_tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp_path


def test_current_tree_matches_import_baseline_exactly(checker):
    actual = checker.scan_banned_imports(REPO_ROOT)
    baseline = checker.load_banned_imports_baseline(BASELINE_PATH)
    assert actual == baseline
    assert checker.compare_banned_imports_to_baseline(actual, baseline) == []


def test_cli_check_passes_on_current_tree():
    result = subprocess.run(
        [sys.executable, str(CHECKER_PATH), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "banned-import ratchet: clean" in result.stdout


def test_new_import_family_is_new_debt(checker, tmp_path):
    root = _make_tree(tmp_path, {"src/rebalance/ingest/probe.py": "import datetime\n"})
    actual = checker.scan_banned_imports(root)
    assert actual == {"src/rebalance/ingest/probe.py": {"datetime": 1}}
    findings = checker.compare_banned_imports_to_baseline(actual, {})
    assert len(findings) == 1
    assert "NEW datetime import debt" in findings[0]


def test_import_growth_and_cleanup_both_require_baseline_update(checker, tmp_path):
    root = _make_tree(
        tmp_path,
        {"src/rebalance/ingest/probe.py": "import datetime\nimport datetime\n"},
    )
    findings = checker.compare_banned_imports_to_baseline(
        checker.scan_banned_imports(root),
        {
            "src/rebalance/ingest/probe.py": {"datetime": 1, "subprocess": 1},
            "src/rebalance/ingest/retired.py": {"datetime": 1},
        },
    )
    assert any("datetime import debt grew 1 -> 2" in finding for finding in findings)
    assert any("subprocess import debt is now clean" in finding for finding in findings)
    assert any("src/rebalance/ingest/retired.py" in finding for finding in findings)


def test_line_moves_do_not_change_identity(checker, tmp_path):
    root = _make_tree(tmp_path, {"src/rebalance/ingest/probe.py": "\n\nfrom subprocess import run\n"})
    actual = checker.scan_banned_imports(root)
    baseline = {"src/rebalance/ingest/probe.py": {"subprocess": 1}}
    assert checker.compare_banned_imports_to_baseline(actual, baseline) == []


def test_reasoned_pragma_exempts_and_empty_reason_fails(checker, tmp_path):
    root = _make_tree(
        tmp_path,
        {
            "src/rebalance/ingest/exempt.py": "import datetime  # CANONICAL-PATH-OK: stdlib type required at boundary\n",
            "src/rebalance/ingest/empty.py": "import subprocess  # CANONICAL-PATH-OK:\n",
        },
    )
    assert checker.scan_banned_imports(root) == {"src/rebalance/ingest/empty.py": {"subprocess": 1}}


def test_parse_and_read_failures_fail_closed(checker, tmp_path, monkeypatch):
    root = _make_tree(tmp_path, {"src/rebalance/ingest/broken.py": "import datetime\n"})
    real_read_text = Path.read_text

    def refusing_read_text(self, *args, **kwargs):
        if self.name == "broken.py":
            raise OSError("permission denied")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", refusing_read_text)
    with pytest.raises(SystemExit, match="cannot parse"):
        checker.scan_banned_imports(root)

    (root / "src/rebalance/ingest/broken.py").write_text("import datetime (\n", encoding="utf-8")
    monkeypatch.setattr(Path, "read_text", real_read_text)
    with pytest.raises(SystemExit, match="cannot parse"):
        checker.scan_banned_imports(root)

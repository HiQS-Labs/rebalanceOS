"""GH-136: the SQLite gateway ratchet in utils/pdda/check_banned_imports.py.

The ratchet pins every direct ``sqlite3.connect`` outside the two gateway
directories (``src/rebalance/ingest/db/`` and ``HiQS/hiqs/``) to an exact
per-file baseline. Additions are new debt and fail; shrinks mean the baseline
is stale and also fail until deliberately updated. These tests constrain both
directions plus the exemptions and the fail-closed read path.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "utils" / "pdda" / "check_banned_imports.py"
BASELINE_PATH = REPO_ROOT / "utils" / "pdda" / "sqlite_connect_baseline.json"


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


def test_current_tree_matches_baseline_exactly(checker):
    actual = checker.scan_sqlite_calls(REPO_ROOT)
    baseline = checker.load_baseline(BASELINE_PATH)
    assert actual == baseline
    assert checker.compare_to_baseline(actual, baseline) == []


def test_cli_check_passes_on_current_tree():
    result = subprocess.run(
        [sys.executable, str(CHECKER_PATH), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_new_bypass_is_new_debt(checker, tmp_path):
    root = _make_tree(tmp_path, {"src/new_thing.py": 'import sqlite3\nsqlite3.connect("x")\n'})
    actual = checker.scan_sqlite_calls(root)
    assert actual == {"src/new_thing.py": 1}
    findings = checker.compare_to_baseline(actual, {})
    assert len(findings) == 1
    assert "NEW sqlite3.connect bypass" in findings[0]


def test_growth_beyond_baseline_is_new_debt(checker, tmp_path):
    root = _make_tree(tmp_path, {"src/probe.py": "x = 1\n" + 'sqlite3.connect("y")\n' * 4})
    findings = checker.compare_to_baseline(checker.scan_sqlite_calls(root), {"src/probe.py": 3})
    growth = [f for f in findings if f.startswith("src/probe.py")]
    assert len(growth) == 1
    assert "grew" in growth[0]


def test_cleanup_requires_deliberate_baseline_tightening(checker, tmp_path):
    root = _make_tree(tmp_path, {"src/unrelated.py": "x = 1\n"})
    actual = checker.scan_sqlite_calls(root)
    findings = checker.compare_to_baseline(actual, {"src/retired.py": 2})
    stale = [f for f in findings if f.startswith("src/retired.py")]
    assert len(stale) == 1
    assert "stale baseline" in stale[0]


def test_gateway_dirs_and_tests_are_exempt(checker, tmp_path):
    root = _make_tree(
        tmp_path,
        {
            "src/rebalance/ingest/db/connection.py": 'c = sqlite3.connect("own")\n',
            "HiQS/hiqs/db.py": 'c = sqlite3.connect("own")\n',
            "tests/test_probe.py": 'c = sqlite3.connect("probe")\n',
            "HiQS/tests/test_probe.py": 'c = sqlite3.connect("probe")\n',
        },
    )
    assert checker.scan_sqlite_calls(root) == {}


def test_unreadable_file_fails_closed(checker, tmp_path, monkeypatch):
    _make_tree(tmp_path, {"src/broken.py": "x = 1\n"})
    real_read_text = Path.read_text

    def refusing_read_text(self, *args, **kwargs):
        if self.suffix == ".py" and self.name == "broken.py":
            raise OSError("permission denied")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", refusing_read_text)
    with pytest.raises(SystemExit, match="cannot read"):
        checker.scan_sqlite_calls(tmp_path)

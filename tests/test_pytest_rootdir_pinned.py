"""Guard pytest's project discovery when it is invoked outside the repository."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"


@pytest.mark.parametrize("with_stray_conftest", [False, True], ids=["foreign-cwd", "stray-conftest"])
def test_pytest_collection_uses_repository_configuration(tmp_path: Path, with_stray_conftest: bool) -> None:
    """An unrelated working directory must not replace this repo's pytest root."""
    foreign_cwd = tmp_path / "foreign"
    foreign_cwd.mkdir()
    if with_stray_conftest:
        (foreign_cwd / "conftest.py").write_text(
            "raise RuntimeError('foreign conftest must not be imported')\n", encoding="utf-8"
        )

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-v", str(TESTS_DIR)],
        cwd=foreign_cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    output = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert result.returncode == 0, output
    assert re.search(rf"^rootdir: {re.escape(str(REPO_ROOT))}$", result.stdout, re.MULTILINE), output
    assert re.search(r"^configfile: pyproject\.toml$", result.stdout, re.MULTILINE), output

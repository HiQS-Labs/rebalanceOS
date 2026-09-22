"""GH-241: Script inventory sprawl ratchet conformance tests.

Validates that utils/pdda/check_script_inventory.py strictly enforces:
1. The live tree matches script_inventory_baseline.json exactly.
2. New loose scripts under scripts/ or utils/ cause a failure (new debt blocked).
3. Script deletions cause a stale-baseline failure until --update-baseline ratchets down.
4. LaunchAgent plist template ceiling is enforced at <= 13.
5. Pragma exemption (# SCRIPT-INVENTORY-OK: <reason>) works, but fails closed on empty reason.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "utils" / "pdda" / "check_script_inventory.py"
BASELINE_PATH = REPO_ROOT / "utils" / "pdda" / "script_inventory_baseline.json"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_script_inventory_mod", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def checker():
    return _load_checker()


def test_current_tree_matches_baseline_exactly(checker):
    """The live repository scripts/ and utils/ inventory must match the committed baseline."""
    actual = checker.scan_inventory(REPO_ROOT)
    baseline = checker.load_baseline(BASELINE_PATH)
    findings = checker.compare_to_baseline(actual, baseline)
    assert findings == [], f"Script inventory divergence: {findings}"


def test_new_script_addition_fails(checker, tmp_path: Path):
    """Adding a new script without baseline update must fail."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    new_script = scripts_dir / "unapproved_reader.py"
    new_script.write_text("print('sprawl')\n", encoding="utf-8")

    actual = checker.scan_inventory(tmp_path)
    baseline = {"max_launchd_templates": 13, "launchd_templates": [], "scripts": [], "utils": []}
    findings = checker.compare_to_baseline(actual, baseline)
    assert any("NEW script detected" in f for f in findings)


def test_script_removal_fails_until_update_baseline(checker, tmp_path: Path):
    """Removing a script must fail with stale baseline until --update-baseline locks the reduction."""
    actual = {"launchd_templates": [], "scripts": [], "utils": []}
    baseline = {
        "max_launchd_templates": 13,
        "launchd_templates": [],
        "scripts": ["scripts/install_legacy.sh"],
        "utils": [],
    }
    findings = checker.compare_to_baseline(actual, baseline)
    assert any("script removed — inventory shrank" in f for f in findings)


def test_launchd_template_ceiling(checker, tmp_path: Path):
    """Exceeding the max launchd templates ceiling must fail immediately."""
    actual = {
        "launchd_templates": [f"scripts/job{i}.plist.template" for i in range(14)],
        "scripts": [],
        "utils": [],
    }
    baseline = {
        "max_launchd_templates": 13,
        "launchd_templates": [f"scripts/job{i}.plist.template" for i in range(14)],
        "scripts": [],
        "utils": [],
    }
    findings = checker.compare_to_baseline(actual, baseline)
    assert any("LaunchAgent ceiling exceeded" in f for f in findings)


def test_pragma_exemption(checker, tmp_path: Path):
    """Valid pragma with reason exempts a file; empty reason fails closed."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    exempt_script = scripts_dir / "exempt_utility.sh"
    exempt_script.write_text(
        "#!/bin/bash\n# SCRIPT-INVENTORY-OK: temporary operational bridge\necho hi\n", encoding="utf-8"
    )
    actual = checker.scan_inventory(tmp_path)
    assert "scripts/exempt_utility.sh" not in actual["scripts"]

    invalid_script = scripts_dir / "invalid_utility.sh"
    invalid_script.write_text("#!/bin/bash\n# SCRIPT-INVENTORY-OK:\necho hi\n", encoding="utf-8")
    actual2 = checker.scan_inventory(tmp_path)
    assert "scripts/invalid_utility.sh" in actual2["scripts"]

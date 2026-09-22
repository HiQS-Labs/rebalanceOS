"""Script and LaunchAgent inventory sprawl ratchet (GH-241).

Freezes the inventory of shell, python, swift, and LaunchAgent template scripts
under ``scripts/`` and ``utils/`` to prevent architectural sprawl and background
item accumulation.

Contract mirrors GH-136 (``check_banned_imports.py``) and GH-150 (``check_read_layer.py``):
- Compares live tree against an exact baseline (``script_inventory_baseline.json``).
- Additions fail (new debt): no new loose scripts allowed. New operator CLI verbs must
  be added to ``src/rebalance/cli/``, MCP tools to ``src/rebalance/mcp/``, and background
  work to the central orchestrator (``index_ops.py``).
- Shrinks fail (stale baseline): when scripts or LaunchAgents are consolidated or retired,
  the test fails until deliberately updated via ``--update-baseline``, permanently locking
  in the reduction (enforcing the 'deleting code counts as progress' KPI).
- LaunchAgent ceiling: ``launchd_templates`` count is capped at <= 13 (and ratchets downward).
- Pragma exemption: A file whose first 10 lines contain ``# SCRIPT-INVENTORY-OK: <reason>``
  (or ``// SCRIPT-INVENTORY-OK: <reason>``) is exempted. An empty reason fails closed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).with_name("script_inventory_baseline.json")

PRUNED_DIRS = {"__pycache__", "tests", ".git", "3-eyes"}
SCRIPT_EXTENSIONS = {".py", ".sh", ".swift"}
PRAGMA_RE = re.compile(r"(?:#|//)\s*SCRIPT-INVENTORY-OK:\s*(.*)$")
MAX_LAUNCHD_TEMPLATES = 13


def is_exempt(path: Path) -> bool:
    """Check if file has a valid SCRIPT-INVENTORY-OK pragma with non-empty reason."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    lines = content.splitlines()[:10]
    for line in lines:
        m = PRAGMA_RE.search(line)
        if m:
            reason = m.group(1).strip()
            if reason:
                return True
    return False


def scan_inventory(root: Path = REPO_ROOT) -> dict[str, list[str]]:
    """Scan scripts/ and utils/ for tracked script and LaunchAgent template files."""
    launchd_templates: list[str] = []
    scripts: list[str] = []
    utils: list[str] = []

    scripts_dir = root / "scripts"
    if scripts_dir.is_dir():
        for p in sorted(scripts_dir.rglob("*")):
            if not p.is_file():
                continue
            if any(part in PRUNED_DIRS for part in p.parts):
                continue
            rel = p.relative_to(root).as_posix()
            if is_exempt(p):
                continue
            if p.name.endswith(".plist.template"):
                launchd_templates.append(rel)
            elif p.suffix in SCRIPT_EXTENSIONS:
                scripts.append(rel)

    utils_dir = root / "utils"
    if utils_dir.is_dir():
        for p in sorted(utils_dir.rglob("*")):
            if not p.is_file():
                continue
            if any(part in PRUNED_DIRS for part in p.parts):
                continue
            rel = p.relative_to(root).as_posix()
            if is_exempt(p):
                continue
            if p.suffix in SCRIPT_EXTENSIONS:
                utils.append(rel)

    return {
        "launchd_templates": sorted(launchd_templates),
        "scripts": sorted(scripts),
        "utils": sorted(utils),
    }


def load_baseline(path: Path = BASELINE_PATH) -> dict:
    """Load and validate the inventory baseline."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"script-inventory ratchet: cannot load baseline {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"script-inventory ratchet: invalid baseline format in {path}")
    for section in ("launchd_templates", "scripts", "utils"):
        if section not in data or not isinstance(data[section], list):
            raise SystemExit(f"script-inventory ratchet: missing or invalid '{section}' in {path}")
    return data


def compare_to_baseline(actual: dict[str, list[str]], baseline: dict) -> list[str]:
    """Compare actual inventory to baseline and return findings."""
    findings: list[str] = []
    max_templates = baseline.get("max_launchd_templates", MAX_LAUNCHD_TEMPLATES)

    # Ceiling guard
    template_count = len(actual.get("launchd_templates", []))
    if template_count > max_templates:
        findings.append(
            f"scripts:1: LaunchAgent ceiling exceeded: {template_count} templates found, "
            f"maximum allowed is {max_templates} (GH-241)"
        )

    for section in ("launchd_templates", "scripts", "utils"):
        actual_files = set(actual.get(section, []))
        baseline_files = set(baseline.get(section, []))

        # Check additions (new debt)
        for added in sorted(actual_files - baseline_files):
            findings.append(
                f"{added}:1: NEW script detected — ad-hoc scripts in scripts/ or utils/ are prohibited. "
                f"Route commands through src/rebalance/cli/ and tasks through the orchestrator (GH-241)"
            )

        # Check removals (stale baseline that must be tightened)
        for removed in sorted(baseline_files - actual_files):
            findings.append(
                f"{removed}:1: script removed — inventory shrank; re-run with --update-baseline "
                f"to lock in the reduction (GH-241)"
            )

    return findings


def update_baseline(path: Path = BASELINE_PATH, root: Path = REPO_ROOT) -> None:
    """Scan the repository and write the live inventory as the new baseline."""
    inv = scan_inventory(root)
    payload = {
        "max_launchd_templates": MAX_LAUNCHD_TEMPLATES,
        "launchd_templates": inv["launchd_templates"],
        "scripts": inv["scripts"],
        "utils": inv["utils"],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Updated baseline at {path} ({len(inv['launchd_templates'])} templates, {len(inv['scripts'])} scripts, {len(inv['utils'])} utils)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Script and LaunchAgent inventory sprawl ratchet (GH-241)")
    parser.add_argument("--check", action="store_true", help="Fail if actual inventory does not match baseline")
    parser.add_argument("--update-baseline", action="store_true", help="Update baseline with current scan")
    parser.add_argument("--json", action="store_true", help="Print actual inventory as JSON")
    args = parser.parse_args()

    if args.update_baseline:
        update_baseline()
        return

    actual = scan_inventory()

    if args.json:
        print(json.dumps(actual, indent=2))
        return

    if args.check:
        baseline = load_baseline()
        findings = compare_to_baseline(actual, baseline)
        if findings:
            for f in findings:
                print(f, file=sys.stderr)
            sys.exit(1)
        print("script-inventory ratchet: clean (matches baseline)")
        return

    # Default summary
    print(f"LaunchAgent templates: {len(actual['launchd_templates'])} (ceiling: {MAX_LAUNCHD_TEMPLATES})")
    print(f"Scripts (scripts/):    {len(actual['scripts'])}")
    print(f"Utilities (utils/):    {len(actual['utils'])}")


if __name__ == "__main__":
    main()

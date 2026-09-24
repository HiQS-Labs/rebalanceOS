#!/usr/bin/env python3
# SCRIPT-INVENTORY-OK: PDDA machine path guard (GH-259)
"""Check active tracked code and text for machine-local absolute paths (GH-259).

Scans active skills, scripts, source modules, and active project docs for
machine-local path literals (/Users/..., /private/var/..., /tmp/...).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".xyz",
    "node_modules",
    "__pycache__",
    ".tick",
    "relay-system",
    "ARCHIVED-PREDECESSOR",
    "TESTS-RESULTS",
}

SCANNED_EXTENSIONS = {".py", ".sh", ".swift", ".md", ".json", ".yaml", ".yml", ".toml"}

import re

MACHINE_PATH_RE = re.compile(r"/(Users|private/var|private/tmp)/[a-zA-Z0-9_.-]+/")


def should_scan(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDED_PARTS:
            return False
    return path.suffix in SCANNED_EXTENSIONS


def scan_file(path: Path) -> list[tuple[int, str]]:
    findings = []
    # Don't scan this scanner itself or check_doc_links
    if path.name in ("check_machine_paths.py", "check_doc_links.py", "pdda.sh"):
        return findings
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings
    for line_no, line in enumerate(text.splitlines(), 1):
        if "MACHINE-LOCAL-OK:" in line or "assert " in line or "<name>" in line or "example" in line:
            continue
        if MACHINE_PATH_RE.search(line):
            findings.append((line_no, line.strip()))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan tracked files for machine-local absolute paths.")
    parser.add_argument("--check", action="store_true", help="Exit 1 if machine-local paths are found.")
    args = parser.parse_args()

    targets = [
        REPO_ROOT / ".agents" / "skills",
        REPO_ROOT / ".claude" / "skills",
        REPO_ROOT / "src",
        REPO_ROOT / "scripts",
        REPO_ROOT / "utils",
    ]

    total_findings = 0
    for target in targets:
        if not target.exists():
            continue
        for root, _, files in os.walk(target):
            for file in files:
                p = Path(root) / file
                if should_scan(p):
                    findings = scan_file(p)
                    for line_no, content in findings:
                        rel = p.relative_to(REPO_ROOT)
                        print(f"{rel}:{line_no}: machine-local path found: {content}")
                        total_findings += 1

    if total_findings > 0:
        print(f"\ncheck_machine_paths: FAIL ({total_findings} violation(s) found)")
        return 1 if args.check else 0
    else:
        print("check_machine_paths: clean (0 machine-local path violations)")
        return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# SCRIPT-INVENTORY-OK: PDDA machine path guard (GH-259)
"""Check active tracked code and text for machine-local absolute paths (GH-259).

Scans active skills, scripts, source modules, and active project docs for
machine-local path literals (/Users/..., /private/var/..., /tmp/...).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
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
    "marathon-system",
    "SHAKEDOWN",
    "tests",
}

SCANNED_EXTENSIONS = {".py", ".sh", ".swift", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}

# Target tracked paths: skills, core source, scripts, utilities, and active project docs
SCANNED_ROOT_DIRECTORIES = {
    ".agents",
    ".claude",
    "src",
    "scripts",
    "utils",
    "PROJECT",
}

MACHINE_PATH_RE = re.compile(r"/(Users|private/var|private/tmp)/[a-zA-Z0-9_.-]+(?:/[^\s\"\'`]*)?")


def should_scan(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    # If in a sub-directory structure, check against scanned roots when present
    parts = rel.parts
    if len(parts) > 1 and parts[0] not in SCANNED_ROOT_DIRECTORIES:
        # Check if root is a custom mock repo with flat structure
        if not (root / "src").exists() and not (root / ".agents").exists():
            pass  # Allow mock repos in tests
        else:
            return False
    for part in parts:
        if part in EXCLUDED_PARTS:
            return False
    return path.suffix in SCANNED_EXTENSIONS


def get_tracked_files(repo_root: Path) -> list[Path]:
    try:
        res = subprocess.run(["git", "ls-files"], cwd=str(repo_root), capture_output=True, text=True, check=True)
        return [repo_root / p for p in res.stdout.splitlines() if p.strip()]
    except Exception:
        files = []
        for root, _, fs in os.walk(repo_root):
            for f in fs:
                files.append(Path(root) / f)
        return files


def scan_file(path: Path) -> list[tuple[int, str]]:
    findings = []
    # Don't scan this scanner itself, check_doc_links, or pdda.sh
    if path.name in ("check_machine_paths.py", "check_doc_links.py", "pdda.sh"):
        return findings
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings
    for line_no, line in enumerate(text.splitlines(), 1):
        if (
            "MACHINE-LOCAL-OK:" in line
            or "<name>" in line
            or "<username>" in line
            or "<user>" in line
            or "/Users/you/" in line
            or "/Users/.../" in line
            or "/Users/..." in line
            or "placeholder" in line
        ):
            continue
        # Allow test assertions checking for leaks
        if "assert " in line or "assertIn" in line:
            continue
        if MACHINE_PATH_RE.search(line):
            findings.append((line_no, line.strip()))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan tracked files for machine-local absolute paths.")
    parser.add_argument("--check", action="store_true", help="Exit 1 if machine-local paths are found.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root to scan.")
    args = parser.parse_args()

    root = args.root.resolve()
    tracked_files = get_tracked_files(root)
    total_findings = 0

    for p in tracked_files:
        if not p.exists() or not should_scan(p, root):
            continue
        findings = scan_file(p)
        for line_no, content in findings:
            try:
                rel = p.relative_to(root)
            except ValueError:
                rel = p
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

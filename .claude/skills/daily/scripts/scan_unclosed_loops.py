#!/usr/bin/env python3
"""
scan_unclosed_loops.py — Forwarding entry point for Claude Code compatibility.

Delegates directly to the canonical implementation at:
.agents/skills/daily/scripts/scan_unclosed_loops.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    cur_dir = Path(__file__).resolve().parent
    repo_root = cur_dir.parents[3]
    canonical_script = repo_root / ".agents" / "skills" / "daily" / "scripts" / "scan_unclosed_loops.py"

    if not canonical_script.exists():
        # Fallback relative search
        alt_root = Path.cwd().resolve()
        canonical_script = alt_root / ".agents" / "skills" / "daily" / "scripts" / "scan_unclosed_loops.py"

    if not canonical_script.exists():
        sys.stderr.write(
            f"Error: Canonical scanner not found at {canonical_script}.\n"
            "Please ensure .agents/skills/daily/scripts/scan_unclosed_loops.py is present.\n"
        )
        return 1

    cmd = [sys.executable, str(canonical_script), *sys.argv[1:]]
    try:
        res = subprocess.run(cmd)
        return res.returncode
    except Exception as exc:
        sys.stderr.write(f"Failed to forward to canonical scanner: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

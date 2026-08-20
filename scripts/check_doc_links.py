#!/usr/bin/env python3
"""Check markdown links in tracked docs (GH-92).

Two guards, from the two failure modes GH-88 found:

  1. Broken relative links. The repo hit 45% breakage once, silently -- a doc link
     is never exercised by a test, so nothing fails until someone audits.
  2. Committed machine-local absolute paths (/Users/..., /private/var/..., /tmp/...).
     Broken for everyone including their author. This is a process bug: a tool writes
     host-specific paths into a file that then gets committed. It has bitten twice.

**This scanner is deliberately code-aware, and that is the load-bearing part.** A naive
`[...](...)` matcher flags inline code spans that *document* markdown syntax. During GH-88
one such false positive was "repaired" from `![a](100%.png)` into `![a 100%.png]`,
destroying the meaning of a technical sentence, and ROADMAP.md's own row-format template
was de-linked. A CI check that blocks pull requests on those gets switched off within a
week, so it must not produce them.

Usage:
    python3 scripts/check_doc_links.py            # check the repo, exit 1 on findings
    python3 scripts/check_doc_links.py --list     # also print every link checked
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories never walked: vendored, generated, or a historical record we must not rewrite.
SKIP_DIRS = {
    ".git",
    ".venv",
    ".xyz",
    "node_modules",
    "__pycache__",
    ".tick",
    # Archived agent transcripts. They record what agents actually wrote at the time;
    # repointing their links would falsify the record (GH-88).
    "relay-system",
}

# Absolute paths that are machine-local by construction.
MACHINE_LOCAL = ("/Users/", "/private/var/", "/private/tmp/", "/tmp/", "/home/")

# Link targets that are not filesystem paths.
NON_PATH_SCHEMES = ("http://", "https://", "mailto:", "#", "tel:", "data:")

LINK = re.compile(r"\[([^\]]*)\]\(\s*([^)\s]+?)\s*\)")
FENCE = re.compile(r"^\s*(```|~~~)")


def iter_links(text: str):
    """Yield (line_no, label, target) for real markdown links only.

    Skips fenced code blocks and inline code spans -- see the module docstring for
    why that is not optional.
    """
    in_fence = False
    for line_no, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in LINK.finditer(line):
            # An odd number of backticks before the match means we are inside a code span.
            if line[: m.start()].count("`") % 2 == 1:
                continue
            yield line_no, m.group(1), m.group(2)


def check(root: Path, show_all: bool = False) -> tuple[list[str], list[str], int]:
    broken: list[str] = []
    machine: list[str] = []
    checked = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            path = Path(dirpath) / fn
            rel = path.relative_to(root)
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for line_no, _label, target in iter_links(text):
                if target.startswith(NON_PATH_SCHEMES):
                    continue
                checked += 1

                if target.startswith(MACHINE_LOCAL):
                    machine.append(f"{rel}:{line_no}: machine-local absolute path -> {target}")
                    continue

                # Strip the anchor before resolving; keep it out of the existence test.
                bare = target.split("#", 1)[0]
                if not bare:  # a pure "#anchor" link
                    continue
                resolved = (path.parent / bare).resolve()
                if not resolved.exists():
                    broken.append(f"{rel}:{line_no}: broken link -> {target}")
                elif show_all:
                    print(f"  ok  {rel}:{line_no} -> {target}")

    return broken, machine, checked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--list", action="store_true", help="print every link checked")
    args = ap.parse_args()

    broken, machine, checked = check(args.root.resolve(), args.list)

    print(f"checked {checked} relative markdown links under {args.root}")

    if machine:
        print(f"\n{len(machine)} machine-local absolute path(s) — these are broken for everyone, including you:")
        for m in machine:
            print(f"  {m}")

    if broken:
        print(f"\n{len(broken)} broken relative link(s):")
        for b in broken:
            print(f"  {b}")

    if broken or machine:
        print(
            "\nFix the link, or unwrap it to plain text if the target is genuinely gone.\n"
            "Do NOT 'fix' something inside a code span or fenced block — this checker skips\n"
            "those, so if one is reported it is a real link (GH-92)."
        )
        return 1

    print("no broken links, no machine-local paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

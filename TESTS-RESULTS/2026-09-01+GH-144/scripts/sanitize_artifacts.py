#!/usr/bin/env python3
"""GH-144 Phase 0 — mechanical sanitizer for campaign artifacts.

The repo ratchets against committed machine-local absolute paths
(scripts/check_doc_links.py MACHINE_LOCAL, enforced by
tests/test_doc_links.py::RepoTests::test_repo_is_clean — it has "bitten twice"
per that checker's own docstring). Campaign artifacts legitimately quote such
paths (QA transcripts from advisors, pip/pytest console captures, argv
provenance records), so every artifact is passed through this *mechanical,
disclosed* substitution before commit. Substitution is prefix-level only; no
content is paraphrased or removed. The literal table plus the generic regex
pass below are the definition — if a pattern is not in them it is not
sanitized. The regex pass exists because MACHINE_LOCAL matches ANY username
under /Users/, not just this operator's.

Usage: python3 sanitize_artifacts.py FILE [FILE ...]   (edits in place)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

SUBS: list[tuple[str, str]] = [
    # longest/most-specific first; order is load-bearing
    (str(REPO), "<repo>"),
    ("/private/var/folders/", "<var-folders>/"),
    ("/private/tmp/", "<ptmp>/"),
    ("/private/var/", "<var>/"),
    ("/tmp/", "<tmp>/"),
    ("/home/", "<home>/"),
]

# any other user's home prefix — mirrors MACHINE_LOCAL's generic /Users/
USER_HOME = re.compile(r"/Users/[A-Za-z0-9_.-]+/")


def sanitize(text: str) -> tuple[str, int]:
    n = 0
    for old, new in SUBS:
        if old in text:
            n += text.count(old)
            text = text.replace(old, new)
    text, k = USER_HOME.subn("<userhome>/", text)
    return text, n + k


def main() -> None:
    total = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        raw = p.read_bytes()
        text, n = sanitize(raw.decode("utf-8", errors="replace"))
        if n:
            p.write_bytes(text.encode("utf-8"))
        print(f"{arg}: {n} substitution(s)")
        total += n
    print(f"total: {total}")


if __name__ == "__main__":
    main()

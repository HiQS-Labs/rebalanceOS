---
gh_issue: 127
source: https://github.com/HiQS-Labs/rebalanceOS/issues/127
title: "GH-127 README test-suite install note omits the server extra"
status: "Done (0.70.0 Green Board quick win)"
created: 2026-08-27
updated: 2026-08-27
owner: noel
doc_type: hygiene
goal: >
  Following README Getting Started verbatim must yield a clean pytest collection —
  the "server" extra was missing from the documented test-running command, causing
  13 ModuleNotFoundError: fastapi collection errors on a fresh clone.
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
roadmap_exempt: true
---

# GH-127 — README test-suite install note omits the `server` extra

## Status

| What was just completed | What's next |
|---|---|
| README.md's "To run the test suite" note now installs `.[dev,server]` instead of `.[dev]`; verified 0 collection errors on this tree. | None — closed as a Green Board quick win. |

## Why

README's Getting Started note told contributors to add only the `dev` extra to run tests,
but `fastapi`/`uvicorn` live in the separate `server` extra. Anyone following the doc
verbatim hit 13 `ModuleNotFoundError: fastapi` collection errors on first run, with no way
to tell an environment gap from a real regression — directly blocking 0.70.0 Green Board's
exit criterion (clean-clone install with no undocumented step).

## What changed

- `README.md`: "To run the test suite" note installs `.[dev,server]`, and states that
  `--collect-only` should report 0 errors (the exact count is left unpinned since it drifts
  as tests are added/removed — pinning it would just create a new source of false alarms).

## Investigation note

CI (`.github/workflows/ci.yml:100`) already installs `.[calendar,server,embeddings]` +
pytest — the real extras were always correct there. Only the README's *manual* instructions
for a human contributor were wrong. GH-127's acceptance criterion "a CI job exercises the
documented path" is therefore already satisfied by the existing CI job; no CI change was
needed.

## Lessons Learned (For Future Agents)

Two extras cover "runs the test suite" (`dev` for pytest itself, `server` for the modules
several test files import) — a note that mentions only one will pass review but fail in
practice. Grep for `ModuleNotFoundError` counts, not just for the extra names, before
trusting an install doc is complete.

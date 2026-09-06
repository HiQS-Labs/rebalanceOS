---
gh_issue: 127
source: https://github.com/HiQS-Labs/rebalanceOS/issues/127
title: "GH-127 — the documented README install must produce a clone whose test suite collects"
status: "Proposed (2-WORKING — marathon lane 2026-09-05). The earlier quick win fixed the test-suite NOTE; the Getting Started path itself still installs .[embeddings,calendar] and cannot collect."
created: 2026-09-05
updated: 2026-09-05
owner: noel
doc_type: bugfix
rating: "pri/sev/appeal/effort 75/70/75/85 · calc 305"
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
goal: >
  Make README Getting Started, followed verbatim on a fresh clone, yield `pytest --collect-only`
  with 0 errors; state the expected collected count; add a CI job that exercises the documented
  path on a clean checkout so it cannot regress.
non_goals:
  - Redesigning extras. The `dev` extra exists (#165); `server` exists. This lane only makes the documented path use them.
---

# GH-127 — README install must collect

## Status

| What was just completed | What's next |
|---|---|
| The "To run the test suite" note was fixed earlier (`.[dev,server]`). Getting Started at README.md:28 still says `.[embeddings,calendar]`, which cannot collect (13 `fastapi` import errors). | Builder lane: fix the Getting Started line, state the expected count, add the clean-checkout CI job. |

## Acceptance

Verbatim from #127:

- [ ] Following README Getting Started verbatim on a fresh clone yields `--collect-only` with 0 errors.
- [ ] The expected collected-test count is stated somewhere a caller can check against.
- [ ] A CI job exercises the documented path on a clean checkout, so this cannot regress unnoticed.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest --collect-only -q tests/ | tail -1 | grep -q ' collected' && ! .venv/bin/python -m pytest --collect-only -q tests/ 2>&1 | grep -q 'errors during collection'",
  "fix_probes": [
    { "type": "grep_present", "path": "README.md", "pattern": "pip install -e \\\".\\[embeddings,calendar\\]\\\"" }
  ],
  "artifacts": [
    "README.md",
    ".github/workflows/ci.yml"
  ],
  "remediation": {
    "source": "issue#127",
    "criteria": "README Getting Started installs extras that collect; expected count stated; a clean-checkout CI job runs the documented path."
  },
  "lanes": { "agy_safe": ["README.md", ".github/workflows/ci.yml"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified.*

## Phase 1

- [ ] README.md:28 → an extras set that collects (`.[embeddings,calendar,server,dev]` or the `dev` extra pulling `server` — pick one and say why in the PR).
- [ ] State the expected collected count where the test note lives, with the command that prints it.
- [ ] New CI job: fresh checkout, follow the README lines verbatim, `--collect-only` must report 0 errors.

### QA checklist — Phase 1
- [ ] Witnessed red: the new CI job fails on the current README (before the fix) — prove it in the PR.
- [ ] No other CI job's behaviour changes.

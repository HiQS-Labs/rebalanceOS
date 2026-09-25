---
gh_issue: 126
source: https://github.com/HiQS-Labs/rebalanceOS/issues/126
title: "GH-126 — turn the datetime/subprocess banned-import warnings into an exact-baseline ratchet"
status: "Active (2-WORKING) — Phases 2–3 (baseline ratchet, tests, and CI wiring) shipped in v0.84.0; Phase 1 (PR-template reuse proof) remains."
created: 2026-09-05
updated: 2026-09-24
owner: noel
doc_type: hygiene
rating: "pri/sev/appeal/effort 60/55/65/45 · calc 225"
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
goal: >
  The 33 datetime/subprocess findings under src/rebalance/ingest/ that pdda reports as WARN become an
  exact, line-independent JSON baseline in the existing checker; additions and stale shrinks both
  fail in CI and in pdda.sh; a reasoned pragma exempts a reviewed import.
non_goals:
  - Adding `json` to the ban (explicitly excluded by the issue).
  - A second validator. Extend utils/pdda/check_banned_imports.py; do not add a file beside it.
---

# GH-126 — banned-imports exact-baseline ratchet

## Status

| What was just completed | What's next |
|---|---|
| Phases 2–3 shipped in v0.84.0: `utils/pdda/check_banned_imports.py` enforces `banned_imports_baseline.json`, tested by `tests/test_banned_imports_ratchet.py` and run as a named CI step. | Phase 1: PR template integration for prior-art reuse proof. |

## Acceptance

Verbatim from #126. This lane delivers criteria 2–5 and must not break 6–7; criterion 1 is
Phase 1 (docs/governance) and is left for a separate lane — see `non_goals`.

- [ ] `ROUTER.md` is the only source of prior-art check wording; the PR template links to it and captures a Reuse Proof.
- [ ] No new validator duplicates `check_banned_imports.py` or `tests/test_collector_contracts.py`.
- [ ] The current debt is represented by an exact, line-independent baseline.
- [ ] New debt and stale/reduced baselines both fail locally and in CI.
- [ ] Fixture, current-tree, and mutation tests constrain the ratchet.
- [ ] `pytest tests/` and `pytest HiQS/tests` pass; `rebalance doctor` passes.
- [ ] Existing 3-Eyes CI exclusions remain untouched.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest tests/test_sqlite_gateway_ratchet.py tests/test_banned_imports_ratchet.py -q && .venv/bin/python utils/pdda/check_banned_imports.py --check",
  "fix_probes": [
    { "type": "path_absent", "path": "utils/pdda/banned_imports_baseline.json" },
    { "type": "path_absent", "path": "tests/test_banned_imports_ratchet.py" }
  ],
  "artifacts": [
    "utils/pdda/check_banned_imports.py",
    "utils/pdda/banned_imports_baseline.json",
    "tests/test_banned_imports_ratchet.py",
    "utils/pdda/pdda.sh"
  ],
  "artifacts_new": [
    "utils/pdda/banned_imports_baseline.json",
    "tests/test_banned_imports_ratchet.py"
  ],
  "remediation": {
    "source": "issue#126",
    "criteria": "datetime/subprocess findings pinned to an exact line-independent baseline in the existing checker; additions and shrinks fail in CI and pdda.sh; reasoned pragma exempts; parse failures fail closed."
  },
  "lanes": { "agy_safe": ["utils/pdda/check_banned_imports.py", "utils/pdda/banned_imports_baseline.json", "tests/test_banned_imports_ratchet.py", "utils/pdda/pdda.sh"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified. CI wiring (`.github/workflows/ci.yml`) is deliberately NOT in this lane's artifacts to avoid colliding with GH-127; the existing `--check` call at ci.yml:41 already runs the checker, so a new family in the checker is picked up without a workflow edit.*

## Phase 2–3

- [ ] Finding identity = relative path + import family + occurrence count; line numbers diagnostic only.
- [ ] `utils/pdda/banned_imports_baseline.json` committed, exact, matching the current tree.
- [ ] `--check` fails on additions AND on decreases/renames; `--update-baseline` is local and explicit.
- [ ] `# CANONICAL-PATH-OK: <reason>` same-line pragma exempts; blank reason fails.
- [ ] AST parse/read failure fails closed.
- [ ] `pdda.sh banned-imports` uses the same code path.

### QA checklist
- [ ] Mutation control: add one forbidden import to a fixture → `--check` red; remove one → red until baseline updated; move a line → stable; empty pragma → red.
- [ ] Current tree matches the committed baseline exactly.

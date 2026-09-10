---
gh_issue: 204
source: https://github.com/HiQS-Labs/rebalanceOS/issues/204
title: Focus 5 full clone detection and parent checkout grouping
status: Complete (Ready for PR)
created: 2026-09-10
updated: 2026-09-10
owner: Maintainer
doc_type: execution_plan
rating: pri/sev/appeal/effort 75/65/50/60 · calc 250
effort: 3
complexity: 2
risk: 2
phases: 3
goal: >
  Detect full clones sharing the same repository identity (repo_full_name or remote origin)
  and group them under their primary/parent checkout in Focus 5. Roll up clone activity to
  the parent repository so clones no longer crowd out other active projects on the Focus 5
  board, and render active clones directly on the parent card in the Focus 5 macOS Swift app.
non_goals:
  - Modifying or deleting git clone directories on disk
  - Altering git configuration or remotes in user checkouts
  - Changing non-Focus 5 signals or GitHub sync mechanics
---

# Focus 5 Full Clone Detection & Parent Grouping (#204)

## Status

| What was just completed | What's next |
|---|---|
| Phase 1 (Python data plane grouping & recency rollup), Phase 2 (Focus5Float Swift UI & model support), Phase 3 (Python & Swift test suites verified, frontdoor checks passing, version bumped to 0.87.0). | Commit, push branch, open pull request referencing #204. |

## Phases

### Phase 1: Python Data Plane (`focus5_scan.py`)
- [x] Group discovered `RepoSignals` by canonical `repo_full_name` / remote identity.
- [x] Disambiguate the parent checkout from task clones.
- [x] Roll up activity recency to the parent repo so work in a clone surfaces the parent.
- [x] Attach `clones: [RepoClone]` to `RepoCard` payload in `_build_roster_card`.
- [x] Update `summarize_focus5` and wire contract.

### Phase 2: macOS Swift App (`Focus5Float`)
- [x] Add `RepoClone` model and `clones` property to `RepoCard`.
- [x] Add client-side grouping in `Focus5Model.swift` as resilient fallback.
- [x] Render active clones in `RepoCardView` with branch tags, tree health, and "Open ↗" actions.
- [x] Update `CONTRACT.md`.

### Phase 3: Verification & QA
- [x] Python tests in `tests/test_focus5_clones.py` (7 tests).
- [x] Swift tests in `Focus5FloatTests/CloneGroupingTests.swift` (78 tests passing).
- [x] Full test suite (168 Python tests, 78 Swift tests).
- [x] Frontdoor health check clean.
- [x] Version bump 0.87.0 in `pyproject.toml`, `__init__.py`, `manifest.json`, `CHANGELOG.md`.

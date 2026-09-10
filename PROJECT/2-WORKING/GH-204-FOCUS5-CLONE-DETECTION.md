---
gh_issue: 204
source: https://github.com/HiQS-Labs/rebalanceOS/issues/204
title: Focus 5 full clone detection and parent checkout grouping
status: In Progress (Phase 1 — Implementation)
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
| Phase 0: Grounded recon, wire contract definition, and implementation plan approved. Task clone and branch created. | Implement Phase 1: Python signal grouping, recency rollup, and `clones` payload in `focus5_scan.py`. |

## Phases

### Phase 1: Python Data Plane (`focus5_scan.py`)
- Group discovered `RepoSignals` by canonical `repo_full_name` / remote identity.
- Disambiguate the parent checkout from task clones.
- Roll up activity recency to the parent repo so work in a clone surfaces the parent.
- Attach `clones: [RepoClone]` to `RepoCard` payload in `_build_roster_card`.
- Update `summarize_focus5` and wire contract.

### Phase 2: macOS Swift App (`Focus5Float`)
- Add `RepoClone` model and `clones` property to `RepoCard`.
- Add client-side grouping in `Focus5Model.swift` as resilient fallback.
- Render active clones in `RepoCardView` with branch tags, tree health, and "Open ↗" actions.
- Update `CONTRACT.md`.

### Phase 3: Verification & QA
- Python tests in `tests/test_focus5_clones.py`.
- Swift tests in `Focus5FloatTests`.
- Full test suite and frontdoor check.

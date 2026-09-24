---
title: Marathon Plan — rebalanceOS Governance & Data Plane Stabilization
status: Active (2-WORKING)
created: 2026-09-24
updated: 2026-09-24
owner: noel
branch: development
doc_type: project
roadmap_exempt: true
reversibility: Easy — file-scoped feature branches, no destructive DB drops
goal: >
  Execute high-value governance, script-sprawl, skill-path, and data-plane
  stabilization across two sequentially ordered waves with audited disjoint write sets.
---

# Marathon Plan 2026-09-24 — rebalanceOS

| Most recently completed phase | What's next |
|---|---|
| Issue triage completed & adjudicated via Codex relay; stale tickets closed (#148, #55, #66, #33, #4) | **Wave 1 & Wave 2 PR #265 Review & Refinements** (Refs #54, #62, #253, #258, #259, #260, #261, #262) |

## Disjoint Write-Set Collision Matrix

| Lane | Target Issue(s) | Primary Write Set (Disjoint) | Tests & Verification |
|---|---|---|---|
| **Wave 1 Lane 1** | #255 (Installer Sprawl) | `scripts/stack.sh`, `scripts/lib/scheduler_common.sh` (Installer deletion merged in #256) | `tests/test_stack_script.py`, `tests/test_scheduler_policy.py` |
| **Wave 1 Lane 2** | #258, #259, #253 (Skills & Paths) | `.agents/skills/daily/`, `.claude/skills/daily/`, `utils/pdda/check_machine_paths.py` | `tests/test_skills_drift.py`, `tests/test_machine_path_guard.py` |
| **Wave 1 Lane 3** | #260 (CI Ratchets) | `.github/workflows/ci.yml`, `tests/test_ci_ratchets.py` | `tests/test_ci_ratchets.py`, named steps in `ci.yml` |
| **Wave 2 Lane 1** | #54, #62 (GitHub ETag & Budget Plumbing) | `src/rebalance/ingest/_http.py` | `tests/test_github_etag_budget.py` |
| **Wave 2 Lane 2** | #150 (Activity Read Layer) | Shipped in 0.83.0/0.84.0; reconciled in #262 | `tests/test_activity_pipeline.py` |

---

## Wave 1: Governance, Skills & CI Ratchets

### Lane 1: Installer Sprawl Unification (#255)
- **Status:** Initial unification merged in #256 (commit `891c7df`).
- **Remaining Scope:** Runtime validation on Mac Studio (QA Gate 1) followed by Phase 2 runner consolidation (`scheduler_common.sh`).
- **Write Set:** `scripts/stack.sh`, `scripts/lib/scheduler_common.sh`.
- **Proof of Done:** `pytest tests/test_stack_script.py tests/test_scheduler_policy.py` passes; `utils/pdda/check_script_inventory.py --check` passes with baseline shrinkage.

### Lane 2: Skills Canonical Source & Path Guard (#258, #259, #253)
- **Goal:** Parity lock between `.agents/skills/daily/` and `.claude/skills/daily/`; eliminate hardcoded machine paths; extend machine-path CI guard to all tracked text via `git ls-files`.
- **Write Set:** `.agents/skills/daily/`, `.claude/skills/daily/`, `utils/pdda/check_machine_paths.py`.
- **Proof of Done:** `pytest tests/test_skills_drift.py` passes; `python3 utils/pdda/check_machine_paths.py --check` reports 0 violations.

### Lane 3: Read-Layer & Near-Duplicate Named CI Steps (#260)
- **Goal:** Elevate `check_read_layer.py`, `check_near_duplicates.py`, and `check_machine_paths.py` into named, fast-failing CI lint steps in `ci.yml`.
- **Write Set:** `.github/workflows/ci.yml`, `tests/test_ci_ratchets.py`.
- **Proof of Done:** `pytest tests/test_ci_ratchets.py` passes; `.github/workflows/ci.yml` runs all ratchets as explicit steps.

---

## Wave 2: Data Plane & Ingest Rate Safety

### Lane 1: GitHub PAT Ingest ETag Throttling & Request Budgeting (#54, #62)
- **Goal:** Implement foundational ETag conditional requests (`If-None-Match`), 304 caching, response stream closure, and per-run API request attribution in `GitHubClient`. (Caller-side persistence store tracked in next slice of #62).
- **Write Set:** `src/rebalance/ingest/_http.py`.
- **Proof of Done:** `pytest tests/test_github_etag_budget.py` asserts outgoing `If-None-Match` request header and 304 response handling.

### Lane 2: Activity Read-Layer Consolidation (#150)
- **Goal:** Consolidated read layer and repo identity normalization.
- **Status:** Shipped in 0.83.0 and 0.84.0; stale ticket reconciled under #262.

---

## Acceptance & Quality Checklist
- [x] Every lane runs on an audited feature branch with disjoint write sets.
- [x] Each lane includes a mechanical "Proof of Done" test artifact before merge.
- [x] Wave Post-Build Codex QA Relay executed and recorded on disk.
- [x] CI lint and ratchet checks pass cleanly.
- [ ] PR merged to `development` with post-merge lifecycle reconciliation.

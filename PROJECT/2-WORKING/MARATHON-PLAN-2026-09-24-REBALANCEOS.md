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
| Wave 1 & Wave 2 merged in PR #265 (commit `e21ec19` / v0.95.0); post-merge deployment verified | **Wave 3: Governance, PDDA & Docs Reconciliation** (#261, #262, #263) |

## Disjoint Write-Set Collision Matrix

| Lane | Target Issue(s) | Primary Write Set (Disjoint) | Tests & Verification |
|---|---|---|---|
| **Wave 1 Lane 1** | #255 (Installer Sprawl) | `scripts/stack.sh`, `scripts/lib/scheduler_common.sh` (Merged in #256) | `tests/test_stack_script.py`, `tests/test_scheduler_policy.py` |
| **Wave 1 Lane 2** | #258, #259, #253 (Skills & Paths) | `.agents/skills/daily/`, `.claude/skills/daily/`, `utils/pdda/check_machine_paths.py` (Merged in #265) | `tests/test_skills_drift.py`, `tests/test_machine_path_guard.py` |
| **Wave 1 Lane 3** | #260 (CI Ratchets) | `.github/workflows/ci.yml`, `tests/test_ci_ratchets.py` (Merged in #265) | `tests/test_ci_ratchets.py`, named steps in `ci.yml` |
| **Wave 2 Lane 1** | #54, #62 (GitHub ETag & Budget Plumbing) | `src/rebalance/ingest/_http.py` (Merged in #265) | `tests/test_github_etag_budget.py` |
| **Wave 2 Lane 2** | #150 (Activity Read Layer) | Shipped in 0.83.0/0.84.0; reconciled in #262 | `tests/test_activity_pipeline.py` |
| **Wave 3 Lane 1** | #261 (Completed Docs Lessons & Promotion Guard) | `PROJECT/3-COMPLETED/`, `PROJECT/2-WORKING/GH-25-CONSOLIDATE-TIMESTAMPS.md`, `utils/pdda/pdda.sh` | `pdda.sh issue-doc-sync`, zero `(fill in...)` placeholders in `3-COMPLETED/` |
| **Wave 3 Lane 2** | #262 (Reconcile GH-150 & GH-126 Status) | `PROJECT/3-COMPLETED/GH-150-ACTIVITY-SIGNAL-CONSOLIDATION.md`, `PROJECT/2-WORKING/GH-126-BANNED-IMPORTS-RATCHET.md` | `releases_app.py roadmap sync && check` (0 errors) |
| **Wave 3 Lane 3** | #263 (ROUTER.md 3-Eyes De-routing) | `ROUTER.md` | `pdda.sh governance` passes with zero 3-Eyes contradictions |

---

## Wave 1: Governance, Skills & CI Ratchets (Merged in PR #265)

### Lane 1: Installer Sprawl Unification (#255)
- **Status:** Merged in PR #256.

### Lane 2: Skills Canonical Source & Path Guard (#258, #259, #253)
- **Status:** Merged in PR #265 (`e21ec19`).

### Lane 3: Read-Layer & Near-Duplicate Named CI Steps (#260)
- **Status:** Merged in PR #265 (`e21ec19`).

---

## Wave 2: Data Plane & Ingest Rate Safety (Merged in PR #265)

### Lane 1: GitHub PAT Ingest ETag Throttling & Request Budgeting (#54, #62)
- **Status:** Merged in PR #265 (`e21ec19`).

### Lane 2: Activity Read-Layer Consolidation (#150)
- **Status:** Shipped in 0.83.0/0.84.0; reconciled in Wave 3 Lane 2 (#262).

---

## Wave 3: Governance, PDDA & Docs Reconciliation

### Lane 1: Completed Doc Lessons Learned & PDDA Promotion Guard (#261)
- **Goal:** Replace `(fill in...)` placeholders with substantive lessons in completed docs (`GH-7`, `GH-26`, `GH-27`, `GH-28`, `GH-30`); return active `GH-25` to `2-WORKING`; add deterministic PDDA promotion check in `pdda.sh`.
- **Write Set:** `PROJECT/3-COMPLETED/GH-{7,26,27,28,30}.md`, `PROJECT/2-WORKING/GH-25-CONSOLIDATE-TIMESTAMPS.md`, `utils/pdda/pdda.sh`.
- **Proof of Done:** `grep -rn "fill in" PROJECT/3-COMPLETED/` returns 0 hits; `pdda.sh issue-doc-sync` passes.

### Lane 2: Reconcile GH-150 & GH-126 Shipped Status & Roadmap (#262)
- **Goal:** Move shipped `GH-150` audit to `PROJECT/3-COMPLETED/` with status `Shipped (v0.84.0)` and lessons learned; update `GH-126` to reflect shipped baseline ratchets and active PR-template phase; sync roadmap ledger.
- **Write Set:** `PROJECT/3-COMPLETED/GH-150-ACTIVITY-SIGNAL-CONSOLIDATION.md`, `PROJECT/2-WORKING/GH-126-BANNED-IMPORTS-RATCHET.md`.
- **Proof of Done:** `python3 utils/py/releases_app.py roadmap sync && python3 utils/py/releases_app.py check` passes with 0 errors.

### Lane 3: ROUTER.md 3-Eyes De-routing (#263)
- **Goal:** Update `ROUTER.md` prior-art check 4, command rails, and routing hints to point to `scripts/stack.sh status`, `rebalance doctor`, and `/launchd-triage`, marking 3-Eyes as deferred per `AGENTS.md`.
- **Write Set:** `ROUTER.md`.
- **Proof of Done:** `pdda.sh governance` passes with zero 3-Eyes routing contradictions.

---

## Acceptance & Quality Checklist
- [x] Every lane runs on an audited feature branch with disjoint write sets.
- [x] Each lane includes a mechanical "Proof of Done" test artifact before merge.
- [x] Wave 1 & 2 landed cleanly in `development` (commit `e21ec19`).
- [x] Wave 3 changes verified locally against `pdda.sh`, `frontdoor-check.sh`, and `releases_app.py check`.
- [ ] PR created and reviewed for Wave 3.

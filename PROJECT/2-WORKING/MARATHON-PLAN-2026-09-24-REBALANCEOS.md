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
| Issue triage completed & adjudicated via Codex relay; stale tickets closed (#148, #55, #66, #33, #4) | **Wave 1 Execution:** Lane 1 (#255) ‖ Lane 2 (#258/#259/#253) ‖ Lane 3 (#260) |

## Disjoint Write-Set Collision Matrix

| Lane | Target Issue(s) | Primary Write Set (Disjoint) | Tests & Verification |
|---|---|---|---|
| **Wave 1 Lane 1** | #255 (Installer Sprawl) | `scripts/stack.sh`, `scripts/install_*.sh`, `src/rebalance/cli/` | `tests/test_stack_install.py`, `tests/test_cli.py` |
| **Wave 1 Lane 2** | #258, #259, #253 (Skills & Paths) | `.agents/skills/daily/`, `.claude/skills/daily/`, `utils/pdda/check_machine_paths.py` | `tests/test_skills_drift.py`, `tests/test_machine_path_guard.py` |
| **Wave 1 Lane 3** | #260 (CI Ratchets) | `scripts/ci-local.sh`, `.github/workflows/ci.yml`, `utils/pdda/` | `tests/test_read_layer_ratchet.py`, `tests/test_near_duplicates_ratchet.py` |
| **Wave 2 Lane 1** | #54, #62 (GitHub ETag & Budget) | `src/rebalance/ingest/github.py`, `src/rebalance/lib/http_client.py` | `tests/test_github_etag_budget.py` |
| **Wave 2 Lane 2** | #150 (Activity Read Layer) | `src/rebalance/ingest/activity_ops.py`, `src/rebalance/db/querier.py` | `tests/test_activity_pipeline.py` |

---

## Wave 1: Governance, Skills & CI Ratchets

### Lane 1: Installer Sprawl Unification (#255)
- **Goal:** Unify `scripts/install_*.sh` into `scripts/stack.sh` or `rebalance install` CLI subcommand.
- **Write Set:** `scripts/stack.sh`, `scripts/install_*.sh`, `src/rebalance/cli/install_cmds.py`.
- **Proof of Done:** `pytest tests/test_stack_install.py` passes; `utils/pdda/check_script_inventory.py --check` passes with baseline shrinkage.

### Lane 2: Skills Canonical Source & Path Guard (#258, #259, #253)
- **Goal:** Single canonical Daily skill folder; eliminate hardcoded `/Users/` paths; extend machine-path CI guard to all tracked text.
- **Write Set:** `.agents/skills/daily/`, `.claude/skills/daily/`, `utils/pdda/check_machine_paths.py`.
- **Proof of Done:** `pytest tests/test_skills_drift.py` passes; `python3 utils/pdda/check_machine_paths.py --check` reports 0 `/Users/` violations.

### Lane 3: Read-Layer & Near-Duplicate Named CI Steps (#260)
- **Goal:** Elevate `check_read_layer.py` and `check_near_duplicates.py` from nested pytest fixtures into named, fast-failing CI lint steps.
- **Write Set:** `scripts/ci-local.sh`, `.github/workflows/ci.yml`.
- **Proof of Done:** `bash scripts/ci-local.sh` runs both ratchets explicitly and outputs named summary lines.

---

## Wave 2: Data Plane & Ingest Rate Safety (Dependency-Ordered)

### Lane 1: GitHub PAT Ingest ETag Throttling & Request Budgeting (#54, #62)
- **Goal:** Implement ETag conditional requests (`If-None-Match`), 304 caching, and per-run API request counters in GitHub sync.
- **Write Set:** `src/rebalance/ingest/github.py`, `src/rebalance/lib/http_client.py`.
- **Proof of Done:** `pytest tests/test_github_etag_budget.py` asserts < 50 requests consumed on warm 304 sync.

### Lane 2: Activity Read-Layer Consolidation (#150)
- **Goal:** Merge parallel day-window queries into single canonical read layer with upstream de-duplication and org alias normalization.
- **Write Set:** `src/rebalance/ingest/activity_ops.py`, `src/rebalance/db/querier.py`.
- **Proof of Done:** `pytest tests/test_activity_pipeline.py` passes with non-inert duplicate fixtures (`SOP.md` §6).

---

## Acceptance & Quality Checklist
- [ ] Every lane runs on a fresh task clone branched from `development`.
- [ ] Each lane includes a mechanical "Proof of Done" test artifact before merge.
- [ ] Wave 1 completes and merges to `development` before Wave 2 commences.
- [ ] All ratchets ratchet downward permanently.

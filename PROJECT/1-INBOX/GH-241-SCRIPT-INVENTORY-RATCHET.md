---
gh_issue: 241
source: https://github.com/HiQS-Labs/rebalanceOS/issues/241
title: "Audit and consolidate reader scripts and add mechanical script-inventory CI ratchet gate"
status: "Active — in progress on feat/gh241-script-inventory-ratchet"
created: 2026-09-22
updated: 2026-09-22
owner: noel
doc_type: refactor
goal: >
  Halt and permanently ratchet script and LaunchAgent sprawl: audit reader scripts, establish a
  deterministic script inventory ratchet (failing CI on new loose scripts or unmanaged LaunchAgents),
  and update core governance in AGENTS.md, GUIDING-PRINCIPLES.md, and ROUTER.md.
effort: 2
complexity: 2
risk: 2
phases: 4
ratings_provisional: false
roadmap_exempt: false
---

# GH-241 — Audit and consolidate reader scripts and add mechanical script-inventory CI ratchet gate

## Status

| What was just completed | What's next |
|---|---|
| Issue #241 filed; task branch cut off `origin/development`; cross-model consult launched to audit reader scripts. **Phase 0 audit complete** — cataloged all 63 scripts in `scripts/` and 71 in `utils/`; confirmed 13 `install_*.sh` scripts (~800 LOC) are pure redundancy slated for elimination upon daemon consolidation; identified manual vs scheduled reader scripts. | Phase 1: Build `utils/pdda/check_script_inventory.py` and `script_inventory_baseline.json`. Phase 2: Add `tests/test_script_inventory_ratchet.py` and wire into CI. Phase 3: Update governance docs. |

## Problem

RebalanceOS has accumulated 67 files in `scripts/`, including 13 LaunchAgent plist templates, 12 separate `install_*.sh` scripts, and numerous loose reader scripts across `scripts/` and `utils/`.
On boot or stack reload, macOS fires up to 13 separate notifications ("Background Items Added: python", "Background Items Added: pulse_server.sh"), and repository discovery scans fall back to `$HOME` and trigger macOS TCC privacy prompts for `~/Desktop`.
While GH-136 (SQLite connection gateway) and GH-150 (SQL emitters / LLM clients) successfully placed ratchets on database and query sprawl, no mechanical gate ever stopped contributors from adding new shell scripts, python entry points, or LaunchAgents.

## Primary KPI: Code Removed vs. Added

Per `GUIDING-PRINCIPLES.md` Principle 6 ("Least code that clears the bar; deleting code counts as progress"), the primary success metric for the scheduler and script architecture is **reducing the net script inventory**:
1. Freezing the current inventory with a strict zero-growth ceiling.
2. Requiring all deletions to ratchet downward via `--update-baseline`, permanently locking in code reductions.
3. Preparing the elimination of the 13 `install_*.sh` scripts (~800 LOC of boilerplate) and consolidating the 13 LaunchAgents down to 1 daemon.

## Phase 0 Audit Findings

- **Catalog**:
  - `scripts/`: 13 `.plist.template`, 13 `install_*.sh`, 8 scheduled wrappers, 10 loose shell scripts, 16 loose python scripts, 3 swift helpers.
  - `utils/`: 50 python scripts (synthesis, rollups, PDDA checks), 20 shell scripts.
- **Reader Script Classification**:
  - *Group A (Manual Tools)*: `scripts/dashboard.py`, `scripts/audit_modules.py`, `scripts/apple_reminders.sh`. Can be migrated into canonical `rebalance` CLI commands.
  - *Group B (Scheduled Readers / Synthesizers)*: `scripts/pulse_web.py`, `scripts/pulse_warning_watch.py`, `scripts/health_issue_reporter.py`, `utils/hiqs_digest.py`, `utils/daily_synthesis.py`, `utils/daily_work_synthesis.py`. Currently invoked by launchd; targeted for in-process async dispatch inside the unified `rebalance daemon`.
  - *Group C (Redundant Installers)*: The 13 `install_*.sh` scripts are completely superseded by `stack.sh up`, but retained in baseline today because `tests/test_scheduler_policy.py:234` still validates their presence.
- **Ratchet Design**:
  - Checker tracks: `scripts/*.py`, `scripts/*.sh`, `scripts/*.plist.template`, `scripts/*.swift`, `utils/*.py`, `utils/*.sh`.
  - Hard constraint: `plist.template` count $\le 13$.
  - Enforces fail-on-growth and fail-on-shrink-without-update contract.

## Phases

- **Phase 0 — Reader Script & Inventory Audit**: Complete taxonomy of all files in `scripts/` and `utils/`; assess safe consolidation opportunities into `rebalance` CLI / daemon; run cross-model consult. *(COMPLETE)*
- **Phase 1 — Deterministic Script Inventory Checker & Baseline**: Build `utils/pdda/check_script_inventory.py` and `utils/pdda/script_inventory_baseline.json` following the proven GH-136 / GH-150 contract (fails on additions, fails on unratcheted shrinks).
- **Phase 2 — CI Test & LaunchAgent Cap**: Add `tests/test_script_inventory_ratchet.py` enforcing baseline conformance and capping LaunchAgents at $\le 13$; wire checker into `.github/workflows/ci.yml`.
- **Phase 3 — Governance & Guidance Hardening**: Update `AGENTS.md`, `GUIDING-PRINCIPLES.md`, and `ROUTER.md` to forbid creating loose scripts or uncoordinated LaunchAgents, directing all operator CLI commands to `src/rebalance/cli/` and background tasks to the central orchestrator.

## Task Ratings

`rated 85/80/50/85` (sum = 300)
- **pri (85)**: High urgency — directly impacts operator experience (system notification spam and desktop permission warnings on boot).
- **sev (80)**: System alert noise, process churn, SQLite locking hazards, and developer friction.
- **appeal (50)**: Standard neutral default.
- **effort (85)**: High cheapness — inventory check is fast AST/path analysis; test harness and CI workflow are established patterns.

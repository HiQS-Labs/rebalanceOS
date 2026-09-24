---
gh_issue: 255
source: https://github.com/HiQS-Labs/rebalanceOS/issues/255
title: "One install path — fold the per-job installers into stack.sh and fix the drift between them"
status: "Phase 1 merged (PR #256) — macOS proof and Phase 2 open"
created: 2026-09-23
updated: 2026-09-23
owner: noel
doc_type: refactor
goal: >
  One install flow for the launchd fleet, so no path can skip a job-specific step; delete the 13
  per-job installers; make the scheduled wrappers share one resilient Python runner.
related: [241, 59, 211, 210, 81]
effort: 2
complexity: 2
risk: 2
phases: 2
ratings_provisional: false
roadmap_exempt: false
---

# GH-255 — One install path

## Status

| What was just completed | What's next |
|---|---|
| Phase 1 merged 2026-09-23 via PR #256 (891c7df): one install flow in `install_common.sh`, `stack.sh install <job>...`, 13 installers deleted (inventory 50 → 37), EINTR-safe runner on every heredoc wrapper, plus review fixes (retire-after-load, lapsed opt-in removal, retirement binding guard, all-skipped `install` exits 3, comment-blind secret check — #264). | Prove on the Mac Studio via the GH-211 runbook (QA gate 1, unchecked below). Then Phase 2. |

## Table of contents
1. [Findings](#findings)
2. [Phase 1 — one install flow (this PR)](#phase-1--one-install-flow-this-pr)
3. [Phase 2 — wrapper consolidation](#phase-2--wrapper-consolidation)
4. [GH-59 gate — resolved](#gh-59-gate--resolved)

## Findings

Follow-up audit to GH-241. The main problem is not duplicated code. It is that two install paths
had drifted apart. Each item below is a real bug surface, cited to the tree before this change:

| # | Finding | Impact |
|---|---|---|
| F1 | `stack.sh up` never created `~/Library/Logs/rebalance-os/`; only 4 per-job installers did | On a fresh machine bootstrapped the documented way, `daily-synthesis`, `obsidian-rollover`, `hiqs-digest`, `daily-work-synthesis` logged nowhere (launchd does not create parent dirs) |
| F2 | Legacy `vault-sync` retirement lived only in one installer | `stack.sh up` could leave both `vault-sync` and `obsidian-vault-embeddings` firing at :15 (GH-175 collision) |
| F3 | `daily-work-synthesis` opt-in gate (GH-210) lived only in its installer | `stack.sh up` loaded it unconditionally, every 15 min, with no local ceilings config |
| F4 | Per-job installers had no fleet-binding guard | Running one from a dev clone silently rebound that job (GH-36/GH-59) |
| F5 | Only 2 of 13 installers warned that a reinstall drops a hand-added API key; `stack.sh restart` never did | Silent secret loss → next scheduled run fails |
| F6 | `rb_run_python_stdin` (bootstrap-EINTR retry) used by 1 of 4 heredoc wrappers | The transient-crash fix protected `github-sync` only |
| F7 | `pulse_sync.sh` ran its Python bare under `set -e` | On failure the script exited before its exit-code labelling and log trim ever ran |

Not a finding: the installers were already thin (all sourced `install_common.sh`), so they were
never an independent fallback for the shared flow — which weakens the GH-59 reason to keep them.

## Phase 1 — one install flow (this PR)

- [x] `install_common.sh` owns every job-specific step: precondition gate (exit 3 = SKIPPED), retired-label map, dropped-secret warning, log dirs read from the rendered plist (F1–F3, F5)
- [x] `stack.sh install <job>...` — same flow and binding guard as `up`, limited to the named jobs; unknown job names fail before launchd is touched (F4)
- [x] `stack.sh up` reports SKIPPED jobs and passes on per-job warnings instead of swallowing them
- [x] Delete the 13 `install_*scheduler.sh`; ratchet `script_inventory_baseline.json`
- [x] `daily_sync.sh`, `obsidian_vault_embeddings.sh`, `pulse_sync.sh` → `rb_run_python_stdin` (F6); `pulse_sync.sh` `if/else` (F7)
- [x] Repoint doctor hint, lifecycle stage, onboard text, welcome skill, SCHEDULER.md, UPGRADE.md, AGENTS.md, GH-211 runbook
- [x] Tests: `TestInstallFlow` (log dirs, retirement, opt-in skip/install, render-check ignores gate, secret warning, no installers remain, `stack.sh` executable in git); `stack.sh install` arg handling and per-job binding guard

### QA gate 1
- [x] `pytest tests/test_scheduler_policy.py tests/test_stack_script.py tests/test_scheduler_liveness.py`
- [x] `check_script_inventory.py --check`, `ruff check`, `ruff format --check`
- [ ] On macOS (second machine, via the GH-211 runbook): `bash scripts/stack.sh verify`, then `bash scripts/stack.sh install pulse-server` on the runtime checkout, then `status`. Record the result here.

## Phase 2 — wrapper consolidation

- [ ] Collapse the three `refresh_index` heredoc wrappers (`daily_sync`, `github_sync`, `obsidian_vault_embeddings`) onto one `rb_refresh <scope...>` helper or the `rebalance refresh` CLI — one exit-code contract instead of three copies
- [ ] Move `utils/obsidian_rollover.sh` and `utils/daily_synthesis.sh` onto `scheduler_common.sh` (they differ on venv fallback: one silently uses system python, one fails)
- [ ] Re-audit `scripts/spike_*.py` and `*_write_spike*` Swift files for deletion (spikes whose findings are recorded)

## GH-59 gate — resolved

GH-59 said to keep the installers until `stack.sh` had been proven on a second machine. The
deletion goes ahead, because (a) the installers shared `install_common.sh` and so could not rescue
a shared-flow bug, and (b) they had already drifted (F1–F5). Operator decision on PR #256: do not
hold the merge. Fold the proof into the GH-211 Mac Studio recovery instead. Its per-job
`stack.sh install` steps exercise the new path end to end on the second machine. Phase 1 is not
done until the macOS item in QA gate 1 is recorded here. A full `stack.sh up` on that machine is
the GH-211 exit criterion. If it fails, the rollback is `git revert`.

## Task Ratings

`rated 70/65/55/60`

## Merge evidence

- PR #256 merged 2026-09-23 (891c7df). The PR's "Closes #255" closed the issue at merge, and the operator kept it closed as the umbrella for #36/#60. The doc stays in 2-WORKING because the macOS proof (QA gate 1) and Phase 2 are still open. Promote it once both are done, or once Phase 2 is split into its own issue.
- Follow-up bug found in review and fixed in the same PR: #264. Its remaining operator checks are tracked there.

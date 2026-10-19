---
gh_issue: 334
source: https://github.com/HiQS-Labs/rebalanceOS/issues/334
title: "git-pulse-sync-repair: agent skill that diagnoses and repairs a stalled Git Pulse Sync"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-10-18
owner: noel
doc_type: bugfix
goal: >
  One bounded agent skill that diagnoses a stalled Git Pulse Sync with the doctor and the pulse
  checkout's git state. It applies the existing documented repairs once, resyncs once through the
  scheduled job, rechecks once, and stops. It adds no new scripts, LaunchAgents or code paths.
effort: 2
complexity: 2
risk: 3
phases: 1
ratings_provisional: false
roadmap_exempt: false
---

# GH-334: git-pulse-sync-repair skill

## Observed problem (2026-10-18, noels-Mac-Studio)

- `rebalance doctor`:
  - `scheduler:pulse-sync` is **error**: "installed on this device but NOT loaded in launchd". #333 has seen this 7×.
  - `pulse` is ok (configured at `~/git-pulse-sync`).
  - `pulse fleet` is warning: "this Mac is not enrolled in fleet mode".
- `~/git-pulse-sync` is `main...origin/main [ahead 10, behind 38]`, with a clean tree and no rebase in progress. The 10 local commits include Skills Army HQ vendor commits, which reach no other device while the scheduler is down. Skills Army HQ's `sync.py --status` reports `WARN STALE_PULSE_COLLECTION`.
- Every repair exists but is a manual step:
  - The doctor is read-only; it has only `--json` (`src/rebalance/cli/__init__.py:116`). It prints hints at `src/rebalance/doctor.py:842-848` (scheduler), `:2155` (`pulse`) and `:2201` (`pulse fleet`).
  - `scripts/stack.sh install <job>` / `up` (`scripts/stack.sh:599`), with a preflight.
  - `rebalance config refresh-pulse-clone --path` (`src/rebalance/cli/config_cmds.py:482`): a locked reconcile that never autostashes. Fleet checkouts only.
  - `rebalance config fleet-enroll [--apply]` (`config_cmds.py:522`), with its bounded procedure in UPGRADE.md "Fleet self-repair" (GH-325).
- An in-progress Git operation blocks both writers: `src/rebalance/lib/git_ops.py:580` and `experimental/git-pulse/collect.sh:238` say "preserve it for its owner". SOP.md:358 adds "never reset, stash or discard" pending history.

## Operator decisions (Noel, 2026-10-18)

- **Authority: repair and resync.** Diagnose, apply the documented repairs once, run the sync once, recheck once, stop.
- **Location:** `experimental/git-pulse/git-pulse-sync-repair/SKILL.md`.
- **Stuck rebase:** abort it after creating a backup branch of the current state. This is a deliberate, narrow exception to the "preserve for owner" rule. SOP.md records it in this PR.
- RebalanceOS is on every device, and Git Pulse Sync exists for it (Skills Army HQ is secondary). The skill depends on RebalanceOS tooling directly.
- Install after merge, on each device, through the Skills Army HQ CLI only (Forge `skills-army-hq` `intake.py`/`sync.py`).

## Plan

**Outcome sought:** a stalled pulse on any device recovers in one agent pass, or stops with the exact remaining blocker. Today an operator has to piece together four tools and two docs.

**Smallest viable bet:** one `SKILL.md`, an ordered procedure over the existing commands, plus one SOP.md paragraph. No code. GH-241 rules out new scripts, LaunchAgents and helpers.

**Alternatives rejected:**
- A `rebalance doctor --fix` command: new code and a new write path, more than the operator asked for.
- Reviving `RepairFSM` (`src/rebalance/repair.py`): unwired, and documented as automatic when it is not. That is a separate issue.
- 3-Eyes `launchd-triage`: stood down (AGENTS.md:225-255).

### Skill procedure (`git-pulse-sync-repair`)

0. **Resolve.**
   - RebalanceOS root: the primary clone on this device, `$REBALANCE_ROOT` if set, else the clone holding `.venv/bin/rebalance`.
   - Pulse checkout: the path the doctor's `pulse` row reports.
   - Fleet mode: the `pulse fleet` row.
   - If the root, the CLI or the checkout cannot be resolved, stop and report.
1. **Diagnose (read-only).**
   - `rebalance doctor --json`: the rows `scheduler:pulse-sync`, `pulse`, `pulse fleet*` and collector health.
   - On the pulse checkout:
     - an in-progress operation (`rebase-merge`/`rebase-apply`, `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`)
     - detached HEAD
     - `git status --porcelain`
     - after `git fetch`, ahead/behind against upstream
   - Print one table of findings before any change.
2. **Repair, once each, only for diagnosed faults.**
   1. `scheduler:pulse-sync` is installed but not loaded, or not installed: run `bash scripts/stack.sh install pulse-sync`, the repo's preflight-guarded loader. If it refuses, stop and report its output.
   2. `pulse` is missing keys: ask the operator for the GitHub login and clone path, never guessing them (UPGRADE.md step 2).
   3. `pulse fleet`:
      - Enrolled with WARN/FAIL: run `rebalance config fleet-enroll --apply` once (UPGRADE.md step 4).
      - Not enrolled: report it. Enrollment is the operator's per-Mac rollout decision (UPGRADE.md step 5).
      - "collector config missing": stop.
   4. **A rebase in progress in the pulse checkout (operator exception):**
      - Create `pulse-repair-backup/<UTC-stamp>` at the rebase's original branch tip (`rebase-merge/orig-head` or `rebase-apply/orig-head`).
      - Create a second backup branch at the current HEAD.
      - Run `git rebase --abort`, then verify the branch is back at the original tip.
      - Merge, cherry-pick or revert in progress, a dirty tree, or a detached HEAD: report with the exact state and stop. No reset, stash or discard.
3. **Resync, once.** Only when the scheduler is loaded, no Git operation is in progress and the tree is clean: `launchctl kickstart gui/$(id -u)/<label>`. The label is `com.rebalance-os.pulse-sync`, or `com.user.git-pulse` in fleet mode (the collector is the only pusher there, SCHEDULER.md:174-180). This runs the scheduled command exactly as launchd does. Read the outcome from the job's logs (`temp/logs/pulse_{stdout,stderr}.log`, or the collector log).
   - Exit 75 (lock busy or deferred): report it as busy, not as a failure.
   - In fleet mode, `rebalance config refresh-pulse-clone --path <clone>` first reconciles the checkout.
4. **Recheck once and stop.**
   - Re-run the doctor rows and ahead/behind, and report before → after.
   - Anything still WARN/FAIL: report the exact row and values.
   - No retries or loops, no choosing between clones, no moving or re-cloning (UPGRADE.md step 6).

### Changes

1. `experimental/git-pulse/git-pulse-sync-repair/SKILL.md`: the procedure above. Frontmatter `name` and `description`; under about 150 lines.
2. `SOP.md`, next to line 358: one paragraph stating the GH-334 exception. Only `git-pulse-sync-repair` may abort a stuck **rebase** in the pulse checkout, and only after the backup branches. Every other in-progress operation keeps the preserve-for-owner rule.
3. `ROADMAP.md`: a queue entry at capture, moved as the doc is promoted.
4. A `CHANGELOG.md`/version bump, only if the repo's rule applies. Docs and skill only, so no bump (AGENTS.md:212-218).

### Non-goals

- No new code, scripts, LaunchAgents or doctor flags.
- No change to the git_ops/collect.sh refusals themselves.
- No fleet enrollment decision.
- No RepairFSM or README cleanup. Filed separately if wanted.
- No 3-Eyes changes.

### Verification (bounded; docs and skill only)

- `utils/pdda/pdda.sh run` (doc gate) and the static pre-push hook.
- **Smoke main path (read-only):** run the skill's step 0–1 diagnosis on this Mac. Expect `scheduler:pulse-sync` error, fleet not enrolled, ahead/behind reported.
- **Smoke adjacent path (disposable):** in a throwaway repo pair under `$TMPDIR`, create a conflicting rebase and run step 2.4 exactly as written. Expect both backup branches at the right SHAs, `rebase --abort` restoring the original tip, and no commit lost. **Red control:** with a merge in progress instead, the skill stops and reports, and the tree is unchanged.
- Record both under `TESTS-RESULTS/2026-10-18+GH-334/` with provenance.
- **Not run before merge:** the real repairs (loading the scheduler, kickstarting the sync) on this Mac. They mutate the device and happen when the operator runs the installed skill after merge.

### Rollback

Revert the PR: one skill folder and one SOP paragraph. Deployed copies are withdrawn with the Skills Army HQ `intake.py --apply remove git-pulse-sync-repair` plus `sync.py --apply`.

## Ratings

`rated 70/55/50/75`
- pri 70: blocks cross-device delivery of pulse data and skills; recurring, #333 seen 7×.
- sev 55: data is delayed, not lost. Local commits are preserved, and recovery is manual but possible.
- appeal 50: neutral.
- effort 75: one docs and skill change over existing commands.

Recurrence: #333 has 7 sightings on this device (2026-10-18). Trend on other devices is unknown.

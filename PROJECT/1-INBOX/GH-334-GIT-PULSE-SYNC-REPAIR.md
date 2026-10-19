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
  - `rebalance config refresh-pulse-clone --path` (`src/rebalance/cli/config_cmds.py:482`): a locked reconcile that never autostashes.
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

### Skill procedure (`git-pulse-sync-repair`), revised after plan QA round 1

0. **Resolve the CLI, then diagnose.**
   - RebalanceOS root: `$REBALANCE_ROOT`, else this device's primary clone holding `.venv/bin/rebalance`. Without a CLI, stop and report.
   - Run `rebalance doctor --json` first.
   - The pulse checkout path comes from the `pulse` row (`configured (<path>)`). When that row says "missing keys", go to 2.2 before anything else (there is no path yet).
1. **Diagnose (read-only).**
   - The doctor rows `scheduler:pulse-sync`, `pulse`, `pulse fleet*` and collector health.
   - On the pulse checkout:
     - any in-progress operation: `rebase-merge`/`rebase-apply`, `MERGE_HEAD`, `CHERRY_PICK_HEAD` or `REVERT_HEAD`
     - detached HEAD
     - `git status --porcelain`
     - after `git fetch`, ahead/behind against upstream
   - The effective push policy: `PULSE_PUSH` in the installed job and in fleet mode (`scripts/pulse_sync.sh:37-42`).
   - Print one findings table before any change.
2. **Repair, once each, only for diagnosed faults.**
   1. **Scheduler.**
      - Installed but not loaded: `launchctl load -w ~/Library/LaunchAgents/com.rebalance-os.pulse-sync.plist`, the doctor's own hint (`src/rebalance/doctor.py:842-848`). The `-w` clears a launchd disable that plain `load` ignores (`scripts/lib/install_common.sh:238`).
      - Not installed: `bash scripts/stack.sh install pulse-sync`, which runs its preflight.
      - In both cases verify registration once with `launchctl print gui/$(id -u)/com.rebalance-os.pulse-sync`. No `--force` and no whole-stack restart. On a refusal, stop and report.
   2. **`pulse` "missing keys".** Ask the operator for the GitHub login and clone path, never guessing them. Run `rebalance config set-pulse --github-login … --target-path …` once (`src/rebalance/cli/config_cmds.py:499-519`). Re-run the doctor row: continue only if it reports `configured (<path>)`, otherwise stop.
   3. **`pulse fleet`.**
      - Enrolled with WARN/FAIL: run `rebalance config fleet-enroll --apply` once.
      - Not enrolled: report it. Enrollment is the operator's per-Mac decision (UPGRADE.md step 5).
      - "collector config missing": stop.
   4. **Stuck rebase in the pulse checkout (operator exception, GH-334).** All of the following must hold, in order; stop on any failure:
      - (a) Take the writers' shared advisory lock `<gitdir>/rebalance-publish.lock`, non-blocking (`git_ops.py:272-285`, `collect.sh:391-410`), with an inline `python3 -c` `fcntl.flock(LOCK_EX|LOCK_NB)` held for steps b–f. If the lock is busy, stop: a writer owns the rebase. Never delete the lock file.
      - (b) No live git process is working on the checkout. Check with `lsof +D <checkout>`, which lists processes whose cwd or open files are inside it, and stop on any `git` entry. `pgrep -fl 'git.*(rebase|am)'` is supporting evidence only, since it cannot see a cwd.
      - (c) Re-read the state under the lock. The rebase must still be present, with readable `orig-head` and `head-name`. If the original-tip metadata cannot be read, stop.
      - (d) Create branches `pulse-repair-backup/<UTC>-orig` at `orig-head` and `pulse-repair-backup/<UTC>-head` at the current HEAD, then verify both refs resolve to those SHAs.
      - (e) Save in-progress conflict edits: write `git diff HEAD` to `<gitdir>/pulse-repair-<UTC>.patch`. Untracked files survive an abort and are left alone.
      - (f) Run `git rebase --abort` once. Verify the branch named in `head-name` is back at `orig-head` and no rebase directory remains.
      - A merge, cherry-pick or revert in progress, or a dirty tree or detached HEAD outside this conflicted-rebase case: report the exact state and stop. Never reset, stash or discard.
3. **Resync, once, through the scheduled jobs.** Run only when the scheduler is loaded, no Git operation is in progress and the tree is clean.
   - **Non-fleet:** `launchctl kickstart gui/$(id -u)/com.rebalance-os.pulse-sync`. If the effective `PULSE_PUSH` is false, report that delivery is disabled, rather than claiming it was delivered.
   - **Fleet:** first `rebalance config refresh-pulse-clone --path <clone>` (a shared-lock reconcile; it is not limited to fleet mode, `src/rebalance/ingest/pulse.py:75-103`). Then run pulse-sync once to render and queue. Then, after checking that the collector `com.user.git-pulse` is loaded and its paths exist, kickstart it once to deliver. If the collector is missing, or any prerequisite fails or is deferred, stop.
   - **Completion is observed, not assumed.** Kickstart returning 0 only means launchd accepted the job. For each job, baseline it **before** its kickstart:
     - Resolve the job's own `StandardOutPath`/`StandardErrorPath` from its installed plist, plus the dated runtime log `temp/logs/pulse_sync_YYYY-MM-DD.log` for pulse-sync (`scripts/pulse_sync.sh:26,49`). The collector writes `git-pulse.out`/`.err` (`experimental/git-pulse/com.user.git-pulse.plist.template:17-20`).
     - Record the time, the `runs = N` count from `launchctl print gui/$(id -u)/<label>`, its state, and each log's byte size.
     - If the job is already running, observe and report that run without claiming a new invocation.
     - After the kickstart, poll every 30 s for at most 10 minutes. A **new** run is proven by `runs` rising above N, or by bytes appended past the recorded offsets. Completion is proven by state not running plus `last exit code`.
     - Read only the appended log bytes. Exit 75 means busy or deferred, not failed.
     - With no new-run evidence, or at the deadline: report not started, running or unknown. Never kill or restart the job, and never count an older success.
4. **Recheck once and stop.**
   - Re-run the doctor rows and ahead/behind, and report before → after.
   - Anything still WARN/FAIL: report the exact row and values.
   - No retries or loops, no choosing between clones, no moving or re-cloning (UPGRADE.md step 6).

#### Plan QA round 1 dispositions (codex)

| # | Finding | Disposition |
|---|---|---|
| 1 | Disabled installed job not cleared by `stack.sh install`'s plain `load` | **Accepted**: `load -w` for installed-not-loaded; `stack.sh install` only when not installed; verify once |
| 2 | Rebase abort must respect the writers' lock and a live owner | **Accepted**: non-blocking lock held through the abort, live-process check, re-read under the lock, fail-closed backups, conflict-diff patch. Mirrored in the SOP exception |
| 3 | Fleet: the collector alone does not re-render; `PULSE_PUSH=false` off-fleet | **Accepted**: render → deliver in fleet mode; push policy checked off-fleet |
| 4 | Kickstart is not completion; dated runtime log | **Accepted**: bounded 10-minute observation from `launchctl print` exit plus fresh log entries; 75 = busy; no kill or restart |
| 5 | Missing pulse config can never reach `set-pulse` | **Accepted**: doctor first; the missing-keys branch runs `set-pulse` once, then re-verifies |
| — | `refresh-pulse-clone` "fleet only" wording | Corrected: it is a shared-lock reconcile, not limited to fleet mode |
| R2 | Completion attribution: per-job logs, baseline before kickstart | **Accepted**: per-job installed log paths, pre-kickstart `runs`/offset baseline, new-run proof, already-running case |
| R2 | `pgrep` cannot see a cwd | **Accepted**: `lsof +D <checkout>` is the live-owner check. The smoke covers a relative-path git process, a held lock and patch retention |
| — | Gates and recovery not run by the reviewer | Expected: disposable-clone evidence is captured at implementation |

### Changes

1. `experimental/git-pulse/git-pulse-sync-repair/SKILL.md`: the procedure above. Frontmatter `name` and `description`; under about 150 lines.
2. `SOP.md`, next to line 358: one paragraph stating the GH-334 exception. Only `git-pulse-sync-repair` may abort a stuck **rebase** in the pulse checkout, and only with the writers' lock free and held, no live git process, both backup branches verified and the conflict diff saved. Every other in-progress operation keeps the preserve-for-owner rule.
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

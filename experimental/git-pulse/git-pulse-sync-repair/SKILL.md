---
name: git-pulse-sync-repair
description: >
  Diagnose and repair a stalled Git Pulse Sync on this device in one bounded pass: rebalance doctor
  plus the pulse checkout's Git state; then reload the pulse-sync scheduler, fix pulse or fleet
  config, abort a stuck rebase after verified backups, resync once through the scheduled jobs,
  recheck once and stop. Use when the pulse is stale, behind its upstream, not pushing, or when
  doctor or Skills Army HQ reports scheduler:pulse-sync, pulse or STALE_PULSE_COLLECTION.
---

# git-pulse-sync-repair

Git Pulse Sync is RebalanceOS's cross-device pulse repository. Skills Army HQ's `Deployed Skills`
collection also rides in it. This skill uses only existing commands (GH-334, plan in
`PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md`). It adds no scripts, jobs or code.

**Contract: one pass.** Make one repair attempt per fault, one resync, one recheck, then stop and
report. Never loop or retry. Never guess config values. Never choose between clones, move or
re-clone anything, or reset, stash or discard work. The only exception is the stuck-rebase
procedure in step 2.4.

## 0. Resolve

- `RB` = `$REBALANCE_ROOT`, or else this device's RebalanceOS clone that holds `.venv/bin/rebalance`.
  If none exists, stop: "RebalanceOS CLI not found".
- Run `"$RB/.venv/bin/rebalance" doctor --json` from `$RB`. Keep the rows `scheduler:pulse-sync`,
  `pulse`, `pulse fleet*` and collector health.
- `PULSE` = the path in the `pulse` row (`configured (<path>)`). If that row says "missing keys",
  go straight to 2.2.
- `FLEET` = whether the `pulse fleet` row says this Mac is enrolled.

## 1. Diagnose (read-only)

On `$PULSE`, with `G=$(git -C "$PULSE" rev-parse --absolute-git-dir)`:

- An operation in progress: `$G/rebase-merge` or `$G/rebase-apply` (rebase), `$G/MERGE_HEAD`,
  `$G/CHERRY_PICK_HEAD` or `$G/REVERT_HEAD`.
- `git -C "$PULSE" symbolic-ref -q HEAD` fails, meaning HEAD is detached.
- `git -C "$PULSE" status --porcelain`, which shows a dirty tree.
- `git -C "$PULSE" fetch -q` then `git -C "$PULSE" rev-list --left-right --count @{u}...HEAD`,
  which gives behind and ahead counts.
- Push policy: `PULSE_PUSH` in `~/Library/LaunchAgents/com.rebalance-os.pulse-sync.plist`. Off-fleet,
  `false` disables delivery (`scripts/pulse_sync.sh:37-42`). In fleet mode the collector pushes.

Print one findings table (check, observed value, planned action) **before any change**.

## 2. Repair (once each, only for diagnosed faults)

**2.1 Scheduler** (`scheduler:pulse-sync`):
- Installed but not loaded: `launchctl load -w ~/Library/LaunchAgents/com.rebalance-os.pulse-sync.plist`.
  `-w` clears a launchd disable that plain `load` ignores (doctor's hint, `src/rebalance/doctor.py:842-848`).
- Not installed: `bash "$RB/scripts/stack.sh" install pulse-sync`. Its preflight runs first. Never
  use `--force` or a whole-stack restart.
- Verify once with `launchctl print gui/$(id -u)/com.rebalance-os.pulse-sync`. If the command
  refuses or the job is still unregistered, stop and report.

**2.2 `pulse` "missing keys"**: ask the operator for the GitHub login and this Mac's pulse clone
path; never guess them. Run `"$RB/.venv/bin/rebalance" config set-pulse --github-login <login>
--target-path <path>` once. Re-run doctor and continue only if `pulse` now reads `configured (<path>)`.

**2.3 `pulse fleet`** (UPGRADE.md "Fleet self-repair"):
- Enrolled with WARN/FAIL: run `rebalance config fleet-enroll --apply` once.
- Not enrolled: report it. Enrollment is the operator's per-Mac decision. Do not enroll.
- "collector config missing": stop. The collector must be installed first.

**2.4 Stuck rebase in `$PULSE`** (operator exception, SOP.md "GH-334"). Run the steps in order and
stop on any failure, leaving everything as found:

a. **Take the writers' lock, non-blocking, and hold it through step f.** Both writers use
   `$G/rebalance-publish.lock` (`src/rebalance/lib/git_ops.py:272-285`, `collect.sh:391-410`).
   Run b–f under:
   ```bash
   python3 -c 'import fcntl,os,subprocess,sys
   fd=os.open(sys.argv[1],os.O_RDWR|os.O_CREAT,0o644)
   try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError: sys.exit("lock busy: a writer owns this rebase — stop")
   sys.exit(subprocess.call(["bash","-c",sys.argv[2]]))' "$G/rebalance-publish.lock" '<steps b-f>'
   ```
   A busy lock means a writer owns the rebase: stop. Never delete the lock file.
b. **Check for a live owner.** If `lsof +D "$PULSE"` lists any `git` process (cwd or open
   file), stop. `pgrep -fl 'git.*(rebase|am)'` is supporting evidence only.
c. **Re-read the state under the lock.** `R=$G/rebase-merge` (or `rebase-apply`) must still exist,
   with readable `$R/orig-head` and `$R/head-name`. If not, stop.
d. **Back up, verified.** Run `S=$(date -u +%Y%m%dT%H%M%SZ)`, then
   `git -C "$PULSE" branch "pulse-repair-backup/$S-orig" "$(cat $R/orig-head)"` and
   `git -C "$PULSE" branch "pulse-repair-backup/$S-head" HEAD`. Both refs must resolve to those SHAs.
e. **Save the conflict edits.** Run `git -C "$PULSE" diff HEAD > "$G/pulse-repair-$S.patch"`. The patch
   must be non-empty when `git diff HEAD` is non-empty. Untracked files survive the abort.
f. **Abort once.** Run `git -C "$PULSE" rebase --abort`. Verify the branch in `head-name` points at
   `orig-head` and that no rebase directory remains.

A merge, cherry-pick or revert in progress, or a dirty tree or detached HEAD outside this conflicted
rebase: **report the exact state and stop.** Those stay preserved for their owner (SOP.md:358).

## 3. Resync (once, through the scheduled jobs)

Run this step only if the scheduler is loaded, no Git operation is in progress and the tree is clean.

- **Off-fleet:** run pulse-sync (label `com.rebalance-os.pulse-sync`) once. If the effective
  `PULSE_PUSH` is false, report "delivery disabled". Never claim it was delivered.
- **Fleet:**
  1. Run `rebalance config refresh-pulse-clone --path "$PULSE"`, the shared-lock reconcile.
  2. Run pulse-sync once to render and queue.
  3. Check the collector `com.user.git-pulse` is loaded and its paths exist, then run it once to deliver.
  Stop on any missing, failed or deferred prerequisite.

**Run and observe each job.** `kickstart` returning 0 only means launchd accepted the job.
1. **Before** the kickstart, resolve the job's `StandardOutPath` and `StandardErrorPath` from its
   installed plist. Pulse-sync uses `temp/logs/pulse_{stdout,stderr}.log` plus its dated runtime
   log `temp/logs/pulse_sync_YYYY-MM-DD.log`; the collector uses `git-pulse.out` and `git-pulse.err`.
2. Record the time, `runs = N`, the state from `launchctl print gui/$(id -u)/<label>`, and each
   log's byte size.
3. If the job is already running, observe that run and do not claim a new one.
4. Run `launchctl kickstart gui/$(id -u)/<label>`. Poll every 30 s for at most **10 minutes**.
   - A new run is proven by `runs` > N, or by bytes appended past the recorded sizes.
   - Completion is proven by the job no longer running, plus its `last exit code`.
   - Read only the appended bytes. Exit 75 means busy or deferred, not failed.
   - With no new-run proof, or at the deadline, report not started, running or unknown. Never
     kill or restart the job, and never count an older success.

## 4. Recheck once, report, stop

Re-run the doctor rows and the ahead/behind counts. Report a before → after table: each fault, the
action taken with its evidence (backup refs, patch path, exit codes, log lines) and the final row
values. Anything still WARN or FAIL is reported with exact values, as the next step for the
operator. Do not attempt it again.

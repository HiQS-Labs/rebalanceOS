# RELAY · rebalanceOS GH-334 git-pulse-sync-repair plan QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-18.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 2 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
     **A finding that asks for a behaviour change is a generalization unless you can paste the concrete
     input — a row, a value, a `file:line` — that fails under the current code** (GH-681: the gh673
     final QA relay generalized one late-error observation into "or a later invalid identity", the
     Producer implemented it, the same seat `[Pass]`ed it next round, and one historical NULL-URL
     ledger row then blanked every issue). Every `[Blocker]` or `[Should]` requesting a behaviour
     change MUST carry three lines: `Observed input:` (the failing input you saw), `Affected scope:`
     (the input predicate the change would govern), `Falsifier:` (the fixture or data that would show
     the change unnecessary or wrong, and its expected result).
     A `[Blocker]` must cite an observed failure. This is a protocol rule, not a mechanical check —
     the Producer may disposition a request lacking these as `Declined — unproven generalization`.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why,
     including `Declined — unproven generalization` for a behaviour-change request that carries no
     `Observed input:` / `Affected scope:` / `Falsifier:`), make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh334-plan-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh334-plan-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-18

### Artifact — gh334-plan-brief.md
```
# Plan QA: RebalanceOS GH-334 git-pulse-sync-repair skill

You are reviewing a PLAN, not code. The target repo is HiQS-Labs/rebalanceOS. Your worktree is that repo at branch `feat/rebalanceOS-gh334-git-pulse-sync-repair-2026-10-18` (head 84307c8).

Read in full: `PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md` (the plan).

Then verify its claims against:
- `src/rebalance/doctor.py`: the scheduler liveness check near line 767, the hints at 842-848, `_check_pulse` at 2155, `_check_pulse_fleet` at 2201, `_check_pulse_collectors` at 1885
- `scripts/stack.sh` (install/up and its preflight, near 599)
- `scripts/com.rebalance-os.pulse-sync.plist.template` and `scripts/pulse_sync.sh`
- `src/rebalance/cli/config_cmds.py`: `refresh-pulse-clone` at 482, `fleet-enroll` at 522
- `src/rebalance/lib/git_ops.py` 570-640
- `experimental/git-pulse/collect.sh` 230-262
- UPGRADE.md "Fleet self-repair" (185-216)
- SOP.md around line 358
- SCHEDULER.md 170-185
- ROUTER.md 51-65 (GH-241 no new scripts)
- AGENTS.md 212-255

Operational envelope: a single-operator, per-device agent skill (a `SKILL.md` procedure) for one person's Macs. Grade against the stated operator decisions at commensurate complexity. Do not ask for new code, daemons, test frameworks or enterprise hardening.

Operator decisions are fixed; do not re-litigate them:
- repair + resync authority
- location `experimental/git-pulse/`
- abort a stuck rebase after a backup branch, with an SOP exception
- install after merge via the Skills Army HQ CLI

Questions:
1. **Grounding.** Is every command in the procedure real, with the stated behavior? In particular, does `bash scripts/stack.sh install pulse-sync` load an installed-but-unloaded job? Is `launchctl kickstart gui/$(id -u)/com.rebalance-os.pulse-sync` the right way to run the scheduled job once (label, domain)? Are the log paths right?
2. **Fleet versus non-fleet.** Is the resync step right in both modes: which job pushes, and when does `refresh-pulse-clone` apply? Is anything missing for a non-enrolled Mac like this one?
3. **Stuck-rebase exception.** Are the backup refs right (`rebase-merge/orig-head` versus `rebase-apply/orig-head`, plus the current HEAD)? Is the abort safe? After the abort, does the publisher's own lock (`<gitdir>/rebalance-publish.lock`) or a live rebase process need checking first, so the skill does not abort a rebase the publisher is running right now?
4. **Bounds.** Is the one-attempt / one-recheck / stop contract complete? Can any step loop, guess values, or touch other clones?
5. **Scope.** Is anything over-built or missing against issue #334? Is the SOP edit placed and scoped right?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines.
```
- Definition of Done: the plan is grounded in real commands and paths, safe within the operator's decisions, and bounded. No Blocker.

### Reviewer block template (copy exactly; `VERDICT:` and `Basis:` each start at the beginning of a line)

```
### Round N — Reviewer (codex)
Findings:
- [Severity] file:line — finding
  Observed input: ...
  Affected scope: ...
  Falsifier: ...
Answers: 1) ... 2) ... 3) ... 4) ... 5) ...
VERDICT: PASS
Basis: <one line>
```
Use `VERDICT: CHANGES` if there is any Blocker or Should; otherwise PASS and set `STATUS: Approved`.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1
swept file: yes

Reviewed the entire embedded brief and the entire referenced plan, including verification and rollback. The findings below include existing defects in the procedure; no additional plan defects found in the full sweep. Source-grounded review only: the available rebalanceOS graph belongs to another checkout, generation 2026-09-02, with changed metadata and excluded scripts; current seeded source was read directly. No Git commands, test suites, executable fixtures, repairs or scheduler mutations were run.

Findings:
- [Should] PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md:72 — The proposed loader does not cover a disabled installed job. `scripts/lib/install_common.sh:238` uses plain `load`; `src/rebalance/doctor.py:844-846` explicitly requires `load -w` for that case. Keep preflight for installation, but distinguish an existing disabled/unloaded job and use the documented single-job recovery against its verified installed plist; verify registration once, without `--force` or whole-stack changes. Do not promise that `install` clears disablement. Live recovery remains unverified.
  Observed input: the plan routes "installed but not loaded" to `stack.sh install pulse-sync`; the called installer uses `"$LAUNCHCTL_BIN" load "$dest"`, without `-w`.
  Affected scope: installed pulse-sync jobs whose launchd disable override prevents ordinary loading.
  Falsifier: in a disposable/mocked loader run, a disabled installed pulse-sync job becomes registered using the current plain-load path; if demonstrated, this recovery branch is unnecessary.
- [Should] PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md:78-82 — Rebase-directory existence does not establish a stuck, unowned rebase. Both writers hold the same advisory lock (`src/rebalance/lib/git_ops.py:272-285`, `experimental/git-pulse/collect.sh:391-410`), but repair currently bypasses it. Require nonblocking acquisition of that existing lock through inspection, both successful backup refs, abort and restoration verification; stop on busy or evidence of a live external rebase. Re-read state under the lock. Stop if either original-tip metadata or either backup cannot be verified; never delete the lock file. Clarify that the dirty/detached refusal applies outside the deliberately accepted conflicted-rebase state, and preserve unrelated edits before allowing abort. Carry these prerequisites into the SOP exception at plan line 94.
  Observed input: lines 78-81 unconditionally back up and abort any detected rebase; no lock ownership or live-operation check appears in steps 0-2. The existing writer lock explicitly spans its rebase.
  Affected scope: pulse-checkout rebases eligible for the operator's narrow abort exception, including a publisher currently reconciling or an externally owned rebase.
  Falsifier: a clone-run red control with the existing publication lock held must stop without refs/state changes; a confirmed abandoned conflicted rebase with the lock free must retain both tips and abort once. If current instructions already enforce that distinction, show the clause.
- [Should] PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md:83-85 — Fleet mode substitutes the check-in collector for pulse-sync entirely. The renderer and delivery job have separate responsibilities: `scripts/pulse_sync.sh:44-49` calls the renderer, and `src/rebalance/ingest/pulse.py:1039-1075` records the render attempt; SCHEDULER.md:174-180 assigns pushing to the collector. After repairing a stopped renderer, merely delivering old queued output does not refresh its page/status. Specify a bounded sequence: reconcile successfully, run pulse-sync once to completion to queue fresh output, then run the loaded local collector once to deliver. Check the selected collector's registration and actual installed paths/logs, and stop on its absence or any failed/deferred prerequisite. In non-fleet mode run pulse-sync once; inspect effective push policy because `PULSE_PUSH=false` also suppresses its push outside fleet mode (`scripts/pulse_sync.sh:37-42`). No enrollment or new job is required.
  Observed input: line 83 chooses `com.user.git-pulse` instead of `com.rebalance-os.pulse-sync` when fleet mode is true, including after line 72 repairs an unloaded renderer.
  Affected scope: enrolled devices with stale/missing rendered output, plus non-enrolled devices whose installed publisher explicitly disables pushing.
  Falsifier: a clone-run stale-render fixture must show a fresh successful render receipt and delivered corresponding page after one pass; collector delivery alone would invalidate this finding only if it also invokes the renderer. For non-fleet push-disabled input, report the actual delivery owner or stop, rather than claim delivery from renderer exit zero.
- [Should] PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md:83-88 — Define bounded completion observation before the one recheck and distinguish kickstart acceptance from the job's exit. The listed stdout/stderr logs exist, but detailed JSON/errors are redirected into `temp/logs/pulse_sync_YYYY-MM-DD.log` (`scripts/pulse_sync.sh:26,49`, `scripts/lib/scheduler_common.sh:62-66`). Add that log, resolved from the installed runtime, and correlate a fresh attempt/completion or launchd result to this invocation; do not treat old log success or kickstart return zero as delivery. Set a finite observation deadline and report running/busy/unknown on expiry without killing or restarting the job. Apply the same rule between fleet render and delivery.
  Observed input: line 83 names only `pulse_{stdout,stderr}.log`; line 84 classifies exit 75 without specifying where the completed job exit is obtained, and line 87 immediately rechecks.
  Affected scope: asynchronous scheduled runs, especially delayed collectors and failed runs whose decisive JSON is absent from stdout/stderr.
  Falsifier: a delayed run and an old successful log followed by a new failed run must never be reported as newly complete/successful; a fresh exit-75 run must be classified as busy. Probe: `/bin/launchctl help kickstart` exited 0 and printed `Usage: launchctl kickstart [-k] [-p] <service-target>`; its listed flags start/terminate/print PID/suspend, with no completion-wait flag. No service was started.
- [Should] PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md:58-73 — Missing pulse configuration cannot reach its advertised repair: step 0 requires the checkout path from the doctor row and stops if unresolved, while the missing-keys row contains no path (`src/rebalance/doctor.py:2176-2185`). Also step 2.2 asks for values without actually invoking the existing setter. Resolve the CLI first, run doctor, then allow the missing-key case to collect the operator's values and run the documented `rebalance config set-pulse --github-login … --target-path …` once (`src/rebalance/cli/config_cmds.py:499-519`), validate the checkout, and continue only on success. Retain stop-on-ambiguous/missing checkout for other cases.
  Observed input: `_check_pulse` returns `pulse config missing keys: ...` instead of `configured (<path>)`; step 0's path resolution therefore fails before step 2.2.
  Affected scope: missing github_login or pulse_target_path; no guessing or enrollment authority is added.
  Falsifier: a missing-target-path input must reach the explicit operator-value request and setter once; invalid/ambiguous paths must stop without sync. If current step 0 already allows that exception, cite it.
- [Pass] PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md:93-104 — One skill plus a narrow SOP exception, no new scripts/agents and no enrollment decision respects the fixed scope. Documentation-only no-bump rule is present at AGENTS.md:216. Both rebase metadata backends and current HEAD are included at plan lines 79-80; they are the right backup targets, subject to the safety prerequisites above. The SOP insertion is adjacent to the pending-history preservation rule at SOP.md:356-359.
- [Unverified — needs clone run] PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md:108-112 — Gates, conflicting-rebase recovery and merge red control were not executed in this reviewer worktree. Require disposable full-clone evidence during implementation; do not interpret this review as runtime qualification or a live scheduler-state measurement.

Answers: 1) Commands exist; installation uses preflight but plain load does not clear disablement. Both labels match their templates; GUI targeting assumes the logged-in user's loaded LaunchAgent. Detailed results need the dated runtime log and fresh completion evidence. 2) Non-fleet normally renders/pushes; fleet needs render/queue then collector delivery. refresh-pulse-clone is a shared-lock reconcile, not a pusher; its implementation is not fleet-gated (src/rebalance/ingest/pulse.py:75-103), despite the plan's line-33 restriction. 3) Original tip plus current HEAD are suitable refs, but lock/live-owner checks and fail-closed backup handling are missing. 4) The one-attempt intent is present at lines 71,83,86-89; asynchronous completion and failed-prerequisite stops need explicit bounds. 5) Scope and SOP location are appropriate; the procedure corrections above need no new subsystem.

VERDICT: FAIL
Basis: Five concrete procedure corrections remain; safety and completed-run evidence are not yet sufficient for approval. FAIL follows TAKE YOUR TURN's exact PASS/FAIL/PARKED vocabulary (the later CHANGES template conflicts).

Handing off to Producer (claude-a) — disposition each finding and revise the plan in the Producer window, then open the next review round.

### Producer · Round 1 dispositions (claude-a)

All five Shoulds were checked against the source and **Accepted**. The plan's procedure is rewritten in `PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md` ("Skill procedure … revised after plan QA round 1"), and the dispositions table is in the same doc.
1. `load -w` for an installed-but-unloaded job; `stack.sh install` only when the job is not installed; registration verified once.
2. Rebase abort: the writers' lock is taken non-blocking and held through the abort, a live-process check runs first, state is re-read under the lock, the backups fail closed, and the conflict diff is saved as a patch. The SOP exception carries the same prerequisites.
3. Fleet mode renders with pulse-sync and then delivers with the collector. Off-fleet, the `PULSE_PUSH` policy is checked.
4. Completion is observed for at most 10 minutes from the `launchctl print` exit code plus log entries newer than the start; 75 = busy; never kill or restart the job.
5. The doctor runs first, and the missing-keys branch runs `set-pulse` once, then re-verifies.

Also corrected: `refresh-pulse-clone` is not limited to fleet mode. The verdict vocabulary is PASS/FAIL, per the TAKE YOUR TURN block.

Reviewer: please re-review the revised procedure only. Round 2 of 3.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

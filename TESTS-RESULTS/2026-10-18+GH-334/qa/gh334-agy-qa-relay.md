# RELAY · rebalanceOS PR #335 GH-334 independent QA (agy)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-19.
-->

NEXT: Producer
STATUS: Approved
ROUND: 1 / 3

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
6. **Commit only the relay file** (`relay(rebalanceos-pr-335-gh-334-independent-qa-agy): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh334-agy-brief.md** (embedded below — read it here).
- Reviewer: agy   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh334-agy-brief.md
```
# Independent QA (agy): RebalanceOS PR #335 / GH-334 git-pulse-sync-repair

You are a second-family reviewer. Codex approved both the plan and the implementation. Look for what a different reviewer misses.

Your worktree is HiQS-Labs/rebalanceOS at PR #335's head (475f2e2). The diff against `origin/development` is:
- `experimental/git-pulse/git-pulse-sync-repair/SKILL.md`: the new skill, a procedure document with no code
- `SOP.md`: the GH-334 stuck-rebase exception paragraph, after the GH-325 rollback rule
- `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md`: the approved plan, which is the spec
- `ROADMAP.md`: one entry
- `TESTS-RESULTS/2026-10-18+GH-334/`: smoke logs, `SUMMARY.md`, provenance, and the plan and final QA relays

Operational envelope: a single operator's per-device agent skill, run on their own Macs. Grade at commensurate complexity. Do not ask for new code, suites, daemons or enterprise hardening.

Operator decisions are fixed:
- authority to repair and resync
- location `experimental/git-pulse/`
- a stuck rebase may be aborted after verified backups (an SOP exception)  [Unverified — no citation]
- install after merge via the Skills Army HQ CLI
- RebalanceOS is on every device

Read alongside the skill:
- `src/rebalance/doctor.py` (around 767-848, 1885, 2155-2230)
- `scripts/stack.sh`
- `scripts/pulse_sync.sh`
- `scripts/com.rebalance-os.pulse-sync.plist.template`
- `experimental/git-pulse/com.user.git-pulse.plist.template`
- `experimental/git-pulse/collect.sh` (230-262, 391-410)
- `src/rebalance/lib/git_ops.py` (272-290, 570-640)
- `src/rebalance/cli/config_cmds.py` (482-560)
- UPGRADE.md "Fleet self-repair"
- SCHEDULER.md 170-185

Questions:
1. **Would it work on a real Mac, end to end?** Walk this Mac's actual state through the skill: scheduler installed but not loaded, `pulse` configured, fleet not enrolled, clean tree, 39 behind / 10 ahead, `PULSE_PUSH` unset. Does every step produce the right action? In particular, after `launchctl load -w`, does `kickstart` of a job with `RunAtLoad` false actually run it? Does the off-fleet pulse-sync push rebase over 39 upstream commits safely through `git_pull_rebase_safe`?
2. **Copy-paste correctness.** Check each shell line in SKILL.md: quoting, `$G` resolution, `@{u}` with no upstream configured, the PlistBuddy key path versus the real plist structure, `launchctl print`/`kickstart` target syntax, and how the step 2.4 `bash -c` wrapper receives `R`/`S` across steps b–f. Cite `file:line` for any line that would fail as written.
3. **Safety gaps.**
   - Can any step lose local commits or uncommitted work, or race the hourly job?
   - Is the 10-minute observation window right for a job capped at 1800 s (`job_guard --max-runtime-seconds 1800`)?
   - Is anything missing that could leave the device worse than it started?
4. **Doc agreement.** Do `SKILL.md`, the plan and the SOP exception agree with each other, and with doctor's own hints?
5. **Over or under-built.** What could be cut, and is anything that #334 asks for missing?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines. You may run narrow read-only probes; quote the command and its output.
```
- Definition of Done: the skill would work as written on a real Mac within the operator's decisions; no Blocker or Should.

Reviewer block: plain lines; `VERDICT: PASS` or `VERDICT: FAIL` and `Basis:` each at the start of a line, with no bold. On PASS set `STATUS: Approved`.

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

Reviewed the whole embedded brief, `experimental/git-pulse/git-pulse-sync-repair/SKILL.md` (all 127 lines), `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md` (all 163 lines), `SOP.md` (lines 1–480), `ROADMAP.md` (line 41), `TESTS-RESULTS/2026-10-18+GH-334/` (`SUMMARY.md`, `provenance.jsonl`, `smoke-main-path.log`, `smoke-rebase-recovery.log`, `smoke-rebase-recovery.sh.txt`, and both prior QA relays), plus the referenced source files (`src/rebalance/doctor.py`, `scripts/stack.sh`, `scripts/pulse_sync.sh`, `scripts/com.rebalance-os.pulse-sync.plist.template`, `experimental/git-pulse/com.user.git-pulse.plist.template`, `experimental/git-pulse/collect.sh`, `src/rebalance/lib/git_ops.py`, `src/rebalance/ingest/pulse.py`, `src/rebalance/cli/config_cmds.py`, `UPGRADE.md`, `SCHEDULER.md`). No pre-existing defects requiring changes in the touched files were found beyond the two non-blocking Nits below.

Findings:
- [Nit] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:24-28` — On a dual-clone machine (dev checkout vs declared `~/.config/rebalance/runtime-root`), `temp/rbos.config` is resolved per-CWD (`src/rebalance/ingest/config.py:217-220`), whereas installed LaunchAgents execute against the declared runtime root (`~/Library/LaunchAgents/com.rebalance-os.pulse-sync.plist:10-16`). On this Mac today, running `doctor` from `/Users/noelsaw/Documents/GH Repos/rebalanceOS` reads `pulse_fleet_enabled: None` (not enrolled, as recorded in `TESTS-RESULTS/2026-10-18+GH-334/smoke-main-path.log:2-5`), while `/Users/noelsaw/rebalance-runtime/temp/rbos.config` has `pulse_fleet_enabled: True` and `~/.config/git-pulse/config.sh` has `fleet_mode=true` (and the runtime root is currently 11 commits behind `origin/development` at `9dd2665`, pre-GH-325). Because `publish_pulse` in `pulse-sync` runs in the runtime root, a fleet-enrolled runtime will queue commits locally (`push=False` at `src/rebalance/ingest/pulse.py:958-959`) and rely on `com.user.git-pulse` (`~/Library/LaunchAgents/com.user.git-pulse.plist`, currently also unloaded in `launchctl`) to push. Hinting in Step 0 to prefer `~/.config/rebalance/runtime-root` when present (or pull runtime drift per `SOP.md:227-233`) would avoid diagnosing the dev clone's config when the scheduled jobs run from the runtime clone; however, even as written, Step 4's single recheck (`SKILL.md:123-126`) honestly surfaces any remaining ahead count if `pulse-sync` queues instead of pushing.
- [Nit] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:40` — If a pulse clone branch ever had no upstream tracking ref configured, `git -C "$PULSE" rev-list --left-right --count @{u}...HEAD` exits 128 (`fatal: no upstream configured for branch`). On a normal clone (`main...origin/main`) it succeeds, and under the skill's stop-on-error posture an unconfigured upstream simply halts diagnosis for the operator.
- [Pass] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:49-55` and `99-119` — End-to-end walkthrough of the off-fleet diagnosis state (`scheduler:pulse-sync` installed but not loaded, `pulse` configured, fleet not enrolled, clean tree, 39 behind / 10 ahead, `PULSE_PUSH` unset) produces the right sequence: Step 2.1 runs `launchctl load -w ~/Library/LaunchAgents/com.rebalance-os.pulse-sync.plist` (`src/rebalance/doctor.py:844-846`), Step 2.3 reports non-enrollment without enrolling (`UPGRADE.md:203-206`), and Step 3 kickstarts `gui/$(id -u)/com.rebalance-os.pulse-sync`. Having `<key>RunAtLoad</key><false/>` (`scripts/com.rebalance-os.pulse-sync.plist.template:44-45`) only suppresses automatic execution at `load` time; `launchctl kickstart gui/$(id -u)/com.rebalance-os.pulse-sync` explicitly triggers an immediate run of a loaded calendar-interval job. Off-fleet with `PULSE_PUSH` unset, `scripts/pulse_sync.sh:41` sets `push=True`, `publish_git_paths` (`src/rebalance/lib/git_ops.py:718-732`) attempts `git push`, catches the non-fast-forward rejection, and calls `git_pull_rebase_safe(repo_path, resolve_conflicts=resolve_page)` (`src/rebalance/lib/git_ops.py:618-660`, `src/rebalance/ingest/pulse.py:878-907`), which runs `git -c rebase.autoStash=false pull --rebase` under `rebalance-publish.lock` and replays the local commits over upstream (aborting cleanly via `_cleanup_failed_rebase` if any non-replaceable conflict occurs).
- [Pass] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:34-43` and `69-90` — Shell syntax and quoting are copy-paste accurate: `G=$(git -C "$PULSE" rev-parse --absolute-git-dir)` (`SKILL.md:34`), `"$G/rebalance-publish.lock"` (`SKILL.md:77`), `export PULSE G` (`SKILL.md:71`) passes both variables into the `subprocess.call(["bash","-c",sys.argv[2]])` child while `R` and `S` are defined inside that same `bash -c` script (`SKILL.md:83-89`) and `$(cat "$R/orig-head")` is properly quoted (`SKILL.md:85`). `launchctl print gui/$(id -u)/<label>` and `launchctl kickstart gui/$(id -u)/<label>` (`SKILL.md:54,112,114`) use valid macOS launchd domain/service-target syntax, and `StandardOutPath`/`StandardErrorPath` (`SKILL.md:108-110`) match the top-level dict keys in `scripts/com.rebalance-os.pulse-sync.plist.template:47-51` and `experimental/git-pulse/com.user.git-pulse.plist.template:17-20`.
- [Pass] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:66-93` and `SOP.md:361-371` — Safety invariants and doc agreement hold: Step 2.4 acquires `$G/rebalance-publish.lock` with `LOCK_EX | LOCK_NB` (`SKILL.md:74-76`), checks `lsof +D "$PULSE"` (`SKILL.md:80-81`), re-reads `$R/orig-head` and `$R/head-name` under the lock (`SKILL.md:82-83`), verifies both `pulse-repair-backup/$S-orig` and `pulse-repair-backup/$S-head` (`SKILL.md:84-86`), saves `git -C "$PULSE" diff HEAD > "$G/pulse-repair-$S.patch"` (`SKILL.md:87-88`), and aborts once (`SKILL.md:89-90`). `SOP.md:361-371`, `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md:90-97`, and `SKILL.md:66-93` agree on all four prerequisites and on preserving merges, cherry-picks, reverts, and dirty/detached states outside the conflicted rebase. If the hourly job fires concurrently, both `pulse-sync` (`src/rebalance/ingest/pulse.py:816,825-832`) and `collect.sh` (`experimental/git-pulse/collect.sh:404-407`) use non-blocking `LOCK_EX | LOCK_NB` on the same lock and defer with exit 75 (`scripts/pulse_sync.sh:55-56`), which Step 3 (`SKILL.md:117`) explicitly classifies as busy/deferred without killing or restarting the job. While `job_guard.py` caps `pulse-sync` at 1800s (`scripts/com.rebalance-os.pulse-sync.plist.template:13`), a normal `pulse-sync` run takes ~5s (`pulse_sync_2026-10-18.log` recorded `elapsed_seconds: 4.56`), and at the 10-minute polling deadline (`SKILL.md:114,118-119`) the skill leaves a still-running job untouched and reports `"running"`.
- [Pass] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:1-127`, `ROADMAP.md:41`, and `TESTS-RESULTS/2026-10-18+GH-334/SUMMARY.md:1-12` — Scope is minimal and matches GH-334: one 127-line `SKILL.md`, one `SOP.md` exception paragraph, one `ROADMAP.md` entry, and campaign evidence in `TESTS-RESULTS/2026-10-18+GH-334/`, with zero new scripts, LaunchAgents, or Python code paths.
- [Unverified — needs clone run] Live scheduler loading (`launchctl load -w`), `kickstart` execution, and runtime completion attribution were not run in this review turn (as `TESTS-RESULTS/2026-10-18+GH-334/SUMMARY.md:10` also notes, those mutate the host). No test suites or mutating git commands were executed.

Read-only probe command (environment: `PYTHONDONTWRITEBYTECODE=1`, `TMPDIR="$PWD/.relay-scratch/tmp"`), exit 0:
```bash
git -C ~/git-pulse-sync rev-list --left-right --count @{u}...HEAD
git -C ~/git-pulse-sync merge-tree --write-tree HEAD @{u}
(cd "/Users/noelsaw/rebalance-runtime" && git rev-parse --short HEAD)
(cd "/Users/noelsaw/Documents/GH Repos/rebalanceOS" && bash scripts/stack.sh drift)
```
Decisive output:
```text
85	11
9eabcafa59fe8f44b702a3510c51004774b11516
9dd2665
RUNTIME: 11 commit(s) BEHIND origin/development — fleet is running 9dd2665 from 2026-10-07
         deploy: git -C "/Users/noelsaw/rebalance-runtime" pull --ff-only origin development
```
(`merge-tree --write-tree` exiting 0 with tree `9eabcafa59fe8f44b702a3510c51004774b11516` confirms the 11 local commits in `~/git-pulse-sync` have zero file-level conflict against the 85 upstream commits on `origin/main`.)

Answers:
1. **Would it work on a real Mac, end to end?** Yes. Walking the diagnosed off-fleet state (`scheduler:pulse-sync` installed/unloaded, `pulse` configured, fleet not enrolled, clean tree, 39 behind / 10 ahead, `PULSE_PUSH` unset) runs `launchctl load -w`, skips enrollment, and kickstarts `com.rebalance-os.pulse-sync` (`RunAtLoad=false` only affects load-time firing, not `kickstart`). In off-fleet mode with `PULSE_PUSH` unset, `publish_pulse` commits the rendered page, attempts `git push`, catches the non-fast-forward rejection, and rebases cleanly over upstream via `git_pull_rebase_safe` (`git merge-tree --write-tree HEAD @{u}` exits 0 with no conflicts). Note (Nit 1): on this specific Mac, `~/.config/rebalance/runtime-root` points to `/Users/noelsaw/rebalance-runtime` (which has `pulse_fleet_enabled: True` in its `temp/rbos.config` and trails `origin/development` by 11 commits), whereas the dev clone has `pulse_fleet_enabled: None` and `com.user.git-pulse` is also currently unloaded; once the runtime root is pulled to `origin/development` and used as `$RB` (or after `com.user.git-pulse` is loaded), fleet-mode resync (Step 3 Fleet: `refresh-pulse-clone` → `pulse-sync` → `com.user.git-pulse`) handles it directly.
2. **Copy-paste correctness.** Every shell line in `SKILL.md` is valid as written: `$G` resolves via `--absolute-git-dir` (`SKILL.md:34`), `export PULSE G` (`SKILL.md:71`) exports `PULSE` and `G` to the `bash -c` child while `R` and `S` are assigned inside that child (`SKILL.md:83-88`), `"$(cat "$R/orig-head")"` is quoted (`SKILL.md:85`), `StandardOutPath`/`StandardErrorPath` match the top-level plist keys (`scripts/com.rebalance-os.pulse-sync.plist.template:47-51`, `experimental/git-pulse/com.user.git-pulse.plist.template:17-20`), and `launchctl print`/`kickstart` use `gui/$(id -u)/<label>` (`SKILL.md:54,112,114`).
3. **Safety gaps.** None that can lose work or corrupt state. Uncommitted conflict edits are saved to `$G/pulse-repair-$S.patch` (`SKILL.md:87-88`), `orig-head` and `HEAD` are saved and verified as `pulse-repair-backup/$S-{orig,head}` branches (`SKILL.md:84-86`), untracked files survive `git rebase --abort`, and all other in-progress operations or dirty states outside the conflicted rebase stop untouched (`SKILL.md:92-93`). Concurrent hourly runs cannot race the abort because both writers acquire `$G/rebalance-publish.lock` with `LOCK_NB` and exit 75 when busy (`src/rebalance/lib/git_ops.py:282-284`, `experimental/git-pulse/collect.sh:404-407`). The 10-minute observation window is safe for an 1800s-capped job because the skill never kills or restarts a still-running job at the deadline (`SKILL.md:118-119`).
4. **Doc agreement.** `SKILL.md:49-93`, `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md:80-107`, `SOP.md:361-371`, `UPGRADE.md:185-210`, and `src/rebalance/doctor.py:842-848,2176-2262` all agree on the repair commands and the four stuck-rebase prerequisites.
5. **Over or under-built.** Commensurate with a single-operator per-device skill: 127 lines, no new code or scripts, and all requirements of GH-334 are covered.

VERDICT: PASS
Basis: `SKILL.md`, `SOP.md`, and the plan agree on all commands and safety prerequisites; shell invocations and lock/backup semantics are sound; no Blocker or Should found.

Relay closed (Approved), no further turn needed — handing off to Producer (claude-a).

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

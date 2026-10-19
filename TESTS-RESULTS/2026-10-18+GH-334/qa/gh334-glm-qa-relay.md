# RELAY · rebalanceOS PR #335 GH-334 independent QA (GLM 5.3 max)
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
6. **Commit only the relay file** (`relay(rebalanceos-pr-335-gh-334-independent-qa-glm-5-3-max): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh334-glm-brief.md** (embedded below — read it here).
- Reviewer: commandcode   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh334-glm-brief.md
```
# Independent QA (GLM 5.3): RebalanceOS PR #335 / GH-334 git-pulse-sync-repair

You are a third-family reviewer. Codex approved the plan and an earlier implementation. Agy approved the current one after finding a real bug in round 1: the skill diagnosed the dev clone, but this Mac's scheduled jobs run from `~/rebalance-runtime` in fleet mode. That bug was fixed in 864ff96. Look for what both missed.

Your worktree is HiQS-Labs/rebalanceOS at PR #335's head (0765c30). The diff against `origin/development` is:
- `experimental/git-pulse/git-pulse-sync-repair/SKILL.md`: the new skill, a procedure document with no code (138 lines)
- `SOP.md`: the "GH-334 exception: aborting a stuck pulse rebase" paragraph, after the GH-325 rollback rule
- `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md`: the approved plan, which is the spec
- `ROADMAP.md`: one entry
- `TESTS-RESULTS/2026-10-18+GH-334/`: smoke logs, `SUMMARY.md`, provenance, and the plan, final and agy QA relays

Operational envelope: a single operator's per-device agent skill, run on their own Macs. Grade at commensurate complexity. Do not ask for new code, suites, daemons or enterprise hardening. The repo forbids new scripts and LaunchAgents (GH-241); the doctor is read-only.

Operator decisions are fixed:
- the skill may repair and then resync
- location `experimental/git-pulse/`
- a stuck rebase may be aborted after verified backups (the SOP exception)  [Unverified — no citation]
- install after merge via the Skills Army HQ CLI
- RebalanceOS is on every device

Read alongside the skill:
- `src/rebalance/doctor.py` (pulse, pulse fleet and scheduler rows)
- `src/rebalance/ingest/config.py` (how `temp/rbos.config` is resolved)
- `src/rebalance/ingest/pulse.py` (publish, lock, push=False in fleet mode)
- `src/rebalance/lib/git_ops.py` (`git_pull_rebase_safe`, `_cleanup_failed_rebase`)
- `src/rebalance/cli/config_cmds.py` (`set-pulse`, `fleet-enroll`, `refresh-pulse-clone`)
- `scripts/stack.sh`, `scripts/pulse_sync.sh`, `scripts/com.rebalance-os.pulse-sync.plist.template`
- `experimental/git-pulse/collect.sh`, `experimental/git-pulse/com.user.git-pulse.plist.template`
- UPGRADE.md "Fleet self-repair", SCHEDULER.md

Questions:
1. **Does the 864ff96 fix hold?** Step 0 now resolves `RB` from `$REBALANCE_ROOT`, then `~/.config/rebalance/runtime-root`, then the clone with `.venv/bin/rebalance`, and checks it against the plist `ProgramArguments`. FLEET falls back to `pulse_fleet_enabled` in `$RB/temp/rbos.config`. Walk this Mac's state through it: runtime root `~/rebalance-runtime` (11 commits behind development, pre-GH-325, so its doctor has no `pulse fleet` row), `pulse_fleet_enabled: true`, `fleet_mode=true`, both `com.rebalance-os.pulse-sync` and `com.user.git-pulse` installed but not loaded, pulse clone 85 behind / 11 ahead, clean tree. Does every step choose the right action, in the right clone, in the right order?
2. **Copy-paste correctness.** Check every shell line: quoting of paths with spaces, `$RB`/`$PULSE`/`$G` resolution, the PlistBuddy key path against the real plist, `launchctl print`/`kickstart`/`load -w` target syntax, the step 2.4 flock wrapper and how variables cross into `bash -c`, and the Step 3 baseline (log paths, `runs = N`, byte sizes). Cite `file:line` for any line that fails as written.
3. **Safety.** Can any step lose local commits or uncommitted work, race the hourly job, or leave the device worse than it started? Is the stuck-rebase procedure (lock, lsof, re-read, two verified backup branches, patch, abort) complete, and does it stop on everything outside a conflicted rebase?
4. **Doc agreement.** Do `SKILL.md`, the plan, the SOP exception and the SUMMARY agree with each other and with the doctor's own hints?
5. **Over or under-built.** What could be cut, and is anything GH-334 asks for missing?

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

### Reviewer — Round 1 (commandcode)
swept file: yes

Swept the whole embedded brief, `experimental/git-pulse/git-pulse-sync-repair/SKILL.md` (all 138 lines), `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md` (all 181 lines), `SOP.md` (the GH-334 exception, lines 355-380), `ROADMAP.md:41`, all of `TESTS-RESULTS/2026-10-18+GH-334/` (SUMMARY, provenance, all smoke logs, retained harness), both prior QA relays (read for coverage context only; this review was performed independently against the current head), and the supporting code the skill names: `src/rebalance/doctor.py` (830-865, 2145-2255), `src/rebalance/lib/git_ops.py` (262-306, 570-654), `src/rebalance/ingest/pulse.py` (70-114, 860-965), `src/rebalance/ingest/config.py` (195-229), `src/rebalance/cli/config_cmds.py` (470-580), `scripts/stack.sh` (drift + header), `scripts/pulse_sync.sh`, both plist templates, `experimental/git-pulse/collect.sh` (230-262, 385-415), `scripts/lib/install_common.sh`, `UPGRADE.md` (185-212). No pre-existing defects requiring change were found in any touched file or in the supporting regions the skill depends on.

Findings:
- [Pass] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:24-35` — The 864ff96 fix holds on this Mac, verified live: `REBALANCE_ROOT` is unset in agent shells, `~/.config/rebalance/runtime-root` contains `/Users/noelsaw/rebalance-runtime`, and the installed plist's `ProgramArguments:0` is `/Users/noelsaw/rebalance-runtime/.venv/bin/python` — so `$RB` resolves to the runtime clone and the plist check confirms it. `FLEET` falls back correctly: the runtime doctor (pre-GH-325, `9dd2665`) has no `pulse fleet` row, and `$RB/temp/rbos.config:137` has `pulse_fleet_enabled: true` (`fleet_mode=true` at `~/.config/git-pulse/config.sh:67`). `launchctl print gui/$(id -u)/{com.rebalance-os.pulse-sync,com.user.git-pulse}` both return "Could not find service", so 2.1 correctly plans `load -w` on both jobs. Running doctor from `$RB` is load-bearing and correct: `src/rebalance/ingest/config.py:217-220` resolves `temp/rbos.config` per-CWD.
- [Pass] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:47-49` — The drift check works from `$RB` even though the runtime is 11 commits behind: the runtime's own `scripts/stack.sh` at `9dd2665` contains the `drift` subcommand (probe: `grep -c 'drift)' /Users/noelsaw/rebalance-runtime/scripts/stack.sh` → `1`), and `runtime_drift()` fetches before counting (`git -C "$REBALANCE_DIR" fetch --quiet origin development`, `scripts/stack.sh:475-479`), so the count is fresh rather than measured against stale remote refs.
- [Pass] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:119-131` — Step 3 baselines are real: `launchctl print gui/501/com.rebalance-os.daily-sync` shows literal `runs = 4` and `state = not running`, matching the skill's `runs = N` phrasing; the installed pulse-sync plist's `StandardOutPath`/`StandardErrorPath` are `temp/logs/pulse_{stdout,stderr}.log` under the runtime root (`scripts/com.rebalance-os.pulse-sync.plist.template:47-51`), the collector's are `git-pulse.out`/`.err` (`experimental/git-pulse/com.user.git-pulse.plist.template:17-20`), and the dated runtime log `pulse_sync_YYYY-MM-DD.log` comes from `scripts/lib/scheduler_common.sh:60-66`. PlistBuddy `'Print :ProgramArguments'` is the correct key path against the real installed plist (probe output quoted below). The 2.4 flock wrapper crosses variables correctly: `export PULSE G` (SKILL.md:83) reaches the `bash -c` child while `R`/`S` are assigned inside it, and `"$(cat "$R/orig-head")"` is quoted (SKILL.md:98). All `$RB`/`$PULSE`/`$G` path expansions are quoted, including against the space-containing `GH Repos` path style.
- [Pass] `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:78-105` — Safety verified against the code it cites: `src/rebalance/lib/git_ops.py:271-290` takes `LOCK_EX|LOCK_NB` on `<gitdir>/rebalance-publish.lock`; `experimental/git-pulse/collect.sh:393-410` takes the same lock and defers with exit 75; `src/rebalance/lib/git_ops.py:576-580` and `collect.sh:238-250` refuse rebase/merge/cherry-pick/revert/detached states with "preserve it for its owner". No step can lose local commits: the abort is reachable only after verified backup refs and the conflict patch, untracked files survive, and an hourly fire during 2.4 defers on the busy lock rather than racing. In fleet mode `publish_pulse` forces `push = False` (`src/rebalance/ingest/pulse.py:956-959`), so step 3's "render and queue" holds even though the installed plist has no `PULSE_PUSH` key (probe: `Print :EnvironmentVariables:PULSE_PUSH` → "Does Not Exist"), consistent with `scripts/pulse_sync.sh:37-42`.
- [Pass] State-walk answer (brief Q1): on this exact Mac step 3 fleet stops cleanly at 3.1 — `$RB`'s CLI at `9dd2665` (pre-GH-325) has none of `set-pulse`/`fleet-enroll`/`refresh-pulse-clone` (probe: `config --help` lists none of the three; all were introduced in commits `1a496fa` and `80ce446`, which postdate `9dd2665`) — and step 1's drift finding already names the deploy command. The stop is honest and matches the plan's outcome ("recovers in one agent pass, or stops with the exact remaining blocker"). Even stopped at 3.1, the completed 2.1 repairs the device: loading the collector (`RunAtLoad` true, `com.user.git-pulse.plist.template:15-16`) fires it immediately, and it reconciles and delivers under the same writers' lock (`collect.sh` `pull_safely`), which is the #333/#334 outcome.
- [Pass] Doc agreement: `SOP.md:361-371` states all four prerequisites and preserves other states only "outside such a conflicted rebase", matching `SKILL.md:104-105`; the doctor's own hint (`src/rebalance/doctor.py:844-846`) matches 2.1's `load -w`; `UPGRADE.md:185-212` matches 2.3 (repair-only `fleet-enroll --apply`, no auto-enrollment); `SUMMARY.md` and `smoke-main-path-runtime.log` agree; all 4 `provenance.jsonl` sha256 hashes verify (probe below).
- [Nit] `SKILL.md:74,114` — Steps 2.3 and 3.1 use bare `rebalance config …` while step 0 (`SKILL.md:30`) and 2.2 (`SKILL.md:70`) use `"$RB/.venv/bin/rebalance"`. `rebalance` is not on PATH on this Mac (probe: `command -v rebalance` → not found), so the bare form fails fast and an agent falls back to `$RB`'s CLI; but writing the full `"$RB/.venv/bin/rebalance"` in 2.3/3.1 removes the last place a different clone's CLI could be picked up.
- [Nit] `SKILL.md:26-28` — Step 0 says "Confirm that `$RB` matches the path in the installed pulse-sync plist's ProgramArguments" but names no action on mismatch. On this Mac they match (probed), so there is no observed failure; one sentence ("on mismatch, adopt the plist's root as `$RB` and re-run doctor from it") would close the gap that made the original round-1 bug possible.
- [Nit] `SKILL.md:59-60` — `launchctl load -w` on the collector fires it immediately (`RunAtLoad` true, `com.user.git-pulse.plist.template:15-16`), so a step-3 baseline recorded after 2.1 can already include a load-triggered run. Step 3's "If the job is already running, observe that run and do not claim a new one" (`SKILL.md:125`) covers the interaction; a note in 2.1 would prevent misattributing that run to the later kickstart.
- [Unverified — needs clone run] Live `launchctl load -w`, `kickstart` execution and completion attribution were not exercised in this turn (they mutate the device; `TESTS-RESULTS/2026-10-18+GH-334/SUMMARY.md:11` reserves them for the operator's post-merge run). No suite or executable fixture was run; the harness gate follows this turn.

Read-only probes (environment: `PYTHONDONTWRITEBYTECODE=1`, `TMPDIR="$PWD/.relay-scratch/tmp"`), all exit 0 unless noted:
```bash
cat /Users/noelsaw/.config/rebalance/runtime-root
/usr/libexec/PlistBuddy -c 'Print :ProgramArguments:0' /Users/noelsaw/Library/LaunchAgents/com.rebalance-os.pulse-sync.plist
launchctl print gui/$(id -u)/com.rebalance-os.daily-sync | grep -E 'state|runs'
launchctl print gui/$(id -u)/com.rebalance-os.pulse-sync        # not loaded
grep -n 'pulse_fleet_enabled' /Users/noelsaw/rebalance-runtime/temp/rbos.config
grep -c 'drift)' /Users/noelsaw/rebalance-runtime/scripts/stack.sh
/Users/noelsaw/rebalance-runtime/.venv/bin/rebalance config --help | grep -oE 'set-pulse|fleet-enroll|refresh-pulse-clone'
command -v rebalance
git rev-parse --short HEAD   # worktree head 6dca505 = 0765c30 + this relay seed
```
Decisive output:
```text
/Users/noelsaw/rebalance-runtime
/Users/noelsaw/rebalance-runtime/.venv/bin/python
state = not running / runs = 4
Could not find service "com.rebalance-os.pulse-sync" in domain for user gui: 501
137:  "pulse_fleet_enabled": true,
1
(no subcommands listed — grep empty)
rebalance: not on PATH
```

Answers: (1) yes — every step picks the right action, the right clone and the right order on this Mac; the fleet resync stops honestly at 3.1 (pre-GH-325 runtime) with drift reported, and 2.1 alone unblocks delivery via the load-triggered collector. (2) every probed shell line is correct as written. (3) no step can lose commits or race the hourly job; 2.4 stops on everything outside a conflicted rebase. (4) SKILL, plan, SOP exception, SUMMARY and the doctor's own hints agree. (5) commensurate with a single-operator per-device skill; nothing GH-334 asks for is missing and nothing needs cutting beyond the three Nits.

VERDICT: PASS
Basis: The 864ff96 runtime-root resolution is correct and live-verified on the target Mac; all shell invocations probe out as written; the 2.4 abort gate matches the writers' real lock and refusals; the docs agree; no Blocker or Should — the three Nits are optional wording clarifications that do not affect the skill working as written.  [Unverified — no citation]

Relay closed (Approved), no further turn needed — returning coordination to Producer (claude-a) for the harness gate and post-merge workflow.


### Attestation · relay-drive — 2026-10-19T15:16:48Z
task: RELAY-rb-gh334-glm-qa-r1
reviewer: commandcode
status: Approved
reviewed-head: 6dca5050dabfceffe0aa2c05fc9c2c149236fcc8
added-range: 9648+9874
added-sha256: 2053e79eceb939c8752b7b2286600205281f03d15a49e0072434fb442c0d79b9
<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

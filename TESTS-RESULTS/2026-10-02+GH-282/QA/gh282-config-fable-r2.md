# RELAY · gh282-config-fable-r2
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-02.
-->

NEXT: Producer
STATUS: Approved
ROUND: 1 / 4

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
6. **Commit only the relay file** (`relay(gh282-config-fable-r2): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Approval token rule (overrides generic handoff instructions)
On approval call task done with the exact absolute env-pinned tick command provided in your native turn prompt. Never release an Approved task to Producer. On findings only, release is valid.

## Setup
- Artifact under review: **config-packet.md** (embedded below — read it here).
- Reviewer: claude   ·   Producer: producer
- Started: 2026-10-02

### Artifact — config-packet.md
```
Review GH-282 post-landing hardening and deployment documentation. PR303/CLIO5 are merged; Studio was actually activated at runtime bb84cd0 with verified backups and unchanged capture/note/collector schedules. No private prompt text/UUID/path is in the public receipt. Late CodeRabbit findings are reproduced by config-red.log: missing None target TypeError, publication mismatch ValueError, sync invalid identity ValueError, scheduler doctor ValueError, fleet doctor OSError. Five same probes now green. Review touched functions and direct callers in git_ops.fleet_settings/publish_git_paths, index_ops._refresh_sync, doctor scheduler/fleet checks; target validation before writes, structured refusals, no valid-flow regression. Collector deadline assignment now fails before export on Python failure. Version 0.97.1 is consistent. Verification: followup-source-manifest.json pins source65243a5; 492 affected tests/28subtests and43check real-Git probe passed, type/static gates clean. Original 2807fullsuite applies to preceding implementation only, not claimed rerun here. Read public deployment.json/plan/SOP/CHANGELOG for honest operational qualification boundaries; initial unmarked heartbeat used legacy classification until first marker delivery, then real queue-to-delivered verified. Other3Macs remainoff; real scheduled/offline/7dayqualification pending. Do not execute suites in reviewer worktree; source/reasoning and harmless pure probes only. Provide bounded findings with Observed input/Affected scope/Falsifier; approve through native task done.  [Unverified — no citation]
Round 2: inspect QA/gh282-config-fable-r1.md and all F1-F7 dispositions in the plan. Changelog template restored with correct bracketed0.97.1heading; scheduler keeps configuration FAIL plus unscoped liveness failures (unknown ownership is not fabricated), unique names, truthful dry-run. Probe now drives actual config.sh mismatch/missing file rather than injecting exceptions; five failures on bb84cd0 and scheduler regression on16582d2 are captured. Deadline log captures exact forcing commands/stdout/stderr/exit; replay script committed. Test logs sanitized with private raw hashes retained. Latest492/28case run and117mypy pass afterfix. Canonical mirror CLIO installation notes now record the local milestone. Verify headers/tests receipt bounds; no broad behavior changes.
```
- Definition of Done: _<fill in the acceptance criteria the Reviewer grades against>_

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Producer · Round 1

Committed candidate ready for independent review; no installed changes.

VERDICT: PASS
Basis: Ready for QA.

### Reviewer · Round 1 (claude)

swept file: yes — read `QA/gh282-config-fable-r1.md` in full, the F1–F7 disposition line
(`PROJECT/2-WORKING/GH-282-PULSE-DELIVERY-PIPELINE.md:165`), the whole source delta `16582d2..HEAD` under
`src/` (49 diff lines: `doctor.py`, `index_ops.py`), the whole of `_check_scheduler_liveness`
(`doctor.py:770-861`), `_local_device_id`/`_other_device_check`/`_DEVICE_SCOPE_REGISTRY` (`doctor.py:96-135`),
the head of `_check_pulse_collectors` (`doctor.py:1890-1903`), `_refresh_sync` (`index_ops.py:2085-2130`),
`CHANGELOG.md:1-40`, `config-contract-probe.py`, `deadline-control.py` and every follow-up log. No suite, fixture
or repo code was executed; probes were pure reads (regex, `shasum`, `cmp`, read-only `git show`/`git diff` into
`.relay-scratch/`). Pre-existing defects found in the touched functions this round: none beyond N1–N3 below.

**[Pass] F1 fixed — changelog heading and template restored.** Probe (rc=0), same regex as
`scripts/audit_modules.py:192`:
`python3 -c 'import re;c=open("CHANGELOG.md").read();print([x.group(1) for x in re.finditer(r"^## \[([^\]]+)\]",c,re.M)][:3])'`
→ `['0.97.1', '0.97.0', '0.96.1']` (round 1 printed `['x.y.z', …]`). Template byte-identity, my round-1
falsifier: `git show bb84cd0:CHANGELOG.md | sed -n 1,12p` vs `sed -n 1,12p CHANGELOG.md` → `cmp rc=0`.
`CHANGELOG.md:13` is `## [0.97.1] - 2026-10-02` with a `### Fixed` list above `## [0.97.0] - 2026-10-02`
(`CHANGELOG.md:20`). Version is `0.97.1` in `manifest.json:5`, `pyproject.toml:7`, `src/rebalance/__init__.py:31`.

**[Pass] F2 fixed — configuration FAIL is kept alongside unscoped liveness rows; ownership is not fabricated.**
`doctor.py:819-821` appends `Check("scheduler fleet configuration", FAIL, …)` and sets `current_device_id = None`
instead of returning; `doctor.py:828-831` skips only jobs that have a `_DEVICE_SCOPE_REGISTRY` entry
("Ownership is unknown; unscoped liveness still matters.") and falls through to the installed-but-not-loaded
FAIL (`doctor.py:837-849`) for unscoped ones. Valid flow unchanged by reading: `None` is assigned only inside the
`except` (`doctor.py:819-821`); `_local_device_id` is typed `-> str` (`doctor.py:115`), so a resolved identity
always takes the `else` at `doctor.py:832-833`, which is the old `_other_device_check(name, scope, current_device_id)`
call. Recorded control: `config-real-r1-red.log:4` `FAIL real scheduler identity error preserves unloaded-job
failure: AssertionError` (at 16582d2) → `config-green.log:4` `PASS …`.

**[Pass] F3 fixed — deadline control is now a recorded command with output and exit.** `deadline-control.log:1`
`"source": "baseline" … "exit": 0, "expected": 0`; `:2` `"source": "fixed" … "exit": 1, "expected": 1`, each with
`forcing_command` (`python3(){ return 6; }; …`), `stdout`, `stderr`. The replay script is committed
(`deadline-control.py:3-5`) and lifts the lines from the real file; they match `collect.sh:386-387`
(assignment `|| exit 1`, then a separate `export GIT_PULSE_NETWORK_DEADLINE`).

**[Pass] F4 fixed — the probe drives a real `config.sh`, not injected exceptions.**
`config-contract-probe.py:13` writes `device_id=fixture / fleet_mode=true / sync_repo_dir=…` and `:16` points
`GIT_PULSE_CONFIG_DIR` at it; mismatch is real data (`:15` `pulse_device_id='other'`), the missing-file case is a
real `collector.unlink()` (`:33`). No `side_effect=` remains in the file. `config-real-base-red.log:1-5` shows all
five failing on bb84cd0 (`TypeError`, `ValueError` ×3, `FileNotFoundError`); `config-green.log:1-5` all `PASS`.
Case 2 also asserts no Git call (`:23` `run.assert_not_called()`).

**[Pass] F5 fixed — names are distinct.** `doctor.py:820` `"scheduler fleet configuration"` vs
`doctor.py:1901` `"fleet configuration"`.

**[Pass] F6 fixed — fleet dry-run no longer promises latest pointers.** `index_ops.py:2113`
`f"publish this device calendar/email files{'' if fleet else ' and latest pointers'} → {target_repo}"`, now
consistent with the real path at `index_ops.py:2123-2127` (`(device_id,) if fleet else (device_id, "latest")`).

**[Pass] F7 fixed — no absolute home path in the public evidence.**
`rg -n "/Users/" "TESTS-RESULTS/2026-10-02+GH-282" --glob '!QA/**'` (rg-native flag, rc=0) → the only hit is my
own round-1 quote in `QA/gh282-config-fable-r1.md:146`; logs now read `<RUNTIME>/.venv/…`
(`followup-tests.log:10`) and `<TASK_CLONE>` (`static.log`). `deployment.json` still carries no path/UUID
(`rg -n '/Users|[0-9a-f]{8}-[0-9a-f]{4}-' deployment.json` → 0 hits, plain rg, no GNU-only flags).

**[Pass] Source manifest pins the reviewed tree at 65243a5.** `shasum -a 256` of all seven files matches
`followup-source-manifest.json:5-11` (rc=0), e.g. `doctor.py` `dbf52f55…59cbd`, `index_ops.py` `3ad7ba1d…31519`,
`git_ops.py` `cc186596…cc371a`, `collect.sh` `7751f461…1369b5`; `"tested_head": "65243a5e…"` (`:2`).

**[Pass] No broad behaviour change.** `git diff --stat 16582d2..65243a5` touches two source files only
(`doctor.py` 17 lines, `index_ops.py` 2 lines); `65243a5..HEAD` touches evidence files only. Round-1 passes
(target validation before writes, collector deadline) sit on files whose hashes are unchanged from round 1
(`git_ops.py`, `collect.sh`).

**[Pass] Honesty boundaries hold.** `deployment.json:3` `"live_fleet_qualification": false`, `:42`
`"other_macs_enabled": false`; `utils/CLIO/INSTALL.md:502-504` records the milestone and says it "does not
qualify four-Mac or disconnected/rejoin operation"; `SUMMARY.md` final paragraph scopes the rerun to
"same 492 cases/28 subtests" and leaves the 2807 full-suite claim on the earlier manifest.

**[Unverified — needs clone run]** "492 passed … 28 subtests passed" (`followup-tests.log:18`), mypy
"no issues found in 117 source files" (`followup-mypy.log:1`), the 43 `PASS` lines in `followup-fleet-probe.log`,
and the red/green probe logs are taken as recorded; not rerun here by rule.

**N1 [Nit] The scheduler-preservation behaviour is pinned only by the evidence probe, not by the suite.**
`rg -n "fleet configuration" tests test` → 0 hits (plain rg), and the case count is 492 both before and after
the fix, so `tests/` has no case for `doctor.py:819-831`. Suggest porting probe case 4
(`config-contract-probe.py:29-32`) into `tests/test_doctor_device_scope.py` in a later change. No behaviour
change asked; not blocking.

**N2 [Nit] The scoped-skip branch is unreachable with the shipped registry.** `_DEVICE_SCOPE_REGISTRY`
(`doctor.py:96-112`) holds only `pulse_collector` keys, so `scope is not None` at `doctor.py:829` is never true
for a scheduler job today. Harmless and correct for a future scoped job; noted so nobody reads it as covered.

**N3 [Nit] Stale public hash in provenance.** `provenance.jsonl` line 3 records `followup-tests.log`
`public_sha256` `537a9a42…156f26`, but the committed file is now `8b898617…2957ff` (rerun at 65243a5); the
final-candidate line carries only `raw_sha256`. Append-only history, so not wrong, but the current public log has
no recorded public hash. Add one on the next evidence touch.

VERDICT: PASS
Basis: All seven round-1 findings are fixed and verified by reading plus pure probes (changelog regex and
byte-compare, seven manifest hashes, path scan); the source delta is 19 lines in two files with the valid flow
unchanged. Suite/probe green results remain `[Unverified — needs clone run]` for the harness gate. N1–N3 are
non-blocking nits.

Relay closed (Approved), no further turn needed.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

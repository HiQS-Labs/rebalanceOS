# RELAY · gh282-implementation-fable-r1
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-02.
-->

NEXT: Producer
STATUS: Open
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
6. **Commit only the relay file** (`relay(gh282-implementation-fable-r1): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Approval token rule (overrides generic handoff instructions)
On approval call task done with the exact absolute env-pinned tick command provided in your native turn prompt. Never release an Approved task to Producer. On findings only, release is valid.

## Setup
- Artifact under review: **implementation-packet.md** (embedded below — read it here).
- Reviewer: claude   ·   Producer: producer
- Started: 2026-10-02

### Artifact — implementation-packet.md
```
Review GH-282 implementation against PROJECT/2-WORKING/GH-282-PULSE-DELIVERY-PIPELINE.md and source recon. Read the entire touched producer/collector/health files, including pre-existing behavior. Verification is in TESTS-RESULTS/2026-10-02+GH-282: final candidate full suite 2804/143 passed, real-Git probe and source hashes. Read canonical CLIO helper from environment QA_CLIO_HELPER; its separately reviewed PR #5 is the deployment prerequisite. Operational envelope: four personal Macs, one existing pusher per Mac, stable private SQLite replicas, same note/exporter schedules; initially only Studio activation. No new store/timer/ledger writer. Questions: 1. Does fleet configuration enforce identity/checkout/subdir before write and prevent every scheduled/CLI/MCP producer from pushing? 2. Do exact owner staging, bounded retries/deadlines/once-before-lock stagger preserve pending/foreign data? 3. Does CLIO owner validation, cumulative export and post-pull path guard preserve imported history without echo? 4. Does upstream page/status verification correctly distinguish queued, failed, legacy and delivered output? 5. Are docs/rollback/qualification limits honest and complexity proportionate? Optional A9 unchanged-page optimization and external B4/four-Mac/seven-day qualification remain explicitly open. No pytest/executable fixtures in reviewer worktree. Provide PASS or concrete bounded findings citing file:line plus Observed input, Affected scope, Falsifier. The source-manifest pins tested code; no installed capture/private history is changed by QA. Do not count plan-driver exit4 as attestation. Approve only through native task done, not release.
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

### Reviewer · Round 1 (claude — claude-fable-5-1)

swept file: yes

Scope read in full: `experimental/git-pulse/collect.sh` (773 lines), `src/rebalance/lib/git_ops.py`,
`src/rebalance/ingest/pulse_health.py`, `src/rebalance/ingest/sync_snapshot.py`,
`src/rebalance/ingest/pulse.py:811-1117` (publish path; render sections 560-810 read, earlier
collectors skimmed only), plus the base→HEAD diffs of `health-check.py`, `doctor.py`, `config.py`,
`index_ops.py`, `daily_synthesis.py`, `hiqs_digest.py`, `pulse_sync.sh`, and the canonical helper's
`atomic` / `export_device` / `snapshot_records` (`$QA_CLIO_HELPER:56-72, 798-843`). No pytest,
validate.sh or fixture was run here; suite/probe counts below are the Producer's records, not mine.

**Findings**

1. `[Blocker]` Fleet health reports a healthy, fully delivered device as `ALIVE_NOT_PUBLISHING`
   whenever the delivered render is older than 75 minutes — which the documented schedule produces
   every night and, depending on collector phase, every hour.
   `pulse_health.py:173` requires `(now - last_pulse_publish_utc) <= 1.25h`. pulse-sync only renders
   hourly 06:00–23:00 (`SCHEDULER.md:17`), the collector is `StartInterval 3600` with no fixed phase
   (`com.user.git-pulse.plist.template:13-14`) and health-check runs at :10 around the clock
   (`SCHEDULER.md:22`), exiting 1 on any priority-2 device (`health-check.py:254`); doctor maps the
   state to WARN (`doctor.py:1855`). The repo already recorded this lesson for local pulse health:
   "respecting the planned overnight schedule gap (#211)" (`CHANGELOG.md:267-268`).
   Probe (non-mutating, pure function), exit 0:
   `PYTHONPATH=src python3 -` constructing `CollectorHealth(fleet_mode=True, last_pulse_exit=0, pulse_delivery_pending=False, …)` → `classify()`:
   ```
   overnight: heartbeat 10m, last render 190m (23:00 render seen 02:10), exit0, delivered -> ALIVE_NOT_PUBLISHING
   daytime: heartbeat 40m, delivered render 80m old, exit0, delivered -> ALIVE_NOT_PUBLISHING
   daytime: delivered render 70m old -> ALIVE
   legacy same inputs -> ALIVE
   ```
   Observed input: fleet device, heartbeat 10 min old, delivered status `last_exit=0`, matching page
   hash, `last_render_success_utc` 190 min old (the 23:00 render observed at 02:10); and the same with
   an 80-minute-old render (collector phase later than :15 past the render).
   Affected scope: `fleet_mode == true` devices with a fresh heartbeat, `last_exit == 0`, nothing
   pending, and render age > 1.25 h. Legacy devices are unaffected (probe row 4).
   Falsifier: a `classify()` fixture for those two inputs expecting `ALIVE`; it fails today. If the
   operator intends a nightly WARN on an always-on Mac, the finding is void — but then SOP/SCHEDULER
   must say so, and today they do not (`SOP.md:350-357` only says unverifiable evidence is "not publishing").
   Fix (bounded, no new store/timer): make the delivered-age bound cover the longest scheduled render
   gap plus one collector interval and the stagger (23:00→06:00 + 60 min + 240 s ≈ 8.25 h), as a named
   constant or config value. Explicit failure stays immediate through `last_exit != 0` and
   `pulse_delivery_pending`; only detection of a silently dead pulse-sync job slows to that bound.
   Add the two fixtures above plus one just past the new bound, and state the bound in SOP.
   Unverified — needs clone run: whether the Studio's collector actually runs overnight (if the Mac
   sleeps, the heartbeat goes stale first and this path is masked at night; the daytime case stands).

2. `[Should]` Queued and failed are indistinguishable to the operator, which is the distinction Q4
   asks for. `classify()` folds pending, non-zero exit, missing and aged evidence into one state
   (`pulse_health.py:169-175`); doctor prints one phrase, "alive but not publishing"
   (`doctor.py:1855`), and health-check prints only the label (`health-check.py:154-155`). The
   fields exist (`pulse_health.py:53-55`) but never reach output. Same probe:
   ```
   queued only (pending), exit0, render 10m -> ALIVE_NOT_PUBLISHING
   delivered failure exit70, render 130m -> ALIVE_NOT_PUBLISHING
   ```
   Consequence with the current schedule: on its own Mac a device shows the warning from each :00
   render until its collector's next run, i.e. normal operation reads the same as a render failure.
   Observed input: the two probe rows above (pending-only vs delivered `last_exit=70`).
   Affected scope: fleet devices in state `ALIVE_NOT_PUBLISHING`; output text only, no state change.
   Falsifier: a doctor/health-check output fixture for those two inputs showing different detail
   text; if existing output already differs, this is void (I read `doctor.py:1853-1912` and
   `health-check.py:142-272` and found no use of `last_pulse_exit` / `pulse_delivery_pending`).
   Fix: carry a reason into the detail/notes — e.g. "queued, awaiting collector", "render failed
   (exit N)", "no delivered status", "delivered render Nh old" — without adding states.

3. `[Nit]` A CLIO export fault stops the collector before the heartbeat. Any `sys.exit` in the
   export block (`collect.sh:630-647`, e.g. "CLIO export regressed") aborts under `set -euo pipefail`
   (`collect.sh:5`) before the metadata write at `collect.sh:671`, so a CLIO-only problem surfaces as a
   stale collector with exit 1. Pending commits are already delivered by the early push
   (`collect.sh:616`) and `last-run` is not advanced, so nothing is lost; this is fail-closed and
   defensible. By code reading only, not executed. Fix: one SOP sentence saying a CLIO fault
   deliberately halts that Mac's heartbeat and how to recover (a DB restored from the step-2 backup
   is the likely trigger of the regression guard).

4. `[Nit]` Page/status hash comparison reads the page in text mode. `run_git` uses `text=True`
   (`git_ops.py:235-241`), which folds `\r` to `\n` (probe: `printf 'a\r\nb\rc'` read with
   `text=True` → `'a\nb\nc'`), while the producer hashes the raw rendered string (`pulse.py:1039`) and
   health hashes `payload.stdout.encode()` (`pulse_health.py:241`). A page containing a carriage
   return would read as permanently mismatched. Only two fields strip `\r` (`pulse.py:291, 315`). I
   have no observed CR-bearing page, so no behaviour change is requested; noting the mechanism.

5. `[Nit]` Small inconsistencies, no behaviour impact: `publish_git_paths` docstring says "deliver
   once plus one race retry" but loops three attempts (`git_ops.py:499, 540`); the state comment omits
   the new state (`pulse_health.py:57`); `import re` is repeated inside the loop
   (`pulse_health.py:220`, already imported at line 29); a status-write failure sets `status_error`
   (`pulse.py:1093`) but `pulse_sync.sh:51-60` still exits 0.

6. `[Nit]` Pre-existing, unchanged by this work: the final "upstream does not contain local HEAD"
   check exits 1 (`collect.sh:763-766`; same at base `4349ff5` lines 625-627) although the taxonomy
   reserves 1 for config and 2 for Git errors.

**Review questions**

- Q1 `[Pass]` Identity, checkout and subdirectory are validated before any write and no Python
  producer pushes in fleet mode. `fleet_settings` refuses a missing/unsafe/mismatched device ID
  (`git_ops.py:57-59`), collector mode off (`:60-61`), subdir mismatch (`:62-69`) and a different
  checkout (`:70-73`); it runs before the write in pulse (`pulse.py:962`, `:1052-1054`), snapshots
  (`sync_snapshot.py:66-70`, `index_ops.py:2098-2101`), daily synthesis (`daily_synthesis.py:434-435`)
  and digests (`hiqs_digest.py:954-956`). The only `git push` in Python is `git_ops.py:541`, and
  `publish_git_paths` forces `push = False` for the fleet checkout (`git_ops.py:508-515`). CLI
  (`cli/refresh.py:136-138`) and MCP (`mcp/tools/index.py:192-194`) both call `publish_pulse`, so they
  inherit it. Collector-side identity/subdir validation runs before the lock (`collect.sh:370-385`).
- Q2 `[Pass]` Exact owner staging (`collect.sh:574, 584-588, 743-750`), foreign dirt refused rather
  than stashed (`:599, 608-609`), three attempts with 2–20 s jitter (`:59-72`), per-call and 900 s
  total deadlines (`:28-34, 386`), stagger once before the lock (`:370-385` vs `:392-411`), pending
  work committed before pull (`:610-612`) and the watermark advanced only after upstream contains
  HEAD (`:763-770`). Runtime behaviour under fault is the Producer's probe
  (`fleet-probe.log`: "foreign dirt refused and preserved", "timed-out push exits 2 …") —
  `[Unverified — needs clone run]` by me.
- Q3 `[Pass]` Owner-only cumulative export without echo: the helper selects `WHERE origin_id=?` for
  the DB owner (`$QA_CLIO_HELPER:813`), `snapshot_records` rejects a wrong owner and any foreign row
  (`:826-827, 837-838`), the collector checks symlink/escape after the pull (`collect.sh:634-641`),
  refuses a shrinking record set (`:644-647`) and stages exactly `devices/<uuid>/clio.jsonl`
  (`:584, 750`). Helper hash matches the manifest (sha256 `4ab6c0a2…29d6a`, recomputed here).
- Q4 `[Blocker]` — findings 1 and 2. Legacy compatibility and the delivered-failure path are correct
  (`pulse_health.py:212-213`; probe rows "legacy same inputs -> ALIVE", "delivered failure exit70").
- Q5 `[Pass]` with the gap in finding 1: qualification limits are stated honestly — "Synthetic probes
  do not satisfy these live gates" (plan doc, Deployment boundary), "Synthetic probe only; live fleet
  qualification remains pending." (`fleet-probe.log` last line), plan-driver exit 4 not counted
  (`SUMMARY.md`). Rollback preconditions are explicit (`SOP.md:346-348`). No new store, timer or
  ledger writer found. All 14 `source-manifest.json` hashes recomputed and match this tree
  (`python3` sha256 loop, 14 × `OK`, exit 0).

Pre-existing defects in the touched files: finding 6 and the text-mode read in finding 4 (shared
with `_verify_remote_content`, `pulse.py:938-939`). I found no other pre-existing defect in the
files listed under scope; `pulse.py:1-559` was not read line by line.

VERDICT: FAIL
Basis: One observed false-negative in fleet health (finding 1) contradicts the "honest liveness"
goal on the first Mac to be activated; finding 2 should land with it. Everything else in Q1–Q3 and
Q5 holds. Fix is local to `classify()` output plus fixtures and one SOP line.

Handing off to Producer — go to the Producer window and say "take your turn".

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

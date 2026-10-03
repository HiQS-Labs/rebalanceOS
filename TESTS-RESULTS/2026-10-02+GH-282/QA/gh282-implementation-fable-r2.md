# RELAY · gh282-implementation-fable-r2
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
6. **Commit only the relay file** (`relay(gh282-implementation-fable-r2): <role> r<N>`); no push. **Stop** and report one line.
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
Review GH-282 implementation against PROJECT/2-WORKING/GH-282-PULSE-DELIVERY-PIPELINE.md and source recon. Read the entire touched producer/collector/health files, including pre-existing behavior. Verification is in TESTS-RESULTS/2026-10-02+GH-282: final candidate full suite 2807/146 passed, real-Git probe and source hashes. Read canonical CLIO helper from environment QA_CLIO_HELPER; its separately reviewed PR #5 is the deployment prerequisite. Operational envelope: four personal Macs, one existing pusher per Mac, stable private SQLite replicas, same note/exporter schedules; initially only Studio activation. No new store/timer/ledger writer. Questions: 1. Does fleet configuration enforce identity/checkout/subdir before write and prevent every scheduled/CLI/MCP producer from pushing? 2. Do exact owner staging, bounded retries/deadlines/once-before-lock stagger preserve pending/foreign data? 3. Does CLIO owner validation, cumulative export and post-pull path guard preserve imported history without echo? 4. Does upstream page/status verification correctly distinguish queued, failed, legacy and delivered output? 5. Are docs/rollback/qualification limits honest and complexity proportionate? Optional A9 unchanged-page optimization and external B4/four-Mac/seven-day qualification remain explicitly open. No pytest/executable fixtures in reviewer worktree. Provide PASS or concrete bounded findings citing file:line plus Observed input, Affected scope, Falsifier. The source-manifest pins tested code; no installed capture/private history is changed by QA. Do not count plan-driver exit4 as attestation. Approve only through native task done, not release.
Round 2: recheck round 1 dispositions in QA/gh282-implementation-fable-r1.md against current source. Overnight silence now allows 10 hours based on schedule plus DST/delivery grace; explicit queued/failure states remain immediate and explain the reason. Status write failure surfaces exit 2 (busy75), final delivery proof fails 2. CLIO failure stops before new heartbeat and this is documented. Retry docstring/import/state comment corrected. Existing CR text normalization is retained as an unobserved limitation. Latest full/focused/red/probe/static receipts and manifest are updated. Read all relevant files, not only previous snippets.
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

Scope read in full at HEAD 9719f95 (tested head df2acf8): `experimental/git-pulse/collect.sh` (773 lines),
`experimental/git-pulse/health-check.py` (328), `src/rebalance/ingest/pulse_health.py` (285),
`src/rebalance/lib/git_ops.py` (576), `scripts/pulse_sync.sh` (85), `src/rebalance/ingest/pulse.py:920-1121`,
`src/rebalance/doctor.py:1845-1945`, the 7c01d5d→HEAD diff of every source/doc file, `SOP.md:340-370`,
`SCHEDULER.md:17-23,170-182`, `scripts/health_issue_reporter.py:736-850`, and the round-1 thread
(`QA/gh282-implementation-fable-r1.md`). Not re-read this round: `sync_snapshot.py`, `index_ops.py`,
`config.py`, `daily_synthesis.py`, `hiqs_digest.py` (unchanged since round 1; hashes match the manifest),
and `pulse.py:1-919`. No pytest, validate.sh or fixture was run here; suite counts are the Producer's records.

**Round-1 dispositions against current source**

1. `[Pass]` Overnight/phase false alarm fixed. Bound is a named constant, `MAX_SCHEDULED_RENDER_AGE_HOURS = 10.0`
   (`pulse_health.py:45`), applied at `pulse_health.py:180`; fixtures at `tests/test_pulse_health.py:36-61`;
   bound stated in `SOP.md:364-367`. Pure-function probe, exit 0
   (`PYTHONPATH=src python3 -` building `CollectorHealth(fleet_mode=True, heartbeat 10m, last_pulse_exit=0, …)` → `classify()`):
   ```
   delivered 80m -> ALIVE p3 | ''
   delivered 190m -> ALIVE p3 | ''
   delivered 600m -> ALIVE p3 | ''
   delivered 601m -> ALIVE_NOT_PUBLISHING p2 | 'delivered render 10.0h old; outside scheduled freshness bound'
   legacy -> ALIVE p3 | ''
   ```
2. `[Pass]` Queued and failed now read differently. Reasons set at `pulse_health.py:183-194`; a queued local
   attempt exposes its own exit (`pulse_health.py:266-276`); carried to doctor (`doctor.py:1933-1934`) and
   health-check (`health-check.py:310-311`). Same probe:
   ```
   queued ok render, delivered 70m -> ALIVE_NOT_PUBLISHING p2 | 'queued, awaiting collector'
   delivered exit70 -> ALIVE_NOT_PUBLISHING p2 | 'render failed (exit 70)'
   local exit70 queued -> ALIVE_NOT_PUBLISHING p2 | 'render failed (exit 70); awaiting collector delivery'
   no status -> ALIVE_NOT_PUBLISHING p2 | 'delivery evidence unavailable'
   ```
   The reason strings in `read_collector_health` itself (local-status branch) have no direct fixture —
   `tests/test_pulse_health.py:64-85` exercises `classify()` only; that branch is
   `[Unverified — needs clone run]` and correct by reading.
3. `[Pass]` CLIO halt documented: "A CLIO export/validation fault deliberately stops that Mac's collector
   before a new heartbeat" (`SOP.md:368-370`); matches the code order (export `collect.sh:618-651`, heartbeat
   write `collect.sh:671`, `set -euo pipefail` `collect.sh:5`).
4. `[Pass]` CR text-mode limitation retained as declared (plan doc, "Implementation QA dispositions" item 4).
   I still have no CR-bearing page to show, so no change is requested.
5. `[Pass]` Docstring now "at most three attempts" (`git_ops.py:499`, loop `git_ops.py:540`); state comment
   lists the new state (`pulse_health.py:64`); the in-loop `import re` is gone (only `pulse_health.py:29`).
   Status-write failure no longer exits 0: `pulse.py:1094-1097` sets `deferred` for a busy lock and
   `git_error` otherwise, which `pulse_sync.sh:55-59` maps to 75 and 2.
6. `[Pass]` Final delivery proof exits 2 (`collect.sh:763-766`).

**Evidence integrity**

- `[Pass]` All 14 `source-manifest.json` hashes and the canonical CLIO helper hash recomputed here and match
  (`python3` sha256 loop: "files 14 mismatches 0", "clio True", exit 0); manifest `tested_head` is
  `df2acf87…`, the last source commit before this relay's seed.
- `[Pass]` Red control is recorded, not asserted: `schedule-red.log` ends "5 failed, 1 passed, 11 deselected"
  against the old source, including `SUBFAILED(render_age_minutes=80)` and `(…=190)`.
- `[Unverified — needs clone run]` "2807 passed, 21 skipped, 11 xfailed … 146 subtests passed"
  (`pytest.log` last line), "54 passed, 3 subtests passed" (`focused.log`) and the 43-check real-Git probe
  (`fleet-probe.log`) are the Producer's runs; I did not execute them.

**New findings (none blocking)**

1. `[Should]` A normally queued render is a doctor WARN, and the warning-level reporter can file an issue
   for it. Every render stamps a new `last_attempt_utc` (`pulse.py:1078`), so the local status differs
   from upstream after each :00 render until the collector's next push (`pulse_health.py:274`), and that
   maps to WARN (`doctor.py:1855`). `health-check-triage` runs with `--warn` at 08:25/14:25/20:25
   (`SCHEDULER.md:23`) and files or re-comments on warnings (`health_issue_reporter.py:739, 821-838`).
   The collector is `StartInterval`-phased, not clock-phased, so whether a :25 run lands inside the
   queue window is installation-dependent. The label is accurate and the operator packet states queued
   stays immediate by intent, so this is not graded a blocker; it was the "Consequence" line of round-1
   finding 2 and the text fix asked for there was delivered.
   Observed input: probe row "queued ok render, delivered 70m -> ALIVE_NOT_PUBLISHING p2 | 'queued, awaiting collector'"
   (heartbeat 10 min, local exit 0, pending, delivered render 70 min old).
   Affected scope: the device's own Mac only (other Macs read identical local/upstream status), fleet mode,
   local `last_exit == 0`, pending, local attempt younger than one collector interval plus stagger.
   Falsifier: on the Studio, `rebalance doctor` at :10 and :25 across three real Pulse cycles (already a
   listed live gate). If the `fleet:<Studio>` row is OK at those minutes, or the operator wants the WARN,
   this is void. `[Unverified — needs clone run]` — I cannot observe the Studio's collector phase here.
   Fix if it does fire (bounded, no new store/timer): either treat a pending local success younger than
   ~75 minutes as ALIVE while keeping the "queued, awaiting collector" note, or add one SOP sentence
   that this WARN is expected between a render and the next collector run.
2. `[Nit]` Reason wording is off for non-render exits and for unverifiable evidence. Probe rows:
   `git error exit2 -> … 'render failed (exit 2)'`, `config exit1 -> … 'render failed (exit 1)'`, and
   `hash mismatch after delivered exit70 -> … 'render failed (exit 70); awaiting collector delivery'`
   (the exception path sets pending at `pulse_health.py:279`, then `pulse_health.py:183-186` overwrites the
   "delivery evidence unavailable" reason). Text only; "attempt failed (exit N)" would cover all three.
3. `[Nit]` Plan status row still says "2804 tests and 143 subtests green"
   (`GH-282-PULSE-DELIVERY-PIPELINE.md:29`) while `SUMMARY.md` records 2807/146.
4. `[Nit]` Pre-existing: the `health-check.py:8-10` exit-code docstring does not mention that
   `ALIVE_NOT_PUBLISHING` also returns 1 (`health-check.py:155, 254`).

**Review questions (round 2)**

- Q1–Q3 `[Pass]` unchanged from round 1 and re-read in current source: identity/subdir/checkout refused
  before write (`git_ops.py:57-73`), fleet forces commit-only (`git_ops.py:514-515`, `pulse.py:964-965`);
  exact owner staging and foreign-dirt refusal (`collect.sh:574-609`), three attempts with 2–20 s jitter
  (`collect.sh:59-72`), 900 s deadline (`collect.sh:386`), stagger before the lock (`collect.sh:370-385`);
  CLIO owner validation, escape guard and shrink guard (`collect.sh:633-647`).
- Q4 `[Pass]` — dispositions 1 and 2 above; legacy devices unaffected (probe row "legacy -> ALIVE").
- Q5 `[Pass]` — limits stay honest: "Synthetic probe only; live fleet qualification remains pending."
  (`fleet-probe.log` last line); `provenance.jsonl` records `"live_fleet_qualification": false`.
  The one documentation gap is new finding 1.

Pre-existing defects in the touched files: new finding 4 and the retained CR limitation. I found no
other pre-existing defect in the files listed as read in full; the files listed as not re-read were
swept in round 1 only.

VERDICT: PASS
Basis: Every round-1 finding is implemented or knowingly retained and checks out against current source;  [Unverified — no citation]
the two round-1 false alarms no longer reproduce in the probe. No blocker found. New finding 1 is a
warning-noise question that only the Studio's real collector phase can settle, and the live gate that
measures it is already open in the plan.

Relay closed (Approved), no further turn needed. Carry new finding 1 into the Studio activation check.


### Attestation · relay-drive — 2026-10-02T19:53:05Z
task: REBALANCE-GH282-IMPLEMENTATION-FABLE-R2
reviewer: claude
status: Approved
reviewed-head: 9719f95e2fa389f45866b1f5e0b0024a5498a101
added-range: 7988+8573
added-sha256: 9c44086302a8306449dfd029416d78d42eaf12f56a5d40fed5068eaa3db7a129
<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

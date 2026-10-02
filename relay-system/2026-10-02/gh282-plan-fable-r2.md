# RELAY · gh282-plan-fable-r2
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
6. **Commit only the relay file** (`relay(gh282-plan-fable-r2): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Approval token rule (overrides generic handoff instructions)
On approval execute exactly `TICK_REPO_ROOT=/Users/noelsaw/task-clones/rebalanceos-gh282-fleet "/Users/noelsaw/Documents/GH Repos/XYZ-forge/bin/tick" done REBALANCE-GH282-PLAN-FABLE-R2 --agent claude` before ending. Never release an Approved task to Producer. On findings only, release is valid.

## Setup
- Artifact under review: **plan-packet.md** (embedded below — read it here).
- Reviewer: claude   ·   Producer: producer
- Started: 2026-10-02

### Artifact — plan-packet.md
```
Review PROJECT/2-WORKING/GH-282-PULSE-DELIVERY-PIPELINE.md and GH-282-RECON.md against current code. Operational envelope: four personal Macs, existing Git Pulse schedule, one pusher per Mac, independent local SQLite replicas and same Obsidian note. No new store, timer, ledger writer or central host. Read the producer/collector paths cited in recon. Questions: 1. Is the opt-in ownership/commit-only policy sufficient across all entries? 2. Are snapshot read aggregation and collector staging/retry contracts safe and proportionate? 3. Does CLIO integration preserve distinct UUID and existing schedule/path without imported-origin echo? 4. Are live qualification limits and rollback honest? Cite concrete file:line failures; no pytest or executable fixtures in reviewer worktree. Approve or provide bounded concrete findings with Observed input, Affected scope and Falsifier. Do not demand enterprise machinery or close the live pilot gates with simulated evidence.
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

### Reviewer · Round 1 (claude — Claude Fable 5.1)

Reviewed `PROJECT/2-WORKING/GH-282-PULSE-DELIVERY-PIPELINE.md` (120 lines) and `GH-282-RECON.md` (52 lines) at
worktree HEAD ec38f81 (plan amended in db9f8ad), against current source and against my five `[Should]` findings in
`relay-system/2026-10-02/gh282-plan-fable-r1.md`. Definition of Done in Setup is still an unfilled placeholder, so I
graded against the packet's four questions. No pytest, validate.sh or fixtures were run; read-only `rg` / `git grep` /
`sed` probes only.

swept file: yes
Sweep coverage: both plan docs in full; `experimental/git-pulse/collect.sh` 1-635 in full;
`src/rebalance/lib/git_ops.py` 170-501; `src/rebalance/ingest/sync_snapshot.py` 56-358; `pulse_health.py` 1-202 in
full; `pulse.py` 56-120 and 796-1031; `index_ops.py` 2066-2168; `scripts/pulse_sync.sh` 1-85 in full;
`utils/daily_synthesis.py` 440-475; `utils/hiqs_digest.py` 955-975; `doctor.py` 1850-1944;
`experimental/git-pulse/health-check.py` 128-187. Not read: the rest of `pulse.py`, `doctor.py`, `view.sh`, `install.sh`
bodies. Pre-existing defects in the swept files: none found beyond those already raised in r1 (nits 9-10), which the
plan now covers at line 120.

**Round-1 findings — disposition check**

- `[Pass]` r1-1 (commit-only success contract) closed. Plan 115: "fleet results carry `queued=True`, not
  `pushed=True`; daily synthesis, digest and sync outcome gates explicitly accept queued success. Fleet mode always
  wins over caller push=True and PULSE_PUSH". That names the gates I cited (`utils/daily_synthesis.py:465-466`,
  `utils/hiqs_digest.py:972`). The commit-only path is already safe inside the publisher: `pulse.py:868-877` returns
  "no content change" without a remote check when `push` is false, and `pulse.py:896` skips the pending-delivery
  branch.
- `[Pass]` r1-2 (identity source of truth) closed. Plan 116: "the collector config remains the device identity source
  of truth … missing, unsafe or mismatched values refuse before write … Collector fleet_sync_subdir must match Python
  sync_subdir; no hostname inference." Every mismatch I could construct from `collect.sh:280-306` fails closed
  (refuse), never writes to a wrong namespace.
- `[Pass]` r1-3 (deadline mechanism, lock placement) closed. Plan 117: "deterministic stagger runs before lock
  acquisition. Existing python3 supplies collector Git deadlines through subprocess process-group termination, no
  timeout(1) dependency." The lock exec is `collect.sh:316-334`; the reusable kill pattern is `git_ops.py:186-199`.
- `[Pass]` r1-4 (CLIO path versus `snapshots/` wildcard) closed on paper. Plan 118: "canonical CLIO owner export is
  exactly devices/<configured-CLIO-UUID>/clio.jsonl. Imported history remains solely in the private SQLite DB outside
  the Git checkout … No broad devices/ staging." No collision with existing readers: they glob `devices/*.yaml`
  non-recursively (`pulse_health.py:188`, `health-check.py:162`). The helper itself (CLIO PR #5) is
  `[Unverified — external repo, not in this worktree]`; plan step 5 keeps it a separately reviewed prerequisite.
- `[Pass]` r1-5 (not-publishing predicate) closed. Plan 119: "collector YAML carries fleet_mode=true only for opted-in
  devices. Legacy/unmarked collector devices keep existing ALIVE classification." A new state cannot read as healthy
  by accident: `doctor.py:1873` maps any unrecognised state to a warning, and the legacy collector rewrites the whole
  YAML (`collect.sh:530-549`), so rollback drops the marker on its own.
- `[Pass]` r1 nits 6-10 dispositioned at plan 120, including the rollback precondition "Rollback requires a clean
  private checkout and no unpushed fleet commits".

**Packet questions**

- `[Pass]` Q1 — policy covers every entry. Probe (rc=0):
  `rg -n 'publish_git_paths\(|_commit_and_push_if_changed\(|commit_and_push_sync\(|git_pull_rebase_safe\(' src utils scripts experimental -g '!*.md'`
  → callers are only `pulse.py:999`, `utils/daily_synthesis.py:456`, `utils/hiqs_digest.py:960`,
  `index_ops.py:2127,2138`, all through `git_ops.py:435`. `git grep -nE 'git .*(pull|push|fetch|commit|add|stash|reset)\b' -- experimental/git-pulse ':!*.md' ':!collect.sh'`
  → no match, so the collector is the only shell writer. `reconcile_pulse_mirror` (`pulse.py:74`) has no caller:
  `git grep -n reconcile_pulse_mirror -- src utils scripts experimental` → definition only. Policy at the shared
  boundary is therefore sufficient.
- `[Pass]` Q2 — snapshot and staging contracts are safe and proportionate. Sync export and commit already run inside
  the lock (`index_ops.py:2116-2144`) and the live page is written inside it (`pulse.py:821`, `:906`), so a busy-lock
  deferral leaves no dirty file for the collector to trip on. The collector refuses foreign dirt today
  (`collect.sh:501-503`) and proves upstream before the watermark (`collect.sh:625-632`); step 3 extends, not replaces.
- `[Pass]` Q3 — distinct UUID, no hostname inference: plan step 5 "Do not infer canonical capture identity from a
  hostname or echo imported origins"; recon 31-32 "CLIO owner UUID is a third, intentionally distinct identity".
  Same-note / 300-second exporter behaviour lives in the external helper: `[Unverified — external repo]`.
- `[Pass]` Q4 — limits and rollback are honest. Plan 101-103: issue stays open until "the real four-Mac rollout, at
  least three actual Pulse cycles including an offline/rejoin interval … seven-day failure-rate qualification …
  Synthetic probes do not satisfy these live gates." Plan 81: "A failed network delivery cannot instantly report its
  failure remotely".
- `[Unverified — needs clone run]` Baseline "2804 passed, 21 skipped, 11 xfailed, 143 subtests" (plan 61-62).
- `[Unverified — outside worktree]` "Installed runtime: 17e08c1, 14 commits behind" (recon 13).

**Nits — non-blocking, carry into implementation QA (step 6)**

1. `[Nit]` Plan 115-120 label the contracts "Implemented", but nothing is in code yet. Probe:
   `git grep -n 'pulse_device_id\|fleet_mode\|fleet_sync_subdir' -- src utils scripts experimental` → 2 hits, both the
   unrelated local variable at `collect.sh:149,157`. Reword to "Plan amended" so a later reader does not take it for
   shipped behaviour; implementers should treat 115-120 as binding parts of steps 1-5, since the ordered steps were
   not all updated to carry them (stagger-before-lock and the status record appear only there).
2. `[Nit]` The device-ID comparison should apply the collector's own normalisation, or require the literal to be
   canonical already. The collector lowercases and sanitises (`collect.sh:280-281`) and falls back to the hostname
   slug when `device_id` is empty without writing it back (`collect.sh:302-306`; `set_config_value` runs only in the
   migration at `:269`). A raw literal compare refuses a working Mac. Fails closed, so not a blocker; add an opt-in
   precondition "no pending device-ID migration, `device_id` present and canonical in config.sh".
3. `[Nit]` The "owned status" record in plan 119 has no path or write point. Name it (under `devices/<id>/`), commit it
   in the same locked transaction as the page, and note that exit 75 and exit 1 runs cannot record themselves
   (`pulse_sync.sh:55-56`, `:51-52`) — age of the last delivered status is the only signal for those.
4. `[Nit]` Reading "committed upstream status" needs local git, which changes the health reader's stated contract
   "Reading is pure: flat-YAML line parse, no subprocess, no git" (`pulse_health.py:14`). Say so, keep it to bounded
   local commands, and fall back to the legacy classification on git error.
5. `[Nit]` Two classifiers exist: `pulse_health.py:138` and `experimental/git-pulse/health-check.py:135`
   ("thresholds and states mirror that script exactly", `pulse_health.py:20`). State whether ALIVE_NOT_PUBLISHING
   lands in both or only the doctor path.
6. `[Nit]` State the worst-case time the collector holds the lock with three attempts at 120-second deadlines plus the
   early pull/push, so the "busy is not failure" window for Python publishers is a known number.

VERDICT: PASS
Basis: All five round-1 contract gaps are answered in the plan with text that matches the cited code, every writer
into the shared checkout goes through the one boundary the policy governs, and the live-pilot gates stay open and are
not closed by simulated evidence. The six nits are wording and small implementation notes, none backed by an observed
failing input; they belong to implementation QA, not another plan round. Two items remain unverifiable from this
worktree (the external CLIO helper and the baseline test counts) and are labelled as such.

Relay closed (Approved), no further turn needed. Producer: proceed to implementation per steps 1-7, carrying nits 1-6.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

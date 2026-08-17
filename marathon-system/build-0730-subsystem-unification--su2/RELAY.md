# Marathon Phase su2
STATUS: Open
NEXT: agy (Reviewer)

<!-- marathon-drive: task=MARATHON-SU2-TURN builder=codex reviewer=agy round-cap=7 -->

## Phase Brief

---
title: "Phase su2 Timestamp Handling Consolidation"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su2 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su2 — Timestamp Handling Consolidation (#25)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su2 in marathon harness. |

## Objective
Consolidate remaining timestamp handling through `src/rebalance/lib/time_ops.py`, eliminating alias wrappers and inline cutoff-date implementations.

## Context & Files
- Target files: `src/rebalance/lib/time_ops.py`, `src/rebalance/ingest/sleuth_reminders.py`, `src/rebalance/ingest/pulse_health.py`, `src/rebalance/ingest/claude_cloud.py`, `src/rebalance/ingest/index_ops.py`
- Issue: #25 — Four one-line alias wrappers and multiple inline cutoff calculations bypass the canonical freeze-clock seam.

## Tasks
1. Collapse alias wrappers (`_parse_datetime`, `_parse_utc`, `_parse_ts`, `_parse_status_timestamp`) onto direct `parse_utc_iso` imports.
2. Standardize cutoff-date expressions onto `time_ops.now_utc()` or a dedicated cutoff helper.
3. Switch private imports (`_parse_iso`, `_now`) to public exports in `time_ops.py`.

## Definition of Done
- `pytest tests/test_time_ops.py` green; 0 datetime alias wrappers remain in active ingest modules.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): src/rebalance/lib/time_ops.py,src/rebalance/ingest/sleuth_reminders.py,src/rebalance/ingest/pulse_health.py,src/rebalance/ingest/claude_cloud.py,src/rebalance/ingest/index_ops.py
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick claim MARATHON-SU2-TURN --agent codex --paths "marathon-system/build-0730-subsystem-unification--su2/RELAY.md,src/rebalance/lib/time_ops.py,src/rebalance/ingest/sleuth_reminders.py,src/rebalance/ingest/pulse_health.py,src/rebalance/ingest/claude_cloud.py,src/rebalance/ingest/index_ops.py"
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick ping MARATHON-SU2-TURN --agent codex
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-SU2-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/build-0730-subsystem-unification--su2/RELAY.md and src/rebalance/lib/time_ops.py,src/rebalance/ingest/sleuth_reminders.py,src/rebalance/ingest/pulse_health.py,src/rebalance/ingest/claude_cloud.py,src/rebalance/ingest/index_ops.py. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: src/rebalance/lib/time_ops.py,src/rebalance/ingest/sleuth_reminders.py,src/rebalance/ingest/pulse_health.py,src/rebalance/ingest/claude_cloud.py,src/rebalance/ingest/index_ops.py. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-SU2-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick done MARATHON-SU2-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   Edit ONLY marathon-system/build-0730-subsystem-unification--su2/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
4b. TO VERIFY A FINDING, WRITE PROBE FILES OUTSIDE THE REPO — under $TMPDIR, never inside the
   working tree. Creating even one scratch file in the repo is an off-lane write: containment
   reverts it and FAILS YOUR WHOLE TURN, discarding the review you just did (GH-441). Observed
   2026-08-08: a reviewer found a real latent crash, wrote two probe files in-tree to demonstrate
   it, and lost the turn for doing so — the finding survived only because RELAY.md happens to be
   on your allowlist. `cp` what you need to "$TMPDIR/probe.$$/" and work there instead. Verifying
   is wanted; verifying in-tree is what costs you the turn.
5. HAND OFF EXPLICITLY (GH-268): end your turn by naming who acts next — "handing off to codex —
   codex, take your turn" when requesting changes, or "relay closed, no further turn needed" when
   approving. The beta report singled this out: the Reviewer turn did not tell the user to go back to the
   Producer, so the relay looked stalled when it was simply waiting. Do this EVERY round.

### Round 1 · Builder · codex

- Replaced the four ingest-local ISO timestamp wrappers with direct `parse_utc_iso` calls.
- Made `parse_iso` / `now_iso` / `now_utc` the public implementations in `time_ops`; legacy private names remain compatibility bridges for out-of-scope callers.
- Routed local-day and cutoff computations through `time_ops.now_utc()` so they share the freeze-clock seam.
- Static checks confirm no targeted alias wrappers, private time imports, or raw clock reads remain in the four ingest files. Focused pytest invocation was attempted for the changed modules, but the local test runner terminated with exit code 134 and produced no diagnostic output.

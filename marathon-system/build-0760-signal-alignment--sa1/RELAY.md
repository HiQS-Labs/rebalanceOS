# Marathon Phase sa1
STATUS: Approved
NEXT: agy (Reviewer)

<!-- marathon-drive: task=MARATHON-SA1-TURN builder=codex reviewer=agy round-cap=7 -->

## Phase Brief

---
title: "Phase sa1 Sleuth Reminder Disappearance and Staling Sweep Validation"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Phase sa1 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase sa1 — Sleuth Reminder Disappearance & Staling Sweep Validation (#113)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase sa1 in marathon harness. |

## Objective
Verify that reminders dropped from the Sleuth publisher export flip to `is_active=0` and `state='stale'` via `src/rebalance/ingest/sleuth_reminders.py`, and add behavioral regression tests in `tests/test_sleuth_reminders.py`.

## Context & Files
- Target files: `src/rebalance/ingest/sleuth_reminders.py`, `tests/test_sleuth_reminders.py`
- Issue: #113 (Point 3) — Verify how reminders get retired from What's next once completed/removed upstream.

## Tasks
1. Verify `sleuth_reminders.py` staling logic (`active_only=False` path) correctly transitions missing reminders to `is_active=0, state='stale'` without deleting the audit history.
2. Add `test_staling_sweep_reconciles_missing_reminders` and edge-case coverage (e.g., empty payload, partial disappearance, clock drift) in `tests/test_sleuth_reminders.py`.
3. Verify test suite passes cleanly with `.venv/bin/pytest tests/test_sleuth_reminders.py -q`.

## Definition of Done
- `pytest tests/test_sleuth_reminders.py` passes with full coverage over the staling sweep reconciliation paths.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): src/rebalance/ingest/sleuth_reminders.py,tests/test_sleuth_reminders.py
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /tmp/rebalance-marathon-set-a-1787360615/.xyz/bin/tick
   - /tmp/rebalance-marathon-set-a-1787360615/.xyz/bin/tick claim MARATHON-SA1-TURN --agent codex --paths "marathon-system/build-0760-signal-alignment--sa1/RELAY.md,src/rebalance/ingest/sleuth_reminders.py,tests/test_sleuth_reminders.py"
   - /tmp/rebalance-marathon-set-a-1787360615/.xyz/bin/tick ping MARATHON-SA1-TURN --agent codex
   - /tmp/rebalance-marathon-set-a-1787360615/.xyz/bin/tick release MARATHON-SA1-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/build-0760-signal-alignment--sa1/RELAY.md and src/rebalance/ingest/sleuth_reminders.py,tests/test_sleuth_reminders.py. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: src/rebalance/ingest/sleuth_reminders.py,tests/test_sleuth_reminders.py. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /tmp/rebalance-marathon-set-a-1787360615/.xyz/bin/tick release MARATHON-SA1-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /tmp/rebalance-marathon-set-a-1787360615/.xyz/bin/tick done MARATHON-SA1-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /tmp/rebalance-marathon-set-a-1787360615/.xyz/bin/tick
   Edit ONLY marathon-system/build-0760-signal-alignment--sa1/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
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

Implemented the staling-sweep regression coverage in `src/rebalance/ingest/sleuth_reminders.py` and `tests/test_sleuth_reminders.py`.

- Added `test_staling_sweep_reconciles_missing_reminders`, asserting an empty full pull marks a missing active reminder stale while preserving its audit fields.
- Covered partial disappearance and local clock drift; sync timestamps now remain monotonic when the local clock is behind a previous run.
- Verified with `/opt/homebrew/bin/python3 -m pytest tests/test_sleuth_reminders.py -q -rA` (exit 0). The relay worktree has no `.venv/bin/pytest`.

### Round 1 · Reviewer · agy

swept file: yes

The staling sweep logic correctly sets `is_active = 0` and `state = 'stale'` for reminders that are no longer in the payload when `active_only=False`. It also handles clock drifts appropriately by ensuring `last_synced_at` doesn't regress. The regression tests are comprehensive and pass successfully.

**Verdict:** Approved

# Marathon Phase ro2
STATUS: Approved
NEXT: agy (Reviewer)

<!-- marathon-drive: task=MARATHON-RO2-TURN builder=codex reviewer=agy round-cap=7 -->

## Phase Brief

---
title: "Phase ro2 Missing slack_users Diagnostic and Lifecycle Onboarding Stage"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Phase ro2 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase ro2 — Missing slack_users Diagnostic & Lifecycle Onboarding Stage (#115)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase ro2 in marathon harness. |

## Objective
Add a doctor diagnostic check in `src/rebalance/doctor.py` that flags when `temp/slack_users.json` is absent while Sleuth activity exists in the database, and add an optional `slack_users_configured` stage to the setup lifecycle in `src/rebalance/ingest/lifecycle.py`.

## Context & Files
- Target files: `src/rebalance/doctor.py`, `src/rebalance/ingest/lifecycle.py`, `tests/test_doctor.py`, `tests/test_lifecycle_contract.py`
- Issue: #115 — Missing `temp/slack_users.json` degrades silently with no signal in doctor or onboarding.

## Tasks
1. Implement `_check_slack_users(db_path)` in `src/rebalance/doctor.py`: reports `WARN` only if Sleuth records are present in DB and `temp/slack_users.json` does not exist; returns `OK` if file exists or no Sleuth rows exist.
2. Add optional stage `slack_users_configured` in `src/rebalance/ingest/lifecycle.py` with remediation and executor hints.
3. Update `tests/test_doctor.py` and `tests/test_lifecycle_contract.py` to cover the new check and lifecycle stage.
4. Verify tests pass with `.venv/bin/pytest tests/test_doctor.py tests/test_lifecycle_contract.py -q`.

## Definition of Done
- `pytest tests/test_doctor.py tests/test_lifecycle_contract.py` passes.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): src/rebalance/doctor.py,src/rebalance/ingest/lifecycle.py,tests/test_doctor.py,tests/test_lifecycle_contract.py
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick
   - /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick claim MARATHON-RO2-TURN --agent codex --paths "marathon-system/build-0770-resolvers-and-onboarding--ro2/RELAY.md,src/rebalance/doctor.py,src/rebalance/ingest/lifecycle.py,tests/test_doctor.py,tests/test_lifecycle_contract.py"
   - /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick ping MARATHON-RO2-TURN --agent codex
   - /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick release MARATHON-RO2-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/build-0770-resolvers-and-onboarding--ro2/RELAY.md and src/rebalance/doctor.py,src/rebalance/ingest/lifecycle.py,tests/test_doctor.py,tests/test_lifecycle_contract.py. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: src/rebalance/doctor.py,src/rebalance/ingest/lifecycle.py,tests/test_doctor.py,tests/test_lifecycle_contract.py. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick release MARATHON-RO2-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick done MARATHON-RO2-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick
   Edit ONLY marathon-system/build-0770-resolvers-and-onboarding--ro2/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
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

Implemented the Slack-user readiness contract in the allowed artifacts. Doctor
now checks the canonical Slack cache path and warns only when indexed Sleuth
reminders exist without it; absent Sleuth data (including its pre-sync table)
is an OK no-op. The lifecycle has an optional `slack_users_configured` stage
that exposes cache state plus a refresh executor and remediation. Focused
tests cover the no-data/missing-cache/present-cache doctor cases and lifecycle
visibility/completion for the optional stage.

### Round 1 · Reviewer · agy

swept file: yes

The implementation correctly meets all requirements in the phase brief. `_check_slack_users` securely avoids false positives via appropriate exception handling and correctly assesses both empty state and un-synced sleuth tables. The setup stage accurately checks `get_slack_users_path` as optional, integrated safely within the lifecycle map.
All local checks pass (pytest, ruff, mypy) and there are no pre-existing defects or regressions in the existing files.

**Verdict:** Approved

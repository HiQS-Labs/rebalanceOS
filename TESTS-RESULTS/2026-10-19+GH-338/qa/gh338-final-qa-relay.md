# RELAY · rebalanceOS GH-338 final QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-19.
-->

NEXT: Reviewer
STATUS: Open
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
6. **Commit only the relay file** (`relay(rebalanceos-gh-338-final-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh338-final-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh338-final-brief.md
```
# Final QA (Codex): RebalanceOS GH-338, a long-silent Mac is a FAIL on every other Mac

Review the implementation against the approved plan, `PROJECT/1-INBOX/GH-338-DOCTOR-PULSE-DELIVERY-ROWS.md` (plan QA approved at 28bfb7a; the plan has since been amended with a scope correction). Your worktree is the task branch head. The diff against `origin/development`:
- `src/rebalance/doctor.py`: `_FOREIGN_SILENCE_HOURS`, and the rule in `_check_pulse_collectors` (long_silent, escalate, acknowledgement through the local `_matches_notice` import, FAIL status through the single constructor, shlex-quoted hint)
- `tests/test_doctor_device_scope.py`: 5 new tests
- the plan, ROADMAP, and `TESTS-RESULTS/2026-10-19+GH-338/` (SUMMARY, smoke.log, smoke-probe.py.txt, provenance.jsonl, plan-QA relay)

Operational envelope: a single operator's 4-Mac fleet. Operator decisions are fixed:
- the level is FAIL (auto-filed)
- the bound is 72 h
- the render-stall case is follow-up #340 and out of scope here

Do not ask for reporter, classifier or config changes, or for new scripts.

Questions:
1. **Does the code match the approved plan and its behavior table exactly?** Cover all of these: scoped ≤72h, scoped >72h, scoped >72h acknowledged, unscoped ALERT ≤72h, unscoped >72h, own device, foreign NO PUSHES. Name any branch where the code diverges.
2. **Correctness details.**
   - The strict `>` boundary.
   - The `escalate` path when the classifier state is DEGRADED, not ALERT.
   - The local import and config read never crashing doctor.
   - The notice patterns read once per call.
   - The hint quoting.
   - The `detail` suffix wording.
3. **Pins and tests.**
   - Does `tests/test_doctor_exit_pins.py` still enumerate exactly `{_check_pulse_collectors}` as the dynamic site, with an unchanged literal counter?
   - Do the 5 new tests fail on base, as the red control claims?
   - Is there any weak or vacuous assertion?
4. **Evidence.** Do `smoke.log` and `SUMMARY.md` support each claim?
   - The main path plans 1 filing with no mutating request.
   - The real fleet shows no false alarm.
   - The acknowledged row becomes a notice.
   - The base red control shows "not applicable".
   - Full suite: 2798 passed.
   - Is the scope correction (#340) and the "MacBook Pro" notice note accurate?
5. **Anything over- or under-built** for a one-rule change?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines.
```
- Definition of Done: the implementation matches the approved plan, its tests pin the behavior, and the evidence supports the claims; no Blocker or Should.

Reviewer block: plain lines; `VERDICT: PASS` or `VERDICT: FAIL` and `Basis:` each at the start of a line, with no bold. On PASS set `STATUS: Approved`.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

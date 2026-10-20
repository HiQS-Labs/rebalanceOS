# RELAY · rebalanceOS GH-338 plan QA (codex)
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
6. **Commit only the relay file** (`relay(rebalanceos-gh-338-plan-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh338-plan-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh338-plan-brief.md
```
# Plan QA (Codex): RebalanceOS GH-338, a long-silent Mac becomes an error on every other Mac

Review the plan `PROJECT/1-INBOX/GH-338-DOCTOR-PULSE-DELIVERY-ROWS.md` before implementation. Your worktree is HiQS-Labs/rebalanceOS on `feat/rebalanceOS-gh338-doctor-pulse-delivery-rows-2026-10-19` (the intake commit on top of development 3b31a67).

Read in full:
- the plan
- `src/rebalance/doctor.py`: `_DeviceScope`/`_DEVICE_SCOPE_REGISTRY` (~:83-112), `_other_device_check` (~:127), `_PULSE_STATE_TO_CHECK` and `_map_pulse_state` (~:1858-1882), `_check_pulse_collectors` (~:1885-1980)
- `src/rebalance/ingest/pulse_health.py` (`classify`, `read_collector_health`)
- `src/rebalance/health.py` (`_matches_notice` ~:137, `compute_health_status` ~:213)
- `scripts/health_issue_reporter.py` (filing threshold ~:739, dedup by row name)
- `tests/test_doctor_device_scope.py`, `tests/test_doctor_exit_pins.py`, `tests/test_doctor_pulse_severity.py`
- issue https://github.com/HiQS-Labs/rebalanceOS/issues/338, including the re-scope comment

Operational envelope:
- RebalanceOS is a single operator's 4-Mac fleet.
- The change is one rule in one doctor function, plus tests in an existing test file.
- Do not ask for new scripts (GH-241), new config keys, reporter changes or classifier changes.
- The operator decisions are fixed: the level is error (auto-filed), and the bound is 72h.

Questions:
1. **Grounding.** Are the recon claims true at the cited lines?
   - a scoped foreign device always shows "not applicable"
   - an unscoped foreign ALERT is capped at WARNING
   - the reporter files only on error
   - health notices demote only warnings
   - stuck delivery is already covered by ALIVE_NOT_PUBLISHING, which justifies dropping the second proposed row
2. **Correctness of the rule.** Walk the behavior table against the actual code. Does the plan's order of operations (long_silent → bypass the short-circuit → bypass the Phase F cap unless acknowledged) produce exactly that table?
   - Check edge cases: the intermittent-window override (`scope.stale_after_hours`), DEGRADED foreign devices, ALIVE_NOT_PUBLISHING with an old scan, NO PUSHES, and the own device.
3. **Acknowledgement.** Is reusing `get_health_notice_patterns()` and `_matches_notice` at row construction sound? It keeps the foreign row at WARNING so the reconciler demotes it to a notice. Does it import cleanly from `doctor.py` with no cycle? Is there a simpler existing hook?
4. **Pins and blast radius.** Will reusing the single `Check(...)` constructor keep `test_doctor_exit_pins.py` green as written? Who else consumes `fleet:` row severity or doctor's exit code that the plan has not named (dashboard, pulse_web, experimental/git-pulse/health-check.py)?
5. **Verification.** Do the planned tests and smoke (main path, notice-acknowledged adjacent path, and a red control on base) prove the change and detect the old behavior? Is the reporter `--dry-run` usable as described?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines.
```
- Definition of Done: the plan is grounded, produces exactly its behavior table, and is sufficient and minimal for #338 under the operator's decisions; no Blocker or Should.

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

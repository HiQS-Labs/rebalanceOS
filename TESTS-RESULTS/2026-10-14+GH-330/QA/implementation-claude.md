# RELAY · GH330 implementation QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-14.
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
6. **Commit only the relay file** (`relay(gh330-implementation-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: PROJECT/2-WORKING/GH-330-FLEET-SAFETY-FOLLOWUP.md, src/rebalance/cli/config_cmds.py, src/rebalance/ingest/config.py, src/rebalance/ingest/pulse.py, src/rebalance/lib/git_ops.py, src/rebalance/lib/time_ops.py, scripts/setup_sleuth_file_source.sh, tests/test_fleet_enroll.py, tests/test_pulse_reconcile.py, tests/test_config_read_shape_guard.py, tests/test_daily_loop_inputs.py, SOP.md, SLEUTH_SYNC.md, UPGRADE.md, vscode-extensions/pulse-tree-view, TESTS-RESULTS/2026-10-14+GH-330, TESTS-RESULTS/2026-10-14+GH-325
- Reviewer: claude   ·   Producer: codex-supervisor
- Started: 2026-10-14
- Definition of Done: Issue330 acceptance implemented on merged development1a496fa; no duplicate writer/framework. Local operator CLI; assess preservation, safety, recovery context and existing locked refresh within stated envelope. Full gates will run after approval and are not yet claimed. No live deployment, concurrency transaction/ACL/power-loss promises.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Questions
1. Do strict opt-in reads and canonical setter validation preserve broken existing bytes and reject typo timezones before writes while retaining ordinary getter/bootstrap semantics?
2. Does the existing collector writer publish completed independent first backups without clobber, preserve source modes and clean staging on ordinary failure? Are limits honestly documented?
3. Are partial apply/postcondition failures clear, nonzero and actionable without unsafe automatic rollback?
4. Does the thin refresh facade call the existing shared lock/mirror owner, and setup stop before set-sleuth for contention/dirty/pull failure without autostash?
5. Does reader migration precede retirement, without changing parser behavior? Is existing fixture-only shell wrapper correct for paths with spaces?
6. Are current version0.101.1, rating88/88/50/65 and focused/red controls grounded; is any requirement missing, unrelated scope or duplicate utility/writer added? Read changed functions and their relevant file context; cite exact findings.

On PASS: STATUS Approved, NEXT Producer. Keep reviewer tick claim, DO NOT release it; run exact environment-pinned native tick done supplied by harness. Only relay thread writes. Do not run tests in relay worktree. Existing full suite, doctor and static routes follow separately; approval assesses implementation and focused evidence, not pending full qualification.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

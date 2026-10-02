# RELAY · gh282-implementation-fable-r2
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-02.
-->

NEXT: Reviewer
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

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

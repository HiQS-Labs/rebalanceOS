# RELAY · gh305-studio-fable-r1
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
6. **Commit only the relay file** (`relay(gh305-studio-fable-r1): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Approval token rule
On approval call task done with the exact absolute env-pinned tick command from your native turn prompt. Do not release an Approved task to Producer. Findings may release.

## Setup
- Artifact under review: **review-packet.md** (embedded below — read it here).
- Reviewer: claude   ·   Producer: producer
- Started: 2026-10-02

### Artifact — review-packet.md
```
Review the focused Studio follow-through for Rebalance #282 and cross-repo Forge #937, pointer #305. Source6aa883e plus evidence-only updates. Code changes limited to clio.py, semantic_index.py maintenance facade, daily_work_synthesis.py and0.97.2version. Existing Studio consumer config already points to canonical full-history compatibility export (3976source rows,3knownorigins), so no new reader/store/transport. Live consumer refresh/deployment not yet performed. Guard prevents recent scheduled derived jobs (exit75); no guard/plist/schedule changes permitted or claimed. OtherMacs stayoff.
Read complete touched functions/directcallers and TESTS-RESULTS/2026-10-02+GH-305/PROTOCOL.md, controls-base.log, controls-green.log, qualification-controls.py. Seven synthetic checks fail base535bb7a and passcandidate: LFUnicode framing, stableDailycanonical IDs, provenanceidempotence, multioriginunion withoutconsumerkeychange, samepasscollision/reorderedreplay/cachedrefs, nonemptyselectedCLIOmaintenanceprojection,3Unicodeseparators. Existing41focusedtests pass in separatefullclone, typecheck/staticresults willbeadded whenavailable. Canonical references are additive JSON onexistingclio_prompts; primary IDs andsemantic keysunchanged. IncludesDBfallbacksource_records tokeepcanonicalrefs visible; metadata-freelegacyDailyrecords use stablehash insteadposition. Maintenancefacadeuse_registry_providers=True respectsselectedsources anddoesnotembed. NoCloudsynthesis/liveprompt injection/newtestsuitegate. Reviewmigrationandprojectionunion, timestamp/legacycompatibility, fallbackcites, scopedbackfill, correctprivacy/docs/verificationclaims; sourceDDLadditive only. Do not run mutation-heavy suites inreviewworktree. Provide bounded observedfindings with input/scope/falsifier; do not expand into transportarchitecture or memorypolicy review. Ifsound, approveusingnative taskdone; earliertranscriptsarenotQAapprovalforthispatch.
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

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

# RELAY · GH199 CLIO first-prompt plan review
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-08.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 3 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **Verdict**
     (Approved | Changes requested | Blocked). **Review the whole file, not just the diff** (GH-268):
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
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh199-clio-first-prompt-plan-review): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md`, `utils/CLIO/clio-codex-tail.sh`, `test/clio-codex-tail.sh`, and the shared writer in `utils/CLIO/INSTALL.md`
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-09-08
- Definition of Done: Review the plan before implementation. Read the full named source files. Answer with file:line evidence:
  1. Does the persisted capture-start boundary solve completed prompts arriving before first discovery without historical import, including absent sessions, migration, downtime and partial lines?
  2. Does the proposed first-metadata child exclusion avoid retimestamped inherited prompts while preserving root/resume behavior? Any overlooked metadata boundary?
  3. Are existing writer acceptance, cursor retries and dedup contracts preserved by the minimal in-place change?
  4. Are the synthetic regressions falsifiable/nonempty with matching negative controls, and are rating/recurrence claims honest?
  Scope is this producer defect. Do not expand into unrelated exporter or collector work. Do not run installed hooks or edit code. Only the relay thread may be written. No deployment/backfill is authorized. A passing final review will need deterministic results; this is plan review only.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer — codex — Round 1

Verdict: Changes requested
swept file: yes

Read all four Setup artifacts in full, plus the referenced rollout fixture. Static plan review only: no source/artifact execution, installed-hook access, tests, or git commands. Graph tools were unavailable; direct source reads supplied the evidence. Live hashes, private incident observations, and graph freshness reported by the plan were not independently verified.

- **[Blocker] R1 — The no-history boundary disappears on known-file rescans.** `PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:86` limits filtering to unseen files and leaves known-file behavior intact. But `utils/CLIO/clio-codex-tail.sh:176` resets a replaced/truncated known file to byte zero. A root containing old prompt A and eligible prompt B would initially log only B; replacing it with the same bytes would then import A, whose ID was never written. The existing rotation test starts with explicit backfill (`test/clio-codex-tail.sh:69`, `test/clio-codex-tail.sh:111`), so it cannot detect this leak. **Fix:** specify how boundary eligibility survives rotation/truncation and empty-file first discovery, while preserving delivery of pending legacy-cursor chunks during migration. Add a default-mode mixed old/new fixture, replace/truncate it, and assert the exact eligible ID set stays unchanged; retain a separate legacy pending-row retry control. Do not apply a blanket cutoff to legacy pending rows without resolving that contract.
- **[Should] R2 — Define comparison precision and validation before normalization.** The plan promises no historical import and rejection of invalid timestamps (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:86`), but the current normalizer truncates any sufficiently long `Z` string without parsing it (`utils/CLIO/clio-codex-tail.sh:96`); the writer checks timestamp length, not date validity (`utils/CLIO/INSTALL.md:119`). This is a pre-existing defect material to the new cutoff. Comparing second-normalized values either admits a pre-start event in the same second or loses a post-start event, depending on the comparator. **Fix:** specify a persisted timezone-aware UTC instant, compare validated raw event instants at full available precision with an explicit equality rule, then retain existing second-precision output/IDs. Specify missing, malformed, and timezone-less input behavior. Add fixed before/equal/after-boundary cases within one second, offset-equivalent timestamps, and invalid-date controls; use distinct session IDs where needed so dedup cannot mask cutoff errors.
- **[Should] R3 — Pin child identity and a nonempty root/resume counter-control.** Immutable first-metadata classification is the right direction (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:91`), but the current cached-context fast path seeks past it (`utils/CLIO/clio-codex-tail.sh:107`), and later metadata changes session/cwd (`utils/CLIO/clio-codex-tail.sh:132`). Step 5 names second-tick child tests but does not explicitly require a root/resume assertion; the supplied fixture has only one root metadata record (`test/fixtures/clio/codex-rollout.jsonl:1`). **Fix:** name the exact child-marker predicate and treatment of absent/incomplete first metadata; require first-file identity to be re-read or retained independently of mutable context on subsequent ticks, including legacy cursors. Add sanitized child→parent metadata replay and a genuine root resume with multiple metadata records; assert exact nonempty root rows/session/cwd on both ticks while child rows remain absent. Require a reject-all mutation to fail the root control and a nearest-context-only mutation to fail the child control, with raw evidence in the named campaign.
- **[Should] R4 — Bound the downtime claim by the existing tailer-lock failure mode.** A persisted epoch survives an ordinary polling gap, but `utils/CLIO/clio-codex-tail.sh:46` silently returns whenever the lock directory exists; its `born` timestamp is never read, and the EXIT trap cannot clean up after SIGKILL. This pre-existing same-file defect can stop all later capture, regardless of the boundary; the overlap test only removes the lock normally (`test/clio-codex-tail.sh:119`). **Fix:** explicitly distinguish clean downtime/delayed discovery from abandoned-lock recovery in the plan's guarantee and acceptance cases. Record the existing limitation and an operator recovery prerequisite; do not claim crash recovery from the current overlap test or expand this repair into a replacement supervisor.
- **[Pass] Existing acceptance and dedup contracts are identified for preservation, not redefined.** The plan retains writer/IDs/consumers and timestamp dedup policy (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:110`, `PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:116`). Writer exit 0 includes deliberate drops (`utils/CLIO/INSTALL.md:47`); tailer nonzero handling prevents cursor advancement (`utils/CLIO/clio-codex-tail.sh:234`, `utils/CLIO/clio-codex-tail.sh:247`), and writer ID collision suppression occurs under its append lock (`utils/CLIO/INSTALL.md:168`, `utils/CLIO/INSTALL.md:175`). Retain these exact contracts and their existing retry checks when resolving R1.
- **[Pass] The main regression is nonempty and has a specified red baseline; recurrence language is appropriately limited.** Step 1 requires one exact JSONL row and retained baseline failure (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:79`), and step 5 requires mutated exclusion controls (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:98`). The assessment labels one observed incident, distinguishes other issues, and says “Trend remains unknown” (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:68`). These are plan commitments and qualified author-reported observations, not executed results or independently reproduced ratings.

Whole-file sweep found the relevant pre-existing rescan, timestamp-validation, and abandoned-lock weaknesses above; implementation correctness remains untested at this plan-review stage. No deployment or historical backfill is approved.

Handing off to Producer (claude-a) — address R1–R4 in the plan, log each disposition, then return for Round 2 review.

### Producer — claude-a — Round 2

R1–R4 accepted; the plan now pins per-file cutoff persistence, legacy pending eligibility,
full-precision validated comparisons, immutable child identity and nonempty root controls.
Abandoned locks are explicitly excluded from the clean-downtime claim. See the revised
steps and review-disposition section. Baseline reproduction retained in TESTS-RESULTS.
The prior driver exit 6 is not treated as approval; parent evidence is now committed.
Please re-review the plan only. No code has changed.

### Reviewer — codex — Round 2

Verdict: Changes requested
swept file: yes

Read all four Setup artifacts in full and the referenced rollout fixture; reviewed the retained baseline JSON and tailer log. Static plan review only: no artifact/source execution, tests, installed hooks, or git commands. Graph tools were unavailable; direct source reads supplied evidence. Applied SWE and debug-mantra plan-review criteria. Private incident observations, installed hashes, graph freshness, and live issue/rating state remain author-reported, not independently verified.

- **[Blocker] R1 remains partly open — zero-cutoff legacy rows cannot uphold the migration no-history promise on rescan.** The plan promises legacy pending delivery “without replaying previously skipped history” (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:85`), but assigns legacy rows cutoff zero and retains their policy (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:89`). The current reset reads from zero after inode/size changes (`utils/CLIO/clio-codex-tail.sh:176`); old default discovery skipped historical rows without writing their IDs (`utils/CLIO/clio-codex-tail.sh:188`). Concrete counterexample: legacy cursor is after skipped old A with pending old B; upgrade delivers B; replacement with A+B then imports A under cutoff zero. The new mixed-history rotation control covers default-mode files, while the legacy control only specifies pending retry (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:108`). **Fix:** distinguish legacy pending-byte eligibility on the original file from reset eligibility. Preserve the old pending chunk through retries, but explicitly choose a conservative reset policy that does not import skipped history when provenance is lost; document any resulting limitation. Add this combined legacy-upgrade → retry B → replace/truncate A+B case with exact nonempty IDs and a zero-cutoff-reset negative control. Do not describe unrestricted legacy rescans as no-history migration.
- **[Should] R5 — Specify the timestamp rule for a partial record completed at a nonzero offset.** The cutoff is required “whenever reading from byte zero,” while incremental reads retain existing partial-line semantics (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:90`). The extractor advances past complete metadata and leaves the trailing partial pending (`utils/CLIO/clio-codex-tail.sh:113`, `utils/CLIO/clio-codex-tail.sh:247`), so an old partial prompt can become a nonzero-offset read next tick and bypass that rule. The existing first-partial test deliberately expects such an old timestamp to be delivered (`test/clio-codex-tail.sh:54`, `test/clio-codex-tail.sh:60`). **Fix:** pin the intended exception or invariant explicitly. For timestamp-based eligibility on new default-mode files, apply their persisted cutoff on every extraction, preserving newline/cursor retry mechanics and the separately defined legacy/backfill policy; update the old fixture accordingly. If pre-start partial completion is deliberately eligible, state that exception to timestamp/no-history claims. Require paired pre-start and post-start partials after complete metadata, completed on tick two, with exact nonempty eligible IDs and a matching bypass-cutoff control. This resolves an acceptance-contract ambiguity before implementation, not a request to discard legacy pending rows.
- **[Pass] R2 is resolved at plan level.** Full-precision validated timezone-aware comparison, inclusive equality, UTC-second output, malformed/missing/naive rejection, and distinct-session boundary controls are explicit (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:94`). This addresses the material pre-existing normalization shortcut (`utils/CLIO/clio-codex-tail.sh:96`) without changing the shared writer's ID format (`utils/CLIO/INSTALL.md:53`). Implementation and red controls remain pending.
- **[Pass] R3 and R4 are resolved at plan level.** The first-metadata predicate, independent per-extraction provenance check including legacy cached reads, defer-on-incomplete rule, and nonempty two-tick root/resume counter-controls are explicit (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:98`). Clean downtime is distinguished from abandoned-lock recovery, with an operator prerequisite (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:137`); that matches the existing lock-directory early return (`utils/CLIO/clio-codex-tail.sh:46`).
- **[Pass] Writer acceptance and dedup remain preservation requirements.** The plan retains writer/IDs/consumers (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:123`) and append-lock retry coverage (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:110`). Exit 0 includes deliberate drops (`utils/CLIO/INSTALL.md:47`), nonzero writer results leave the cursor pending (`utils/CLIO/clio-codex-tail.sh:234`, `utils/CLIO/clio-codex-tail.sh:247`), and ID suppression runs under the append lock (`utils/CLIO/INSTALL.md:168`, `utils/CLIO/INSTALL.md:175`). Resolve R1/R5 within those contracts.
- **[Pass] Recurrence claims remain appropriately qualified; test commitments are falsifiable.** The assessment says “One observed first-prompt incident” and “Trend remains unknown” (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:70`, `PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:73`). Exact positive rows and baseline/mutated failures are required (`PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:79`, `PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md:111`). The retained baseline JSON reports `"expected_rows": 1`, `"actual_rows": 0`, and `"nonempty_source_bytes": 430` (`TESTS-RESULTS/2026-09-08+GH-199/baseline-first-prompt.json`); this is inspected producer output, not an independently rerun reproduction. Final QA still needs the promised deterministic evidence, including the new paired controls above.

Whole-file sweep revisited the pre-existing rescan, timestamp-validation, and abandoned-lock weaknesses from Round 1; no additional pre-existing defect material to this producer repair was identified. Approval here would approve a plan only; no implementation correctness, deployment, or historical backfill is approved.

Handing off to Producer (claude-a) — resolve R1 and R5, log both dispositions, and return for Round 3 review.

### Producer — claude-a — Round 3

R1 and R5 accepted. Legacy eligibility now uses a distinct sentinel and is replaced
by the global cutoff on rotation/truncation; numeric cutoffs apply on every extraction,
including partials. Combined legacy-rescan and paired-partial controls are explicit.
Please review the revised plan. This is the final plan review round.

IMPORTANT OUTPUT CONTRACT: append a complete reviewer block beginning with
`### Reviewer — codex — Round 3`, then a literal uppercase `VERDICT: PASS` for
approval or `VERDICT: FAIL` for changes requested, plus `swept file: yes`.
Set top-level STATUS: Approved and NEXT: none only if approving. Otherwise keep
STATUS: Open and NEXT: Producer. Preserve all earlier turns. Do not edit code.
The previous driver exit 8 came from malformed verdict syntax, not successful QA.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

---
gh_issue: 330
source: https://github.com/HiQS-Labs/rebalanceOS/issues/330
title: Fleet safety follow-up
status: Completed
created: 2026-10-14
updated: 2026-10-15
owner: noel
doc_type: bugfix
goal: Preserve operator configuration and backup integrity during enrollment and stop unlocked setup refresh.
effort: 2
complexity: 2
risk: 2
phases: 1
---

# GH-330 — Fleet safety follow-up

## Table of contents
- [Status](#status)
- [Phase 0 - Prior Art Review](#phase-0---prior-art-review)
- [Plan and acceptance](#plan-and-acceptance)
- [Verification and handoff](#verification-and-handoff)

## Status

| What was just completed | What's next |
|---|---|
| PR331 merged as80ce446; issue330 closed; bot comments and dated test fixture corrected; latest CI green | Deployment remains separate; retain pending rollout work under GH-282/GH-328; safe clone retirement |

Tracking [#330](https://github.com/HiQS-Labs/rebalanceOS/issues/330), follow-up to merged [#326](https://github.com/HiQS-Labs/rebalanceOS/pull/326). Related #328's remaining rollout/hash-check gaps stay separate.
Base development1a496fac55e5d56eaebf6aaf3c444d9c5017e65d. Clone rebalanceOS-gh330-fleet-safety-followup-2026-10-14; branch fix/rebalanceOS-gh330-fleet-safety-followup-2026-10-14. Primary preserved; no deploy or live configuration/database operations.

## Phase 0 - Prior Art Review

The [bounded recon](recon-gh325-review-followup.md) and [scratch evidence](../../TESTS-RESULTS/2026-10-14+GH-325/SUMMARY.md) already reproduce malformed-config overwrite, invalid timezone admission, widened0600 permissions, partial first backup, opaque partial apply and setup continuing after failed unlocked pull. Tests seeded into baseline8ff740b produced25 intended failures. Candidate focused suites passed67+40 cases. Claude plan approved round2 with driver0 at a02fb489; historical receipt is in the retained campaign. These safety changes at a696887 remained unpublished when another session merged326. The relevant runtime modules are identical between old baseline8ff740b and current development1a496fa; port only this delta, preserving all unrelated merged work and regenerating ledger through its existing writer.

Graph project rebalanceOS is stale (generation2026-09-02); material symbols and callers were checked then source-read, excluded scripts/docs read directly. No exhaustive graph claim. New issue328 remaining scope6/7/8/10 does not cover these fixes. Merge-batch issue327 records two existing Daily fixture failures on paths containing spaces. Correct only that existing fixture if reproduced; scanner behavior stays unchanged. No performance claim or benchmark. Phase0 findings support extending existing owners, not a replacement system.

### Outcome, bet, alternatives and rollback
Preserve original operator bytes and private mode; ensure usable first backups and honest failures. Extend the existing strict-admission boundary, collector editor, shared timezone resolver and locked mirror helper. Docs-only warnings still permit data loss; making every reader strict breaks intentional fallback; automatic two-file rollback could restore stale state. Use strict opt-in and actionable partial-state reporting instead. Revert code without automatic configuration rollback; inspect existing backups manually. No atomic two-file/concurrent-writer transaction, ACL/ownership guarantee, directory-power-loss claim, new config store, suite, gate, launchd job or3-Eyes work.

### Rating
rated88/88/50/65, no operator override. Reproduced loss of original configuration and exposure of private mode justify high severity/priority; appeal neutral; bounded existing helpers justify cheapness65. Compared windows2026-09-30..10-14 and09-16..09-30: linked same-class PR304/config errors and268/publication safety establish prior work, but distinct incident counts/trend unknown; scratch failures are not fleet incidents. The supported Releases CLI has roadmap sync/list only, so ROADMAP's owned row supplies the rating and the canonical writer mirrors it to DB/dump. No schema change/raw SQL write.

## Plan and acceptance

1. Port existing _read_config/get_pulse_config strict=False; strict reads reject existing malformed/nonobject/unreadable bytes while missing config permits bootstrap. Fleet preview/apply/discovery and canonical set_pulse_config reread strictly; ordinary tolerant readers preserved. Public invalid discovery exits2; apply nonzero and original bytes preserved.
2. Promote existing timezone resolver into lib/time_ops with pulse compatibility alias. Validate supplied nonempty timezone before writes. Bad set-pulse input refuses unchanged bytes; valid/default semantics remain.
3. Harden existing set_collector_values with unique sibling staged independent backup and replacement, original mode, flush/fsync before publication, no-clobber first-backup hardlink of staged copy, cleanup. Never hardlink live inode. Existing backup unchanged; failures leave original/complete backup, no partial published file. Extend existing writer tests only.
4. Catch expected IO/config failures and missing postcondition explicitly in fleet apply; report incomplete state and recovery context, nonzero; no automatic rollback. Inject second-write failure and absent postcondition in existing cases.
5. Add thin config refresh-pulse-clone --path facade over existing reconcile_pulse_mirror. Setup reuses it and stops before set-sleuth on failure; no direct pull/autostash. Existing real throwaway-Git tests prove shared lock, dirty preservation, no stash and successful refresh. Shadow setup42 must stop42 without setter.
6. Require explicit reader/sidebar migration and verification before legacy root-page deletion. Correct Sleuth fetch/blob docs and extension setting descriptions without parser changes. Bump current patch0.101.1 across metadata and use path-free changelog prose. Preserve merged0.100/0.99 release history. No rollout/retirement performed.
7. If existing Daily fixtures fail because shebang contains spaces, use quoted shell exec to invoke its separate Python fixture; no runtime scanner change/new suite. Run focused existing cases then Claude final implementation QA. Once approved, run root and HiQS separately with declared extras, current static/pre-push ratchets and scratch doctor. Keep known skips/xfails/backlog honest; publish sanitized evidence.

## Verification and handoff

No new tests suites/frameworks/CI lanes. Existing test_config_read_shape_guard, test_fleet_enroll, test_pulse_reconcile plus time/publication cases cover failures; full tests/ and HiQS/tests in separate processes include CI-skipped embedding tests. Existing pre-push hook installed (.githooks), no bypass. Doctor fixture checks fleet row only; intentionally missing DB/auth remain and do not qualify deployed health. Preserve baseline failures and approved review receipts; final full suite on approved implementation once, rerun only for concrete failures/new changes. Issue/doc/ledger remain awaiting merge at PR readiness. Retain task clone for /merge-cleanup after origin landing. No old clone disposal until unique work/evidence is safely preserved on origin.

Current-base plan confirmation: [Claude review](../../TESTS-RESULTS/2026-10-14+GH-330/QA/plan-claude.md), Approved round1 driver0. New graph fixture lookup returned no nodes; coverage freshness missing, exact source read fallback. Fixture baseline reproduced2 failures/3pass, so the bounded shell wrapper correction is justified. ROADMAP title carries GH-330 for the existing ledger parser; its issue_url column is XYZ-forge-only legacy behavior and is not changed here. Raw text and canonical plan retain the full tracking URL.

## Final handoff (2026-10-14)

[Current qualification](../../TESTS-RESULTS/2026-10-14+GH-330/SUMMARY.md) retains exact commands, sanitized receipts, full-suite outputs and known limits. Native Claude plan reviewed4c7bc5c; implementation reviewed5e5db53; supplemental guides reviewed5fc59de. All accepted driver exits0; rejected guide close remains explicit and consumed one round (implementation total3). Code and guides are unchanged from the full qualification revisione2e72e8. Existing skips/xfails and PDDA backlog remain; no deployed/four-Mac qualification. No live config/CLIO database/history changes. Source/installed version0.101.1 verified. Required push gate and hosted CI are inspected on the published PR head; issue330 tracks that PR. Preserve this task clone and prior unique evidence until origin landing is verified; /merge-cleanup owns retirement. No merging/deployment performed.

## Landed and reconciled (2026-10-15)

[PR331](https://github.com/HiQS-Labs/rebalanceOS/pull/331) merged as80ce446ce57cb5e5f2f7f2716af7ea05c790ac66, head812a153. Issue330 closed as completed. Both minor CodeRabbit comments were fixed in00474b7. Hosted CI then exposed a dated existing close-loop CLI fixture after its15-day window expired; a two-line test-only clock pin restored7/7cases and passed independent native Claude review. [Final CI](https://github.com/HiQS-Labs/rebalanceOS/actions/runs/38829778912) passed all10jobs. No product change after original implementation QA. Supplemental receipts retained in the existing campaign.

Merge-cleanup's dry run selected the older native CLI and refused its missing roadmap reconcile-state verb (#329). The already vendored reader ran that required read-only gate successfully against the disposable landing candidate; native check and three-way semantic check passed, and roadmap sync was a no-op. No schema/install change, suppressed error or skipped gate. The policy-selected merge helper landed the PR; this repo's existing roadmap sync/gen/check writer and PDDA checks own post-merge reconciliation. The root's previously generated view still carried generation69; regenerate it through the canonical CLI, not by hand.

## Lessons Learned (For Future Agents)

- Pin a CLI fixture's imported clock seam to its declared fixture time. Fixed timestamps plus a real wall clock create an expiry date for CI; do not change production windows or weaken assertions.
- Audit receipts must name the committed result files, even when execution originally wrote temporary filenames.
- Preserve historical QA snapshots, document small later corrections honestly, and distinguish a native CLI exit0 from nonessential session-end hook status.
- Use available read-only capabilities and the repository-owned writer separately while the tracked Forge installation gap329 remains; never migrate the ledger merely to land a scoped fix. A merge is not a runtime deployment.

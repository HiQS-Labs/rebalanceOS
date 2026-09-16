# GH-232 batch 1 — reference safeguards rejected

## Decision

The four-step batch ended through its failure-report branch. Two bounded guard attempts improved
some reference extraction, but the second still lost a valid PR and failed a synthetic control.
**Do not advance automatic linking or outcome reconstruction.** The attempted code is preserved in
`rejected-candidate.patch`; runtime parser and runtime tests were restored byte-for-byte to the
pre-batch `5f70294` state. That baseline still has the previously documented limitations.
No third repair pass, new source capture, index refresh, model synthesis, merge or deployment.

## Protocol and review

[Frozen protocol](../../PROJECT/2-WORKING/GH-232-CLIO-JOURNEY-FOLLOWUP.md): baseline parser f8a2078,
same retained capture, cutoff 2026-09-16T04:25:38Z; negative and positive controls, review every
changed reference including the prior 24 cases, cap two repair passes and two hours. A reference
gate failure sends step four to a failure report, not forced journey reconstruction.

Agy timed out without feedback (exit 7). The [Codex fallback](../../relay-system/2026-09-16/gh232-protocol-codex.md)
returned FAIL: unresolved additions must also block progression. That condition was incorporated
before replay. The fallback driver exited 6 on generated gate-evidence containment while a harness
validation was still running; it is **not** an approved relay. Only public-safe protocol/source
material was sent for review, not the private capture. The current implementation is not QA-approved.

## Experiment ledger

| Attempt | Evidence | Result |
|---|---|---|
| Add synthetic foreign-project, ordinal, chat-ID and formatted-PR cases | red-console.txt | 12 failed, 43 passed before guard |
| First guard | green-pass1-console.txt | 58 focused tests passed, including CLIO tests |
| First frozen replay | reference-deltas-pass1.jsonl | 9 prompts changed; 0 additions, 40 removals; valid references lost |
| Pin the newly discovered over-broad guard | red-pass2-console.txt | 5 failed, 55 passed |
| Second/final guard | failed-pass2-console.txt | 1 failed, 62 passed: valid PR after a preceding task ID is lost |
| Second frozen replay | reference-deltas-pass2.jsonl | 7 prompts changed; 2 additions, 12 removals; a valid PR after “CLOSED” is lost |
| Review all prior/new affected cases | reference-audit.jsonl | 24 cases reviewed; see disposition limits below |
| Restore pre-batch runtime | restored-baseline-console.txt | Original 41 focused tests pass; no parser change retained |

Both replays retain 288 eligible prompts, nine starts/journeys, nine parent groups, 76 assigned,
212 unassigned and one represented device. `compare_replay.py` asserts identical source metadata,
window, prompt identity/text/start metadata, journey membership, orphan IDs and source coverage.
Private capture and evidence remain local. Public extraction deltas can be recomputed from the
JSONL records; private semantic judgments cannot be independently reconstructed from these counts.

## What changed and what did not

The second attempt rejects the two observed foreign-project associations, the non-GitHub chat ID,
two planned-PR ordinals and one ambiguous issue ordinal. It corrects several issue/PR type duplicates.
But the capitalized-word guard mistakes “CLOSED PR” for a different project's PR and drops a valid
reference. Another synthetic failure shows that a preceding task ID followed by punctuation can
cause the same loss. Stop rule fired; the second replay was diagnostic despite the red unit test,
not evidence that this candidate qualified for the next phase.

Assistant inspection of all 24 affected cases records final-reference dispositions in sorted
reference order (mapped to source identities only in the private review). Of 49 retained references,
35 are source-supported **candidates**, 12 have pre-existing type conflicts, and two remain unresolved.
One known-good reference was removed. These are diagnostic dispositions, **not human labels,
verified completed tasks, accuracy percentages or new errors all caused by this patch**.
The type conflicts expose an older weakness: a bare hash is assumed to mean “issue” even when its
surrounding paragraph/table says it is a PR. Merely finding that number on GitHub cannot repair that
semantic mismatch. Assistant labels must not be used as human ground truth or fine-tuning labels.

## Reproduce safely

Do not apply the rejected patch in a working checkout. To reproduce synthetic failures, use a
disposable checkout at this report's commit, confirm a clean tree, then:

```sh
git apply --check TESTS-RESULTS/2026-09-16+GH-232/rejected-candidate.patch
git apply TESTS-RESULTS/2026-09-16+GH-232/rejected-candidate.patch
PYTHONPATH=src python -m pytest tests/test_journey_replay.py tests/test_clio.py -q --tb=short
# Expected: 1 failed, 62 passed (candidate remains rejected).
```

`compare_replay.py --baseline ORIGINAL --before PREVIOUS --after CANDIDATE --public-output NEW_JSONL
--private-output NEW_PRIVATE_MD` reproduces the extraction deltas when authorized private bundles
are available. The candidate bundles were emitted by the existing `utils/CLIO/journey_replay.py`
with `--source-format md`, the frozen cutoff above, a verified XYZ Forge checkout, the original
retained capture, and a new private output directory for each pass. Nothing overwrote replay-1.
`test_compare_replay.py` exercises nonempty input plus deliberate source/start/membership/coverage
corruptions; these controls are separate from judging real-world reference correctness.

## Next recommendation

Separate unambiguous fixes (formatted PRs and chat IDs) from project/type inference. The next
bounded proposal should preserve uncertain references as uncertain, rather than growing a list
of words that guesses project identity or defaults every bare hash to an issue. Review that small
representation/consumer change before building it; this batch does not authorize a schema change
or another parser pass. Continue using the prior assistant-reviewed reconstruction only as a
qualified preview, not as automatically verified output.

## Readiness and threats to validity

Full application readiness remains blocked: doctor exit 1 (missing typer); full tests/HiQS/3-Eyes
collection exit 2 (66 collection errors). Private raw logs remain under ignored scratch; sanitized
gate results are retained separately. No dependencies were installed or deferred services enabled.
The required tests/ run also exits 2 (62 collection errors, one skipped). PDDA reports six
frontmatter, seven status-table and seven roadmap-coverage errors in other documents; observe-mode
exit 0 is not a clean verdict. No finding names the GH-232 document.
The wide harness validation produced failures and was terminated (exit 143); it was incomplete
and does not qualify this project's code. Verification outcomes are in verification.jsonl;
application-gates-excerpts.txt retains the non-private diagnostic lines.

This is one frozen week, one represented device, no independent human labeling, no blinded test,
and rules devised after inspecting these failures. The same-sample reruns detect regressions;
they do not measure generalization, usability or saved time. Reverting the candidate means these
particular improvements are **not shipped**. No new journeys were reconstructed in this batch.

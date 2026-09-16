# Three endings and the path to the ideal

Ideal: a small repeatable local work-history companion showing explicit task evidence, separate
attempts, attested delivery and visible gaps. Fallback: plain issue-linked evidence notebook. Stop:
retain the lessons if neither saves explanation/resume effort. These are planned product endings,
not experiment results or model-accuracy scores.

[Issue #232](https://github.com/HiQS-Labs/rebalanceOS/issues/232) owns the actionable plan; the
[repo mirror](../../PROJECT/2-WORKING/GH-232-OUTCOME-PLAN.md) gives phases and frozen usefulness rules.
The plan compares stories against simple lists, then repeats three tasks from another period;
operator feedback—not another model—decides usefulness. No new implementation began.

Fable 5.1 low-effort plan-only review returned PASS with three non-blocking clarifications, all
incorporated. [Full reviewer text and dispositions](QA.md). The full automated relay did not
complete its own gate, so there is no clean relay approval. Temporary supported Claude CLI used;
global install unchanged. CLI budget flag was not raised and is not a hard actual-spend ceiling.

Verification: existing focused runtime/CLIO/campaign controls rerun, 77 passed. New document
frontmatter/status-table issues were found and corrected; rerun reports only older unrelated
findings (six frontmatter, seven status-table, five hardcoded-path findings). Observe-mode zero
exit is not a global clean verdict. Diff whitespace checks run. Runtime/tests/version unchanged.
Full app dependency blockers keep PR #231 draft; ending selection is separate from integration.

Next: when the operator authorizes execution, build the optional explicit issue-evidence view,
keeping the two missing #568 mentions visible but unassigned. Do not infer starts from future
prompts, erase attempts or broaden a semantic detector. Any driven execution requires its own
passing automation gates. No new ingestion, private egress, Terra client, merge or deployment.

Limits: plan QA is not implementation verification, human usefulness, generalization or a clean
relay result. Historical capture has one represented device and incomplete activity coverage;
future results must retain their own primitives. Requested clarifications and operational fallback
are transparently distinguished from what Fable actually reviewed.
# Phase 1 implementation batch

The operator authorized one bounded 15-minute implementation batch after plan review.
Added `--issue-evidence` to the existing private replay renderer, not a new collector or database.
It appends all qualified XYZ Forge issue mentions in eligible prompts, including unassigned
mentions. Captured chats have separate local labels; missing sessions remain unknown. A later
start does not absorb an earlier mention. Multi-issue prompts keep their original identity and
“also mentions” label; unique counts do not sum appearances. Intent excerpts use existing redaction
and the 500-character display limit. Original stored prompt text remains unchanged.

| Control | Observed result |
|---|---|
| New controls before implementation | 2 failed as expected |
| Focused runtime/CLIO/saved-facts controls | 80 passed |
| Synthetic CLI with all three optional flags | Exit 0; 4 nonempty prompts |
| Frozen original bundle and old preview prefix | Exactly preserved |
| Eligible prompts / original journeys / unassigned | 288 / 9 / 212 |
| Unique issue-linked prompts / appearances / qualified issues | 15 / 15 / 9 |
| #568 mentions / still unassigned | 3 / 2 |
| New private output permissions | Directory 0700, files 0600 |
| Doctor / full suite | Exit 1, missing typer / exit 2, 62 collection errors |
| PDDA frontmatter / status-table | 6 / 7 existing unrelated findings; none on outcome plan |

Public tests use synthetic fixtures; raw frozen prompts and previews remain private.
`check_issue_view.py` recomputes the preservation/#568/permissions checks using explicit local
runtime/evidence/capture/output paths. Coverage totals are not human usefulness, accuracy or
confirmed causal work outcomes. The new section attaches only available direct issue facts,
showing event and retrieval times separately; issue-to-PR delivery composition is still Phase 2.
No model call, live fetch, capture/index write, merge or deployment. Driver reviewed the diff;
no independent implementation approval was obtained this batch. Fable's earlier PASS is plan-only.

Receipts: [controls](phase1-controls.log), [doctor](phase1-doctor.log),
[full-suite output](phase1-full-tests.log), and the committed synthetic tests.
Reproduction: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_journey_replay.py tests/test_clio.py TESTS-RESULTS/2026-09-16+GH-232-RUN15/test_saved_facts.py`.

Next: fresh bounded read-side recon before adding authoritative PR closing-issue relationships.
PR #231 remains draft. Human usefulness, another period/device and integration readiness are
unconfirmed; dependency-blocked full gates prohibit claiming the app is healthy.

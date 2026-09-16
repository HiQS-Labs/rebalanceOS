# Clear transition and current implementation review

The operator authorized a sustained 15-minute window starting 2026-09-16T15:57:53Z,
with a separate implementation agent and independent review. The run stayed within existing
private replay scope: no collector, model call, capture/index write, merge or deployment.

One synthetic chat has four prompts: start qualified issue 10, continue, explicitly switch to
qualified issue 20, continue. The original view remains one segment; the optional candidate view
has two segments of two prompts. Starts are unchanged. A switch does not prove earlier completion.
Questions, same-issue references, unknown prior tasks, quoted/negated/foreign references and
ambiguous next wording abstain. Bare prior issue numbers cannot establish qualified identity.

Independent review found two parser defects (formatted discussion IDs and malformed URL suffixes),
then a transition flag-combination defect: legacy guessed links could attach a wrong event to
the candidate view. All were reproduced before remediation. The amended candidate grouping and
renderer derive identity directly from qualified URLs independently of the explicit-links flag.
The independent reviewer passed both the corrected implementation and campaign composition.

## Observed results

| Check | Result |
|---|---|
| Focused runtime/CLIO + campaign controls | 77 passed |
| Review defect controls before correction | 4 failed, 47 passed |
| Transition controls against pre-remediation e6170d6 | Both new negative controls failed as expected |
| Mutated campaign cutoff | Boundary test failed when cutoff became inclusive |
| Frozen source/window and exact prompts/starts/original membership | Preserved |
| Eligible prompts / original journeys / unassigned | 288 / 9 / 212 |
| Additional qualified transitions in real sample | 0 |
| Explicit URL occurrences / unresolved candidates | 21 / 71 |
| Existing index target facts | 0 |
| Retained metadata composition facts / explicit reference matches | 47 / 12 |
| Private output permissions | Directories 0700; files 0600 |
| Doctor / full tests | Exit 1 (missing typer) / exit 2 (62 collection errors) |

These are coverage and control results, not accuracy. One frozen week/device does not establish
generalization, cross-device continuity or human usefulness. The zero-transition real result is
reported rather than widening grammar to force a success. Legacy context mode remains available
and still has known ambiguity limitations outside the strict candidate view.

`replay_saved_facts.py` is a campaign-only recipe composing the strict private replay with already
retained GitHub metadata. It checks source identity, matching historical cutoff, artifact identity,
seven-day event bounds and nonempty inputs; it reuses the existing private publisher. Retrieval time
is separate from event time. It does not fetch, persist into the index or infer PR↔issue closure
relationships. Twelve matching facts means exact artifact-reference matches, not twelve confirmed
chat-to-outcome causes. Deployment remains unknown.

Public files here contain synthetic inputs, safe receipts and recipe/tests. Raw prompts, retained
snapshots and enriched previews remain ignored/private. PR #231 remains draft. Next: inspect three
enriched histories for usefulness and omissions before expanding inference or ingestion.

## Reproduction

Run from the repository root with its existing environment:

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_journey_replay.py tests/test_clio.py TESTS-RESULTS/2026-09-16+GH-232-RUN15/test_saved_facts.py
PYTHONPATH=src .venv/bin/python utils/CLIO/journey_replay.py --source TESTS-RESULTS/2026-09-16+GH-232-RUN15/transition-fixture.jsonl --source-format jsonl --as-of 2026-09-16T04:25:38Z --explicit-links-only --qualified-transitions --output temp/gh232/new-synthetic-run
```

The private frozen replay uses the GH-230 retained capture and the same cutoff above, followed by
the campaign recipe with explicit runtime/bundle/snapshot/capture/output paths. Outputs must use
new directories. Source SHA256: 2599e168752ea9ccdf10673d363edc3a388f2687891a7f511bcd339d61df4063;
3,000,813 bytes. No private source is required for the public synthetic tests.

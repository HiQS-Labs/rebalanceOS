# CLIO journey replay — technical spike, not an accuracy evaluation

Date: 2026-09-16 UTC. Tracking: [#230](https://github.com/HiQS-Labs/rebalanceOS/issues/230), parent #210.
Protocol: `PROJECT/2-WORKING/GH-230-CLIO-JOURNEY-SPIKE.md`; initial plan review approved at `4acc673`.
Code/fixtures: `utils/CLIO/journey_replay.py`, `tests/test_journey_replay.py` in the containing commit.
Window: 2026-09-09T04:25:38Z inclusive to 2026-09-16T04:25:38Z exclusive.

## Result

The script produced private candidate timelines. It did not prove accurate task inference or completed
work. Separate-session and issue-linked modes yielded the same nine groups; no cross-session join
was observed. There is only one represented device. Terra was not called; no private data was sent.

| Coverage | Count |
|---|---:|
| Export marker blocks inspected | 4033 |
| Eligible prompts | 288 |
| Candidate journeys | 9 |
| Prompts assigned to journeys | 76 |
| Unassigned prompts | 212 |
| Issue-linked view parent groups | 9 |
| Actual GitHub events available | 0 |
| Malformed blocks skipped | 21 |
| Outside the seven-day window | 3439 |
| Other/unresolved repository | 285 |

`measurements.jsonl` retains non-identifying per-journey sizes and source-bin counters. Sum the nine
journey prompt counts for 76; add unassigned for 288; sum source bins for 4033. Private semantic
correctness cannot be independently reconstructed from these sanitized records. Full frozen capture,
evidence and preview are retained only in ignored local scratch, with private permissions.

## Reproduce

Use the source and tests from this commit, not a separately maintained script copy:

```sh
python -m pytest -q tests/test_journey_replay.py tests/test_clio.py tests/test_daily_work_synthesis.py
PYTHONPATH=src python utils/CLIO/journey_replay.py \
  --source "$PRIVATE_CLIO_EXPORT" --source-format md --checkout "$VERIFIED_XYZ_CHECKOUT" \
  --as-of 2026-09-16T04:25:38Z --output temp/gh230/new-run
```

The output directory must not exist. Re-run against the first run's `capture.md` into another new
directory and compare `evidence.json` and `preview.md`; both were byte-identical in this run.
The Markdown fallback follows canonical exporter markers; it is not a general Markdown parser.
It excludes unmarked legacy entries/personal text. The first JSONL attempt failed the nonempty gate;
the accepted Markdown run is separate, with no synthetic entries mixed into historical counts.

## Checks and limits

Agy reviewed the implementation and Markdown adaptation in one round: PASS, driver exit 0,
commit `5eb6ff0`. Verbatim: [review](../../relay-system/2026-09-16/gh230-implementation.md).
Approval is for the bounded spike, not app-wide release readiness. No reviewer requested changes.

Targeted output is in `targeted-console.txt`. Tests include deliberately wrong cross-repo joins and
intent labels that are caught, source-prefix mutation, empty inputs, missing DB, caps, preservation of
existing outputs, repeated starts, missing IDs, multi-issue ambiguity and future-start invariance.
Actual replay stdout is retained as `replay-console.txt` (contains aggregates only).

Full application tests: exit 2, 62 collection errors, missing dependencies in the isolated environment.
Doctor: exit 1, missing `typer`. This is a **draft implementation**, not an app-wide passing release.
No capture/index/scheduler/Obsidian modifications. No cloud/model calls. No refreshed GitHub index.
Terra's fixed daily-log/budget ownership lacks a safe standalone-output seam; it is deferred, not bypassed.
The database has no target GitHub artifacts, so real lifecycle outcomes remain an evidence gap.

## Threats to validity

This is a convenience sample with no human correctness labels. Start heuristics are deliberately
conservative; 212 unassigned prompts are not automatically detector errors or inactivity. Capture
filters and missing/unmarked history constrain coverage. Same-issue grouping is not proof of one
continuous task. Current GitHub snapshots cannot prove historical online availability. No measured
accuracy, time savings, cross-device quality, model quality, or superiority of either view is claimed.

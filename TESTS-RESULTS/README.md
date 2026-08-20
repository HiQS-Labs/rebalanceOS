# Test Results & Artifacts (`TESTS-RESULTS/`)

Committed execution artifacts, benchmark datasets, and structured telemetry from
measurement campaigns — model bake-offs, performance runs, retrieval evaluations,
harness tests.

## Purpose

**A claim whose evidence is unpublished is an assertion.** When an issue, PR,
`ROADMAP.md` entry, or code comment says a thing was measured, the measurement has
to be retained somewhere a reader can check it without access to the machine that
produced it. That is what this directory is for.

This is not archival tidiness. The GH-81 campaign overturned a conclusion this repo
had already acted on — a "we tested it, it didn't help" call made on 5 samples with
no ground truth, which had been used to revert a real improvement. The correction
was only possible because the second run published its per-query records. Retained
evidence is what lets a wrong call get found.

## Directory structure

One folder per campaign, named `YYYY-MM-DD+GH-<issue>`:

```
TESTS-RESULTS/
├── README.md
└── YYYY-MM-DD+GH-<issue>/
    ├── SUMMARY.md              # human-readable rollup: config, findings, threats to validity
    ├── <primitive>.jsonl       # the auditable primitive — one record per measurement
    ├── <aggregate>.jsonl       # derived metrics, if any
    ├── <console>.txt           # raw stdout of the run that produced the numbers
    ├── scripts/                # the code, as run
    └── qa/                     # third-party review transcripts, verbatim
```

The date is when the campaign **ran**, not when it was written up.

### What each part is for

**`SUMMARY.md`** — the only file most readers will open. Leads with a header block
(date, tracking issue, working doc, systems under test, duration, output files),
then the headline table, then findings, then **threats to validity**. That last
section is not optional: a summary that reports only what worked is a sales
document.

**The primitive `.jsonl`** — one record per individual measurement, carrying
`schema_version`, a `run_id`, and enough context to be read standalone. Every
aggregate in `SUMMARY.md` must be recomputable from it. If a number in the summary
cannot be derived from the primitive, either the primitive is incomplete or the
number is unsupported.

**`scripts/`** — copies of what actually ran, not a description of it. Scripts that
live only in `temp/` (gitignored) are not published.

**`qa/`** — review transcripts verbatim, not paraphrased. A summary of a review is
the reviewed party grading their own homework.

## Conventions

- **JSONL, not JSON**, for record streams: appendable, greppable, diffable per line, and a truncated file still parses up to the break.
- **`schema_version` on every record.** Bump it when fields change meaning; add fields freely without bumping.
- **Never rewrite a published campaign's records.** A run that was wrong gets a *new* campaign folder and a note in the old `SUMMARY.md` pointing forward. The audit trail is the point.
- **Large regenerable inputs stay out.** Sidecar databases, model weights, and corpus snapshots belong in `temp/` (gitignored) with the `SUMMARY.md` recording the seed and command needed to rebuild them.
- **Secrets never appear here** — not in logs, not in console captures, not in scripts. Check the console dump before committing it.

## Campaigns

| Campaign | Subject | Outcome |
|---|---|---|
| [`2026-08-20+GH-81`](2026-08-20+GH-81/) | Embedding model bake-off: BGE-small vs Qwen3-0.6B vs Gemini vs FTS5 baseline, 39 queries × 6 lanes | Shipped BGE's query prefix (MRR@10 0.572 → 0.751, p=0.0137); retracted an earlier conclusion; declined Gemini; kept BGE over Qwen |

## Inspecting a run

```bash
# headline metrics for every lane
jq -r 'select(.slice=="ALL") | "\(.lane)\t\(.["mrr@10"])"' \
  TESTS-RESULTS/2026-08-20+GH-81/lane_metrics.jsonl | sort -k2 -rn

# only the statistically significant comparisons
jq -r 'select(.significant) | "\(.lane_a) vs \(.lane_b)  p=\(.p_holm)"' \
  TESTS-RESULTS/2026-08-20+GH-81/pairwise_tests.jsonl

# where did one lane actually lose?
jq -r 'select(.lane=="bge" and .rank!=1) | "\(.qid)\trank=\(.rank)\t\(.query)"' \
  TESTS-RESULTS/2026-08-20+GH-81/per_query_results.jsonl
```

See [`../SOP.md`](../SOP.md) for when a campaign is required and how to run one.

# GH-81 bake-off — receipts

Evidence for every claim in [`../RESULTS.md`](../RESULTS.md), published here because
the working transcripts live under `.xyz/`, which is gitignored. A conclusion
whose evidence is unpublished is an assertion, so the transcripts are copied in
verbatim rather than summarised.

| file | what it is |
|---|---|
| [`qa-01-protocol-review.md`](qa-01-protocol-review.md) | Third-party review of the **protocol**, before any lane was scored. 3 rounds, closed Approved. Two `[Blocker]` findings changed the experiment's design — see below. |
| [`qa-02-pr83-code-review.md`](qa-02-pr83-code-review.md) | Third-party review of **PR #83** (the BGE migration itself). 2 rounds, closed Approved. Two `[Blocker]` findings, both shipping defects CI could not see. |
| [`scoring-run-console.txt`](scoring-run-console.txt) | Raw stdout of the scoring run that produced every number in RESULTS.md — validity gate, lexical labels, all five slices, all 15 pairwise tests. |
| [`../results.json`](../results.json) | Per-query rank of the target under all six lanes. The auditable primitive: every aggregate above is derivable from it. |
| [`../queries.json`](../queries.json) | The frozen 39-query set with targets and set labels. |
| [`../embed_local.py`](../embed_local.py) · [`../embed_gemini.py`](../embed_gemini.py) · [`../score.py`](../score.py) | The scripts, as run. |

## Why the protocol review matters to the result

The protocol was reviewed **before** any lane was scored, which is the only point
at which a review can still change an experiment rather than rationalise it. It
did change it, twice:

1. **The draft would have deleted the queries that matter.** It gated the query
   set on each target appearing in an FTS5 top-50 — a mislabeling guard that
   would have thrown out precisely the semantically-related, lexically-dissimilar
   queries a vector index exists to serve, leaving a query set a keyword search
   could already answer. FTS5 became a *label* and a scored baseline lane
   instead of a filter. The `lexical-hard` split in RESULTS.md exists only
   because of this finding.

2. **The draft's significance test was rigged toward the incumbent.** It declared
   a winner only on non-overlapping 95% bootstrap CIs — roughly a p<0.01 bar,
   which at n=39 would have returned "no measurable difference, keep BGE" almost
   regardless of the data. It also discarded the pairing between lanes answering
   identical queries. Replaced with paired Wilcoxon signed-rank plus Holm
   correction. **The headline finding (the query prefix, p=0.0137) would not have
   been detected under the original rule.**

A third finding corrected a uniform-truncation choice that handicapped the
long-context models, and a fourth caught a logical impossibility in a decision
rule (a lane pinned at zero by construction cannot "win" the subset that defines
it as zero).

## Reading the transcripts

Each is a relay thread: Reviewer appends graded findings
(`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), Producer logs a disposition for every
open finding (Implemented / Modified / Declined, with reasoning), and the thread
closes only on a Reviewer `Approved`. Findings were verified against the code or
the corpus before being accepted — the dispositions cite what was checked, and in
two cases the check changed the fix.

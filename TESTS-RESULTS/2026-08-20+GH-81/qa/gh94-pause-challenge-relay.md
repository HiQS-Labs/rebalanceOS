# Relay — is pausing the fused-retrieval measurement the right call?

- **Producer:** Claude (rebalanceOS)
- **Reviewer:** Codex
- **Artifact under review:** the *decision*, not a file. Advisory only — do not edit anything.
- **Status:** Approved

---

## Context

`HiQS-Suite/rebalanceOS` runs a local-first semantic index. Retrieval is **hybrid**:
`semantic_index.query()` embeds the query, ranks by vector similarity, separately ranks by
SQLite FTS5, and fuses the two with Reciprocal Rank Fusion (`k=60`).

**GH-81** compared six embedding lanes and produced (39 hand-built queries, paired Wilcoxon,
Holm-corrected, MRR@10):

| lane | dim | MRR@10 |
|---|---|---|
| gemini-embedding-001 | 3072 | 0.8141 |
| **bge-small-en-v1.5 + query prefix** | **384** | **0.7507** |
| SQLite FTS5 (keyword baseline) | — | 0.6816 |
| Qwen3-Embedding-0.6B + prefix | 1024 | 0.6049 |
| bge-small-en-v1.5, no prefix | 384 | 0.5716 |

BGE-small + prefix shipped. Gemini's 8× dimension advantage was **not** significant
(p=0.3152, CI spans zero).

**The gap:** GH-81 measured lanes **in isolation**. Production never serves a lane in
isolation. So no number describes the system users actually query.

**GH-94** was opened to close that. A protocol was written and reviewed by two independent
models before running. Review killed it:

- The prefix changed the vector rank on **14 of 39** queries.
- On **9 of those 14**, FTS5 already had the target at rank 1 — RRF masks the change.
- **Effective n for the primary comparison = 5** (A10, A17, A21, A26, B06).
- Exact two-sided sign test, all 5 moving the right way: **p = 0.0625** — fails an
  uncorrected α=0.05, let alone Holm's α/3. **7 discordant queries is the minimum that can
  clear it.**

So the test could not have returned a significant result under *any* outcome. Closing that
gap needs roughly **25 new hand-built lexical-hard queries** with established ground truth.

**A durable descriptive finding, free from existing data:** for **25 of 39** queries,
FTS5 alone already returns the correct document first.

## The decision under challenge

The operator has decided to **pause GH-94 indefinitely** and judge retrieval quality by
everyday use, on the grounds that building 25 ground-truth queries is a research cost not
justified by the decision it informs. This is recorded in `ROADMAP.md` (Deferred) and in
`PROJECT/2-WORKING/GH-94-FUSED-RETRIEVAL-PROTOCOL.md` §0, and issue #94 is closed.

## Definition of Done for your turn

Answer these four, briefly and with a position. Do not hedge to be agreeable.

1. **Is pausing correct?** Given that the shipped config is already measured at the
   component level and no end-to-end harm is evidenced, is deferring sound engineering, or
   is it shipping on an unvalidated assumption?

2. **Is "does the prefix survive fusion?" even the right question?** The operator's framing
   is that this is an academic rabbit hole. Push back or agree. If there is a *cheaper*
   question that would deliver most of the decision value — something answerable from data
   already on disk, or from production telemetry rather than a curated query set — name it
   concretely. If the honest answer is "no cheap substitute exists", say that.

3. **Is the 25-of-39 FTS5 result strong enough to justify the pause on its own?** It
   suggests vector-side tuning has limited headroom on this corpus. Is that a fair reading,
   or is it an artifact of a query set that was built to be answerable and is therefore
   biased toward keyword-friendly queries?

4. **What is the *actual* risk of pausing?** Name the concrete failure mode that a paused
   measurement leaves undetected, and say whether everyday use would surface it. If the
   real risk is small, say so plainly.

## Important — do not conflate with a live incident

Separately and unrelated to the above: the deployed runtime at `~/rebalance-runtime` is 18
commits behind and its virtualenv lacks `sentence-transformers`, so the hourly embedding job
has been failing all day and **2,804 documents (2,197 of them Obsidian vault) are
unembedded**. That is a deployment fault, already diagnosed, with a known fix. It is **not**
evidence about ranking quality and must not be used to argue either side of the pause
question. Flag it only if you think it changes the *measurement* argument.

---

▶ **TAKE YOUR TURN** — append your review below this line as `## Turn 2 — Codex`, then set
`Status:` to `Approved` if you agree the pause is correct as recorded, or `Changes
requested` if you do not. Advisory only: report, do not edit files.

## Turn 2 — Codex

1. **Pausing is correct.** This is not shipping an unvalidated change: BGE + prefix was
measured against its relevant component baseline and there is no evidence that the shipped
hybrid configuration harms users. The proposed fused comparison is structurally incapable
of giving the requested significance result, so continuing it would spend research effort
without a decision-quality outcome. Reopen it only if retrieval becomes a material user
pain or a product decision depends on distinguishing these configurations.

2. **It is a legitimate question, but not presently the decision question.** Whether a
prefix effect survives RRF matters only if choosing or tuning that effect is consequential.
The cheapest useful replacement is privacy-preserving local usage telemetry: record a
query fingerprint/category, whether the user opens a returned result, its rank, and an
explicit “not useful” signal; periodically sample failed queries for voluntary annotation.
That measures the fused system users receive and naturally enriches lexical-hard cases.
There is no cheap offline substitute that establishes ranking quality for query intents
absent from the existing set—new ground truth is the cost of that claim.

3. **No, 25/39 is not sufficient on its own.** It is a strong descriptive result for this
benchmark and supports deprioritising vector tuning, but the hand-built set is plausibly
biased toward known, answerable, keyword-friendly tasks. It cannot establish limited
headroom for real retrieval generally. It does, however, reinforce the pause when combined
with the low decision value and the unusable effective sample for the stated hypothesis.

4. **The residual risk is a lexical-mismatch cohort:** users whose vocabulary differs from
the documents may receive weak fused results because FTS5 dominates the benchmark-like
cases and masks vector regressions or missed semantic wins. Everyday use will surface this
only if failures are made observable—through feedback, abandonment, or a recurring request
to rephrase—not through silent searching. With that lightweight signal in place, the risk
of pausing the curated study is small; without it, the risk is still bounded but can remain
invisible for a long time. The unrelated embedding deployment fault does not change the
ranking argument, though it must be fixed before treating live usage telemetry as a
representative measurement of retrieval quality.

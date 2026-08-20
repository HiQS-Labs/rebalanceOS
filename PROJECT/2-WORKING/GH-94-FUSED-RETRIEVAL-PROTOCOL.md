---
title: Fused hybrid retrieval — end-to-end measurement protocol
status: PAUSED by operator decision 2026-08-20 — not scheduled; see §0 (GH-94)
gh_issue: 94
created: 2026-08-20
branch: feat/gh94-fused-hybrid-measurement
supersedes: []
goal: >
  Measure the retrieval path production actually serves — vector and FTS5 fused through
  RRF — rather than the vector component in isolation, and settle whether the BGE
  query-prefix gain measured in GH-81 survives fusion.
---

# GH-94 — fused hybrid retrieval, measured end-to-end

## 0. ⏸ PAUSED — operator decision, 2026-08-20. Do not restart this without being asked.

**Decision: measurement of the fused retrieval path is deferred indefinitely. Retrieval
quality is assessed through everyday use instead.** Recorded by the repo operator, not
inferred by an agent.

**Rationale, in the operator's terms:** the remaining work — hand-building ~25 lexical-hard
queries with established ground truth — is a research exercise whose cost is not justified
by the decision it would inform. Everyday use is the accepted signal.

**This is not an open question awaiting an answer, and it is not a gap to be helpfully
closed.** An agent reading §§1–12 will find a fully specified, well-reviewed experiment and
a live-looking "what v2 must do" list. That list is **suspended**, not pending. Proposing
this work again, re-deriving it under a new issue number, or treating the shipped
configuration as unvalidated because of it, all re-litigate a decision already made.

**What is settled and needs no further work:**
- BGE-small (`BAAI/bge-small-en-v1.5`) is the canonical embedding model. Not revisited.
- The query-side instruction prefix stays. It is measured at the component level
  (0.5716 → 0.7507 MRR@10, p=0.0137) and there is no evidence of end-to-end harm.
- Hybrid RRF fusion stays on with `k=60`.

**Reopen only if** a concrete retrieval failure is observed in everyday use — a specific
query returning a wrong or missing document that matters — **and** it is traced to ranking
rather than to ingest, coverage, or a stale index. Curiosity is not a trigger.

**What remains useful from this document**, requiring no new measurement: §12.2's
descriptive finding, computed from existing GH-81 data, that for 25 of 39 queries keyword
search alone already returns the correct document first. That bounds how much any
vector-side tuning could ever matter on this corpus, and it is the practical reason the
pause is reasonable rather than merely expedient.


> **This protocol is frozen before any scoring runs.** The decision rule in §7 is written
> in advance precisely so it cannot be chosen after seeing results. Deviations get
> recorded in the results SUMMARY as deviations, not folded in silently.
>
> ## ⛔ v1 did not survive review — do not run it
>
> Two independent reviewers (Codex, agy) each rejected the primary comparison as
> underpowered *by construction*, and a direct check of the GH-81 data confirms it with a
> hard number: **the effective sample size for C1 is 5, and n=5 cannot reach significance
> even if every query moves the right way.** §12 records the finding, the arithmetic, and
> what would have to change. Sections 1–11 below are preserved as written, unamended, so
> the rejected design stays legible.

## 1. The question

GH-81 scored six embedding lanes **in isolation**. Production serves none of them in
isolation: `semantic_index.query()` defaults to `hybrid=True` and fuses a vector ranking
with an FTS5 lexical ranking through Reciprocal Rank Fusion.

So every headline number in `TESTS-RESULTS/2026-08-20+GH-81/SUMMARY.md` describes a
*component*. Two things follow that nobody has measured:

1. **"No embedding lane significantly beats FTS5"** compares component to component. It is
   not a statement about shipped search, though it reads like one — and it has already
   been quoted that way in a cross-repo discussion (AEGIS-Sleuth #126).
2. **The BGE query-prefix fix moved the vector component from 0.5716 to 0.7507 MRR@10**
   (p=0.0137, 14 improved / 0 regressed). Whether that survives fusion is unknown. RRF is
   rank-based, so a component gain does not translate proportionally. If FTS5 was already
   returning the correct document at rank 1 for the queries the prefix rescued, the
   end-to-end gain could be near zero.

**Primary question: does the prefix gain survive fusion?** Everything else is secondary.

## 2. What makes this cheap — and the one fact the whole design rests on

**The BGE instruction prefix is applied to the query only. Stored passages never receive
it.** `_query_embed_text()` is called at exactly one site, on the query text, in
`semantic_index.query()`; the ingest path does not call it, and
`tests/test_semantic_query_prefix.py` pins that asymmetry.

Therefore **the with-prefix and without-prefix lanes read the identical stored vectors**,
and no re-embedding is required for any lane in this experiment. The only thing that
changes between them is the vector the *query* is encoded to.

> This corrects the cost estimate in issue #94, which said a BGE re-embed of the corpus
> was needed. It is not. Verified: the live index is stamped
> `BAAI/bge-small-en-v1.5|384` across 49,668 documents, and `semantic_embeddings` is
> declared `vec0(embedding float[384])`.

Anything that turns out to require re-embedding is out of scope for this run and gets
recorded as such.

## 3. Corpus — the production index, not a downsample

**Corpus: a read-only snapshot of the live index** (52,399 documents, 49,668 embedded,
taken at run start and hashed).

This deliberately differs from GH-81, which sampled 10,000 documents. Three reasons:

1. The question is *what do users experience*, and users query the full index. GH-81's
   own threats-to-validity section lists the 5.2× downsample as inflating absolute scores.
2. The GH-81 sample cannot be reproduced anyway. Protocol §3.2 recorded the RNG seed in
   `corpus.db.meta`, and `corpus.db` was never committed and no longer exists on disk.
   Re-sampling with a *new* seed would produce a corpus that is neither the old one nor
   the production one — the worst of both.
3. All lanes here run against the same snapshot, so within-run comparisons — which is the
   entire experiment — are unaffected.

**Consequence, stated up front:** absolute MRR in this run is **not** comparable to
GH-81's absolute MRR. Lane L3 (§5) exists to bridge the two.

**The live database is opened read-only and is never written.** The snapshot is a file
copy; every lane reads the copy.

## 4. Query set and ground truth

The frozen GH-81 set, unchanged: `TESTS-RESULTS/2026-08-20+GH-81/queries.json` — 39
queries with hand-established `target_doc_id`, carrying their `set` (A/B/C) and
lexical-easy/hard labels.

Re-using it is the point. It was built by hand, screened for target distinctiveness after
a first sample turned out to be dominated by near-duplicates, and it is the only reason
this run can be paired against GH-81 at all.

**Verified against the live index:** all 39 targets are present. **Two — A12 and A24 — are
present but not embedded** (`embedded_hash IS NULL`).

**Decision, frozen now: A12 and A24 are excluded; n = 37.** This is not a convenience.
An unembedded document is unreachable by any vector lane but perfectly reachable by FTS5,
so retaining those two would hand a structural advantage to the FTS5 and hybrid lanes and
bias the primary comparison in a direction that has nothing to do with the prefix. The
exclusion is recorded in SUMMARY as a deviation, with both qids named.

## 5. Lanes

All four run against the same snapshot, the same 37 queries, `top_k=10`.

| lane | configuration | what it is for |
|---|---|---|
| **L1** | `hybrid=True`, BGE **with** prefix | what ships today |
| **L2** | `hybrid=True`, BGE **without** prefix | isolates what the prefix buys end-to-end |
| **L3** | `hybrid=False` (vector only), with prefix | control; reproduces the GH-81 measurement shape on this corpus and bridges to it |
| **L4** | FTS5 only | the dumb baseline, again |

Lanes call the **production `query()` function**, not a reimplementation. If a lane cannot
be expressed through the real code path, that is a finding about the code's testability
and gets written down rather than worked around with a parallel implementation — a
reimplementation would measure the harness rather than the system.

L2 is produced by bypassing the prefix at the single call site, not by editing shipped
behaviour.

## 6. Metrics and statistics

Identical to GH-81 so the two are methodologically comparable:

- **Headline: MRR@10.** Also Recall@1 and Recall@10.
- **Paired Wilcoxon signed-rank** on per-query reciprocal rank. Not a paired t-test:
  reciprocal rank is bounded, discrete and heavily tied.
- **Holm–Bonferroni** across the confirmatory comparisons in §7 — and only those.
- **95% bootstrap CI on the mean paired difference** (10,000 resamples, fixed seed).
  On the *mean*, not the median: ties pin the median at zero and it reports nothing.

`TESTS-RESULTS/2026-08-20+GH-81/scripts/score.py` already implements all of this and is
reused rather than rewritten.

## 7. Confirmatory comparisons and the decision rule — frozen before scoring

Exactly **three** confirmatory comparisons enter Holm correction:

| # | comparison | asks |
|---|---|---|
| C1 | **L1 vs L2** | does the prefix gain survive fusion? *(primary)* |
| C2 | L1 vs L3 | does fusion beat vector alone? |
| C3 | L1 vs L4 | does the shipped system beat plain keyword search? |

**Decision rule, written in advance:**

- **C1 significant and positive** (Holm-adjusted p < 0.05, CI excludes 0) → the prefix fix
  is confirmed end-to-end. `semantic_index.py`'s docstring is updated to cite the
  system-level number instead of the component-level one.
- **C1 not significant** → the prefix's component-level gain **does not demonstrably reach
  users**. This is a publishable negative result. It does *not* justify reverting the
  prefix — a rank-based fusion absorbing a component gain is not evidence of harm — but it
  does mean every public claim tied to 0.5716 → 0.7507 must be restated as component-level,
  including in the AEGIS-Sleuth #126 thread.
- **C1 significant and negative** → the prefix hurts end-to-end. Escalate: this contradicts
  GH-81 and would need to be reproduced before any code change.
- **C3 not significant** → we state plainly that the shipped system is not measurably
  better than keyword search on this query set, and say so without softening.

Sample size is n=37 and the effect may be small. **An inconclusive result is a real
outcome and will be reported as one.** No comparison gets added after seeing results; if
one suggests itself, it is labelled exploratory and excluded from Holm.

## 8. Exploratory, explicitly not confirmatory

Run after the confirmatory analysis is complete and reported separately, so it cannot
inflate multiplicity:

- **RRF `k` sweep.** `k=60` is the paper default and was never tuned for this corpus.
  Sweep k ∈ {10, 20, 40, 60, 100, 200} on L1 and plot MRR@10.
  **Any k chosen from this sweep is a hypothesis, not a result** — adopting it requires a
  fresh run on a query set this sweep did not touch.

## 9. Outputs

A campaign directory `TESTS-RESULTS/2026-08-20+GH-94/` per `SOP.md`:

- `SUMMARY.md` — findings, threats to validity, deviations
- `per_query_results.jsonl`, `lane_metrics.jsonl`, `pairwise_tests.jsonl` — each record
  carrying `schema_version` and `run_id`
- `scripts/` — the runner, plus the reused `score.py`
- `queries.json` — the 37 scored queries, with A12/A24 marked excluded and why
- `snapshot.txt` — snapshot path, size, sha256, document counts, capture time
- `console.txt` — verbatim run output

`TESTS-RESULTS/2026-08-20+GH-81/SUMMARY.md` gets a pointer to this campaign so its
declared scope limit is closed rather than left dangling.

## 10. Threats to validity — declared before the run

1. **Corpus differs from GH-81** (full index vs 10k). Absolute scores are not comparable;
   L3 is the bridge.
2. **n=37 after exclusions.** Underpowered for small effects. A null result means "not
   demonstrated at this power", never "no effect".
3. **Single query set, single corpus, one author.** GH-81 had the same limitation and it
   was called out then; re-using its query set inherits any bias baked into it.
4. **Ground truth is single-target.** A query may have several legitimately correct
   documents; rank of *the* designated one under-credits a lane that surfaces a different
   good answer.
5. **The index is live and drifting.** It grew from 52,178 to 52,399 documents since
   GH-81. The snapshot freezes it for this run, but a rerun later will not see the same
   corpus.
6. **2,731 documents in the index are unembedded**, so the vector lanes see a slightly
   smaller haystack than FTS5 does. This mirrors production exactly and is therefore
   correct for this experiment, but it is not a clean lane-vs-lane comparison.

## 11. Review

Reviewed before any scoring runs, per `SOP.md` ("review the protocol, not just the
results"). The reviewer is asked specifically to attack §7's decision rule and §4's
exclusion of A12/A24, since those are the two places where a convenient choice made after
the fact would be hardest to detect.


## 12. Review outcome — v1 rejected, with the arithmetic

Reviewed by Codex and agy independently, before any scoring, per `SOP.md`. Both returned
the **same primary blocker** without seeing each other's answer. A direct check against the
GH-81 per-query data confirms it and puts a number on it.

### 12.1 The blocker: C1 is unrunnable, not merely underpowered

RRF fusion masks a vector-side improvement whenever the FTS5 leg already ranks the target
at 1. Measured on the frozen query set:

| | count |
|---|---|
| Queries in the set | 39 |
| **Lexical-easy** | **34** |
| FTS5 already returns the target at rank 1 | 25 |
| Prefix changed the *vector* rank at all | 14 |
| ...of those, FTS5 already at rank 1 → fusion masks the change | 9 |
| **Queries that can move the fused result — effective n for C1** | **5** |

The five: A10, A17, A21, A26, B06.

An exact two-sided sign test with **all five** moving in the same direction gives
**p = 0.0625** — failing even an uncorrected α=0.05, before Holm's α/3 = 0.0167. Seven
discordant queries are the minimum that can clear it (p = 0.0156).

**So the design cannot return a significant C1 under any outcome, including one where the
prefix helps on every query it is able to help on.** A guaranteed null is not a test. Worse,
§7's decision rule would have licensed reading that foregone null as "the prefix does not
demonstrably reach users" — publishing a Type II error as a finding.

Both reviewers also warned that `score.py`'s Wilcoxon is a normal approximation with no tie
correction, which is a poor choice for a sample this tie-heavy.

### 12.2 What is *not* a measurement artifact

The masking is real system behaviour, and that is itself informative. On this corpus,
**for 25 of 39 queries keyword search alone already puts the right document first**, so no
vector-side improvement can change what a user sees. That is a descriptive finding about
the *reach* of the prefix fix, available from existing data at zero cost, and it should be
reported as such — carefully separated from any claim about statistical significance.

### 12.3 Other findings accepted

- **[Blocker, Codex + agy] Excluding A12/A24 was wrong.** Both L1 and L2 carry an identical
  FTS5 leg, so an unembedded target ties both lanes rather than biasing C1 — the exclusion
  removed nothing harmful and discarded exactly the production cases where hybrid earns its
  keep over vector-only (C2). **Keep all 39; tag the two as vector-ineligible; report the
  37-query result as a sensitivity analysis.** §4 is superseded.
- **[Blocker, Codex] `score.py` cannot double as the production-path runner.** It queries
  sidecar tables directly, never calls the fused path, uses a different FTS tokenizer, and
  its sidecar vectors were built from `title + body` normalized while production embeds
  `body[:4000]`. **L3 is therefore not a bridge to GH-81's numbers** — it is a new
  production-vector control, and §5 overstated it. Reuse only the vetted statistics
  helpers; write the runner against `semantic_index.query()`.
  *(agy called L3 a valid bridge; Codex's contrary reading is cited to specific lines and
  is adopted.)*
- **[Should, Codex] Add L5: vector-only, no-prefix.** L1/L2/L3/L5 forms the 2×2 of
  fusion × prefix, which is the only way to show fusion *attenuates* the effect rather than
  merely observing a small hybrid contrast.
- **[Should, Codex] Snapshot with SQLite's backup API, not a file copy** — the connection
  runs in WAL mode, so a bare copy can capture a torn state. Pin commit, model revision,
  `source` filter and `top_k`; note that the default source filter is `vault/github/email`,
  not every document in the database.
- **[Pass, both] §2's foundation holds.** Both verified against the code that the BGE prefix
  is applied query-side only and that stored passages never receive it, so no re-embedding
  is needed. The one claim the whole design rested on is sound.

### 12.4 What v2 must do before anything is scored

1. **Demote C1 from confirmatory to descriptive.** Report effect *reach* — how many queries
   the prefix can and does move end-to-end — with no significance claim attached.
2. **Build a lexical-hard query set** (~25 queries with hand-established targets) if a
   confirmatory C1 is still wanted. Those are the queries where the vector leg is the only
   thing that can work, and therefore the only place the prefix can be tested end-to-end.
   This is real work and a separate decision, not a tweak.
3. **Keep C2 and C3 confirmatory** (Holm across two, not three). Neither is subject to the
   same masking, so both remain decidable on the existing set.
4. Adopt every accepted item in §12.3.
5. Pre-register a minimum detectable effect and the discordant-count threshold, so
   "inconclusive" is a predicted outcome rather than a discovered excuse.

# GH-81 — Three-way embeddings bake-off: protocol

**Status:** APPROVED — QA passed (relay-xyz / agy, 3 rounds, 2026-08-20)
**Tracking issue:** [GH-81](https://github.com/HiQS-Suite/rebalanceOS/issues/81)
**Author:** claude-a · 2026-08-20

---

## 0. Why this exists

GH-81 migrated the semantic index from `Qwen3-Embedding-0.6B` (1024-dim, via
`mlx-embeddings`) to `BAAI/bge-small-en-v1.5` (384-dim, via
`sentence-transformers`). That migration shipped on the strength of a
**single-model spot check** — a target-vs-irrelevant cosine comparison recorded
in `GH-81-OBSIDIAN-VAULT-EMBEDDINGS.md` (target 0.8227 / irrelevant 0.4654,
rated "Excellent"). Qwen was never scored on the same scale; its row reads
"Baseline reference".

So the repo currently has **no measurement that compares the model it ships
against the model it replaced**, and none at all against a hosted option.

A follow-up attempt to tune BGE (adding its documented query-instruction
prefix) made retrieval **worse** on the one query with verifiable ground truth
— the correct document fell from rank #1 to rank #3
([comment](https://github.com/HiQS-Suite/rebalanceOS/issues/81#issuecomment-5359722367)).
That result was uninterpretable because the test had no ground-truth set and
n=5. This protocol exists so the next measurement is not throwaway.

**Whether that regression is real is itself a hypothesis this protocol tests**
(§4.3). To be precise about what is being asked: BGE's documented recipe is
genuinely asymmetric — prefix the query, leave the passage alone — so applying
the prefix to queries only was *following* the recipe, not misapplying it. The
open question is therefore not "was the prefix used wrongly" but **"does BGE's
own documented recipe actually help on this corpus, or did n=5 with no ground
truth simply produce noise?"** §4.3 answers that with a proper paired
comparison.

## 1. Question being answered

> For rebalanceOS's actual corpus and actual query style, which of Gemini
> (hosted), Qwen3-Embedding-0.6B (local), and BGE-small-en-v1.5 (local) gives
> the best retrieval quality — and is the gap large enough to justify its cost
> in latency, storage, and (for Gemini) network dependency and per-call spend?

This is a **decision protocol**, not a benchmark for publication. The output is
a recommendation on what the semantic index should ship with, plus the evidence
behind it.

## 2. Models under test

| Lane | Model | Dim | Runtime | Asymmetric prompting (per vendor docs) |
|---|---|---|---|---|
| `bge` | `BAAI/bge-small-en-v1.5` | 384 | local, `sentence-transformers`, MPS | query: `"Represent this sentence for searching relevant passages: "` · passage: **no prefix** |
| `qwen` | `Qwen/Qwen3-Embedding-0.6B` | 1024 | local, `sentence-transformers`, MPS | query: `"Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: "` · passage: **no prefix** |
| `gemini` | `gemini-embedding-001` | 3072 (native) | hosted API | `task_type="RETRIEVAL_QUERY"` vs `task_type="RETRIEVAL_DOCUMENT"` |

All three are confirmed available on this machine: BGE and Qwen are in
`~/.cache/huggingface/hub/`, and `get_gemini_api_key()` returns a key.

**Dimension is deliberately NOT normalized across lanes.** Each model is tested
at the dimension it is actually deployed at, because that is the configuration
a decision would ship. Gemini's dimension is recorded as a cost factor (§6),
not discounted as an unfair advantage.

## 3. Corpus and sidecar databases

### 3.1 Sidecar, one per lane

Each lane writes its own SQLite file — the live database is **never** written
to. Read-only access to `~/Library/Application Support/rebalance-os/rebalance.db`
to snapshot the corpus, once, at the start.

```
temp/bakeoff/corpus.db          # the shared, frozen corpus — built once
temp/bakeoff/emb-bge.db         # vec0(embedding float[384])
temp/bakeoff/emb-qwen.db        # vec0(embedding float[1024])
temp/bakeoff/emb-gemini.db      # vec0(embedding float[3072])
```

`corpus.db` schema:

```sql
CREATE TABLE docs (
  doc_id      INTEGER PRIMARY KEY,   -- carried verbatim from semantic_documents.id
  source_type TEXT NOT NULL,
  title       TEXT,
  body        TEXT,
  is_target   INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
```

Each `emb-*.db` schema:

```sql
CREATE VIRTUAL TABLE vec USING vec0(embedding float[<DIM>]);
CREATE TABLE map (rowid INTEGER PRIMARY KEY, doc_id INTEGER NOT NULL);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
-- meta records: model, dim, passage_prefix, query_prefix, normalized,
--               truncation_chars, truncated_count, embed_seconds, built_at
```

`doc_id` is identical across all four files. **Every lane embeds byte-identical
input text** (before each model's own prefix and its own context limit apply). Any difference in results is attributable to the model, not the input.

### 3.2 Corpus selection

The live index holds 52,149 documents:

| source_type | count |
|---|---|
| github | 47,173 |
| vault | 2,570 |
| code | 1,612 |
| figma | 686 |
| email | 108 |

Embedding all 52k three times is not justified — the Gemini lane alone would be
~52k API calls, and the discrimination signal saturates well before that.

**Corpus = 10,000 documents**, assembled as:

1. **All ground-truth target documents** (§4.1), unconditionally included.
2. A **stratified random sample** of the remainder, preserving the source_type
   proportions in the table above, to fill to 10,000.

Rationale for preserving proportions rather than balancing them: github is 90%
of the real haystack, so it must be 90% of the distractors. A balanced corpus
would flatter every model by deleting the noise they actually have to survive.

Seeded with a fixed RNG seed recorded in `corpus.db.meta` so the sample is
reproducible.

**Declared limitation:** 10k is a 5.2× downsample. Retrieval gets *easier* as a
corpus shrinks, so absolute Recall@1 here will read higher than production.
Only the **relative ordering** of the lanes is claimed; absolute numbers
are not a production forecast.

### 3.3 Text normalization

For every doc, the embedded text is `f"{title}\n\n{body}"` with `title` empty-safe.
**No uniform truncation. Each lane embeds up to its own model's native limit.**

An earlier draft truncated everything to 2,000 chars (BGE-small's ~512-token
context) so no model saw text BGE could not. That was rejected on measurement:

| source_type | n | p50 chars | p90 | p99 | >2,000 chars |
|---|---|---|---|---|---|
| github | 47,173 | 300 | 2,177 | 6,369 | 11.4% |
| vault | 2,579 | 405 | 1,201 | 5,927 | 4.3% |
| code | 1,612 | 671 | 2,446 | 7,825 | 14.3% |
| figma | 686 | 85 | 167 | 298 | 0.0% |
| email | 108 | 286 | 357 | 461 | 0.0% |
| **all** | **52,158** | **300** | **2,124** | **6,369** | **11.0%** |

The median document is 300 characters. Uniform truncation would therefore have
changed nothing for 89% of the corpus while, on the other 11%, deliberately
blinding Qwen and Gemini to context they *would* use in production. That is a
handicap applied to the models under test in order to make the comparison look
tidy — it measures "best on the text BGE can see" and would then be read as
"best". A decision protocol must measure the configuration that would ship.

Instead:

- Each lane truncates at its own model's limit and **records its truncation
  rate** in `meta`.
- Results are reported twice: over all queries, and over the
  **no-truncation subset** — queries whose target document fits inside every
  lane's limit (~89% of the corpus). If the two agree, long-document handling
  is not driving the result. If they disagree, that difference *is* a finding
  and gets reported as one, rather than being designed away in advance.

## 4. Ground truth

This is the part the previous attempt lacked, and the part most likely to be
wrong if rushed.

### 4.1 Query set — 40 queries, two kinds

**Set A — 30 synthetic-from-document queries.**
Sample 30 documents stratified across source types. For each, **Claude (the
protocol author) reads the document and writes a natural-language question that
document answers.** The target is that document's `doc_id`.

*Why the author and not an LLM-in-the-loop:* generating queries with Gemini
would bias the Gemini lane (query and embedding from the same model family).
Generating them with Qwen or BGE is not possible — they are embedding models,
not generative. Claude is not a lane in this bake-off, so authorship by Claude
introduces no family bias toward any tested model.

*Residual bias, declared:* all Set A queries share one author's phrasing style.
Set B exists to bound this.

**Set B — 10 real operator queries.**
Written in the operator's own style (short, keyword-ish — the style that showed
up in the failed prefix test). Targets are identified by **hand inspection of
the corpus**, not by any model's output. A query whose correct answer cannot be
established by hand is discarded, not guessed.

*Set B is scored separately from Set A and never pooled into one headline
number.* If the two sets disagree about which model wins, that disagreement is
the finding — it means query style dominates model choice, and the protocol
must say so rather than average it away.

### 4.2 Target validity gate — run BEFORE any lane is scored

Each (query, target) pair must pass:

- The target doc is present in `corpus.db`.
- No two queries share a target.

Pairs failing the gate are **removed and logged**, not repaired to fit. The
final query count is reported; a silent drop is the failure mode this gate
exists to prevent.

**Lexical overlap is measured, never used as a filter.** An earlier draft
required each target to appear in the top-50 of a plain FTS5 search, as a check
against mislabeling. That was wrong and is removed: it would have discarded
precisely the queries where a vector index earns its keep — semantically
related, lexically dissimilar — leaving a query set that a plain keyword search
could already answer, and a bake-off that could not detect the capability being
bought.

Instead FTS5 runs as a **labeler and a baseline**:

- Each query is tagged `lexical-easy` (target in FTS top-50) or `lexical-hard`
  (target not found lexically).
- All primary metrics are additionally reported split by that label.
  **Performance on `lexical-hard` queries is the most decision-relevant number
  in this protocol** — it is the only part of the workload a vector index is
  strictly necessary for.
- FTS5 itself is scored as a **sixth lane**. If a model cannot beat plain
  keyword search on this corpus, that is the single most important result the
  run could produce, and the protocol must be able to see it.

A `lexical-hard` query is not evidence of mislabeling; the labeling defence is
that a human established every target by reading the document (§4.1).

### 4.3 The asymmetric-prompting sub-experiment

The BGE lane is run **twice**, as two separate scored lanes:

- `bge` — passages unprefixed, queries unprefixed (**what ships today**)
- `bge-asym` — passages unprefixed, queries prefixed (**BGE's documented recipe**)

This directly tests the hypothesis from §0: that the earlier prefix regression
came from applying a query-side treatment against an untreated corpus. Both use
the same `emb-bge.db` — only the query embedding differs, so this costs one
extra query pass and zero extra corpus embedding.

Qwen gets the same treatment (`qwen` / `qwen-asym`) for symmetry. Gemini's
`task_type` is not optional in its API, so it has one lane only.

Total scored lanes: **6** — `bge`, `bge-asym`, `qwen`, `qwen-asym`, `gemini`,
plus the `fts` lexical baseline from §4.2. The baseline is not a formality: a
bake-off that cannot tell you whether *any* of the models beat keyword search
has skipped the most consequential comparison available to it.

## 5. Retrieval and metrics

Every lane uses the identical search path: cosine over L2-normalized vectors via
`sqlite-vec` `MATCH ... k=10`. No reranking, no hybrid, no filters.

### Primary metrics (retrieval quality)

| Metric | Definition |
|---|---|
| **Recall@1** | fraction of queries where the target is rank 1 |
| **Recall@5** | fraction where the target is in the top 5 |
| **Recall@10** | fraction where the target is in the top 10 |
| **MRR@10** | mean of 1/rank, 0 if the target is not in the top 10 |

**MRR@10 is the headline.** It is the only one of the four that distinguishes
"nearly right" from "badly wrong" and does not collapse under a small n.

Reported separately for Set A and Set B. Never merged.

### Secondary metrics (cost)

| Metric | Why |
|---|---|
| corpus embed wall-clock | one-time reindex cost |
| query embed p50 latency | felt on every search |
| sidecar `emb-*.db` size on disk | storage cost of the dimension |
| truncation rate | how much of the corpus each model couldn't see |
| Gemini: API call count + $ | the only lane with marginal per-query cost |

Secondary metrics **never override** a primary result — they are the tiebreaker
when quality is close, and the reason a marginal quality win might still be
declined.

### Significance — paired tests, not independent intervals

An earlier draft declared a winner only when its 95% bootstrap CI did not
overlap the runner-up's. That was doubly wrong and is replaced:

1. **It discarded the pairing.** Every lane answers the *same* queries, so the
   per-query reciprocal ranks are paired observations. Comparing independent
   per-lane intervals throws away the pairing and inflates the apparent
   variance with between-query difficulty — which is by far the largest source
   of spread here, and is *common to all lanes*.
2. **Non-overlapping 95% CIs is roughly a p < 0.01 bar**, not p < 0.05. On
   n=30 it would almost never be met, so the protocol would have returned "no
   measurable difference → keep BGE" nearly regardless of the data. A decision
   rule that reaches its default conclusion whatever happens is not a test.

**The test:** for each pair of lanes, a **Wilcoxon signed-rank test** on the
per-query differences in reciprocal rank, α = 0.05, two-sided. Signed-rank
rather than a paired t-test because reciprocal rank is bounded, discrete, and
heavily tied at 0 and 1 — it is not close to normal.

**Multiple comparisons:** 6 lanes (5 embedding + FTS baseline) give 15 pairwise
tests. Report **Holm–Bonferroni-adjusted** p-values across the family, and state
both raw and adjusted. Holm rather than Bonferroni: uniformly more powerful, no
extra assumptions. Without correction, α=0.05 across 15 tests yields a >50%
chance of at least one false "winner" — which would be the same failure as the
old rule in the opposite direction.

**Effect size, always reported alongside p:** the median paired difference in
reciprocal rank, with a 95% bootstrap CI (10,000 resamples) **on that paired
difference**. Bootstrap CIs stay in the protocol; they are demoted from a
significance gate to what they are good at — describing magnitude. A
statistically significant but tiny effect is a real possible outcome and must be
visible as such.

**Pre-registered:** n=30 (Set A) + n=10 (Set B) is small, and Set B in
particular can only detect large effects. Whatever the run returns is reported.
"No significant difference" remains a legitimate finding — but now it is one the
data can actually fail to produce.

## 6. Decision rule — written down BEFORE seeing results

Fixed in advance so the outcome cannot be rationalized after the fact.
"Beats" below means: **Wilcoxon signed-rank, Holm-adjusted p < 0.05** (§5).

1. **If no lane beats BGE** → keep BGE. Cheapest, smallest, already shipped.
   Record "no significant difference at n=40".
2. **If `bge-asym` beats `bge`** → ship the query prefix. This would retract the
   §0 regression finding on better evidence, and the retraction gets stated
   plainly on GH-81 rather than quietly dropped.
   **If `bge` beats `bge-asym`**, the §0 finding is confirmed and BGE's own
   documented recipe is recorded as not applying to this corpus.
3. **If Qwen beats BGE** → report the effect size against the 2.7× storage and
   the slower embed pass. Recommend reverting GH-81 only if the **median paired
   reciprocal-rank gain exceeds 0.05 and its 95% CI excludes 0**. Below that,
   the migration stands and the result is logged as "real but not worth the
   cost".
   *The 0.05 threshold is a judgement call, not a derived constant* — it is
   roughly the difference between a target sitting at rank 1 vs rank 2 on one
   query in ten. It is fixed here, before results, so that it constrains the
   conclusion instead of being chosen to fit one.
4. **If Gemini wins** → it does **not** automatically ship. A hosted embedder
   makes semantic search network- and quota-dependent and sends corpus content
   off-device: a change to the product's local-first premise, not a config
   change. Record the effect size; escalate the trade-off to the operator as a
   separate decision.
5. **Is the semantic index earning its cost at all?** Two separate checks, and
   either firing supersedes every other finding in this run — report it first:
   - **5a (overall):** if no embedding lane beats the `fts` lane over the *full*
     query set (Wilcoxon, Holm-adjusted p < 0.05), the index is not buying
     retrieval quality over plain keyword search on this corpus.
   - **5b (`lexical-hard`):** if the best embedding lane's MRR@10 on the
     `lexical-hard` subset is **< 0.10**, the index is not recovering the
     queries FTS cannot reach — which is the specific capability it exists to
     add.

   *Note the asymmetry, which an earlier draft got wrong:* FTS cannot "win" on
   `lexical-hard` — that subset is **defined** as FTS's top-50 missing the
   target, so `fts` scores exactly 0 there by construction. The only meaningful
   question on that subset is whether the embedding lanes clear an absolute
   floor, not whether they beat a baseline that is pinned at zero. Comparisons
   against `fts` are therefore only valid on the full set (5a) or the
   `lexical-easy` subset.
6. **If >20% of the authored queries fail the §4.2 gate**, the query set itself
   is invalid: abort the run and rebuild it. The gate is a pre-run check on
   (query, target) pairs and is independent of any lane, so it cannot be
   "failed by a lane".

Rules 2, 3 and 5 each name an outcome that would embarrass a prior decision
(the GH-81 migration, the §0 prefix finding, the semantic index itself). That
is deliberate: a decision rule with no losing branch for the incumbent is not a
decision rule.

## 7. Artifacts produced

- `temp/bakeoff/` — sidecars (gitignored; regenerable)
- `temp/bakeoff/queries.json` — the frozen query set with targets and set labels
- `temp/bakeoff/results.json` — per-query, per-lane ranks (raw, auditable)
- A results table + written finding posted to **GH-81**
- If the decision rule fires (2), (3), or (4): a follow-up issue, not a
  same-branch code change

Raw per-query ranks are published, not just the aggregates, so any conclusion
here can be independently rechecked.

## 8. Explicitly out of scope

Named so they do not resurface mid-run:

- Reranking, hybrid lexical+vector fusion, query expansion
- Chunking strategy changes (the corpus is chunked as the live index chunks it)
- Fine-tuning any model on rebalanceOS content
- `embeddinggemma-300m`, `snowflake-arctic-embed-xs`, `all-MiniLM-L6-v2` —
  present in the HF cache but not requested
- Any change to production code. This protocol writes to `temp/bakeoff/` only.

## 9. Known threats to validity — the honest list

1. **Downsampled corpus (§3.2)** — absolute scores inflated; ordering claimed, magnitudes not.
2. **Single query author for Set A (§4.1)** — one phrasing style; Set B bounds it but does not remove it.
3. **Small n (§5)** — mitigated by paired testing, not eliminated. n=40 can only detect moderate-to-large effects; a true small difference will read as "no significant difference". This protocol cannot distinguish "no effect" from "an effect too small for n=40", and must not claim to.
4. **Ground truth is single-target** — real queries often have several valid answers. A model retrieving a *different but equally correct* doc is scored as a miss. This penalizes all lanes equally but depresses every absolute number.
5. **One machine, one run** — no cross-device or repeat-run variance measured. Embedding is deterministic per model, so re-run variance should be ~0 for the local lanes; Gemini's API is not guaranteed to be.
6. **The author of this protocol also authors the queries, runs it, and reports it.** There is no blinding anywhere in the chain. The mitigations are procedural only: the decision rule (§6) and query set are frozen before any lane is scored, and raw per-query ranks are published (§7) so the conclusion can be independently rechecked. This is the largest unaddressed threat in the list and is named rather than mitigated.
7. **Truncation is now per-lane (§3.3)**, so lanes see different amounts of text on the ~11% of docs over 2,000 chars. This is intentional — it reflects production — but it means a Qwen/Gemini win on long documents is a win on *context length*, not necessarily on embedding quality. The no-truncation-subset analysis (§3.3) exists to separate those two, and any headline claim must cite which one it rests on.

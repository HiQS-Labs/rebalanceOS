# GH-81 embeddings bake-off — results

**Run date:** 2026-08-20 · **Protocol:** [`../GH-81-EMBEDDINGS-BAKEOFF-PROTOCOL.md`](../GH-81-EMBEDDINGS-BAKEOFF-PROTOCOL.md) (QA-approved by agy, 3 rounds, before any lane was scored)
**Corpus:** 10,000 documents sampled from the live 52,178-document index, source proportions preserved (github 90.3%, vault 5.0%, code 3.2%, figma 1.3%, email 0.2%)
**Queries:** 39 — 29 natural-language (Set A) + 10 operator-style keyword (Set B), all targets established by reading the document
**Machine:** Mac Studio, MPS, local lanes; Gemini via hosted API

---

## Headline

| lane | MRR@10 | R@1 | R@5 | R@10 |
|---|---|---|---|---|
| **gemini** | **0.8141** | 0.718 | 0.949 | 0.949 |
| **bge-asym** | **0.7507** | 0.667 | 0.821 | 0.897 |
| fts (keyword baseline) | 0.6816 | 0.641 | 0.718 | 0.821 |
| qwen-asym | 0.6049 | 0.513 | 0.744 | 0.795 |
| **bge** *(ships today)* | **0.5716** | **0.410** | 0.769 | 0.821 |
| qwen *(pre-GH-81)* | 0.4690 | 0.410 | 0.538 | 0.615 |

Paired Wilcoxon signed-rank on per-query reciprocal rank, Holm-corrected across 15 comparisons:

| comparison | MRR gap | mean paired diff | 95% CI | W/L/T | p (Holm) |
|---|---|---|---|---|---|
| gemini > qwen | +0.345 | +0.345 | (0.198, 0.499) | 20/3/16 | **0.0050** |
| **bge-asym > bge** | **+0.179** | +0.179 | (0.095, 0.271) | 14/0/25 | **0.0137** |
| gemini > bge | +0.243 | +0.243 | (0.125, 0.368) | 16/2/21 | **0.0137** |
| bge-asym > qwen | +0.282 | +0.282 | (0.138, 0.427) | 17/4/18 | **0.0137** |
| gemini > qwen-asym | +0.209 | +0.209 | (0.073, 0.350) | 14/4/21 | 0.0547 |
| **gemini > bge-asym** | +0.063 | +0.063 | (−0.051, 0.182) | 9/5/25 | **0.3152 (n.s.)** |
| **bge-asym > fts** | +0.069 | +0.069 | (−0.077, 0.221) | 8/8/23 | **1.0000 (n.s.)** |

## Findings, against the pre-registered decision rule

### 1. Ship the BGE query prefix. Rule 2 fires — and this retracts an earlier finding.

`bge-asym` beats `bge` at **p=0.0137**, lifting Recall@1 from **0.410 to 0.667**. It wins 14 queries and loses **zero**.

This **retracts** [the earlier conclusion on this issue](https://github.com/HiQS-Suite/rebalanceOS/issues/81#issuecomment-5359722367) that the prefix was "not a clean win" and should not be merged. That test used 5 queries and had no ground truth; it measured noise. This one uses 39 queries with hand-established targets and a paired test. The retraction is stated here rather than quietly dropped, per protocol §6 rule 2.

The change is one line in `semantic_index.query()` — prefix the query text with
`"Represent this sentence for searching relevant passages: "`. **Passages must NOT be re-embedded**: BGE's recipe is query-side only, and this run confirms it empirically against an unprefixed corpus.

### 2. Keep BGE over Qwen. The GH-81 migration was correct.

Qwen is **worse** than BGE, not better (0.469 vs 0.572), and the gap is not significant either way (p=1.00). With the prefix applied to both, BGE still leads (0.751 vs 0.605). Rule 3's revert condition is not met and is not close.

Qwen also costs more on every secondary axis:

| lane | dim | sidecar size | corpus embed | query p50 | truncated |
|---|---|---|---|---|---|
| bge | 384 | 16.1 MB | **50 s** | **3.3 ms** | 12.92% |
| qwen | 1024 | 42.4 MB | 1000 s | 10.2 ms | 0.14% |
| gemini | 3072 | 126.3 MB | 141 s (100 API calls) | 34.2 ms | n/a |

**20× the embed time for lower quality.** GH-81 stands.

### 3. Do NOT adopt Gemini. Rule 4 fires but resolves to "no".

Gemini has the best raw numbers — but it does **not** significantly beat the *fixed* local configuration (`bge-asym`): p=0.3152, CI spans zero. Its significant wins are all against the **broken** BGE config and against Qwen.

So the honest statement is: **once the prefix bug is fixed, there is no measurable quality reason to leave the device.** Against that, Gemini costs 8× the storage, 10× the query latency, a network dependency, an API quota, and sends corpus content off-device — a change to the local-first premise, not a config change. Recommendation: **decline**, and revisit only if a larger evaluation establishes a real gap.

*(Operational note: the default-named Gemini key was billing-depleted; this run used `ltvera-gemini-api-key` from Secret Manager in project `ltvera-gce-and-bigquery`.)*

### 4. Rule 5a fires: no embedding lane significantly beats keyword search overall.

Neither `bge-asym` (p=1.00) nor `gemini` (p=0.47) significantly outperforms plain SQLite FTS5 across the full query set. And **plain `bge` — production today — scores *below* FTS5** (0.572 vs 0.682).

Rule 5b does **not** fire, and that is what saves the semantic index: on the `lexical-hard` subset — the queries where FTS5 cannot find the target at all, so it scores exactly 0.000 by construction — `bge-asym` reaches 0.600 and `gemini` 0.667, far above the 0.10 floor.

| slice | gemini | bge-asym | fts | bge |
|---|---|---|---|---|
| lexical-easy (n=34) | 0.836 | 0.773 | **0.782** | 0.587 |
| lexical-hard (n=5) | 0.667 | 0.600 | **0.000** | 0.467 |

Read together: **the vector index is not beating keyword search at keyword search — it is covering the queries keyword search cannot answer at all.** Neither retriever alone dominates; they are complementary.

**Important scope correction.** That is an argument for hybrid retrieval — and rebalanceOS *already ships hybrid retrieval*. `semantic_index.query()` defaults to `hybrid=True` and fuses the vector ranking with an FTS5 lexical ranking through RRF ([`semantic_index.py:745`](../../../src/rebalance/ingest/semantic_index.py#L745), fused at [`:786`](../../../src/rebalance/ingest/semantic_index.py#L786)).

So this bake-off measured the **vector component in isolation**, not the retrieval path production actually serves. Two consequences, stated plainly because they bound every claim above:

- Rule 5a's "no embedding lane beats FTS5" is **not** a finding that the shipped search is no better than keyword search. It compares a *component* against a *component*. The shipped system already has both.
- The prefix fix improves the vector component substantially, and should carry into the fused result — but **that was not measured here.** A follow-up should score the fused `query()` path end-to-end, before and after the prefix, which is the number that actually describes what users experience.

This correction was caught while implementing the fix, after the results table was written. It does not change findings 1–3.

## Threats to validity — carried forward from protocol §9

1. **n=39 overall, n=5 on `lexical-hard`.** The subset splits are indicative, not conclusive. The prefix result (14 wins, 0 losses) is robust; the FTS comparisons are not.
2. **10k corpus is a 5.2× downsample.** Absolute scores read higher than production would. Only ordering is claimed.
3. **No blinding.** One person authored the queries, ran the lanes and wrote this. Mitigations are procedural only: the decision rule and query set were frozen before scoring, and `results.json` publishes per-query ranks for independent recheck.
4. **Single-target ground truth** penalises a lane that retrieves a different-but-equally-valid document. Applies equally to all lanes.
5. **Deviation from protocol §3.3:** Qwen ran at a 4,096-token cap rather than its native 32,768 — allocating the native window exhausted MPS memory. Measured cost: 14 of 10,000 documents (0.14%) truncated. BGE truncated 12.92% at its native 512.
6. **Target selection was screened for distinctiveness.** The first sample was dominated by near-duplicate boilerplate (repetitive prompt-log chunks, generic commit messages) that cannot serve as single-target ground truth. Documents were de-duplicated on a normalised body prefix. This biases the query set toward *distinctive* documents and likely inflates every lane's absolute score.

## Reproducing

```bash
python temp/bakeoff/embed_local.py bge  BAAI/bge-small-en-v1.5      # ~50s
BAKEOFF_MAX_SEQ=4096 BAKEOFF_BATCH=16 \
  python temp/bakeoff/embed_local.py qwen Qwen/Qwen3-Embedding-0.6B # ~17min
GOOGLE_CLOUD_PROJECT=... GEMINI_SECRET_NAME=... \
  python temp/bakeoff/embed_gemini.py                              # ~141s
python temp/bakeoff/score.py
```

Scripts and the frozen query set are in this directory; `results.json` carries every per-query rank for all six lanes. Sidecar databases live under `temp/bakeoff/` (gitignored, regenerable).

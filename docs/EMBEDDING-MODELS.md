# Embedding models — naming, identity, and current configuration

Canonical reference for which embedding model this repo uses and how to name it
without ambiguity. Written because the short forms genuinely confuse people: "is
this BGE-Small or is it v1.5?" is a reasonable question with a counter-intuitive
answer, and the answer is **both, they are different axes**.

## Current configuration

| | value | source of truth |
|---|---|---|
| **Model** | **`BAAI/bge-small-en-v1.5`** | [`embedder.py:97`](../src/rebalance/ingest/embedder.py#L97) (`DEFAULT_MODEL`) |
| **Dimensions** | 384 | `embedder.py` (`EMBEDDING_DIM`), and the `vec0(embedding float[384])` declarations in [`db/schema.py`](../src/rebalance/ingest/db/schema.py) |
| **Context window** | 512 tokens | model config |
| **Parameters** | 33.4M | BGE model card |
| **Runtime** | `sentence-transformers` | [`pyproject.toml`](../pyproject.toml) `embeddings` extra |
| **Query prefix** | `"Represent this sentence for searching relevant passages: "` | [`semantic_index.py`](../src/rebalance/ingest/semantic_index.py) (`BGE_QUERY_INSTRUCTION`) — **query side only** |

`EMBEDDING_DIM` and the `float[N]` in the vec0 table declarations must always
agree. If they diverge, every embedding insert fails with `Dimension mismatch`.

## Reading the model name

`BAAI/bge-small-en-v1.5` encodes **four independent axes**. Dropping any one of
them creates ambiguity:

```
BAAI  /  bge  -  small  -  en  -  v1.5
 │        │       │        │      │
 │        │       │        │      └── release version: v1 (Aug 2023) or v1.5 (Sep 2023)
 │        │       │        └───────── language: en | zh
 │        │       └────────────────── size tier: small (33.4M) | base (109M) | large (335M)
 │        └────────────────────────── family: BAAI General Embedding
 └─────────────────────────────────── publisher / HF org
```

**"small" is the size tier. "v1.5" is the release version.** They are orthogonal —
`bge-small-en-v1.5` is the small tier *of* the v1.5 release. There is also a
`bge-small-en` (v1, older) and a `bge-large-en-v1.5` (bigger, same release).

So the answer to "is it the small one or the v1.5 one?" is **yes**.

### Do not write these

| ✗ ambiguous | ✓ use instead |
|---|---|
| "BGE" | `BAAI/bge-small-en-v1.5` |
| "BGE-Small" | `BAAI/bge-small-en-v1.5` |
| "bge v1.5" | `BAAI/bge-small-en-v1.5` |
| "the embedding model" | `BAAI/bge-small-en-v1.5` (384-dim) |
| "the 384-dim model" | `BAAI/bge-small-en-v1.5` |

Bare `BGE` is acceptable **only** as a possessive referring to the publisher's own
material ("BGE's model card", "BGE's documented recipe"), where no specific
checkpoint is being identified.

`bge`, `bge-asym`, `qwen` etc. in
[`TESTS-RESULTS/`](../TESTS-RESULTS/) are **lane identifiers** for a specific
experiment, not model names. Each campaign's `SUMMARY.md` maps them to full repo
IDs.

## Verifying identity from ground truth

Never repeat a model name from memory or from a doc. Check all three; they should
agree:

```bash
# 1. what the code declares
grep -n "DEFAULT_MODEL" src/rebalance/ingest/embedder.py

# 2. what a recorded run actually used
sqlite3 <sidecar>.db "select key,value from meta where key in ('model','dim')"

# 3. what is on disk
ls ~/.cache/huggingface/hub/ | grep bge
```

**Known trap:** the downloaded v1.5 snapshot's `config.json` contains
`"_name_or_path": "/root/.cache/torch/sentence_transformers/BAAI_bge-small-en/"` —
**without** the `v1.5` suffix. That is a training-time cache path baked in when
v1.5 was initialised from v1. It is not the model identity. **The HuggingFace repo
ID governs.**

## The query prefix, and why it contradicts the vendor

BGE's retrieval recipe is **asymmetric**: prefix the *query*, leave the *passage*
alone. This repo applies it on the query path only
([`semantic_index.py`](../src/rebalance/ingest/semantic_index.py)); passages are
embedded raw. That asymmetry is load-bearing — prefixing passages would require a
full reindex and is not what the recipe says.

Note the tension, because it will otherwise be rediscovered as a "bug":
[BGE's documentation](https://bge-model.com/bge/bge_v1_v1.5.html) states v1.5 was
released to *"enhance its retrieval ability **without** instruction"* — i.e. the
vendor's position is that v1.5 needs the prefix **less** than v1 did.

We use it anyway, because it was **measured on this corpus** and won decisively:

> MRR@10 0.5716 → 0.7507 · Recall@1 0.410 → 0.667 · 14 queries improved, 0 regressed, p=0.0137 (Holm-corrected)

Without it, this configuration scored *below* a plain SQLite FTS5 baseline.

"Needs it less" is not "does not benefit from it", and v1.5's headline improvement
was measured on MTEB-style benchmarks rather than a 90%-GitHub engineering corpus
queried in natural language. But the honest framing is that **this is an empirical,
corpus-local result, not a vendor-endorsed default.** Anyone porting it elsewhere
should re-measure.

Full run, threats to validity, and per-query records:
[`TESTS-RESULTS/2026-08-20+GH-81/`](../TESTS-RESULTS/2026-08-20+GH-81/).

## History

| when | model | dim | why it changed |
|---|---|---|---|
| pre-GH-81 | `Qwen/Qwen3-Embedding-0.6B` | 1024 | — |
| GH-81 (2026-08) | `BAAI/bge-small-en-v1.5` | 384 | Qwen used 1.2+ GB RAM and hit memory-compressor ceilings; the replacement uses ~20 MB |
| GH-81 bake-off (2026-08-20) | *(unchanged)* | 384 | Measurement **confirmed** the migration: Qwen scored *worse*, not better (MRR@10 0.469 vs 0.572), at 20× the embed time. Also added the query prefix, and declined hosted Gemini. |

Changing the model is a **data migration**, not a config change: the vec0 tables
are declared at a fixed width, so a dimension change requires dropping and
rebuilding them and clearing `embedded_hash` so documents re-embed. See the
migration guards in [`db/schema.py`](../src/rebalance/ingest/db/schema.py) and
their regression tests in
[`tests/test_schema_dim_migration.py`](../tests/test_schema_dim_migration.py) —
that path shipped broken once already.

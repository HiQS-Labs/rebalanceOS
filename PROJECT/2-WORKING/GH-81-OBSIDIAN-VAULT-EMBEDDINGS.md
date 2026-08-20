---
title: "Refactor & Rename vault-sync to obsidian-vault-embeddings + Lightweight Embeddings"
status: "Completed"
created: 2026-08-19
updated: 2026-08-19
owner: noel
goal: "Accurate operator-facing naming (obsidian-vault-embeddings), pipeline decoupling, and switching to lightweight 384-dim BGE-Small model to eliminate memory pressure failures."
gh_issue: 81
related: [31, 250, 198, 82]
effort: 2
complexity: 2
risk: 2
phases: 3
ratings_provisional: false
roadmap_exempt: false
---

# GH-81 — Refactor & Rename 'vault-sync' to 'obsidian-vault-embeddings' + Lightweight Embedding Engine

## Status

| What was just completed | What's next |
|---|---|
| Phase 1, 2, & 3 complete: Migrated embedding engine to `BAAI/bge-small-en-v1.5` (384-dim, +20MB RAM, 7.3ms latency); rebuilt `sqlite-vec` tables (`embeddings`, `semantic_embeddings`, `github_embeddings`); renamed `vault-sync` to `obsidian-vault-embeddings` across launchd, plist templates, shell scripts, and docs; re-embedded 51,770 semantic documents cleanly in 251s (~4.8ms/doc); full pytest suite (1,919 passed) and `rebalance doctor` green. | Monitor hourly `obsidian-vault-embeddings` scheduled runs. |

## Quad Concepts
- Inaccurate job name (`vault-sync`) hiding a heavy neural embedding workload → rename launchd job, plist, and scripts to `obsidian-vault-embeddings`.
- `Qwen3-Embedding-0.6B` taking 1.2+ GB RAM and failing on memory compressor ceilings (>16GB) → replace with `BAAI/bge-small-en-v1.5` taking ~20MB RAM (98% reduction).
- Fast markdown parsing (~0.02s) coupled to neural vector model loading → decouple file ingest from vector embedding pass.
- 1024-dim vector tables consuming gigabytes of SQLite storage → migrate to 384-dim `sqlite-vec` tables, reclaiming ~62% vector disk space.

## Table of contents
1. [Phase 0 — Prior Art & Empirical Spike Findings](#phase-0--prior-art--empirical-spike-findings)
2. [Phase 1 — Embedding Engine Migration (`Qwen/Qwen3-Embedding-0.6B` → `BAAI/bge-small-en-v1.5`)](#phase-1--embedding-engine-migration-qwenqwen3-embedding-06b--baaibge-small-en-v15)
3. [Phase 2 — Scheduler & Process Renaming (`vault-sync` → `obsidian-vault-embeddings`)](#phase-2--scheduler--process-renaming-vault-sync--obsidian-vault-embeddings)
4. [Phase 3 — Database Vector Migration & End-to-End Verification](#phase-3--database-vector-migration--end-to-end-verification)

---

## Phase 0 — Prior Art & Empirical Spike Findings

### Spike Results (Measured 2026-08-19 on Host)
A live benchmark was conducted using Hugging Face sentence-transformers on Apple Silicon:

| Model | Parameters | Output Dim | RAM Footprint Delta | Latency | Query Separation Quality |
|---|---|:---:|:---:|:---:|---|
| **`BAAI/bge-small-en-v1.5`** | ~33M | **384** | **+20.3 MB** | **7.3 ms/text** | **Excellent** (Target: `0.8227`, Irrelevant: `0.4654`) |
| **`google/embeddinggemma-300m`** | ~300M | **768** | +1,460 MB *(fp32)* | 171.3 ms/text | High (Target: `0.6439`), but gated on HF and heavy in PyTorch |
| **`sentence-transformers/all-MiniLM-L6-v2`** | ~22M | **384** | +119.2 MB | 138.5 ms/text | High (Target: `0.5585`, Irrelevant: `-0.0290`) |
| **`Snowflake/snowflake-arctic-embed-xs`** | ~22M | **384** | +72.8 MB | 18.3 ms/text | Very High, but tight clustering |
| *Current Baseline: `Qwen3-Embedding-0.6B`* | ~600M | *1024* | *~1,200 MB* | *~120 ms/text* | *Baseline reference* |

### Selection Decision
`BAAI/bge-small-en-v1.5` is selected as the primary embedding model:
1. **Memory:** ~20MB RAM footprint avoids tripping `job_guard` memory ceiling.
2. **Speed:** 7.3ms latency is 16x faster than Qwen3.
3. **Headless Reliability:** 100% open, ungated model requiring no Hugging Face API tokens in launchd environments.
4. **Storage:** 384 dimensions reduces SQLite vector index bloat by 62.5%.

---

## Phase 1 — Embedding Engine Migration (`Qwen/Qwen3-Embedding-0.6B` → `BAAI/bge-small-en-v1.5`)

- [x] Update `src/rebalance/ingest/embedder.py`:
  - Replace `mlx-embeddings` Qwen loader with `SentenceTransformer("BAAI/bge-small-en-v1.5")`.
  - Update `DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"` and `EMBEDDING_DIM = 384`.
  - Ensure model is loaded lazily on first query/embed call.
- [x] Update `src/rebalance/ingest/db/schema.py` and `ensure_semantic_schema()`:
  - Migrate `semantic_embeddings` and `github_embeddings` virtual tables from `float[1024]` to `float[384]`.
  - Bump `embedder_version` in `semantic_embedding_meta` to trigger a clean re-embedding pass.

### QA Gate 1
- `pytest tests/test_embedder.py tests/test_semantic_index.py` passes (100%).
- Generating embeddings for test text produces a 384-dimensional vector in <10ms with <50MB RAM delta.

---

## Phase 2 — Scheduler & Process Renaming (`vault-sync` → `obsidian-vault-embeddings`)

- [x] Rename script and templates:
  - `scripts/vault_sync.sh` → `scripts/obsidian_vault_embeddings.sh`
  - `scripts/com.rebalance-os.vault-sync.plist.template` → `scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template`
- [x] Update [SCHEDULER.md](../../SCHEDULER.md), [ARCHITECTURE.md](../../ARCHITECTURE.md), and `scripts/stack.sh`:
  - Change job label from `vault-sync` to `obsidian-vault-embeddings`.
  - Update installer `scripts/install_obsidian_vault_embeddings_scheduler.sh`.
  - Unload old `com.rebalance-os.vault-sync` and load `com.rebalance-os.obsidian-vault-embeddings`.
- [x] Decouple fast file ingest (`rebalance ingest notes`) from neural vector embedding pass if memory guard is active.

### QA Gate 2
- `bash scripts/stack.sh verify` and `bash scripts/stack.sh status` show `obsidian-vault-embeddings` managed and active.
- `tests/test_scheduler_policy.py` passes with 100% agreement (18/18).

---

## Phase 3 — Database Vector Migration & End-to-End Verification

- [x] Run initial re-embedding pass with `BAAI/bge-small-en-v1.5` over existing `semantic_documents` (51,770 documents embedded in 251s).
- [x] Verify `semantic_query` MCP tool and CLI `rebalance query` return accurate, ranked results.
- [x] Run `rebalance doctor` and verify `launchd:obsidian-vault-embeddings` and vector health are green.


### QA Gate 3
- `rebalance doctor` passes with zero embedding memory errors.
- `pytest tests/` full suite green.

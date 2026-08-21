---
title: Pluggable embeddings — remove the hardcoding, stage the provider layer
status: Plan — drafted, pending review (GH-97)
gh_issue: 97
created: 2026-08-20
branch: feat/gh97-pluggable-embeddings
supersedes: []
goal: >
  Make the embedding model and its dimension configurable and self-consistent, so a model
  swap is a setting rather than a seven-site edit — without building a provider registry
  for the one provider that exists.
---

# GH-97 — pluggable embeddings

## 0. The one-paragraph version

Dimension is a hand-maintained constant that must agree with three DDL literals and three
string guards, and nothing enforces that agreement — it has already caused one
production-class defect. The query prompt is chosen by substring-matching the model name,
so an unrecognised model silently loses a **0.18 MRR** effect with no error. There is no
operator-facing setting for any of it.

**Phase 1 fixes exactly those three things and nothing else.** A provider abstraction is
deliberately *not* in Phase 1, because there is one provider.

## 1. Verified inventory — checked, not remembered

Against `development` @ `ddd6fec`:

| # | site | pins |
|---|---|---|
| 1 | `ingest/embedder.py:98` | `EMBEDDING_DIM = 384`, used at `:150` |
| 2 | `ingest/embedder.py:97` | `DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"` |
| 3 | `ingest/db/schema.py:85,167,597` | three `vec0(... float[384])` DDLs |
| 4 | `ingest/db/schema.py:75,155,586` | three guards vs the literal `"384"` |
| 5 | `ingest/semantic_index.py:109` | `if "bge" in model_name.lower()` — prompt gate |
| 6 | `doctor.py:2083` | `f"{DEFAULT_MODEL}|{EMBEDDING_DIM}"` |
| 7 | `ingest/github_knowledge.py:29`, `ingest/semantic_index.py:25` | re-export `DEFAULT_MODEL` |

Three separate vector tables carry the dimension: `embeddings`, `semantic_embeddings`,
`github_embeddings`.

**Existing machinery to reuse, not reinvent:**
- `SentenceTransformer.get_sentence_embedding_dimension()` — verified present. Dimension
  need not be a constant at all.
- `ingest/config.py` — `_read_config()`, `_write_config()`, `_resolved_config_path()`. A
  setting already has a home.
- `embed_pending(..., embed_texts=)` and `query(..., embed_texts=)` — an injection seam
  **already exists** and already drove six models through one code path in the GH-81
  bake-off. Any future provider work starts here; it does not need a new seam.

## 2. What this plan deliberately does NOT build

Applying the lazy-senior lens, in order:

**A provider registry / plugin protocol — skipped.** There is exactly one provider
(local `sentence-transformers`). An interface with one implementation is a cost with no
payer. The `embed_texts` seam already covers the "run a different embedder" case, and it
has been exercised in anger. **Add the protocol when a second provider actually lands, and
let its real requirements shape it** — rather than guessing them now and discovering the
guess was wrong.

**A hosted-provider implementation — skipped, and it is not one afternoon.** It needs API
keys, rate limits, retries, batching, cost accounting, and an offline story. It also sends
vault and email content off-machine, which is a **product decision for a local-first
tool**, not an engineering one. Out of scope here; it needs its own issue and an operator
decision.

**Runtime multi-model support — skipped.** One index, one model. Supporting two
simultaneously means per-row model tagging and per-model tables. No demand exists.

**Auto-migration on dimension change — skipped.** See §4: a dimension change means
re-embedding tens of thousands of documents. That must be an explicit, operator-initiated
act with a visible cost, never something a config edit triggers silently on next boot.

## 3. Phase 1 — the whole of the near-term work

### 3.1 Derive dimension from the model

Replace the `EMBEDDING_DIM` constant with a value read from the loaded model
(`get_sentence_embedding_dimension()`), cached alongside the model in `_load_model()`.

The DDL then interpolates that value rather than a literal. **One source of truth**:
model → dimension → DDL → meta row. The three guards compare against the derived value
instead of `"384"`.

> **Why this is the highest-value item.** The GH-81 defect was not a typo — the guard
> `if row and str(row[0]) != "384"` never fired on an existing database, so the meta row
> was stamped 384 while a 1024-wide table stayed in place, producing
> `Dimension mismatch: expected 1024, received 384` and permanently broken search. The
> class of bug is *"two places must agree and nothing checks"*. Deriving removes the class,
> not just the instance.

### 3.2 Explicit per-model prompt mapping

Replace the substring gate with a literal mapping, model id → query prefix:

```python
QUERY_PROMPTS = {
    "BAAI/bge-small-en-v1.5": "Represent this sentence for searching relevant passages: ",
}
```

**An unknown model must not silently fall through to "no prompt".** It raises, or the
operator adds an explicit `None` entry meaning "this model takes no prompt". Silence is
the failure mode being removed: the prefix is worth 0.5716 → 0.7507 MRR@10 (p=0.0137) on
our corpus, and losing it produces no error — only worse results, invisible until someone
measures. We have just deferred measuring (#94), so the guard has to be structural.

Passages still get no prompt. That asymmetry is already pinned by
`tests/test_semantic_query_prefix.py` and must stay pinned.

### 3.3 Config knob

Read the model id from existing config (`_read_config()`), defaulting to the current value
when unset. No new config system, no new file, no env-var scheme.

`doctor` reports the configured model, the derived dimension, and the dimension actually
declared in each of the three vector tables — so a disagreement is *visible* rather than
latent.

## 4. Dimension change — an explicit path, not an automatic one

Changing the configured model to a different dimension is a **data migration**: three
`vec0` tables dropped and rebuilt, `embedded_hash` cleared, ~52,000 documents re-embedded.

The plan is deliberately blunt here:

- On detecting configured-dimension ≠ stored-dimension, **refuse to run** and print the
  exact command to migrate. Do not migrate implicitly.
- The migration is one command, it states up front how many documents will be re-embedded,
  and it is resumable — `embedded_hash IS NULL` already makes the embed pass resumable, so
  a killed run continues rather than restarting.
- Re-embedding is the expensive part and it is unavoidable: **vectors from different
  models are not comparable and cannot be converted.** Any plan implying otherwise is
  wrong.

## 5. Tests — one per failure mode that has actually happened or is silent

1. **Dimension agreement.** Given a stub model of dimension N, the DDL, the meta row, and
   the derived constant all report N. Fails if any two can disagree. *(This is the GH-81
   defect as a test.)*
2. **Pre-existing database, changed dimension.** Build a database at dimension A, switch to
   a model of dimension B, assert a clear refusal — **not** a silent stamp and **not** a
   mismatch at query time. *(The exact GH-81 scenario.)*
3. **Unknown model prompt.** A model id absent from `QUERY_PROMPTS` raises rather than
   silently returning the raw query.
4. **Asymmetry preserved.** Queries get the prompt, passages do not, FTS gets raw text.
   Already covered by `test_semantic_query_prefix.py`; must not regress.

No new test framework, no fixtures beyond a stub embedder.

## 6. Risks

1. **`get_sentence_embedding_dimension()` requires loading the model, and several schema
   call sites have no model loaded.** Verified: `query()` loads the model *before*
   `ensure_semantic_schema` (`semantic_index.py:796` then `:800`), so that path is fine —
   but `index_ops.py:525`, `note_ingester.py` and `github_knowledge.py` all ensure schema on
   paths that need not embed anything. Forcing a model load there would put a multi-hundred-MB
   import behind an ordinary ingest, which is a real regression.

   *Mitigation:* read the dimension from the stored meta row when present; require the model
   only when creating a vector table for the first time. **This is the main design constraint
   and the reviewer should attack it** — if it does not hold, §3.1 needs rework. The
   fallback, if it fails, is to keep an explicit configured dimension and *validate* it
   against the model at embed time rather than deriving it — worse, but still removes the
   silent-disagreement class.
2. **Three tables, three call sites.** `ensure_schema`, `ensure_semantic_schema` and
   `_ensure_github_knowledge_schema` each own a dimension. Deriving in one and not the
   others reintroduces the same class of bug in a new place.
3. **Config drift against a live index.** An operator edits the model in config; the index
   still holds old vectors. §4's refusal covers it, but the error must name the fix.
4. **Scope creep into the provider layer.** The most likely failure of this plan is that it
   grows a registry nobody asked for. If Phase 2 starts appearing in Phase 1 review
   comments, that is the signal to stop and split.

## 7. Definition of done

- `EMBEDDING_DIM` no longer exists as a hand-maintained constant.
- No `float[384]` or `"384"` literal remains in `schema.py`.
- Query prompt comes from an explicit mapping; unknown model is an error.
- Model id is settable through existing config; current value is the default.
- Dimension mismatch refuses with an actionable message and a named migration command.
- The four tests in §5 pass, and test 2 fails against today's code.
- No provider protocol, no registry, no hosted implementation.

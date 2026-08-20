"""GH-81 — BGE's query-side instruction prefix is applied, and only there.

The prefix lifted MRR@10 from 0.5716 to 0.7507 (Recall@1 0.410 -> 0.667) in the
GH-81 bake-off: 14 queries improved, 0 regressed, p=0.0137 Holm-corrected. See
PROJECT/2-WORKING/GH-81-BAKEOFF/RESULTS.md.

Two things can silently undo that and neither would fail an existing test:
  * dropping the prefix from the query path (back to the measured-worse config);
  * leaking it onto the passage path or the FTS5 leg, where it is actively harmful.

These pin both directions.
"""

from __future__ import annotations

from rebalance.ingest.semantic_index import BGE_QUERY_INSTRUCTION, _query_embed_text


def test_bge_query_gets_the_instruction_prefix():
    out = _query_embed_text("how is the vault path resolved", "BAAI/bge-small-en-v1.5")
    assert out == BGE_QUERY_INSTRUCTION + "how is the vault path resolved"


def test_prefix_is_case_insensitive_on_the_model_name():
    """Model names arrive from config and env, not only from the constant."""
    for name in ("BAAI/bge-small-en-v1.5", "baai/BGE-Small-EN-v1.5", "BGE-large"):
        assert _query_embed_text("q", name).startswith(BGE_QUERY_INSTRUCTION), name


def test_non_bge_models_are_left_alone():
    """BGE's instruction is BGE's. Qwen has its own form; applying the wrong
    instruction is worse than applying none."""
    for name in ("Qwen/Qwen3-Embedding-0.6B", "sentence-transformers/all-MiniLM-L6-v2", ""):
        assert _query_embed_text("q", name) == "q", name


def test_query_path_prefixes_the_vector_but_not_the_fts_leg(tmp_path, monkeypatch):
    """The load-bearing boundary.

    `query()` runs two retrievers and fuses them with RRF. The prefix belongs to
    the embedding model, not to SQLite: handing FTS5 eight extra high-frequency
    words ("represent this sentence for searching relevant passages") injects
    terms that match nothing meaningful and degrades the lexical ranking that is
    about to be fused in. Assert the vector leg sees the prefix and the FTS leg
    sees the raw text.
    """
    from rebalance.ingest import semantic_index

    seen_embed: list[str] = []
    seen_fts: list[str] = []

    def fake_embed(texts, model_name):
        seen_embed.extend(texts)
        return [[0.0] * 384 for _ in texts]

    def fake_fts(conn, query_text, *a, **kw):
        seen_fts.append(query_text)
        return []

    monkeypatch.setattr(semantic_index.sem, "search_semantic_documents", lambda *a, **kw: [])
    monkeypatch.setattr(semantic_index.sem, "search_semantic_documents_fts", fake_fts)

    semantic_index.query(
        tmp_path / "t.db",
        "how is the vault path resolved",
        model_name="BAAI/bge-small-en-v1.5",
        embed_texts=fake_embed,
        hybrid=True,
    )

    assert seen_embed == [BGE_QUERY_INSTRUCTION + "how is the vault path resolved"]
    assert seen_fts == ["how is the vault path resolved"], (
        "FTS5 must receive the raw query — the instruction prefix is for the embedding model only"
    )

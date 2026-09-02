import sqlite3
from pathlib import Path
from rebalance.ingest.clio import ensure_clio_schema, clio_semantic_docs


def test_ensure_clio_schema(tmp_path: Path):
    conn = sqlite3.connect(tmp_path / "test.db")
    ensure_clio_schema(conn)
    # Ensure it doesn't crash on second run
    ensure_clio_schema(conn)

    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clio_prompts'").fetchall()
    assert len(rows) == 1
    conn.close()


def test_clio_semantic_docs(tmp_path: Path):
    conn = sqlite3.connect(tmp_path / "test.db")
    conn.row_factory = sqlite3.Row
    ensure_clio_schema(conn)

    conn.execute(
        "INSERT INTO clio_prompts (id, timestamp, session_id, prompt, agent, repo, synced_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("id1", "2026-08-31T21:26:07Z", "sess1", "hello world", "claude", "repo1", "now"),
    )

    docs = list(clio_semantic_docs(conn))
    assert len(docs) == 1
    assert docs[0].source_pk == "id1"
    assert docs[0].body == "hello world"
    assert docs[0].metadata["agent"] == "claude"

    conn.close()

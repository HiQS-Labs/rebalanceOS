import sqlite3
from pathlib import Path
from rebalance.ingest.clio import clio_semantic_docs, ensure_clio_schema, load_recent_clio_prompts


def test_ensure_clio_schema(tmp_path: Path):
    conn = sqlite3.connect(tmp_path / "test.db")
    ensure_clio_schema(conn)
    # Ensure it doesn't crash on second run
    ensure_clio_schema(conn)

    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clio_prompts'").fetchall()
    assert len(rows) == 1
    conn.close()


def test_load_recent_clio_prompts_is_bounded_and_time_filtered(tmp_path: Path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    ensure_clio_schema(conn)
    conn.executemany(
        "INSERT INTO clio_prompts (id,timestamp,session_id,prompt,agent,repo,synced_at) VALUES (?,?,?,?,?,?,?)",
        [
            ("old", "2026-09-12T10:00:00Z", "s1", "old", "claude", "one", "now"),
            ("new", "2026-09-12T12:00:00Z", "s2", "new", "codex", "two", "now"),
        ],
    )
    conn.commit()
    conn.close()

    rows = load_recent_clio_prompts(db, "2026-09-12T11:00:00Z", limit=1)
    assert [row["id"] for row in rows] == ["new"]


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

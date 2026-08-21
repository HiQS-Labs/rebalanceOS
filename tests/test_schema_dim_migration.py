"""GH-81 — the 1024 -> 384 embedding-dimension migration must fire on real databases.

The migration guards in `schema.py` read `embedding_dim` out of the `*_meta`
tables and drop the vec0 table when it disagrees with 384. The first version
read `if row and str(row[0]) != "384"`, which looks right and is exactly
backwards for the population it exists to serve:

  * pre-GH-81 `schema.py` created `semantic_embedding_meta` but only ever wrote
    `fts_version` into it — `embedding_dim` was never recorded;
  * so on every pre-existing database the SELECT returns None and `row` is
    falsy, and the drop was skipped precisely where a 1024-dim table was
    sitting there needing to be dropped;
  * `CREATE VIRTUAL TABLE IF NOT EXISTS ... float[384]` is a no-op against the
    surviving 1024-dim table, and the `INSERT OR IGNORE` then stamped the meta
    '384' — so the guard could never fire again on a subsequent run.

The end state was a database whose metadata claimed 384 while its vec0 table
was still 1024, where every embedding write failed with a dimension mismatch.
A fresh-database test cannot catch this: fresh databases have no meta table at
all and take the `except` path. The bug lives entirely in the upgrade path, so
these tests build the OLD schema shape explicitly and then upgrade it.
"""

from __future__ import annotations

import sqlite3
import struct

import pytest

from rebalance.ingest.db.schema import ensure_semantic_schema

sqlite_vec = pytest.importorskip("sqlite_vec")


def _connect(path):
    conn = sqlite3.connect(path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def _build_pre_gh81_db(path, dim=1024):
    """Reconstruct the schema shape a pre-GH-81 clone left on disk.

    Deliberately hand-rolled rather than imported from git history: the point is
    to pin the *shape* that existed in the wild — a meta table with no
    `embedding_dim` row, beside a vec0 table at the old dimension.
    """
    conn = _connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_documents (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type             TEXT    NOT NULL,
            source_table            TEXT    NOT NULL,
            source_pk               TEXT    NOT NULL,
            doc_kind                TEXT    NOT NULL,
            title                   TEXT,
            body                    TEXT    NOT NULL,
            content_hash            TEXT    NOT NULL,
            embedded_hash           TEXT,
            embedded_model_version  TEXT,
            embedded_at             TEXT,
            metadata_json           TEXT,
            created_at              TEXT    NOT NULL,
            updated_at              TEXT    NOT NULL,
            UNIQUE(source_type, source_pk)
        )
    """)
    conn.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS semantic_embeddings USING vec0(embedding float[{dim}])")
    conn.execute("CREATE TABLE IF NOT EXISTS semantic_embedding_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    # The old code wrote fts_version and nothing else. No embedding_dim row —
    # this single omission is what the original guard tripped over.
    conn.execute("INSERT OR REPLACE INTO semantic_embedding_meta (key, value) VALUES ('fts_version', '1')")
    conn.execute(
        "INSERT INTO semantic_documents "
        "(source_type, source_table, source_pk, doc_kind, body, content_hash, "
        " embedded_hash, embedded_model_version, embedded_at, created_at, updated_at) "
        "VALUES ('vault','chunks','1','note','hello','h1','h1','qwen3','t','t','t')"
    )
    conn.execute(
        "INSERT INTO semantic_embeddings(rowid, embedding) VALUES (1, ?)",
        (struct.pack(f"{dim}f", *([0.1] * dim)),),
    )
    conn.commit()
    return conn


def _vec_dim(conn, table):
    row = conn.execute("SELECT sql FROM sqlite_master WHERE name = ?", (table,)).fetchone()
    if not row or "float[" not in row[0]:
        return None
    return int(row[0].split("float[")[1].split("]")[0])


def test_pre_gh81_database_is_migrated_to_384(tmp_path):
    """The upgrade must actually drop the 1024-dim table, not just relabel it."""
    db = tmp_path / "old.db"
    _build_pre_gh81_db(db).close()

    conn = _connect(db)
    assert _vec_dim(conn, "semantic_embeddings") == 1024, "fixture should start at the old dimension"

    ensure_semantic_schema(conn)

    assert _vec_dim(conn, "semantic_embeddings") == 384, (
        "the 1024-dim vec0 table survived the upgrade — CREATE ... IF NOT EXISTS "
        "will not resize it, so it must be dropped explicitly"
    )
    assert conn.execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 0, (
        "stale 1024-dim vectors must not survive into a 384-dim index"
    )


def test_migration_clears_embedded_state_so_documents_are_re_embedded(tmp_path):
    """Dropping the vectors without clearing embedded_hash strands the documents.

    They would be considered already-embedded and never re-queued, leaving a
    permanently empty index that reports itself as fully embedded.
    """
    db = tmp_path / "old.db"
    _build_pre_gh81_db(db).close()

    conn = _connect(db)
    ensure_semantic_schema(conn)

    hash_, model, at = conn.execute(
        "SELECT embedded_hash, embedded_model_version, embedded_at FROM semantic_documents"
    ).fetchone()
    assert (hash_, model, at) == (None, None, None), "embedded state must be cleared so the doc is re-embedded"


def test_384_dim_insert_succeeds_after_migration(tmp_path):
    """The symptom that made this a ship-blocker, asserted directly.

    Before the fix this raised:
      OperationalError: Dimension mismatch for inserted vector for the
      "embedding" column. Expected 1024 dimensions but received 384.
    """
    db = tmp_path / "old.db"
    _build_pre_gh81_db(db).close()

    conn = _connect(db)
    ensure_semantic_schema(conn)
    conn.execute(
        "INSERT INTO semantic_embeddings(rowid, embedding) VALUES (2, ?)",
        (struct.pack("384f", *([0.2] * 384)),),
    )
    conn.commit()


def test_meta_never_claims_384_while_the_table_is_not_384(tmp_path):
    """The specific dishonesty of the original bug: metadata that lies.

    A wrong dimension is recoverable — someone drops the table and reindexes.
    Metadata asserting a migration that did not happen is worse: it suppresses
    every future attempt to run it.
    """
    db = tmp_path / "old.db"
    _build_pre_gh81_db(db).close()

    conn = _connect(db)
    ensure_semantic_schema(conn)

    meta = conn.execute("SELECT value FROM semantic_embedding_meta WHERE key = 'embedding_dim'").fetchone()
    assert meta is not None and str(meta[0]) == "384"
    assert _vec_dim(conn, "semantic_embeddings") == 384, "meta says 384; the table must agree"


def test_migration_is_idempotent(tmp_path):
    """Re-running the upgrade must not drop a correct 384-dim index."""
    db = tmp_path / "old.db"
    _build_pre_gh81_db(db).close()

    conn = _connect(db)
    ensure_semantic_schema(conn)
    conn.execute(
        "INSERT INTO semantic_embeddings(rowid, embedding) VALUES (2, ?)",
        (struct.pack("384f", *([0.2] * 384)),),
    )
    conn.commit()

    ensure_semantic_schema(conn)

    assert conn.execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 1, (
        "a second upgrade pass must be a no-op, not a re-drop of good vectors"
    )


def test_fresh_database_is_untouched_by_the_migration_path(tmp_path):
    """The `not row` guard must not turn every fresh-database create into a drop."""
    db = tmp_path / "fresh.db"
    conn = _connect(db)

    ensure_semantic_schema(conn)
    conn.execute(
        "INSERT INTO semantic_embeddings(rowid, embedding) VALUES (1, ?)",
        (struct.pack("384f", *([0.3] * 384)),),
    )
    conn.commit()

    ensure_semantic_schema(conn)

    assert _vec_dim(conn, "semantic_embeddings") == 384
    assert conn.execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 1


# --- GH-97 -------------------------------------------------------------------
# Found during a relay review of the GH-97 plan. The dim guard used to read
# `*_embedding_meta` BEFORE that table was created. On a database carrying a
# stale-width vec table but no meta table, the SELECT raised `no such table`, the
# bare `except` swallowed it, and the whole guard -- including the DROP -- was
# skipped. Control then reached `CREATE ... IF NOT EXISTS float[384]` (a no-op
# against the existing table) and the trailing `INSERT OR IGNORE`, which stamped
# '384' onto a table still 1024 wide: the same dishonest-metadata state GH-81
# fixed, reached through a shape the GH-81 guard could not observe.


def _vec_width(conn, table):
    row = conn.execute("SELECT sql FROM sqlite_master WHERE name = ?", (table,)).fetchone()
    return None if row is None else row[0].split("float")[1].split("]")[0].lstrip("[")


def _semantic_documents_ddl():
    return (
        "CREATE TABLE semantic_documents (id INTEGER PRIMARY KEY, source_type TEXT, "
        "source_table TEXT, source_pk TEXT, doc_kind TEXT, title TEXT, body TEXT, "
        "content_hash TEXT, embedded_hash TEXT, embedded_model_version TEXT, "
        "embedded_at TEXT, created_at TEXT, updated_at TEXT)"
    )


def test_stale_vec_table_with_no_meta_table_is_migrated(tmp_path):
    """The guard must fire even when the meta table does not exist yet."""
    conn = _connect(tmp_path / "t.db")
    conn.execute(_semantic_documents_ddl())
    conn.execute("CREATE VIRTUAL TABLE semantic_embeddings USING vec0(embedding float[1024])")
    conn.commit()
    assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'semantic_embedding_meta'").fetchone() is None, (
        "precondition: meta table must be absent or this test proves nothing"
    )

    ensure_semantic_schema(conn)

    assert _vec_width(conn, "semantic_embeddings") == "384"
    stored = conn.execute("SELECT value FROM semantic_embedding_meta WHERE key = 'embedding_dim'").fetchone()
    assert stored is not None, "meta row must exist after the guard runs"
    assert stored[0] == "384"


def test_declared_width_and_stored_meta_agree_after_one_pass(tmp_path):
    """One pass must converge, and the two sources of truth must not disagree."""
    conn = _connect(tmp_path / "t.db")
    ensure_semantic_schema(conn)
    stored = conn.execute("SELECT value FROM semantic_embedding_meta WHERE key = 'embedding_dim'").fetchone()[0]
    assert _vec_width(conn, "semantic_embeddings") == stored

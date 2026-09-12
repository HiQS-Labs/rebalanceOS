from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

from rebalance.ingest import audit
from rebalance.ingest.semantic_index import repair_semantic_orphans


def _database(path: Path, orphan_count: int) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE semantic_documents (id INTEGER PRIMARY KEY);"
        "CREATE TABLE semantic_embeddings (rowid INTEGER PRIMARY KEY, embedding BLOB);"
    )
    conn.executemany(
        "INSERT INTO semantic_embeddings(rowid, embedding) VALUES (?, ?)",
        [(row_id, b"vector") for row_id in range(1, orphan_count + 1)],
    )
    conn.commit()
    conn.close()
    return path


def test_repair_defaults_to_read_only_and_reports_sample(tmp_path: Path) -> None:
    db = _database(tmp_path / "semantic.db", 3)
    result = repair_semantic_orphans(db)
    assert result.orphan_count == 3
    assert result.deleted_count == 0
    assert result.sample_ids == (1, 2, 3)
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 3


def test_apply_requires_confirmation_and_large_confirmation(tmp_path: Path) -> None:
    small = _database(tmp_path / "small.db", 2)
    with pytest.raises(ValueError, match="--confirm"):
        repair_semantic_orphans(small, apply=True)

    large = _database(tmp_path / "large.db", 1001)
    with pytest.raises(ValueError, match="--confirm-large"):
        repair_semantic_orphans(large, apply=True, confirm=True)


def test_confirmed_apply_is_transactional_and_audited(tmp_path: Path) -> None:
    db = _database(tmp_path / "semantic.db", 3)
    audit_path = tmp_path / "agent-audit.json"
    with patch.object(audit, "AUDIT_LOG_PATH", audit_path):
        result = repair_semantic_orphans(db, apply=True, confirm=True)
    assert result.deleted_count == 3
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 0
    assert '"action": "DELETE"' in audit_path.read_text(encoding="utf-8")
    assert '"rows": 3' in audit_path.read_text(encoding="utf-8")
    assert '"state": "pending"' in audit_path.read_text(encoding="utf-8")
    assert '"state": "completed"' in audit_path.read_text(encoding="utf-8")


def test_delete_failure_rolls_back_and_audits_failed_outcome(tmp_path: Path) -> None:
    db = _database(tmp_path / "semantic.db", 3)
    audit_path = tmp_path / "agent-audit.json"
    with (
        patch.object(audit, "AUDIT_LOG_PATH", audit_path),
        patch("rebalance.ingest.semantic_index._delete_orphan_ids", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError, match="boom"),
    ):
        repair_semantic_orphans(db, apply=True, confirm=True)
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 3
    audit_text = audit_path.read_text(encoding="utf-8")
    assert '"state": "pending"' in audit_text
    assert '"state": "failed"' in audit_text
    assert '"state": "completed"' not in audit_text


def test_audit_intent_failure_prevents_delete(tmp_path: Path) -> None:
    db = _database(tmp_path / "semantic.db", 3)
    with (
        patch("rebalance.ingest.audit.append_audit_entry", side_effect=OSError("audit unavailable")),
        pytest.raises(OSError, match="audit unavailable"),
    ):
        repair_semantic_orphans(db, apply=True, confirm=True)

    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 3


def test_apply_queries_orphans_only_after_owning_write_transaction(tmp_path: Path) -> None:
    db = _database(tmp_path / "semantic.db", 1)
    primary = sqlite3.connect(db)

    class RacingConnection:
        def execute(self, sql, *args):
            if sql == "BEGIN IMMEDIATE":
                with sqlite3.connect(db) as writer:
                    writer.execute("INSERT INTO semantic_documents(id) VALUES (1)")
            return primary.execute(sql, *args)

        def __getattr__(self, name):
            return getattr(primary, name)

    @contextmanager
    def racing_connection(_path):
        try:
            yield RacingConnection()
        finally:
            primary.close()

    with patch("rebalance.ingest.semantic_index.db_connection", racing_connection):
        result = repair_semantic_orphans(db, apply=True, confirm=True)

    assert result.orphan_count == 0
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 1


def test_orphan_query_propagates_database_lock(tmp_path: Path) -> None:
    from rebalance.ingest.db.semantic import orphaned_embedding_ids

    db = _database(tmp_path / "semantic.db", 1)
    holder = sqlite3.connect(db)
    contender = sqlite3.connect(db, timeout=0)
    try:
        holder.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            orphaned_embedding_ids(contender)
    finally:
        holder.rollback()
        holder.close()
        contender.close()


def test_orphan_query_allows_uninitialized_database(tmp_path: Path) -> None:
    from rebalance.ingest.db.semantic import orphaned_embedding_ids

    with sqlite3.connect(tmp_path / "empty.db") as conn:
        assert orphaned_embedding_ids(conn) == []

from __future__ import annotations

import sqlite3
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


def test_delete_failure_rolls_back_and_does_not_audit(tmp_path: Path) -> None:
    db = _database(tmp_path / "semantic.db", 3)
    audit_path = tmp_path / "agent-audit.json"
    with (
        patch.object(audit, "AUDIT_LOG_PATH", audit_path),
        patch("rebalance.ingest.semantic_index._delete_orphan_ids", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError, match="boom"),
    ):
        repair_semantic_orphans(db, apply=True, confirm=True)
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM semantic_embeddings").fetchone()[0] == 3
    assert not audit_path.exists()

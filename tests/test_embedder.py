"""Unit tests for the SentenceTransformers BGE-Small embedding pipeline."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rebalance.ingest import embedder
from rebalance.ingest.db import db_connection, ensure_schema
from rebalance.ingest.embedder import (
    DEFAULT_MODEL,
    EMBEDDING_DIM,
    _embed_batch,
    _load_model,
    _vec_to_bytes,
    embed_vault_chunks,
)


class EmbedderTests(unittest.TestCase):
    def setUp(self) -> None:
        embedder._cached_model = None
        embedder._cached_tokenizer = None
        embedder._cached_model_name = None
        embedder._batch_count = 0

    def test_default_constants(self) -> None:
        self.assertEqual(DEFAULT_MODEL, "BAAI/bge-small-en-v1.5")
        self.assertEqual(EMBEDDING_DIM, 384)

    def test_vec_to_bytes_round_trip(self) -> None:
        vec = [0.1 * i for i in range(EMBEDDING_DIM)]
        packed = _vec_to_bytes(vec)
        self.assertEqual(len(packed), EMBEDDING_DIM * 4)

    def test_load_and_embed_batch_with_mock_model(self) -> None:
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.5] * EMBEDDING_DIM, [0.8] * EMBEDDING_DIM]

        with patch("sentence_transformers.SentenceTransformer", return_value=mock_model):
            model, tokenizer = _load_model("mock/model")
            self.assertIs(model, mock_model)
            self.assertIsNone(tokenizer)

            results = _embed_batch(model, tokenizer, ["hello", "world"])
            self.assertEqual(len(results), 2)
            self.assertEqual(len(results[0]), EMBEDDING_DIM)
            self.assertEqual(results[0][0], 0.5)

    def test_embed_vault_chunks_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "rebalance.db"
            with db_connection(db_path, ensure_schema) as conn:
                conn.execute(
                    """
                    INSERT INTO vault_files (rel_path, title, content_hash, ingested_at, file_size_bytes, last_modified)
                    VALUES ('note.md', 'Test Note', 'hash1', '2026-08-19T00:00:00Z', 100, '2026-08-19T00:00:00Z')
                    """
                )
                file_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                conn.execute(
                    """
                    INSERT INTO chunks (file_id, chunk_index, heading, heading_level, body, char_count, content_hash)
                    VALUES (?, 0, 'Heading', 1, 'Body content of the test note', 30, 'chash1')
                    """,
                    (file_id,),
                )
                conn.commit()

            mock_model = MagicMock()
            mock_model.encode.return_value = [[0.1] * EMBEDDING_DIM]

            with patch("sentence_transformers.SentenceTransformer", return_value=mock_model):
                res = embed_vault_chunks(db_path, batch_size=10)
                self.assertEqual(res.embedded_chunks, 1)
                self.assertEqual(res.total_chunks, 1)
                self.assertEqual(res.embedding_dim, 384)

                with db_connection(db_path, ensure_schema) as conn:
                    count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
                    self.assertEqual(count, 1)

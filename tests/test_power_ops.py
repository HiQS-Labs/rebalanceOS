"""Tests for power_ops and battery-aware ML embedding deferral (GH-201).

Validates:
1. Unit tests for rebalance.lib.power_ops:
   - Environment variable overrides (REBALANCE_FORCE_BATTERY, REBALANCE_FORCE_AC, REBALANCE_POWER_SOURCE).
   - Subprocess pmset command execution and parsing.
   - Non-macOS neutral fallback.
   - Configuration toggle (defer_embeddings_on_battery).
2. Two-Store Battery Recovery Contract (Codex R3):
   - Store 1: semantic_index (embed_pending / embed_semantic_pending)
   - Store 2: github_knowledge (embed_github_documents)
   - Zero model calls on battery power.
   - Preservation of existing vector embeddings (no destructive deletion even under force_reembed=True).
   - Document projection (backfill_semantic_documents) runs normally.
   - AC reconnection drains backlog across both stores without duplicate rows.
   - Red control demonstrating that bypassing the power check fails the contract.
   - get_index_status honest power_deferred indicators.
"""

from __future__ import annotations

import dataclasses
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import rebalance
from rebalance.cli._core import config_app
import rebalance.ingest.config as config_module
from rebalance.ingest.db import db_connection, ensure_schema, ensure_github_schema, ensure_semantic_schema
from rebalance.ingest.github_knowledge import embed_github_documents
from rebalance.ingest.index_ops import get_index_status, refresh_index
from rebalance.ingest.semantic_index import (
    DEFAULT_EMBED_MODEL,
    EMBEDDING_DIM,
    backfill_semantic_documents,
    embed_pending,
    embed_semantic_pending,
)
from rebalance.lib.power_ops import (
    get_power_source,
    is_on_battery,
    power_source_name,
    should_defer_embeddings,
)


def _fake_embed_texts(texts: list[str], model_name: str) -> list[list[float]]:
    del model_name
    return [[0.1] * EMBEDDING_DIM for _ in texts]


class PowerOpsUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_env = os.environ.copy()
        for k in ("REBALANCE_FORCE_BATTERY", "REBALANCE_FORCE_AC", "REBALANCE_POWER_SOURCE"):
            os.environ.pop(k, None)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_env_override_force_battery(self) -> None:
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"
        self.assertEqual(get_power_source(), "battery")
        self.assertTrue(is_on_battery())
        self.assertEqual(power_source_name(), "Battery Power")

    def test_env_override_force_ac(self) -> None:
        os.environ["REBALANCE_FORCE_AC"] = "1"
        self.assertEqual(get_power_source(), "ac")
        self.assertFalse(is_on_battery())
        self.assertEqual(power_source_name(), "AC Power")

    def test_env_override_power_source_string(self) -> None:
        for val in ("battery", "BATT"):
            os.environ["REBALANCE_POWER_SOURCE"] = val
            self.assertEqual(get_power_source(), "battery")
            self.assertTrue(is_on_battery())

        for val in ("ac", "CHARGER", "plugged"):
            os.environ["REBALANCE_POWER_SOURCE"] = val
            self.assertEqual(get_power_source(), "ac")
            self.assertFalse(is_on_battery())

        os.environ["REBALANCE_POWER_SOURCE"] = "unknown"
        self.assertEqual(get_power_source(), "unknown")
        self.assertFalse(is_on_battery())
        self.assertEqual(power_source_name(), "Unknown")

    @patch("sys.platform", "darwin")
    @patch("subprocess.run")
    def test_pmset_parsing_battery(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pmset", "-g", "batt"],
            returncode=0,
            stdout="Now drawing from 'Battery Power'\n -InternalBattery-0\t85%; discharging; 4:12 remaining present: true\n",
            stderr="",
        )
        self.assertEqual(get_power_source(), "battery")
        self.assertTrue(is_on_battery())

    @patch("sys.platform", "darwin")
    @patch("subprocess.run")
    def test_pmset_parsing_ac(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pmset", "-g", "batt"],
            returncode=0,
            stdout="Now drawing from 'AC Power'\n -InternalBattery-0\t100%; charged; 0:00 remaining present: true\n",
            stderr="",
        )
        self.assertEqual(get_power_source(), "ac")
        self.assertFalse(is_on_battery())

    @patch("sys.platform", "darwin")
    @patch("subprocess.run")
    def test_pmset_error_falls_back_to_unknown(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pmset", "-g", "batt"],
            returncode=1,
            stdout="Error reading battery\n",
            stderr="Permission denied\n",
        )
        self.assertEqual(get_power_source(), "unknown")
        self.assertFalse(is_on_battery())

    @patch("sys.platform", "darwin")
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pmset", timeout=2.0))
    def test_pmset_timeout_falls_back_to_unknown(self, _mock_run: MagicMock) -> None:
        self.assertEqual(get_power_source(), "unknown")
        self.assertFalse(is_on_battery())

    @patch("sys.platform", "linux")
    def test_non_darwin_falls_back_to_unknown(self) -> None:
        self.assertEqual(get_power_source(), "unknown")
        self.assertFalse(is_on_battery())

    def test_should_defer_embeddings_respects_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            orig_config = config_module.CONFIG_PATH
            config_module.CONFIG_PATH = Path(tmp) / "rbos.config"
            try:
                # 1. On battery, config enabled (default) -> True
                os.environ["REBALANCE_FORCE_BATTERY"] = "1"
                self.assertTrue(config_module.get_defer_embeddings_on_battery())
                self.assertTrue(should_defer_embeddings())

                # 2. On battery, config disabled -> False
                config_module.set_defer_embeddings_on_battery(False)
                self.assertFalse(config_module.get_defer_embeddings_on_battery())
                self.assertFalse(should_defer_embeddings())

                # 3. On AC, config enabled -> False
                os.environ.pop("REBALANCE_FORCE_BATTERY", None)
                os.environ["REBALANCE_FORCE_AC"] = "1"
                config_module.set_defer_embeddings_on_battery(True)
                self.assertFalse(should_defer_embeddings())
            finally:
                config_module.CONFIG_PATH = orig_config

    def test_cli_config_commands(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            orig_config = config_module.CONFIG_PATH
            config_module.CONFIG_PATH = Path(tmp) / "rbos.config"
            try:
                # Default is True
                res = runner.invoke(config_app, ["get-defer-embeddings-on-battery"])
                self.assertEqual(res.exit_code, 0)
                self.assertIn("defer_embeddings_on_battery: True", res.output)

                # Set False
                res = runner.invoke(config_app, ["set-defer-embeddings-on-battery", "False"])
                self.assertEqual(res.exit_code, 0)
                self.assertIn("set defer_embeddings_on_battery=False", res.output)
                self.assertFalse(config_module.get_defer_embeddings_on_battery())

                # Set True
                res = runner.invoke(config_app, ["set-defer-embeddings-on-battery", "True"])
                self.assertEqual(res.exit_code, 0)
                self.assertTrue(config_module.get_defer_embeddings_on_battery())
            finally:
                config_module.CONFIG_PATH = orig_config


class TwoStoreBatteryRecoveryTests(unittest.TestCase):
    """Integration test suite proving the Two-Store Battery Recovery Contract (Codex R3)."""

    def setUp(self) -> None:
        self._orig_env = os.environ.copy()
        for k in ("REBALANCE_FORCE_BATTERY", "REBALANCE_FORCE_AC", "REBALANCE_POWER_SOURCE"):
            os.environ.pop(k, None)
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "test_rebalance.db"

        # Isolate power configuration from operator machine (Codex R6)
        self._orig_config = config_module.CONFIG_PATH
        self._test_config = Path(self._tmp.name) / "rbos.config"
        config_module.CONFIG_PATH = self._test_config
        config_module.set_defer_embeddings_on_battery(True)

        # Initialize schema and seed two-store fixtures
        with db_connection(self.db_path) as conn:
            ensure_schema(conn)
            ensure_github_schema(conn)
            ensure_semantic_schema(conn)
            from rebalance.ingest.clio import ensure_clio_schema

            ensure_clio_schema(conn)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS figma_comments (
                    comment_key      TEXT PRIMARY KEY,
                    file_key         TEXT NOT NULL,
                    comment_id       TEXT NOT NULL,
                    parent_id        TEXT,
                    message          TEXT,
                    user_id          TEXT,
                    user_handle      TEXT,
                    created_at       TEXT,
                    resolved_at      TEXT,
                    order_id         REAL,
                    client_meta_json TEXT,
                    reactions_json   TEXT,
                    raw_json         TEXT NOT NULL,
                    synced_at        TEXT NOT NULL
                )
                """
            )

            # Seed raw vault files and chunks so backfill_semantic_documents preserves them
            conn.execute(
                """
                INSERT INTO vault_files (id, rel_path, content_hash, title, file_size_bytes, ingested_at)
                VALUES (1, 'Projects/ExistingNote.md', 'vh1', 'Existing Note', 100, '2026-09-08T00:00:00Z'),
                       (2, 'Projects/PendingNote.md', 'vh2', 'Pending Note', 100, '2026-09-08T01:00:00Z')
                """
            )
            conn.execute(
                """
                INSERT INTO chunks (id, file_id, chunk_index, heading, body, char_count, content_hash)
                VALUES (1, 1, 0, 'Existing Note', 'Existing note body with sufficient length to exceed threshold.', 75, 'shash1'),
                       (2, 2, 0, 'Pending Note', 'New pending note body with sufficient length to exceed threshold.', 75, 'shash2')
                """
            )

            # Store 1 Fixtures: semantic_documents
            current_model_version = f"{DEFAULT_EMBED_MODEL}|{EMBEDDING_DIM}"
            conn.execute(
                """
                INSERT INTO semantic_documents (
                    source_type, source_table, source_pk, doc_kind, title, body,
                    content_hash, embedded_hash, embedded_model_version, created_at, updated_at
                ) VALUES
                ('vault', 'chunks', '1', 'chunk', 'Existing Note', 'Existing note body with sufficient length to exceed threshold.', 'shash1', 'shash1', ?, '2026-09-08T00:00:00Z', '2026-09-08T00:00:00Z'),
                ('vault', 'chunks', '2', 'chunk', 'Pending Note', 'New pending note body with sufficient length to exceed threshold.', 'shash2', NULL, NULL, '2026-09-08T01:00:00Z', '2026-09-08T01:00:00Z')
                """,
                (current_model_version,),
            )
            # Insert existing vector in semantic_embeddings
            existing_sem_id = conn.execute("SELECT id FROM semantic_documents WHERE source_pk = '1'").fetchone()[0]
            conn.execute(
                "INSERT INTO semantic_embeddings (rowid, embedding) VALUES (?, ?)",
                (existing_sem_id, b"\x00" * (EMBEDDING_DIM * 4)),
            )

            # Store 2 Fixtures: github_documents
            conn.execute(
                """
                INSERT INTO github_documents (
                    repo_full_name, source_type, source_number, doc_type, source_key,
                    title, body, content_hash, embedded_hash, updated_at, fetched_at
                ) VALUES
                ('HiQS-Labs/rebalanceOS', 'issue', 101, 'issue', 'issue:101', 'Existing Issue', 'Existing issue body with sufficient length to exceed the minimum threshold for embedding.', 'ghhash1', 'ghhash1', '2026-09-08T00:00:00Z', '2026-09-08T00:00:00Z'),
                ('HiQS-Labs/rebalanceOS', 'issue', 102, 'issue', 'issue:102', 'Pending Issue', 'Pending issue body with sufficient length to exceed the minimum threshold for embedding.', 'ghhash2', NULL, '2026-09-08T01:00:00Z', '2026-09-08T01:00:00Z')
                """
            )
            # Insert existing vector in github_embeddings
            existing_gh_id = conn.execute("SELECT id FROM github_documents WHERE source_key = 'issue:101'").fetchone()[
                0
            ]
            conn.execute(
                "INSERT INTO github_embeddings (doc_id, embedding) VALUES (?, ?)",
                (existing_gh_id, b"\x00" * (EMBEDDING_DIM * 4)),
            )
            conn.commit()

    def tearDown(self) -> None:
        self._tmp.cleanup()
        config_module.CONFIG_PATH = self._orig_config
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_battery_deferral_preserves_vectors_and_zero_model_calls(self) -> None:
        """On battery power: zero model calls occur, existing vectors are untouched, and rows remain pending."""
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"

        model_calls = 0

        def tracked_embed(texts: list[str], _model_name: str) -> list[list[float]]:
            nonlocal model_calls
            model_calls += 1
            return [[0.5] * EMBEDDING_DIM for _ in texts]

        # 1. Run embed_pending on Store 1
        sem_res = embed_pending(self.db_path, embed_texts=tracked_embed)
        self.assertTrue(sem_res.deferred_battery)
        self.assertEqual(sem_res.embedded_docs, 0)
        self.assertEqual(model_calls, 0, "Exactly zero model calls allowed on battery")

        # 2. Run embed_github_documents on Store 2
        gh_res = embed_github_documents(self.db_path, embed_texts=tracked_embed)
        self.assertTrue(gh_res.deferred_battery)
        self.assertEqual(gh_res.embedded_docs, 0)
        self.assertEqual(model_calls, 0, "Exactly zero model calls allowed on battery")

        # 3. Facade test: embed_semantic_pending forwards deferred_battery
        facade_res = embed_semantic_pending(self.db_path, embed_texts=tracked_embed)
        self.assertTrue(facade_res.deferred_battery)
        self.assertEqual(model_calls, 0)

        # 4. Verify existing vectors are preserved in both stores
        with db_connection(self.db_path) as conn:
            sem_emb_count = conn.execute("SELECT count(*) FROM semantic_embeddings").fetchone()[0]
            gh_emb_count = conn.execute("SELECT count(*) FROM github_embeddings").fetchone()[0]
            self.assertEqual(sem_emb_count, 1, "Existing semantic embedding vector must be preserved")
            self.assertEqual(gh_emb_count, 1, "Existing GitHub embedding vector must be preserved")

            # Verify pending rows are still pending (embedded_hash IS NULL)
            sem_pending = conn.execute(
                "SELECT count(*) FROM semantic_documents WHERE embedded_hash IS NULL"
            ).fetchone()[0]
            gh_pending = conn.execute("SELECT count(*) FROM github_documents WHERE embedded_hash IS NULL").fetchone()[0]
            self.assertEqual(sem_pending, 1, "Semantic document must remain pending")
            self.assertEqual(gh_pending, 1, "GitHub document must remain pending")

        # 5. Verify get_index_status reports power_deferred honestly
        status = get_index_status(self.db_path)
        self.assertTrue(status["semantic_index"]["power_deferred"])
        self.assertTrue(status["sources"]["github"]["power_deferred"])
        self.assertTrue(status["freshness"]["power_deferred"])

    def test_force_reembed_on_battery_preserves_vectors_without_destructive_wipe(self) -> None:
        """When force_reembed=True is requested on battery, vectors must NOT be wiped."""
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"

        model_calls = 0

        def tracked_embed(texts: list[str], _model_name: str) -> list[list[float]]:
            nonlocal model_calls
            model_calls += 1
            return [[0.5] * EMBEDDING_DIM for _ in texts]

        # Call force_reembed on both stores under battery
        sem_res = embed_pending(self.db_path, force_reembed=True, embed_texts=tracked_embed)
        gh_res = embed_github_documents(self.db_path, force_reembed=True, embed_texts=tracked_embed)

        self.assertTrue(sem_res.deferred_battery)
        self.assertTrue(gh_res.deferred_battery)
        self.assertEqual(model_calls, 0)

        # Check existing vectors still exist!
        with db_connection(self.db_path) as conn:
            sem_emb_count = conn.execute("SELECT count(*) FROM semantic_embeddings").fetchone()[0]
            gh_emb_count = conn.execute("SELECT count(*) FROM github_embeddings").fetchone()[0]
            self.assertEqual(sem_emb_count, 1, "Vectors must NOT be wiped when force_reembed is called on battery")
            self.assertEqual(gh_emb_count, 1, "Vectors must NOT be wiped when force_reembed is called on battery")

    def test_ac_reconnection_drains_both_stores_cleanly(self) -> None:
        """On AC power, both embedding stores drain their backlog completely without duplicates."""
        # Step 1: Simulate deferral while on battery
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"
        embed_pending(self.db_path, embed_texts=lambda texts, m: [])
        embed_github_documents(self.db_path, embed_texts=lambda texts, m: [])

        # Step 2: Transition to AC power
        os.environ.pop("REBALANCE_FORCE_BATTERY", None)
        os.environ["REBALANCE_FORCE_AC"] = "1"

        model_calls = 0

        def tracked_embed(texts: list[str], _model_name: str) -> list[list[float]]:
            nonlocal model_calls
            model_calls += 1
            return [[0.7] * EMBEDDING_DIM for _ in texts]

        # Drain Store 1
        sem_res = embed_pending(self.db_path, embed_texts=tracked_embed)
        self.assertFalse(sem_res.deferred_battery)
        self.assertEqual(sem_res.embedded_docs, 1)
        self.assertGreater(model_calls, 0)

        # Drain Store 2
        gh_res = embed_github_documents(self.db_path, embed_texts=tracked_embed)
        self.assertFalse(gh_res.deferred_battery)
        self.assertEqual(gh_res.embedded_docs, 1)

        # Step 3: Verify all documents across both stores are embedded
        with db_connection(self.db_path) as conn:
            sem_pending = conn.execute(
                "SELECT count(*) FROM semantic_documents WHERE embedded_hash IS NULL"
            ).fetchone()[0]
            gh_pending = conn.execute("SELECT count(*) FROM github_documents WHERE embedded_hash IS NULL").fetchone()[0]
            self.assertEqual(sem_pending, 0, "Zero pending documents in Store 1 after AC drain")
            self.assertEqual(gh_pending, 0, "Zero pending documents in Store 2 after AC drain")

            # Verify total vector counts
            sem_total_emb = conn.execute("SELECT count(*) FROM semantic_embeddings").fetchone()[0]
            gh_total_emb = conn.execute("SELECT count(*) FROM github_embeddings").fetchone()[0]
            self.assertEqual(sem_total_emb, 2, "Both documents have embeddings in Store 1 (no duplicates)")
            self.assertEqual(gh_total_emb, 2, "Both documents have embeddings in Store 2 (no duplicates)")

        # Step 4: Verify index status reports power_deferred=False after drain
        status = get_index_status(self.db_path)
        self.assertFalse(status["semantic_index"]["power_deferred"])
        self.assertFalse(status["sources"]["github"]["power_deferred"])
        self.assertFalse(status["freshness"]["power_deferred"])

    def test_two_store_recovery_via_refresh_index_recipe(self) -> None:
        """Full refresh_index entry point defers on battery and drains both stores on AC without duplicates (Codex R6)."""
        # Capture pre-existing vector bytes
        with db_connection(self.db_path) as conn:
            orig_sem_vec = conn.execute("SELECT embedding FROM semantic_embeddings").fetchone()[0]
            orig_gh_vec = conn.execute("SELECT embedding FROM github_embeddings").fetchone()[0]

        model_calls = 0

        def tracked_embed(texts: list[str], _m: str) -> list[list[float]]:
            nonlocal model_calls
            model_calls += 1
            return [[0.3] * EMBEDDING_DIM for _ in texts]

        # 1. Run on battery via refresh_index entry point
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"
        with (
            patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault", "github"]),
            patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
            patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=tracked_embed),
            patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=tracked_embed),
            patch("rebalance.ingest.github_knowledge.sync_github_repo") as mock_sync_gh,
            patch("rebalance.ingest.github_scan.scan_github") as mock_scan,
            patch("rebalance.ingest.github_scan.sync_pushed_repos"),
            patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
        ):
            mock_sync_gh.return_value = MagicMock(
                branches_synced=0,
                issues_synced=0,
                prs_synced=0,
                comments_synced=0,
                commits_synced=0,
                checks_synced=0,
                docs_built=0,
                elapsed_seconds=0.1,
            )
            mock_scan.return_value = MagicMock(events=[])

            res_battery = refresh_index(self.db_path, scope=["github", "semantic"], repos=["HiQS-Labs/rebalanceOS"])
            self.assertEqual(
                res_battery["errors"], [], f"Expected 0 errors on battery refresh, got: {res_battery['errors']}"
            )
            battery_scopes = [r["scope"] for r in res_battery["results"]]
            self.assertIn("github", battery_scopes)
            self.assertIn("semantic", battery_scopes)

            # Zero model calls on battery
            self.assertEqual(model_calls, 0, "refresh_index must make zero model calls on battery")

            # Vectors are byte-for-byte identical (untouched)
            with db_connection(self.db_path) as conn:
                sem_vec = conn.execute("SELECT embedding FROM semantic_embeddings").fetchone()[0]
                gh_vec = conn.execute("SELECT embedding FROM github_embeddings").fetchone()[0]
                self.assertEqual(sem_vec, orig_sem_vec)
                self.assertEqual(gh_vec, orig_gh_vec)

                # Documents remain pending
                sem_pending = conn.execute(
                    "SELECT count(*) FROM semantic_documents WHERE embedded_hash IS NULL"
                ).fetchone()[0]
                gh_pending = conn.execute(
                    "SELECT count(*) FROM github_documents WHERE embedded_hash IS NULL"
                ).fetchone()[0]
                self.assertGreater(sem_pending, 0)
                self.assertGreater(gh_pending, 0)

        # 2. Reconnect to AC: run refresh_index without touching source documents
        os.environ.pop("REBALANCE_FORCE_BATTERY", None)
        os.environ["REBALANCE_FORCE_AC"] = "1"

        with (
            patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault", "github"]),
            patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
            patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=tracked_embed),
            patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=tracked_embed),
            patch("rebalance.ingest.github_knowledge.sync_github_repo") as mock_sync_gh,
            patch("rebalance.ingest.github_scan.scan_github") as mock_scan,
            patch("rebalance.ingest.github_scan.sync_pushed_repos"),
            patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
        ):
            mock_sync_gh.return_value = MagicMock(
                branches_synced=0,
                issues_synced=0,
                prs_synced=0,
                comments_synced=0,
                commits_synced=0,
                checks_synced=0,
                docs_built=0,
                elapsed_seconds=0.1,
            )
            mock_scan.return_value = MagicMock(events=[])

            res_ac = refresh_index(self.db_path, scope=["github", "semantic"], repos=["HiQS-Labs/rebalanceOS"])
            self.assertEqual(res_ac["errors"], [], f"Expected 0 errors on AC refresh, got: {res_ac['errors']}")
            ac_scopes = [r["scope"] for r in res_ac["results"]]
            self.assertIn("github", ac_scopes)
            self.assertIn("semantic", ac_scopes)

            # Model calls occurred on AC
            self.assertGreater(model_calls, 0, "Model calls must occur to drain backlog on AC")

            # Backlog drained across both stores without duplicate rows
            with db_connection(self.db_path) as conn:
                sem_pending = conn.execute(
                    "SELECT count(*) FROM semantic_documents WHERE embedded_hash IS NULL"
                ).fetchone()[0]
                gh_pending = conn.execute(
                    "SELECT count(*) FROM github_documents WHERE embedded_hash IS NULL"
                ).fetchone()[0]
                self.assertEqual(sem_pending, 0, "Store 1 pending backlog must be 0 after AC refresh")
                self.assertEqual(gh_pending, 0, "Store 2 pending backlog must be 0 after AC refresh")

                sem_tot = conn.execute("SELECT count(*) FROM semantic_embeddings").fetchone()[0]
                gh_tot = conn.execute("SELECT count(*) FROM github_embeddings").fetchone()[0]
                self.assertEqual(
                    sem_tot, 4, "Store 1 must have exactly 4 vectors (2 vault + 2 projected github, no duplicates)"
                )
                self.assertEqual(gh_tot, 2, "Store 2 must have exactly 2 vectors (no duplicates)")

        # 3. Subsequent AC refresh on unchanged repos: zero new model calls
        calls_before = model_calls
        with (
            patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault", "github"]),
            patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
            patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=tracked_embed),
            patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=tracked_embed),
            patch("rebalance.ingest.github_knowledge.sync_github_repo") as mock_sync_gh,
            patch("rebalance.ingest.github_scan.scan_github") as mock_scan,
            patch("rebalance.ingest.github_scan.sync_pushed_repos"),
            patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
        ):
            mock_sync_gh.return_value = MagicMock(
                branches_synced=0,
                issues_synced=0,
                prs_synced=0,
                comments_synced=0,
                commits_synced=0,
                checks_synced=0,
                docs_built=0,
                elapsed_seconds=0.1,
            )
            mock_scan.return_value = MagicMock(events=[])

            res_unchanged = refresh_index(self.db_path, scope=["github", "semantic"], repos=["HiQS-Labs/rebalanceOS"])
            self.assertEqual(res_unchanged["errors"], [])
            self.assertEqual(model_calls, calls_before, "Unchanged AC run must make zero additional model calls")

    def test_document_projection_runs_on_battery_while_embeddings_deferred(self) -> None:
        """Document projection (backfill_semantic_documents) runs to completion on battery while ML embedding is deferred."""
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"

        # Insert raw vault item
        with db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO vault_files (rel_path, content_hash, title, file_size_bytes, ingested_at)
                VALUES ('Projects/NewNote.md', 'vh123', 'New Note on Battery', 100, '2026-09-08T02:00:00Z')
                """
            )
            file_id = conn.execute("SELECT id FROM vault_files WHERE rel_path = 'Projects/NewNote.md'").fetchone()[0]
            conn.execute(
                """
                INSERT INTO chunks (file_id, chunk_index, heading, body, char_count, content_hash)
                VALUES (?, 0, 'New Note', 'This is content projected while operating on battery power with plenty of length.', 75, 'chash123')
                """,
                (file_id,),
            )
            conn.commit()

        # Run document projection
        backfill_res = backfill_semantic_documents(
            self.db_path,
            source_types=["vault"],
            use_registry_providers=True,
        )
        self.assertGreaterEqual(backfill_res.inserted_count, 1, "Document projection must succeed on battery")

        # Verify document landed in semantic_documents with NULL embedded_hash
        with db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT embedded_hash, title FROM semantic_documents WHERE source_type = 'vault' AND title = 'New Note on Battery'"
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertIsNone(row["embedded_hash"], "Projected document must be pending embedding")

        # Now verify embed_pending defers embedding
        embed_res = embed_pending(self.db_path)
        self.assertTrue(embed_res.deferred_battery)
        self.assertEqual(embed_res.embedded_docs, 0)

    def test_refresh_semantic_pipeline_on_battery_and_ac(self) -> None:
        """_refresh_semantic_only passes through deferred_battery on battery, and drains on AC."""
        from rebalance.ingest.index_ops import _refresh_semantic_only

        # 1. On battery
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"
        res_bat = _refresh_semantic_only(self.db_path, dry_run=False)
        self.assertTrue(res_bat["semantic_embed"]["deferred_battery"])
        self.assertEqual(res_bat["semantic_embed"]["embedded"], 0)

        # 2. On AC
        os.environ.pop("REBALANCE_FORCE_BATTERY", None)
        os.environ["REBALANCE_FORCE_AC"] = "1"

        def fake_embed(texts: list[str], _m: str) -> list[list[float]]:
            return [[0.1] * EMBEDDING_DIM for _ in texts]

        # Patch default embed texts so AC drain doesn't load a real model in tests
        with patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=fake_embed):
            res_ac = _refresh_semantic_only(self.db_path, dry_run=False)
            self.assertFalse(res_ac["semantic_embed"]["deferred_battery"])
            self.assertGreater(res_ac["semantic_embed"]["embedded"], 0)

    def test_grounded_red_control_witnesses_gate_bypass_failure(self) -> None:
        """Grounded Red Control: bypassing power gate executes model calls on battery,
        causing contract assertions to fail (Codex R6).
        """
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"

        model_calls = 0

        def tracked_embed(texts: list[str], _m: str) -> list[list[float]]:
            nonlocal model_calls
            model_calls += 1
            return [[0.2] * EMBEDDING_DIM for _ in texts]

        # Normal run with gate active: model_calls == 0 and deferred_battery is True
        with patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=tracked_embed):
            normal_res = embed_pending(self.db_path)
            self.assertTrue(normal_res.deferred_battery)
            self.assertEqual(model_calls, 0)

        # Bypass the gate by forcing power_defer=False
        with patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=tracked_embed):
            bypassed_res = embed_pending(self.db_path, power_defer=False)

            # Contract verification: witness that bypassing the gate violates the contract assertions
            with self.assertRaises(AssertionError):
                self.assertTrue(bypassed_res.deferred_battery)

            with self.assertRaises(AssertionError):
                self.assertEqual(model_calls, 0)

            self.assertFalse(bypassed_res.deferred_battery)
            self.assertGreater(model_calls, 0, "Bypassing gate invoked model on battery, proving assertions hold")

    def test_power_transition_between_stages_honors_startup_decision(self) -> None:
        """Startup decision captured in refresh_index is honored across all stages (Codex R8)."""
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"

        with (
            patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault", "github"]),
            patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=_fake_embed_texts),
            patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=_fake_embed_texts),
            patch("rebalance.ingest.github_knowledge.sync_github_repo") as mock_sync_gh,
            patch("rebalance.ingest.github_scan.scan_github") as mock_scan,
            patch("rebalance.ingest.github_scan.sync_pushed_repos"),
            patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
        ):
            mock_sync_gh.return_value = MagicMock(
                branches_synced=0,
                issues_synced=0,
                prs_synced=0,
                comments_synced=0,
                commits_synced=0,
                checks_synced=0,
                docs_built=0,
                elapsed_seconds=0.1,
            )
            mock_scan.return_value = MagicMock(events=[])

            call_count = 0

            def transitioning_power() -> bool:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return True  # Startup check in refresh_index -> battery
                return False  # Later checks -> AC

            with patch("rebalance.lib.power_ops.should_defer_embeddings", side_effect=transitioning_power):
                res = refresh_index(self.db_path, scope=["github", "semantic"], repos=["HiQS-Labs/rebalanceOS"])
                self.assertEqual(res["errors"], [])
                sem_res = next(r for r in res["results"] if r["scope"] == "semantic")
                self.assertTrue(sem_res["semantic_embed"]["deferred_battery"])

    def test_power_transition_startup_ac_to_unplug_honors_startup_decision(self) -> None:
        """Startup decision on AC is honored across all stages even if unplugged mid-refresh (Codex R6 & R8)."""
        call_count = 0

        def transitioning_power() -> bool:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False  # Startup check in refresh_index -> AC
            return True  # Later checks -> Unplugged (Battery)

        with (
            patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault", "github"]),
            patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=_fake_embed_texts),
            patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=_fake_embed_texts),
            patch("rebalance.ingest.github_knowledge.sync_github_repo") as mock_sync_gh,
            patch("rebalance.ingest.github_scan.scan_github") as mock_scan,
            patch("rebalance.ingest.github_scan.sync_pushed_repos"),
            patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
            patch("rebalance.lib.power_ops.should_defer_embeddings", side_effect=transitioning_power),
        ):
            mock_sync_gh.return_value = MagicMock(
                branches_synced=0,
                issues_synced=0,
                prs_synced=0,
                comments_synced=0,
                commits_synced=0,
                checks_synced=0,
                docs_built=0,
                elapsed_seconds=0.1,
            )
            mock_scan.return_value = MagicMock(events=[])

            res = refresh_index(self.db_path, scope=["github", "semantic"], repos=["HiQS-Labs/rebalanceOS"])
            self.assertEqual(res["errors"], [])
            sem_res = next(r for r in res["results"] if r["scope"] == "semantic")
            self.assertFalse(
                sem_res["semantic_embed"]["deferred_battery"],
                "Startup AC decision must execute embeddings without deferral",
            )

    def test_power_deferral_disabled_by_config(self) -> None:
        """When defer_embeddings_on_battery is False, refresh_index executes embeddings on battery (Codex R6)."""
        os.environ["REBALANCE_FORCE_BATTERY"] = "1"
        self.assertTrue(should_defer_embeddings())

        with patch("rebalance.ingest.config.get_defer_embeddings_on_battery", return_value=False):
            self.assertFalse(should_defer_embeddings(), "Disabled config must allow embeddings on battery")

            with (
                patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault", "github"]),
                patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
                patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
                patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=_fake_embed_texts),
                patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=_fake_embed_texts),
                patch("rebalance.ingest.github_knowledge.sync_github_repo") as mock_sync_gh,
                patch("rebalance.ingest.github_scan.scan_github") as mock_scan,
                patch("rebalance.ingest.github_scan.sync_pushed_repos"),
                patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
            ):
                mock_sync_gh.return_value = MagicMock(
                    branches_synced=0,
                    issues_synced=0,
                    prs_synced=0,
                    comments_synced=0,
                    commits_synced=0,
                    checks_synced=0,
                    docs_built=0,
                    elapsed_seconds=0.1,
                )
                mock_scan.return_value = MagicMock(events=[])

                res = refresh_index(self.db_path, scope=["github", "semantic"], repos=["HiQS-Labs/rebalanceOS"])
                self.assertEqual(res["errors"], [])
                sem_res = next(r for r in res["results"] if r["scope"] == "semantic")
                self.assertFalse(sem_res["semantic_embed"]["deferred_battery"], "Disabled config must run embeddings")

    def test_unknown_power_defaults_to_ac_behavior(self) -> None:
        """Unknown power source defaults to AC behavior in refresh_index (Codex R6)."""
        os.environ["REBALANCE_POWER_SOURCE"] = "unknown"
        self.assertEqual(get_power_source(), "unknown")
        self.assertFalse(is_on_battery())
        self.assertFalse(should_defer_embeddings())

        with (
            patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault", "github"]),
            patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
            patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=_fake_embed_texts),
            patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=_fake_embed_texts),
            patch("rebalance.ingest.github_knowledge.sync_github_repo") as mock_sync_gh,
            patch("rebalance.ingest.github_scan.scan_github") as mock_scan,
            patch("rebalance.ingest.github_scan.sync_pushed_repos"),
            patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
        ):
            mock_sync_gh.return_value = MagicMock(
                branches_synced=0,
                issues_synced=0,
                prs_synced=0,
                comments_synced=0,
                commits_synced=0,
                checks_synced=0,
                docs_built=0,
                elapsed_seconds=0.1,
            )
            mock_scan.return_value = MagicMock(events=[])

            res = refresh_index(self.db_path, scope=["github", "semantic"], repos=["HiQS-Labs/rebalanceOS"])
            self.assertEqual(res["errors"], [])
            sem_res = next(r for r in res["results"] if r["scope"] == "semantic")
            self.assertFalse(
                sem_res["semantic_embed"]["deferred_battery"], "Unknown power must default to AC embeddings"
            )

    def test_default_refresh_recipe_vault_chunks_power_deferral(self) -> None:
        """Default refresh recipe defers vault chunks embedding on battery and drains on AC (Codex Whole-File)."""
        with tempfile.TemporaryDirectory() as tmp_vault:
            v_path = Path(tmp_vault)
            (v_path / "Note.md").write_text("# Note\n\nSome meaningful content to be chunked and embedded in vault.")

            # 1. Ingest vault files
            from rebalance.ingest.note_ingester import ingest_vault

            ingest_vault(vault_path=v_path, database_path=self.db_path)

            with db_connection(self.db_path) as conn:
                chunk_count = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
                self.assertGreater(chunk_count, 0)

            # 2. Run refresh_index on battery with default recipe (no scope filter)
            os.environ["REBALANCE_FORCE_BATTERY"] = "1"
            sleuth_collector = dataclasses.replace(
                rebalance.ingest.index_ops.COLLECTORS["sleuth"],
                refresh=lambda db, **kw: {"scope": "sleuth", "reminders": 0},
            )
            email_collector = dataclasses.replace(
                rebalance.ingest.index_ops.COLLECTORS["email"],
                refresh=lambda db, **kw: {"scope": "email", "messages": 0},
            )
            with (
                patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault"]),
                patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
                patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
                patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=_fake_embed_texts),
                patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=_fake_embed_texts),
                patch(
                    "rebalance.ingest.github_knowledge.sync_github_repo",
                    return_value=MagicMock(
                        branches_synced=0,
                        issues_synced=0,
                        prs_synced=0,
                        comments_synced=0,
                        commits_synced=0,
                        checks_synced=0,
                        docs_built=0,
                        elapsed_seconds=0.1,
                    ),
                ),
                patch("rebalance.ingest.github_scan.scan_github", return_value=MagicMock(events=[])),
                patch("rebalance.ingest.github_scan.sync_pushed_repos"),
                patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
                patch("rebalance.ingest.index_ops._refresh_calendar", return_value={"scope": "calendar", "events": 0}),
                patch.dict(
                    rebalance.ingest.index_ops.COLLECTORS,
                    {"sleuth": sleuth_collector, "email": email_collector},
                ),
                patch(
                    "rebalance.ingest.index_ops._refresh_apple_reminders",
                    return_value={"scope": "apple_reminders", "reminders": 0},
                ),
                patch("rebalance.ingest.index_ops._refresh_email", return_value={"scope": "email", "messages": 0}),
                patch("rebalance.ingest.index_ops._refresh_clio", return_value={"scope": "clio", "prompts": 0}),
                patch("rebalance.ingest.index_ops._refresh_figma", return_value={"scope": "figma", "comments": 0}),
                patch(
                    "rebalance.ingest.note_builder.build_dashboard_note_content", return_value="# Dashboard\n\nContent"
                ),
                patch("rebalance.ingest.embedder._load_model") as mock_load,
                patch(
                    "rebalance.ingest.embedder._embed_batch",
                    side_effect=lambda m, t, texts: [[0.1] * 384 for _ in texts],
                ),
            ):
                res_battery = refresh_index(self.db_path, vault_path=str(v_path))
                self.assertEqual(res_battery["errors"], [])
                v_res = next(r for r in res_battery["results"] if r["scope"] == "vault")
                self.assertTrue(v_res["embed_chunks"]["deferred_battery"])
                self.assertEqual(v_res["embed_chunks"]["embedded"], 0)
                # Verify dashboard branch was executed and deferred
                dash_res = next(r for r in res_battery["results"] if r["scope"] == "dashboard")
                self.assertTrue(dash_res["embed_chunks"]["deferred_battery"])
                mock_load.assert_not_called()

                # Status check: persistent status reports power_deferred=True
                status_bat = get_index_status(self.db_path)
                self.assertTrue(status_bat["sources"]["vault"]["power_deferred"])
                self.assertTrue(status_bat["freshness"]["power_deferred"])

            # Embeddings table untouched
            with db_connection(self.db_path) as conn:
                embedded_count = conn.execute("SELECT count(*) FROM embeddings").fetchone()[0]
                self.assertEqual(embedded_count, 0)

            # 3. Drain on AC with default recipe
            os.environ.pop("REBALANCE_FORCE_BATTERY", None)
            os.environ["REBALANCE_FORCE_AC"] = "1"
            with (
                patch("rebalance.ingest.index_ops._all_semantic_sources", return_value=["vault"]),
                patch("rebalance.ingest.index_ops.get_github_token", return_value="ghp_test"),
                patch("rebalance.ingest.github_scan.resolve_working_token", return_value="ghp_test"),
                patch("rebalance.ingest.github_knowledge._default_embed_texts", side_effect=_fake_embed_texts),
                patch("rebalance.ingest.semantic_index._default_embed_texts", side_effect=_fake_embed_texts),
                patch(
                    "rebalance.ingest.github_knowledge.sync_github_repo",
                    return_value=MagicMock(
                        branches_synced=0,
                        issues_synced=0,
                        prs_synced=0,
                        comments_synced=0,
                        commits_synced=0,
                        checks_synced=0,
                        docs_built=0,
                        elapsed_seconds=0.1,
                    ),
                ),
                patch("rebalance.ingest.github_scan.scan_github", return_value=MagicMock(events=[])),
                patch("rebalance.ingest.github_scan.sync_pushed_repos"),
                patch("rebalance.ingest.github_commit_backfill.backfill_repos"),
                patch("rebalance.ingest.index_ops._refresh_calendar", return_value={"scope": "calendar", "events": 0}),
                patch.dict(
                    rebalance.ingest.index_ops.COLLECTORS,
                    {"sleuth": sleuth_collector, "email": email_collector},
                ),
                patch(
                    "rebalance.ingest.index_ops._refresh_apple_reminders",
                    return_value={"scope": "apple_reminders", "reminders": 0},
                ),
                patch("rebalance.ingest.index_ops._refresh_email", return_value={"scope": "email", "messages": 0}),
                patch("rebalance.ingest.index_ops._refresh_clio", return_value={"scope": "clio", "prompts": 0}),
                patch("rebalance.ingest.index_ops._refresh_figma", return_value={"scope": "figma", "comments": 0}),
                patch(
                    "rebalance.ingest.note_builder.build_dashboard_note_content", return_value="# Dashboard\n\nContent"
                ),
                patch("rebalance.ingest.embedder._load_model", return_value=(MagicMock(), MagicMock())),
                patch(
                    "rebalance.ingest.embedder._embed_batch",
                    side_effect=lambda m, t, texts: [[0.1] * 384 for _ in texts],
                ),
            ):
                res_ac = refresh_index(self.db_path, vault_path=str(v_path))
                self.assertEqual(res_ac["errors"], [])
                v_res_ac = next(r for r in res_ac["results"] if r["scope"] == "vault")
                self.assertFalse(v_res_ac["embed_chunks"]["deferred_battery"])
                self.assertGreater(v_res_ac["embed_chunks"]["embedded"], 0)
                dash_res_ac = next(r for r in res_ac["results"] if r["scope"] == "dashboard")
                self.assertFalse(dash_res_ac["embed_chunks"]["deferred_battery"])

                # Status check: persistent status reports power_deferred=False after drain
                status_ac = get_index_status(self.db_path)
                self.assertFalse(status_ac["sources"]["vault"]["power_deferred"])
                self.assertFalse(status_ac["freshness"]["power_deferred"])

            with db_connection(self.db_path) as conn:
                embedded_after = conn.execute("SELECT count(*) FROM embeddings").fetchone()[0]
                self.assertGreaterEqual(embedded_after, chunk_count)


if __name__ == "__main__":
    unittest.main()

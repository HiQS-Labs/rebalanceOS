"""Tests for the Collector registry in index_ops."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from rebalance.ingest.index_ops import (
    COLLECTORS,
    Collector,
    _all_scope_names,
    _scope_values,
    refresh_index,
    register_collector,
)


class CollectorRegistryTests(unittest.TestCase):
    def test_builtin_collectors_registered(self) -> None:
        for name in ("vault", "github", "calendar", "sleuth", "email", "semantic", "sync"):
            self.assertIn(name, COLLECTORS, f"missing built-in collector {name}")

    def test_scope_values_includes_all(self) -> None:
        values = _scope_values()
        self.assertIn("all", values)
        for name in ("vault", "github", "calendar", "sync"):
            self.assertIn(name, values)

    def test_all_scope_is_raw_sources_only(self) -> None:
        # `all` token narrowed to raw incoming sources (Decision A / Phase 1b).
        # `clio` joined the raw sources in GH-141.
        self.assertEqual(
            sorted(_all_scope_names()),
            sorted(["vault", "github", "calendar", "sleuth", "email", "clio"]),
        )

    def test_default_refresh_recipe_includes_follow_on_stages(self) -> None:
        # The no-scope default still runs raw sources + code/semantic/sync.
        from rebalance.ingest.index_ops import _default_refresh_scopes

        self.assertEqual(
            sorted(_default_refresh_scopes()),
            sorted(
                [
                    "vault",
                    "github",
                    "calendar",
                    "sleuth",
                    "email",
                    "clio",
                    "code",
                    "semantic",
                    "sync",
                ]
            ),
        )

    def test_register_new_collector_then_unregister(self) -> None:
        calls: list[dict[str, Any]] = []

        def _refresh(db: Path, **opts: Any) -> dict[str, Any]:
            calls.append(opts)
            return {"scope": "linear_test", "dry_run": opts.get("dry_run", False)}

        try:
            register_collector(Collector("linear_test", _refresh, included_in_all=False))
            self.assertIn("linear_test", COLLECTORS)
            # included_in_all=False keeps it OUT of the "all" expansion
            self.assertNotIn("linear_test", _all_scope_names())
            # But it shows up in the full scope-values list
            self.assertIn("linear_test", _scope_values())
            # And calling its refresh works
            result = COLLECTORS["linear_test"].refresh(Path("/tmp/x"), dry_run=True)
            self.assertEqual(result, {"scope": "linear_test", "dry_run": True})
        finally:
            COLLECTORS.pop("linear_test", None)

    def test_duplicate_registration_raises(self) -> None:
        def _refresh(db: Path, **opts: Any) -> dict[str, Any]:
            return {"scope": "vault"}

        with self.assertRaises(ValueError):
            register_collector(Collector("vault", _refresh))

    def test_reserved_name_rejected(self) -> None:
        def _refresh(db: Path, **opts: Any) -> dict[str, Any]:
            return {"scope": "all"}

        with self.assertRaises(ValueError):
            register_collector(Collector("all", _refresh))

    def test_refresh_index_dispatches_through_registry(self) -> None:
        """refresh_index must route scope keys through COLLECTORS, not legacy code."""
        calls: list[tuple[Path, dict[str, Any]]] = []

        def _mock_refresh(db: Path, **opts: Any) -> dict[str, Any]:
            calls.append((db, opts))
            return {"scope": "smoke_test", "synced": 1}

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            try:
                register_collector(Collector("smoke_test", _mock_refresh, included_in_all=False))
                result = refresh_index(
                    db_path,
                    scope=["smoke_test"],
                    dry_run=False,
                    update_dashboard_note=False,
                )
                # The dispatcher must have called our collector exactly once.
                self.assertEqual(len(calls), 1, "collector was not called by refresh_index")
                called_db, called_opts = calls[0]
                self.assertEqual(called_db, db_path.resolve())
                # Result envelope must include our collector's return value.
                scopes_in_result = [r.get("scope") for r in result.get("results", [])]
                self.assertIn("smoke_test", scopes_in_result)
            finally:
                COLLECTORS.pop("smoke_test", None)

    def test_embed_or_defer_separates_deferral_from_failure(self) -> None:
        """GH-296: a guard deferral becomes a stand-in result; a mid-run trip still raises."""
        from rebalance.ingest import _job_guard
        from rebalance.ingest.index_ops import _embed_or_defer, _embedding_deferred

        mod = _job_guard.load_job_guard()
        self.assertIsNotNone(mod)

        def _refused(**_: Any) -> Any:
            raise mod.RefusedToStart("refusing to start: memory compressor holds 9.3 GB")

        def _locked(**_: Any) -> Any:
            raise mod.InstanceConflict("job 'rebalance-embed' is already running")

        def _tripped(**_: Any) -> Any:
            raise mod.MemoryCeilingExceeded("process tree holds 5 GB, ceiling is 3 GB")

        self.assertIn("refusing to start", _embedding_deferred(_embed_or_defer(_refused)))
        self.assertIn("already running", _embedding_deferred(_embed_or_defer(_locked)))
        with self.assertRaises(mod.MemoryCeilingExceeded):
            _embed_or_defer(_tripped)
        self.assertIsNone(_embedding_deferred(object()))

    def test_vault_keeps_its_ingest_when_embedding_is_deferred(self) -> None:
        """GH-296 final QA F4: ingest ran before the guarded leaf refused; it must stay visible."""
        from types import SimpleNamespace
        from unittest import mock

        from rebalance.ingest import _job_guard
        from rebalance.ingest.index_ops import _refresh_vault, classify_sync_outcome

        mod = _job_guard.load_job_guard()
        ingest = SimpleNamespace(
            total_files=10,
            new_files=3,
            updated_files=1,
            touched_files=0,
            deleted_files=0,
            total_chunks=40,
            elapsed_seconds=0.1,
        )

        def _refused(**_: Any) -> Any:
            raise mod.RefusedToStart("refusing to start: memory compressor holds 9.3 GB")

        with (
            mock.patch("rebalance.ingest.note_ingester.ingest_vault", return_value=ingest),
            mock.patch("rebalance.ingest.embedder.embed_chunks", side_effect=_refused),
        ):
            result = _refresh_vault(Path("/tmp/x.db"), Path("/tmp/vault"), dry_run=False)

        self.assertEqual(result["ingest"]["new_files"], 3, "completed ingest work was discarded")
        self.assertIn("refusing to start", result["embedding_deferred"])
        self.assertEqual(result["embed_chunks"]["embedded"], 0)
        self.assertEqual(classify_sync_outcome({"results": [result]}), ("degraded", 0))


if __name__ == "__main__":
    unittest.main()

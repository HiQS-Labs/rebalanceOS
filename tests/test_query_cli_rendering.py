"""`rebalance ask` and `rebalance semantic-query` crashed on every real question.

Both bugs are presentation-layer only — the underlying data was always correct — and both
were found the same way: running the shipped, documented query commands against the live
database rather than a synthetic fixture, per the debug-mantra rule of reproducing against the
real artifact before theorizing.

`ask`: ``cli/query.py``'s GitHub-artifact printer read ``item['repo_full_name']`` and
``item['source_number']`` as top-level keys. They have never lived there — the querier's own
LLM prompt builder (``querier._build_prompt``) has always read them correctly, from inside
``item['metadata']``, and never crashed. The printer was wrong from the initial commit
(``cb1de2c``); it crashed on every call that returned a GitHub hit, which is nearly all of them.

`semantic-query`: ``cli/semantic.py`` formatted ``result['similarity_score']`` with ``:.3f``
unconditionally. A document that matches only the lexical (FTS) leg of the hybrid search, never
the vector leg, carries no distance by design (see ``semantic_index._rrf_fuse``'s docstring) —
``similarity_score`` is legitimately ``None``, not a data bug.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from typer.testing import CliRunner

from rebalance.cli import app
from rebalance.ingest.querier import QueryResult

runner = CliRunner()

GITHUB_HIT = {
    "doc_id": 1,
    "source_type": "github",
    "doc_kind": "issue",
    "title": "Fix the thing",
    "body_preview": "...",
    "metadata": {"repo_full_name": "acme/widgets", "item_type": "issue", "source_number": 42},
    "updated_at": "2026-08-18T00:00:00Z",
    "similarity_score": 0.812,
}


class AskCommandRenderingTests(unittest.TestCase):
    """The literal outage: any GitHub semantic hit crashed the whole command."""

    def _invoke(self, result: QueryResult):
        with (
            patch("rebalance.ingest.querier.ask", return_value=result),
            patch("rebalance.cli.query.resolve_database_path", return_value="/dev/null"),
        ):
            return runner.invoke(app, ["ask", "anything", "--no-llm"])

    def test_a_github_semantic_hit_no_longer_crashes_the_command(self):
        result = QueryResult(query="q", synthesis="", github_semantic_context=[GITHUB_HIT])
        out = self._invoke(result)
        self.assertEqual(out.exit_code, 0, out.output)
        self.assertIn("acme/widgets", out.output)
        self.assertIn("issue", out.output)
        self.assertIn("#42", out.output)
        self.assertIn("Fix the thing", out.output)

    def test_a_hit_missing_metadata_degrades_instead_of_crashing(self):
        """Absence of a field must render as '?', never raise — this is diagnostic output,
        not a contract the caller can fail on."""
        bare = {**GITHUB_HIT, "metadata": {}}
        result = QueryResult(query="q", synthesis="", github_semantic_context=[bare])
        out = self._invoke(result)
        self.assertEqual(out.exit_code, 0, out.output)
        self.assertIn("?", out.output)

    def test_a_fts_only_hit_with_no_similarity_score_renders_as_na(self):
        """The RRF-fused case: no vector distance, so no score — legitimate, not an error."""
        no_score = {**GITHUB_HIT, "similarity_score": None}
        result = QueryResult(query="q", synthesis="", github_semantic_context=[no_score])
        out = self._invoke(result)
        self.assertEqual(out.exit_code, 0, out.output)
        self.assertIn("n/a", out.output)

    def test_a_vault_only_answer_is_unaffected(self):
        """The common case (no GitHub hits at all) must keep working exactly as before."""
        result = QueryResult(
            query="q",
            synthesis="",
            vault_activity=[{"title": "Note", "file_path": "n.md", "last_modified": "2026-08-18T00:00:00Z"}],
        )
        out = self._invoke(result)
        self.assertEqual(out.exit_code, 0, out.output)


class SemanticQueryCommandRenderingTests(unittest.TestCase):
    def _invoke(self, results):
        with (
            patch("rebalance.ingest.semantic_index.query", return_value=results),
            patch("rebalance.cli.semantic.resolve_database_path", return_value="/dev/null"),
        ):
            return runner.invoke(app, ["semantic-query", "anything"])

    def test_a_result_with_no_similarity_score_no_longer_crashes(self):
        rows = [
            {
                "source_type": "github",
                "doc_kind": "direct_commit",
                "title": "initial commit",
                "body_preview": "...",
                "metadata": {},
                "updated_at": None,
                "similarity_score": None,
            }
        ]
        out = self._invoke(rows)
        self.assertEqual(out.exit_code, 0, out.output)
        self.assertIn("n/a", out.output)

    def test_a_normal_scored_result_still_renders_the_score(self):
        rows = [
            {
                "source_type": "vault",
                "doc_kind": "chunk",
                "title": "Note",
                "body_preview": "...",
                "metadata": {},
                "updated_at": None,
                "similarity_score": 0.5,
            }
        ]
        out = self._invoke(rows)
        self.assertEqual(out.exit_code, 0, out.output)
        self.assertIn("0.500", out.output)


if __name__ == "__main__":
    unittest.main()

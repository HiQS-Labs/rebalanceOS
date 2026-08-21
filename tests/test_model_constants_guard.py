"""Gemini and Chat model constants must exist in ONE place (GH-109).

Pins:
- `DEFAULT_GEMINI_MODEL` in `rebalance.ingest.querier` is the single owner of the Gemini model ID.
- `DEFAULT_CHAT_MODEL` in `rebalance.ingest.querier` is the single owner of the local chat model ID.
- No other module in `src/rebalance/` may write down a hardcoded Gemini or Chat model literal.
- CLI options and internal defaults across `note_builder`, `cli.dashboard`, `repair`, and `cli.query`
  must default to these shared constants.
- Includes a negative control verifying that reintroducing a literal fails the guard.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from rebalance.ingest.querier import DEFAULT_CHAT_MODEL, DEFAULT_GEMINI_MODEL

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "rebalance"

#: Regex matching Gemini model identifiers in string literals (e.g. "gemini-3.5-flash", "gemini-2.5-flash")
_GEMINI_MODEL_LITERAL = re.compile(r"""["']gemini-(?:1\.5|2\.0|2\.5|3\.0|3\.5)-(?:flash|pro|flash-lite)["']""")

#: Regex matching Qwen chat model identifiers in string literals
_CHAT_MODEL_LITERAL = re.compile(r"""["']Qwen/Qwen3-[0-9.]+B["']""")


def _find_model_offenders(src_dir: Path) -> list[str]:
    offenders: list[str] = []
    for py_path in sorted(src_dir.rglob("*.py")):
        # querier.py is the single canonical definition owner
        if py_path.name == "querier.py":
            continue
        content = py_path.read_text(encoding="utf-8")
        for match in _GEMINI_MODEL_LITERAL.finditer(content):
            line = content[: match.start()].count("\n") + 1
            rel_path = py_path.relative_to(src_dir)
            offenders.append(f"{rel_path}:{line} Gemini literal {match.group(0)}")
        for match in _CHAT_MODEL_LITERAL.finditer(content):
            line = content[: match.start()].count("\n") + 1
            rel_path = py_path.relative_to(src_dir)
            offenders.append(f"{rel_path}:{line} Chat literal {match.group(0)}")
    return offenders


class ModelConstantsGuardTests(unittest.TestCase):
    def test_no_module_outside_querier_writes_gemini_or_chat_model_literal(self) -> None:
        """THE PIN (GH-109): Modules must import DEFAULT_GEMINI_MODEL / DEFAULT_CHAT_MODEL."""
        offenders = _find_model_offenders(SRC_DIR)
        self.assertEqual(
            offenders,
            [],
            "Modules must import DEFAULT_GEMINI_MODEL / DEFAULT_CHAT_MODEL from querier, not repeat model literals:\n"
            + "\n".join(offenders),
        )

    def test_note_builder_uses_shared_gemini_constant(self) -> None:
        from rebalance.ingest import note_builder
        import inspect

        sig = inspect.signature(note_builder.build_dashboard_note_content)
        self.assertEqual(sig.parameters["gemini_model"].default, DEFAULT_GEMINI_MODEL)

    def test_repair_uses_shared_gemini_constant(self) -> None:
        from rebalance import repair

        self.assertEqual(repair._LLM_MODEL, DEFAULT_GEMINI_MODEL)

    def test_cli_dashboard_uses_shared_gemini_constant(self) -> None:
        from rebalance.cli import dashboard

        self.assertEqual(dashboard.DEFAULT_GEMINI_MODEL, DEFAULT_GEMINI_MODEL)

    def test_cli_query_uses_shared_chat_constant(self) -> None:
        from rebalance.cli import query

        self.assertEqual(query.DEFAULT_CHAT_MODEL, DEFAULT_CHAT_MODEL)

    def test_negative_control_detects_introduced_literal(self) -> None:
        """Negative control: reintroducing a literal at a site fails the guard."""
        fake_code = 'gemini_model: str = "gemini-3.5-flash"\nchat_model: str = "Qwen/Qwen3-0.6B"\n'
        gemini_matches = list(_GEMINI_MODEL_LITERAL.finditer(fake_code))
        chat_matches = list(_CHAT_MODEL_LITERAL.finditer(fake_code))
        self.assertEqual(len(gemini_matches), 1)
        self.assertEqual(gemini_matches[0].group(0), '"gemini-3.5-flash"')
        self.assertEqual(len(chat_matches), 1)
        self.assertEqual(chat_matches[0].group(0), '"Qwen/Qwen3-0.6B"')


if __name__ == "__main__":
    unittest.main()

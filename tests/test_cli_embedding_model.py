"""The embedding model name must exist in ONE place (GH-105).

`rebalance semantic-query` was broken for every invocation that did not pass
`--model` explicitly:

    OperationalError: Dimension mismatch for query vector for the "embedding"
    column. Expected 384 dimensions but received 1024.

The GH-81 migration moved the index to ``BAAI/bge-small-en-v1.5`` (384-dim) by
editing ``embedder.DEFAULT_MODEL``. Six CLI commands had their own copy of the
old ``Qwen/Qwen3-Embedding-0.6B`` string, so they kept embedding queries at 1024
dimensions against a 384-dimension column. Nothing failed at import, nothing
failed in CI, and all 45 doctor checks reported healthy — the break only existed
at the moment a human ran the command.

Pinning the six call sites individually would leave the seventh a coin flip, so
these tests state the invariant over the CLI package as a whole: no module may
write an embedding model identifier down, and the default a user gets must equal
the default the index was built with.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from rebalance.ingest.embedder import DEFAULT_MODEL, EMBEDDING_DIM

CLI_DIR = Path(__file__).resolve().parents[1] / "src" / "rebalance" / "cli"

#: A HuggingFace-style identifier (``org/model-name``) inside a string literal.
#: Deliberately broad — the point is to catch the NEXT hardcoded model, whatever
#: vendor it comes from, not to enumerate the ones already retired.
_MODEL_LITERAL = re.compile(
    r"""["'][A-Za-z0-9_.-]+/[A-Za-z0-9_.-]*(?:[Ee]mbedding|bge|gte|e5|minilm)[A-Za-z0-9_.-]*["']"""
)

#: ``model: str = typer.Option(<default>, ...)`` — captures the default expression.
#: The lookbehind keeps this to the EMBEDDING model option. ``chat_model`` and
#: ``gemini_model`` are different parameters with their own constants
#: (``querier.DEFAULT_CHAT_MODEL`` / ``DEFAULT_GEMINI_MODEL``); they carry the
#: same duplication shape but are not this bug, and folding them in here would
#: make the test assert something it does not mean.
_MODEL_OPTION = re.compile(r"(?<![A-Za-z0-9_])model:\s*str\s*=\s*typer\.Option\(\s*([^,\n]+)")


def _cli_sources() -> list[tuple[Path, str]]:
    return [(p, p.read_text(encoding="utf-8")) for p in sorted(CLI_DIR.glob("*.py"))]


class NoHardcodedModelTests(unittest.TestCase):
    def test_no_cli_module_writes_a_model_identifier_down(self) -> None:
        """THE PIN. This is the test that would have failed during GH-81."""
        offenders: list[str] = []
        for path, src in _cli_sources():
            for match in _MODEL_LITERAL.finditer(src):
                line = src[: match.start()].count("\n") + 1
                offenders.append(f"{path.name}:{line} {match.group(0)}")
        self.assertEqual(
            offenders,
            [],
            "CLI modules must import embedder.DEFAULT_MODEL, not repeat a model name:\n" + "\n".join(offenders),
        )

    def test_every_model_option_defaults_to_the_shared_constant(self) -> None:
        """The complement: catches a default that is neither a literal nor the
        constant (a second alias, a config lookup, a stale re-export)."""
        found = 0
        for path, src in _cli_sources():
            for match in _MODEL_OPTION.finditer(src):
                found += 1
                default = match.group(1).strip()
                line = src[: match.start()].count("\n") + 1
                with self.subTest(site=f"{path.name}:{line}"):
                    self.assertEqual(default, "DEFAULT_MODEL", f"{path.name}:{line} defaults to {default}")
        self.assertGreater(found, 0, "no --model options found; the regex has drifted from the code")


class DefaultsAgreeTests(unittest.TestCase):
    def test_the_cli_default_is_the_model_the_index_was_built_with(self) -> None:
        from rebalance.cli import github, ingest_cmds, query, semantic

        for module in (semantic, query, ingest_cmds, github):
            with self.subTest(module=module.__name__):
                self.assertEqual(module.DEFAULT_MODEL, DEFAULT_MODEL)

    def test_the_model_and_its_dimension_stay_together(self) -> None:
        """A guard on the pair that drifted. ``EMBEDDING_DIM`` is a plain constant
        beside ``DEFAULT_MODEL``, not derived from it, so a model swap that misses
        the dimension reproduces the same mismatch from the other direction."""
        self.assertEqual((DEFAULT_MODEL, EMBEDDING_DIM), ("BAAI/bge-small-en-v1.5", 384))


if __name__ == "__main__":
    unittest.main()

"""GH-5 Phase 1 — canonical LLM-JSON parsing in rebalance.lib.json_ops.

Two jobs:

1. Cover `json_ops` itself — it had zero test coverage before this phase.
2. **The golden-fixture equivalence gate.** `utils/3-eyes/three_eyes/classify.py`
   keeps its own copy of this logic on purpose: 3-Eyes is a standalone package
   that runs from its own launchd shim under a limited PYTHONPATH and is designed
   to degrade gracefully when the repo venv is absent, so importing
   `rebalance.lib` would break it in exactly the conditions it exists to survive.
   The duplication is deliberate; this test is what keeps it honest. Both copies
   are fed the same fixture corpus and must agree on every case.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from rebalance.lib.json_ops import (
    first_json_object,
    parse_llm_json,
    strip_code_fences,
)

_THREE_EYES = Path(__file__).resolve().parents[1] / "utils" / "3-eyes"


def _load_classify():
    """Import 3-Eyes' classify module without importing it as `rebalance.*`.

    Loaded by file path so this test exercises the standalone package exactly as
    it ships, rather than any repo-installed variant.
    """
    if str(_THREE_EYES) not in sys.path:
        sys.path.insert(0, str(_THREE_EYES))
    spec = importlib.util.spec_from_file_location("three_eyes.classify", _THREE_EYES / "three_eyes" / "classify.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The shared corpus. Every case is a real shape a model has produced or could
# produce; each one previously discarded a good answer somewhere in this repo.
GOLDEN_CASES: list[tuple[str, str]] = [
    ("plain object", '{"severity": "error", "action": "file"}'),
    ("fenced with language tag", '```json\n{"severity": "error"}\n```'),
    ("fenced without language tag", '```\n{"severity": "warn"}\n```'),
    ("fenced with surrounding whitespace", '  ```json\n{"a": 1}\n```  '),
    ("trailing unfenced prose", '{"severity": "error"}\nHere is why I said that.'),
    ("leading prose then object", 'Sure! {"severity": "notice"}'),
    ("brace inside a string literal", '{"note": "a } inside a string", "ok": true}'),
    ("explicit null value", '{"severity": null, "action": "file"}'),
    ("nested object", '{"outer": {"inner": [1, 2, 3]}}'),
    ("non-object json array", "[1, 2, 3]"),
    ("non-object json scalar", '"just a string"'),
    ("malformed json", '{"severity": '),
    ("empty string", ""),
    ("whitespace only", "   \n  "),
    ("fence with nothing inside", "```json\n```"),
    ("prose only, no json at all", "I could not classify this."),
    ("unicode content", '{"msg": "café — naïve"}'),
]


class GoldenFixtureEquivalenceTests(unittest.TestCase):
    """The gate: the canonical copy and 3-Eyes' untouched copy must agree.

    If this fails, the two copies have drifted — fix both, or delete one and
    accept the coupling deliberately. Do not silence it.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.classify = _load_classify()

    def test_parse_llm_json_matches_three_eyes_parse_model_json(self) -> None:
        for label, raw in GOLDEN_CASES:
            with self.subTest(case=label):
                self.assertEqual(
                    self.classify._parse_model_json(raw),
                    parse_llm_json(raw),
                    f"copies disagree on {label!r}: {raw!r}",
                )

    def test_first_json_object_matches_three_eyes_copy(self) -> None:
        for label, raw in GOLDEN_CASES:
            with self.subTest(case=label):
                self.assertEqual(
                    self.classify._first_json_object(raw),
                    first_json_object(raw),
                    f"copies disagree on {label!r}: {raw!r}",
                )

    def test_three_eyes_copy_is_still_standalone(self) -> None:
        """3-Eyes must not have been quietly rewired to import rebalance.lib —
        that is the coupling this duplication exists to avoid."""
        source = (_THREE_EYES / "three_eyes" / "classify.py").read_text(encoding="utf-8")
        self.assertNotIn("rebalance.lib", source)
        self.assertNotIn("from rebalance", source)


class StripCodeFencesTests(unittest.TestCase):
    def test_strips_language_tagged_fence(self) -> None:
        self.assertEqual('{"a": 1}', strip_code_fences('```json\n{"a": 1}\n```'))

    def test_strips_bare_fence(self) -> None:
        self.assertEqual('{"a": 1}', strip_code_fences('```\n{"a": 1}\n```'))

    def test_unfenced_text_passes_through_stripped(self) -> None:
        self.assertEqual('{"a": 1}', strip_code_fences('  {"a": 1}  '))

    def test_handles_none_and_empty(self) -> None:
        self.assertEqual("", strip_code_fences(""))
        self.assertEqual("", strip_code_fences(None))  # type: ignore[arg-type]


class ParseLlmJsonTests(unittest.TestCase):
    def test_fenced_json(self) -> None:
        self.assertEqual({"severity": "error"}, parse_llm_json('```json\n{"severity": "error"}\n```'))

    def test_trailing_conversational_prose(self) -> None:
        # The "Extra data" case: json.loads alone would discard this entirely.
        self.assertEqual(
            {"severity": "error"},
            parse_llm_json('{"severity": "error"}\nHere is why I said that.'),
        )

    def test_non_object_json_is_rejected(self) -> None:
        self.assertIsNone(parse_llm_json("[1, 2, 3]"))
        self.assertIsNone(parse_llm_json('"just a string"'))

    def test_malformed_json_returns_none_rather_than_raising(self) -> None:
        # Every caller's correct response to a non-complying model is a
        # fallback, not a traceback.
        self.assertIsNone(parse_llm_json('{"severity": '))
        self.assertIsNone(parse_llm_json("not json at all"))

    def test_explicit_nulls_dropped_by_default(self) -> None:
        # setdefault only fills a MISSING key, so a surviving None would render
        # as the literal "None" in operator-facing output.
        self.assertEqual({"action": "file"}, parse_llm_json('{"severity": null, "action": "file"}'))

    def test_nulls_retained_when_opted_out(self) -> None:
        self.assertEqual(
            {"severity": None, "action": "file"},
            parse_llm_json('{"severity": null, "action": "file"}', drop_nulls=False),
        )

    def test_brace_inside_string_literal_not_miscounted(self) -> None:
        self.assertEqual(
            {"note": "a } inside a string", "ok": True},
            parse_llm_json('{"note": "a } inside a string", "ok": true}'),
        )


class FirstJsonObjectTests(unittest.TestCase):
    def test_finds_object_after_leading_prose(self) -> None:
        self.assertEqual({"severity": "notice"}, first_json_object('Sure! {"severity": "notice"}'))

    def test_returns_none_without_an_object(self) -> None:
        self.assertIsNone(first_json_object("no braces here"))
        self.assertIsNone(first_json_object(""))

    def test_returns_none_for_non_dict_json(self) -> None:
        self.assertIsNone(first_json_object("[1, 2, 3]"))


class DeadCodeRemovedTests(unittest.TestCase):
    def test_reporter_dead_fence_helper_is_gone(self) -> None:
        """`_strip_code_fence` was defined and never called — deleted, not
        migrated. Pinned so it does not get resurrected alongside the shared one."""
        source = (Path(__file__).resolve().parents[1] / "scripts" / "health_issue_reporter.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("def _strip_code_fence", source)


if __name__ == "__main__":
    unittest.main()

"""GH-5 Phase 5a — chunking golden contract.

`rebalance.lib.text_ops.split_oversized` is a deliberate duplicate of
`HiQS/hiqs/chunking.py:split_oversized`. HiQS is architected as an independent
library planned for extraction to `HiQS-Suite/HiQS`, so rewiring it to import
from `rebalance.lib` would create coupling that has to be undone at extraction
time. The duplication is the intended resolution; this file is the gate that
keeps it honest.

Phase 5a is preparatory ONLY. Nothing in rebalance's write paths calls the
promoted copy yet — wiring it into `note_ingester`/`semantic_index` is Phase 5b,
split out because those paths key each semantic document 1:1 off a `chunks` row
id, and splitting a chunk without a stable child-key scheme plus a stale-child
deletion policy would break document identity on re-index.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from rebalance.lib.text_ops import MAX_CHUNK_CHARS, split_oversized

_ROOT = Path(__file__).resolve().parents[1]
_HIQS = _ROOT / "HiQS"


def _load_hiqs_chunking():
    """Load HiQS' chunking module by file path, as the standalone package ships it."""
    if str(_HIQS) not in sys.path:
        sys.path.insert(0, str(_HIQS))
    spec = importlib.util.spec_from_file_location(
        "hiqs.chunking", _HIQS / "hiqs" / "chunking.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The golden corpus. Each case is a document shape the real corpus contains, and
# each exercises a different branch of the splitter.
GOLDEN_BODIES: list[tuple[str, str]] = [
    ("empty", ""),
    ("whitespace only", "   \n\n   \n  "),
    ("short body under cap", "a short note that needs no splitting at all"),
    ("exactly at cap", "x" * MAX_CHUNK_CHARS),
    ("one char over cap", "x" * (MAX_CHUNK_CHARS + 1)),
    ("paragraphs that pack", "\n\n".join(["para " + "y" * 200] * 6)),
    ("paragraphs that do not fit", "\n\n".join(["z" * 700, "w" * 700])),
    ("lines within one paragraph", "\n".join(["line " + "q" * 100] * 12)),
    ("single unsplittable long line", "u" * 2500),
    ("url wall", " ".join(["https://example.com/" + "p" * 60] * 20)),
    ("mixed paragraphs and long line", "short para\n\n" + "m" * 1900 + "\n\nanother para"),
    ("trailing whitespace past cap", "real content\n\n" + "   " * 400),
    ("markdown table", "\n".join(["| a | b | c |", "|---|---|---|"] + ["| 1 | 2 | 3 |"] * 80)),
    ("unicode prose", ("café — naïve résumé. " * 60)),
    ("crlf-ish mixed newlines", "a\n\nb\nc\n\n" + "d" * 900),
]

# Cap values worth probing independently of the default.
GOLDEN_CAPS = [1, 7, 50, 100, MAX_CHUNK_CHARS, 5000]


class GoldenEquivalenceTests(unittest.TestCase):
    """The gate: the promoted copy and HiQS' original must agree exactly.

    If this fails the two copies have drifted. Fix both — do not silence it, and
    do not "fix" it by making HiQS import from rebalance.lib.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.hiqs = _load_hiqs_chunking()

    def test_default_cap_output_is_identical(self) -> None:
        for label, body in GOLDEN_BODIES:
            with self.subTest(case=label):
                self.assertEqual(
                    self.hiqs.split_oversized(body),
                    split_oversized(body),
                    f"copies disagree on {label!r}",
                )

    def test_every_cap_output_is_identical(self) -> None:
        for cap in GOLDEN_CAPS:
            for label, body in GOLDEN_BODIES:
                with self.subTest(cap=cap, case=label):
                    self.assertEqual(
                        self.hiqs.split_oversized(body, cap),
                        split_oversized(body, cap),
                        f"copies disagree on {label!r} at cap={cap}",
                    )

    def test_cap_constant_matches(self) -> None:
        self.assertEqual(self.hiqs.MAX_CHUNK_CHARS, MAX_CHUNK_CHARS)

    def test_invalid_cap_raises_identically(self) -> None:
        for cap in (0, -1):
            with self.subTest(cap=cap):
                with self.assertRaises(ValueError):
                    split_oversized("anything", cap)
                with self.assertRaises(ValueError):
                    self.hiqs.split_oversized("anything", cap)

    def test_hiqs_copy_is_still_standalone(self) -> None:
        """HiQS must not have been quietly rewired to import rebalance — that is
        the coupling this duplication exists to avoid."""
        source = (_HIQS / "hiqs" / "chunking.py").read_text(encoding="utf-8")
        self.assertNotIn("rebalance", source)


class ChunkingContractTests(unittest.TestCase):
    """Properties the promoted copy must hold on its own, independent of HiQS."""

    def test_bodies_within_cap_are_returned_unsplit_and_unmodified(self) -> None:
        body = "a note well under the cap"
        self.assertEqual([body], split_oversized(body))

    def test_no_part_exceeds_the_cap(self) -> None:
        for label, body in GOLDEN_BODIES:
            for cap in GOLDEN_CAPS:
                with self.subTest(case=label, cap=cap):
                    for part in split_oversized(body, cap):
                        # The under-cap early return hands the body back whole.
                        if len(body) <= cap:
                            continue
                        self.assertLessEqual(len(part), cap)

    def test_never_returns_an_empty_list(self) -> None:
        """A document must never vanish — a whitespace-only body past the cap
        would otherwise silently drop."""
        for label, body in GOLDEN_BODIES:
            with self.subTest(case=label):
                self.assertTrue(split_oversized(body))

    def test_no_overlap_between_parts(self) -> None:
        """Deliberate design choice: overlap would put the same text in the index
        twice and make a ranked list look confident about one repeated note."""
        body = "\n\n".join(f"paragraph number {i} " + "t" * 300 for i in range(8))
        parts = split_oversized(body)
        self.assertGreater(len(parts), 1)
        rejoined = "".join(parts)
        # Every part's content appears exactly once across the output.
        for part in parts:
            self.assertEqual(1, rejoined.count(part))


class NotYetWiredTests(unittest.TestCase):
    """Phase 5a is preparatory. Pinned so 5b's wiring is a deliberate, reviewed
    change rather than something that drifts in unnoticed."""

    def test_no_write_path_imports_text_ops_yet(self) -> None:
        offenders = []
        for name in ("note_ingester.py", "semantic_index.py"):
            path = _ROOT / "src" / "rebalance" / "ingest" / name
            if path.exists() and "text_ops" in path.read_text(encoding="utf-8"):
                offenders.append(name)
        self.assertEqual(
            [],
            offenders,
            "a write path now imports text_ops — that is Phase 5b, which needs a "
            "stable child source_pk scheme and a stale-child deletion policy first",
        )


if __name__ == "__main__":
    unittest.main()

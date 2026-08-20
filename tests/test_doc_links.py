"""Pin the doc-link checker's code-awareness (GH-92).

The checker exists to hold GH-88's repair at zero. The thing most likely to regress is
not "does it find broken links" but "does it stay quiet about code examples". A naive
matcher flags inline code spans that document markdown syntax; during GH-88 one such
false positive was 'repaired' from `![a](100%.png)` into `![a 100%.png]`, destroying the
meaning of a technical sentence, and ROADMAP.md's own row-format template was de-linked.

A CI gate that produces those gets disabled, taking the real guard with it. Hence these
tests weigh false positives at least as heavily as true ones.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_doc_links as checker  # noqa: E402


class IterLinksTests(unittest.TestCase):
    def targets(self, text: str) -> list[str]:
        return [t for _ln, _label, t in checker.iter_links(text)]

    def test_plain_link_is_found(self) -> None:
        self.assertEqual(self.targets("see [x](a/b.md) here"), ["a/b.md"])

    def test_inline_code_span_is_ignored(self) -> None:
        # The exact shape that got mangled during GH-88.
        text = "markdown-it's own `![a](100%.png)` syntax percent-encodes stray `%`."
        self.assertEqual(self.targets(text), [])

    def test_roadmap_row_template_is_ignored(self) -> None:
        # ROADMAP.md documents its own row format inside backticks.
        text = "- **Project** — one-line summary. → `[linked project doc](PROJECT/...)`"
        self.assertEqual(self.targets(text), [])

    def test_fenced_block_is_ignored(self) -> None:
        text = "before\n```markdown\n[ex](never-exists.md)\n```\nafter [real](r.md)"
        self.assertEqual(self.targets(text), ["r.md"])

    def test_tilde_fence_is_ignored(self) -> None:
        text = "~~~\n[ex](never-exists.md)\n~~~\n[real](r.md)"
        self.assertEqual(self.targets(text), ["r.md"])

    def test_code_span_and_real_link_on_one_line(self) -> None:
        text = "`[fake](nope.md)` but [real](yes.md) counts"
        self.assertEqual(self.targets(text), ["yes.md"])


class CheckTests(unittest.TestCase):
    def _write(self, tmp: Path, name: str, body: str) -> None:
        p = tmp / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    def test_finds_broken_and_machine_local_but_not_code(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            self._write(tmp, "sub/here.md", "# target\n")
            self._write(
                tmp,
                "doc.md",
                "\n".join(
                    [
                        "[gone](does-not-exist.md)",
                        "[leak](/Users/someone/thing.md)",
                        "[ok](sub/here.md)",
                        "[anchor](sub/here.md#L10)",
                        "[ext](https://example.com/x.md)",
                        "`![a](100%.png)` stays quiet",
                    ]
                ),
            )
            broken, machine, checked = checker.check(tmp)

        self.assertEqual(len(broken), 1, broken)
        self.assertIn("does-not-exist.md", broken[0])
        self.assertEqual(len(machine), 1, machine)
        self.assertIn("/Users/someone/thing.md", machine[0])
        # broken + machine-local + ok + anchored-ok; the external URL and the code span
        # are never counted.
        self.assertEqual(checked, 4)

    def test_anchor_does_not_break_resolution(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            self._write(tmp, "t.md", "# t\n")
            self._write(tmp, "doc.md", "[a](t.md#L5)")
            broken, machine, _ = checker.check(tmp)
        self.assertEqual(broken, [])
        self.assertEqual(machine, [])


class RepoTests(unittest.TestCase):
    def test_repo_is_clean(self) -> None:
        """The whole point: the tree stays at zero. This is the ratchet."""
        broken, machine, checked = checker.check(ROOT)
        self.assertGreater(checked, 100, "scanner found almost nothing — it is probably misconfigured")
        self.assertEqual(broken, [], f"{len(broken)} broken link(s)")
        self.assertEqual(machine, [], f"{len(machine)} machine-local path(s)")


if __name__ == "__main__":
    unittest.main()

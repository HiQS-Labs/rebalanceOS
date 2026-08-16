"""GH-5 Phase 2 — directory-prune consolidation.

Gate for the phase: `rebalance.lib.git_ops` is the sole owner of the prune
blacklist, every in-repo walker shares it, and `local_repos`' widening is
pinned as an *intended* behavior change rather than an accidental side effect.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from rebalance.ingest import ask_self_scan, focus5_scan, local_repos
from rebalance.lib.git_ops import DEFAULT_PRUNE_DIRS, should_descend


def _make_checkout(path: Path) -> None:
    """Create a directory that walkers recognise as a git checkout."""
    (path / ".git").mkdir(parents=True)


class PruneBlacklistOwnershipTests(unittest.TestCase):
    def test_git_ops_is_the_sole_owner_of_the_blacklist(self) -> None:
        # Moved, not copied: the previous owner must no longer define its own.
        self.assertFalse(
            hasattr(ask_self_scan, "_PRUNE_DIRS"),
            "ask_self_scan still defines _PRUNE_DIRS — the constant was copied, not moved",
        )

    def test_both_harness_walkers_share_one_predicate(self) -> None:
        for name in ("node_modules", "site-packages", "DerivedData"):
            self.assertFalse(ask_self_scan._should_descend(name))
            self.assertFalse(focus5_scan._should_descend(name))
        for name in ("src", "projects", "GH Repos"):
            self.assertTrue(ask_self_scan._should_descend(name))
            self.assertTrue(focus5_scan._should_descend(name))

    def test_hidden_dirs_still_pruned_even_when_not_blacklisted(self) -> None:
        self.assertNotIn(".hidden-thing", DEFAULT_PRUNE_DIRS)
        self.assertFalse(should_descend(".hidden-thing"))


class WalkerCallSiteTests(unittest.TestCase):
    """A pruned non-hidden dir is skipped and a valid nested checkout survives,
    at each consuming call site."""

    def _tree(self, root: Path) -> None:
        # A checkout buried inside a blacklisted, NON-hidden directory. The old
        # dot-dirs-only rule descended here; the shared blacklist does not.
        _make_checkout(root / "node_modules" / "some-package")
        # A legitimate nested checkout that must always survive.
        _make_checkout(root / "projects" / "real-repo")

    def test_local_repos_walk_prunes_node_modules_and_keeps_real_checkout(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root)
            found = local_repos.walk_repo_candidates(root, max_depth=4)
            names = {p.name for p in found}
            self.assertIn("real-repo", names)
            self.assertNotIn("some-package", names)

    def test_focus5_walk_prunes_node_modules_and_keeps_real_checkout(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root)
            found = list(focus5_scan.iter_git_repos([root], max_depth=4))
            names = {p.name for p in found}
            self.assertIn("real-repo", names)
            self.assertNotIn("some-package", names)

    def test_ask_self_harness_walk_prunes_node_modules_and_keeps_real_harness(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for parent in ("node_modules/some-package", "projects/real-repo"):
                harness = root / parent / "ask_self" / "ask_self_harness.json"
                harness.parent.mkdir(parents=True)
                harness.write_text("{}", encoding="utf-8")
            found = list(ask_self_scan.iter_repo_harnesses([root], max_depth=6))
            paths = {str(p) for p in found}
            self.assertTrue(any("real-repo" in p for p in paths))
            self.assertFalse(any("some-package" in p for p in paths))


class IntentionalWideningTests(unittest.TestCase):
    """`local_repos` previously skipped ONLY dot-dirs. Widening it to the full
    blacklist is a real, deliberate behavior change — pinned here so it reads as
    intended rather than as an accident, and so a future revert is loud."""

    def test_local_repos_now_prunes_non_hidden_blacklisted_dirs(self) -> None:
        non_hidden = sorted(d for d in DEFAULT_PRUNE_DIRS if not d.startswith("."))
        self.assertTrue(non_hidden, "blacklist should contain non-hidden entries")

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in non_hidden:
                _make_checkout(root / name / "buried")
            _make_checkout(root / "keep-me")

            found = {p.name for p in local_repos.walk_repo_candidates(root, max_depth=4)}

        # Under the OLD dot-dirs-only rule every one of these would be returned.
        self.assertNotIn("buried", found)
        self.assertEqual({"keep-me"}, found)


class StandaloneScriptStaysDecoupledTests(unittest.TestCase):
    """`experimental/git-pulse/discover-repos.py` sets up no sys.path and imports
    nothing from `rebalance`, so it cannot reach `rebalance.lib` at runtime — the
    same constraint that keeps `health-check.py` out of GH-5 Phase 3. It keeps its
    own lighter walk; this pins that it is not silently coupled later."""

    def test_discover_repos_does_not_import_rebalance(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "experimental" / "git-pulse" / "discover-repos.py"
        )
        source = script.read_text(encoding="utf-8")
        self.assertNotIn("import rebalance", source)
        self.assertNotIn("from rebalance", source)


if __name__ == "__main__":
    unittest.main()

"""Tests for the renamed-org alias map and canonical repo identity (#147).

A renamed GitHub org keeps its old URLs alive via redirects, so a stale spelling
still syncs successfully and writes a mirror copy of every row under the old
name. ``github_org_aliases`` + ``canonical_github_repo_name`` are the one place
that collapse is defined — every consumer (watched set, digest SQL, watchlist
guard) routes through them.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rebalance.ingest import config as config_module


class OrgAliasConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig_config_path = config_module.CONFIG_PATH
        config_module.CONFIG_PATH = Path(self._tmp.name) / "rbos.config"

    def tearDown(self) -> None:
        config_module.CONFIG_PATH = self._orig_config_path

    def test_set_then_get_round_trips_with_lowercased_keys(self) -> None:
        config_module.set_github_org_aliases({"HiQS-Suite": "HiQS-Labs"})

        self.assertEqual(config_module.get_github_org_aliases(), {"hiqs-suite": "HiQS-Labs"})

    def test_unmapped_machine_reads_empty(self) -> None:
        self.assertEqual(config_module.get_github_org_aliases(), {})

    def test_malformed_entries_are_dropped(self) -> None:
        # A repo name is not an org alias; blanks are noise. Neither may survive.
        config_module.set_github_org_aliases(
            {"hiqs-suite": "HiQS-Labs", "a/b": "c", "": "x", "ok": "  "}
        )

        self.assertEqual(config_module.get_github_org_aliases(), {"hiqs-suite": "HiQS-Labs"})


class CanonicalRepoNameTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig_config_path = config_module.CONFIG_PATH
        config_module.CONFIG_PATH = Path(self._tmp.name) / "rbos.config"
        config_module.set_github_org_aliases({"hiqs-suite": "HiQS-Labs"})

    def tearDown(self) -> None:
        config_module.CONFIG_PATH = self._orig_config_path

    def test_old_spelling_rewrites_owner_and_keeps_name_casing(self) -> None:
        self.assertEqual(
            config_module.canonical_github_repo_name("HiQS-Suite/XYZ-forge"),
            "HiQS-Labs/XYZ-forge",
        )

    def test_owner_match_is_case_insensitive_so_casing_variants_merge(self) -> None:
        self.assertEqual(
            config_module.canonical_github_repo_name("hiqs-suite/XYZ-forge"),
            "HiQS-Labs/XYZ-forge",
        )

    def test_unaliased_owner_is_returned_unchanged(self) -> None:
        # Forks of an aliased org's repo live under other owners and must not be
        # collapsed into the org (#147).
        self.assertEqual(
            config_module.canonical_github_repo_name("arnoldadero/XYZ-forge"),
            "arnoldadero/XYZ-forge",
        )

    def test_degenerate_inputs_pass_through_without_raising(self) -> None:
        self.assertEqual(config_module.canonical_github_repo_name(""), "")
        self.assertEqual(config_module.canonical_github_repo_name("no-slash"), "no-slash")


if __name__ == "__main__":
    unittest.main()

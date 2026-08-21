"""System Log page — one pipeline, one taxonomy, two composing axes (GH-101).

The page was renamed from Authorization Log to System Log without its pipeline
being widened, so "All" could only ever show Auth and Jobs: those were the only
two families writing to the file. Health checks — the source of the errors on the
dashboard header — never touched it, so the two pages showed unrelated sets of
problems and neither could show the other's.

Three defects are pinned here:

* the source taxonomy existed twice (a Python dict and a hardcoded JavaScript
  Set) and had ALREADY drifted — ``registry`` was in the first and neither
  branch of the second, so a registry row belonged to no filter at all;
* severity sat in the same mutually-exclusive group as the sources, which made
  "errors in jobs" unaskable;
* the row cap was silent, and the counter rendered "12 / 500 shown" — making the
  ceiling look like the total.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from rebalance import web
from rebalance.ingest import auth_log


class SourceTaxonomyTests(unittest.TestCase):
    def test_every_badged_source_is_reachable_by_a_filter(self) -> None:
        """THE PIN. ``registry`` failed this before GH-101.

        It had a badge, so it rendered; it was in neither JS branch, so it was
        invisible under Auth AND under Jobs while showing under All. Deriving the
        buttons from the badge map is what makes this true by construction — this
        test is here so a future hardcoded list cannot quietly reintroduce it.
        """
        filter_keys = {key for key, _label in web._source_filters()}
        for source in web._SOURCE_BADGE:
            with self.subTest(source=source):
                self.assertIn(source, filter_keys)

    def test_the_client_carries_no_second_copy_of_the_taxonomy(self) -> None:
        """The drift was only possible because the list existed twice."""
        self.assertNotIn("AUTH_SOURCES", web._AUTH_LOG_FILTER_JS)
        for source in web._SOURCE_BADGE:
            with self.subTest(source=source):
                self.assertNotIn(f'"{source}"', web._AUTH_LOG_FILTER_JS)

    def test_health_is_a_first_class_source(self) -> None:
        """GH-101's point: health checks now reach the log the page reads."""
        self.assertIn("health", web._SOURCE_BADGE)
        self.assertIn("health", {key for key, _label in web._source_filters()})


class FilterAxesTests(unittest.TestCase):
    def test_source_and_severity_are_separate_axes(self) -> None:
        controls = web._syslog_controls()
        self.assertIn("data-axis='source'", controls)
        self.assertIn("data-axis='severity'", controls)

    def test_severity_is_not_a_source_button(self) -> None:
        """ "Errors & Warnings" used to sit beside Auth and Jobs in ONE group, so
        picking it discarded the source and picking a source discarded it."""
        source_keys = {key for key, _label in web._source_filters()}
        self.assertNotIn("errors", source_keys)
        self.assertNotIn("problem", source_keys)

    def test_the_axes_compose_in_the_client(self) -> None:
        js = web._AUTH_LOG_FILTER_JS
        self.assertIn("sourceMatch && sevMatch && textMatch", js)


class HonestCountTests(unittest.TestCase):
    def test_the_counter_distinguishes_shown_loaded_and_total(self) -> None:
        js = web._AUTH_LOG_FILTER_JS
        self.assertIn("shown", js)
        self.assertIn("loaded", js)
        self.assertIn("in the log", js)
        self.assertNotIn(' + " / " + rows.length + " shown"', js)


class ReadLogWithTotalTests(unittest.TestCase):
    def _seed(self, tmp: Path, count: int) -> None:
        path = tmp / "auth_activity.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for i in range(count):
                fh.write(
                    json.dumps({"ts": f"2026-08-20T00:{i:02d}:00Z", "source": "github", "event": "token_set"}) + "\n"
                )

    def test_total_is_the_whole_file_not_the_page(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            self._seed(tmp, 40)
            with mock.patch.object(auth_log, "_log_dir", return_value=tmp):
                entries, total = auth_log.read_log_with_total(limit=10)
        self.assertEqual(len(entries), 10)
        self.assertEqual(total, 40, "the cap must not be reported as the total")

    def test_newest_first_is_preserved(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            self._seed(tmp, 5)
            with mock.patch.object(auth_log, "_log_dir", return_value=tmp):
                entries, total = auth_log.read_log_with_total(limit=5)
        self.assertEqual(total, 5)
        self.assertEqual(entries[0]["ts"], "2026-08-20T00:04:00Z")


if __name__ == "__main__":
    unittest.main()

"""GH-5 PR2 — badge rendering regressions and the one-vocabulary pin.

Two things live here:

* A regression test for the swapped ``badge_html`` arguments in the sleuth
  group header (``web.py``), which rendered the raw variant word ("info",
  "ok") as the visible badge text in a neutral pill. Found during PR2's
  literal sweep; proven red before the fix.
* The Phase 3 pin: every badge table and status constant draws its words
  from ONE canonical vocabulary, so a future surface cannot quietly invent
  a fourth synonym for the same tier (the fail/danger/error split this PR
  deleted).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from rebalance import doctor, web
from rebalance.web_components import _BADGE_VARIANTS, badge_html

# The one status vocabulary (GH-5 PR2). Severity tiers share their words with
# check status; "info" and "neutral" are categorical badge variants, not
# severities.
CANONICAL = {"ok", "notice", "warning", "error", "info", "neutral"}
RETIRED = {"fail", "warn", "danger"}


class SleuthGroupBadgeTests(unittest.TestCase):
    def _rendered(self) -> str:
        group = SimpleNamespace(
            kind="github",
            label="My Repo",
            reminders=[{"task_text": "do the thing"}],
        )
        with (
            patch.object(web, "grouped_reminders_from_db", return_value=[group]),
            patch.object(web, "resolve_db", return_value=":memory:"),
        ):
            return web._render_sleuth_groups()

    def test_group_header_badge_uses_variant_class_and_label_text(self):
        html = self._rendered()
        # Pre-fix, the arguments to badge_html were swapped: the label ("GH")
        # was validated as a variant (degrading to neutral) and the variant
        # word ("info") became the visible badge text.
        self.assertIn("badge-info", html)
        self.assertIn(">GH</span>", html)
        self.assertNotIn(">info</span>", html)


class OneVocabularyPinTests(unittest.TestCase):
    def test_status_and_severity_constants_are_canonical(self):
        for const in (doctor.OK, doctor.WARN, doctor.FAIL, doctor.NOTICE, doctor.WARNING, doctor.ERROR):
            self.assertIn(const, CANONICAL)

    def test_status_axis_reuses_severity_words(self):
        # The unification itself: a failing check is an "error" everywhere,
        # a warning check is a "warning" everywhere.
        self.assertEqual(doctor.FAIL, doctor.ERROR)
        self.assertEqual(doctor.WARN, doctor.WARNING)

    def test_badge_variants_are_canonical(self):
        self.assertLessEqual(_BADGE_VARIANTS, frozenset(CANONICAL))
        self.assertFalse(_BADGE_VARIANTS & RETIRED)

    def test_badge_tables_emit_only_canonical_variants(self):
        for table_name in ("_EVENT_BADGE", "_SOURCE_BADGE", "_KIND_BADGE"):
            table = getattr(web, table_name)
            for key, (variant, _label) in table.items():
                self.assertIn(
                    variant,
                    CANONICAL,
                    f"{table_name}[{key!r}] uses non-canonical variant {variant!r}",
                )
                self.assertNotIn(variant, RETIRED)

    def test_retired_words_render_as_neutral_not_styled(self):
        # Defense in depth: if an old literal survives somewhere, it degrades
        # to neutral (visible in review) instead of resolving to a live style.
        for word in RETIRED:
            self.assertIn("badge-neutral", badge_html(word, "x"))


if __name__ == "__main__":
    unittest.main()

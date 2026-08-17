"""GH-5 PR2 — badge rendering regressions and the one-vocabulary pin.

Two things live here:

* The Phase 3 pin: every badge table and status constant draws its words
  from ONE canonical vocabulary, so a future surface cannot quietly invent
  a fourth synonym for the same tier (the fail/danger/error split this PR
  deleted).
* Retired variant degradation tests.
"""

from __future__ import annotations

import unittest

from rebalance import doctor, web
from rebalance.web_components import _BADGE_VARIANTS, badge_html

# The one status vocabulary (GH-5 PR2). Severity tiers share their words with
# check status; "info" and "neutral" are categorical badge variants, not
# severities.
CANONICAL = {"ok", "notice", "warning", "error", "info", "neutral"}
RETIRED = {"fail", "warn", "danger"}


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
        for table_name in ("_EVENT_BADGE", "_SOURCE_BADGE"):
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

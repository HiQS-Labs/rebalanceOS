"""GH-5 Phase O3 — suppression windows are coupled by code, not by comment.

`health.py` used to hand-maintain its suppression hours next to a docstring
saying they "MUST track doctor.py warn_days * 24" — policy enforced by
exhortation, the pattern this campaign has been bitten by twice. The windows
are now *derived* from the doctor freshness registry via
``freshness_warn_hours``; these tests pin the derivation and the current
policy values so a registry change to any ``warn_days`` shows up as a visible,
deliberate test update instead of silent suppression drift.
"""

from __future__ import annotations

import unittest

from rebalance.doctor import _COLLECTOR_FRESHNESS, freshness_warn_hours
from rebalance.health import AUTH_RECOVERY, CREDENTIAL_SUPPRESSION_HOURS


class FreshnessWarnHoursTests(unittest.TestCase):
    def test_returns_warn_days_times_24_for_every_registry_entry(self):
        for entry in _COLLECTOR_FRESHNESS:
            self.assertEqual(freshness_warn_hours(entry["name"]), entry["warn_days"] * 24)

    def test_unknown_name_raises_loudly(self):
        # A silent default would reintroduce the drift this accessor exists to
        # prevent — a renamed registry entry must fail at import, not at 3am.
        with self.assertRaises(KeyError):
            freshness_warn_hours("no such source")


class SuppressionWindowDerivationTests(unittest.TestCase):
    # health-check name → doctor freshness-registry entry it derives from.
    # Vault deliberately absent: it has no freshness check, so it carries an
    # explicit safe default instead of a derived window.
    DERIVED_FROM = {
        "calendar": "calendar data",
        "gmail": "email data",
        "sleuth": "sleuth data",
    }

    def test_credential_windows_equal_registry_policy(self):
        for check_name, registry_name in self.DERIVED_FROM.items():
            self.assertEqual(
                CREDENTIAL_SUPPRESSION_HOURS[check_name],
                freshness_warn_hours(registry_name),
                f"{check_name} suppression window drifted from the {registry_name!r} registry policy",
            )

    def test_auth_recovery_windows_equal_registry_policy(self):
        expected = {
            "auth:github": "github data",
            "auth:gmail": "email data",
            "auth:calendar": "calendar data",
        }
        self.assertEqual(set(AUTH_RECOVERY), set(expected))
        for auth_name, registry_name in expected.items():
            _, hours = AUTH_RECOVERY[auth_name]
            self.assertEqual(hours, freshness_warn_hours(registry_name))

    def test_current_policy_values_pinned(self):
        # The absolute numbers, so a warn_days edit in the registry is a
        # *visible* decision here (suppression windows move with it) rather
        # than an unnoticed side effect.
        self.assertEqual(
            CREDENTIAL_SUPPRESSION_HOURS,
            {"vault": 48, "calendar": 72, "gmail": 168, "sleuth": 48},
        )
        # AUTH_RECOVERY needs its own absolute pin: "github data" appears only
        # here, so without it a registry warn_days change would move that
        # window with no test flagging the decision (agy review, r1).
        self.assertEqual(
            AUTH_RECOVERY,
            {
                "auth:github": ("github data", 48),
                "auth:gmail": ("gmail", 168),
                "auth:calendar": ("calendar", 72),
            },
        )


if __name__ == "__main__":
    unittest.main()

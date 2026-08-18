"""A throttled token-validation must not be reported as an invalid token.

The observed defect: `rebalance doctor` failed at error severity with
`auth:github — last auth event was a failure — token_invalid`, and the token was fine. The
auth log tells the story on its own — hour by hour, for one unchanged PAT:

    23:45 token_invalid   {"status": 403, "error": ""}
    00:45 token_validated {"login": "noelsaw1", "scopes": [...]}
    01:45 token_invalid   {"status": 403, "error": ""}
    02:45 token_validated {"login": "noelsaw1", "scopes": [...]}

A revoked credential cannot alternate like that. GitHub answers both "this token is not
allowed" and "you have spent your quota" with 403, and `validate_github_token` mapped the
whole status class to `token_invalid` — which is in `FAILURE_EVENTS`, so doctor graded it
ERROR and pointed the operator at reissuing a healthy PAT.

The rule that separates the two was never missing: `_http._is_rate_limit` has always drawn it
for `get_json`, and `resolve_github_token` already declines to treat a 403 as a
deauthorization (`github_scan.py`, "rate-limit / transient — not a deauth"). Only the logging
disagreed with the rest of the module. So these tests pin the two 403s apart, and pin that the
distinction keeps coming from that one shared helper rather than a second copy of the rule.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from rebalance.ingest import auth_log
from rebalance.ingest.github_scan import validate_github_token

# The primary-rate-limit shape: quota spent, so GitHub refuses with 403 and says so in the
# headers. The secondary ("abuse") limit sends retry-after instead, covered below.
RATE_LIMITED_HEADERS = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1755400000"}


class _ValidationCase:
    """Drive validate_github_token against a canned response and capture what it logged."""

    def __init__(self, status, data, headers):
        self._response = (status, data, headers)

    def __enter__(self):
        self.logged: list[tuple[str, str, dict]] = []
        self._patches = [
            patch(
                "rebalance.ingest.github_scan.GitHubClient.get_with_headers",
                return_value=self._response,
            ),
            patch.object(
                auth_log,
                "_append",
                side_effect=lambda source, event, detail: self.logged.append((source, event, detail)),
            ),
        ]
        for p in self._patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in self._patches:
            p.stop()
        return False

    @property
    def event(self) -> str:
        return self.logged[0][1] if self.logged else ""

    @property
    def detail(self) -> dict:
        return self.logged[0][2] if self.logged else {}


class RateLimitedValidationTests(unittest.TestCase):
    def test_the_exact_observed_403_is_not_reported_as_an_invalid_token(self):
        with _ValidationCase(403, {"message": "API rate limit exceeded"}, RATE_LIMITED_HEADERS) as case:
            result = validate_github_token("ghp_healthy")

        self.assertEqual(case.event, "rate_limited")
        self.assertTrue(result["rate_limited"])
        self.assertFalse(result["valid"], "throttled is not validated — the token went untested")

    def test_a_secondary_rate_limit_counts_too(self):
        """The abuse limit answers 403 with retry-after and no remaining=0, and it is the one
        that actually fired here: core quota read 4955/5000 remaining at the time."""
        with _ValidationCase(403, {}, {"retry-after": "60"}) as case:
            validate_github_token("ghp_healthy")
        self.assertEqual(case.event, "rate_limited")

    def test_the_reset_time_is_carried_so_the_operator_can_act(self):
        """`token_invalid {"status": 403, "error": ""}` was unactionable — it named no cause
        and no horizon. Whatever replaces it has to say when the quota returns."""
        with _ValidationCase(403, {}, RATE_LIMITED_HEADERS) as case:
            validate_github_token("ghp_healthy")
        self.assertEqual(case.detail["reset"], "1755400000")
        self.assertEqual(case.detail["remaining"], "0")

    def test_a_throttled_check_never_claims_the_credential_is_broken(self):
        """The load-bearing invariant, stated where doctor reads it.

        `FAILURE_EVENTS` is what doctor and the dashboard treat as "this integration lost
        access". A throttle asserts nothing about access, and putting it in that set is what
        made a healthy PAT fail the health check at error severity.
        """
        self.assertNotIn("rate_limited", auth_log.FAILURE_EVENTS)


class RejectedTokenStillFailsTests(unittest.TestCase):
    """The other half. A promotion that also demoted real failures would be worse than the bug."""

    def test_a_401_is_still_an_invalid_token(self):
        with _ValidationCase(401, {"message": "Bad credentials"}, {}) as case:
            result = validate_github_token("ghp_revoked")
        self.assertEqual(case.event, "token_invalid")
        self.assertFalse(result["valid"])
        self.assertNotIn("rate_limited", result)

    def test_a_403_that_is_not_a_rate_limit_is_still_an_invalid_token(self):
        """SSO-unauthorized and scope-refused tokens also answer 403. Without the header
        evidence there is no quota claim to believe, so these stay a credential problem —
        this is the case that keeps the fix from becoming "ignore every 403"."""
        with _ValidationCase(403, {"message": "Resource protected by organization SAML"}, {}) as case:
            result = validate_github_token("ghp_no_sso")
        self.assertEqual(case.event, "token_invalid")
        self.assertFalse(result["valid"])

    def test_a_healthy_token_is_unaffected(self):
        with _ValidationCase(200, {"login": "noelsaw1"}, {"x-oauth-scopes": "repo, gist"}) as case:
            result = validate_github_token("ghp_good")
        self.assertEqual(case.event, "token_validated")
        self.assertTrue(result["valid"])
        self.assertEqual(result["scopes"], ["repo", "gist"])

    def test_the_rule_comes_from_the_shared_helper_not_a_second_copy(self):
        """Pins the anti-drift property the module comment claims.

        If validate_github_token ever grows its own status/header rule, this stops seeing the
        patched helper and fails — which is the point. Two copies of "which 403 is which" is
        exactly how the logging drifted from `resolve_github_token` in the first place.
        """
        with patch("rebalance.ingest._http._is_rate_limit", return_value=True) as helper:
            with _ValidationCase(403, {}, {}) as case:
                validate_github_token("ghp_x")
        self.assertTrue(helper.called, "the shared _is_rate_limit helper was never consulted")
        self.assertEqual(case.event, "rate_limited")


if __name__ == "__main__":
    unittest.main()

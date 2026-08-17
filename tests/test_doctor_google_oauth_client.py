"""doctor must not report a Google OAuth credential healthy when it cannot be used.

Regression cover for #52. The leaked OAuth client was deleted on 2026-08-17; every
token it had issued died with it, and `rebalance doctor` reported

    OK   gmail    — OAuth token present (via keyring)
    OK   calendar — OAuth token present (via keyring) · authorized 75d ago

while both collectors were failing with ``deleted_client``. The token really was
present — presence was simply the wrong question.

These checks stay offline by design (see the section comment in doctor.py): they
compare the client id baked into the stored token against the client id of the
OAuth client file that is actually resolved. That catches credential rotation,
which is the failure mode that bit, without a network call.
"""

import json
import unittest
from unittest.mock import patch

from rebalance.doctor import OK, WARN, _check_calendar, _check_gmail
from rebalance.ingest.google_oauth_client import GoogleOAuthClientNotConfigured

OLD_CLIENT = "409298341985-1kub4u1b1bd0leea3b74d4vmo5cqv75t.apps.googleusercontent.com"
NEW_CLIENT = "409298341985-ur6vl1tpv4o6m73agpc7cnc95j54cn7q.apps.googleusercontent.com"


def _token(client_id: str | None) -> str:
    body: dict[str, str] = {"refresh_token": "not-a-real-token", "token": "x"}
    if client_id:
        body["client_id"] = client_id
    return json.dumps(body)


class GoogleOAuthClientPairingTests(unittest.TestCase):
    """Each case runs against both Google checks — they must not drift apart."""

    def _run(self, service: str):
        if service == "gmail":
            with patch("rebalance.ingest.config.get_gmail_ingest_method", return_value="oauth"):
                return _check_gmail(None)
        return _check_calendar()

    def _with_state(self, service: str, stored: str | None, resolved):
        """`resolved` is a client id, or an exception instance to raise."""
        patches = [
            patch("rebalance.doctor._stored_google_token_json", return_value=stored),
            patch(
                f"rebalance.ingest.config.get_{service}_oauth_token_json",
                return_value=stored or "",
            ),
        ]
        if isinstance(resolved, Exception):
            patches.append(
                patch(
                    "rebalance.ingest.google_oauth_client.build_google_oauth_client_config",
                    side_effect=resolved,
                )
            )
        else:
            patches.append(
                patch(
                    "rebalance.ingest.google_oauth_client.build_google_oauth_client_config",
                    return_value={"installed": {"client_id": resolved}},
                )
            )
        return patches

    def _check(self, service: str, stored: str | None, resolved):
        patches = self._with_state(service, stored, resolved)
        for p in patches:
            p.start()
        try:
            return self._run(service)
        finally:
            for p in reversed(patches):
                p.stop()

    def test_token_from_a_different_client_warns(self):
        """The exact #52 case: token minted by the deleted client, new client configured."""
        for service in ("gmail", "calendar"):
            with self.subTest(service=service):
                check = self._check(service, _token(OLD_CLIENT), NEW_CLIENT)
                self.assertEqual(check.status, WARN)
                self.assertIn("different client", check.detail)
                self.assertIn(f"setup_{service}_oauth.py", check.hint)
                # The two ids must be told apart in the message. Truncating from
                # the right renders both as ".apps.googleusercontent.com" and the
                # warning reads as though nothing differs.
                self.assertIn("1kub4u1b", check.detail)
                self.assertIn("ur6vl1tp", check.detail)
                self.assertNotIn("googleusercontent.com", check.detail)

    def test_matching_client_stays_ok(self):
        for service in ("gmail", "calendar"):
            with self.subTest(service=service):
                check = self._check(service, _token(NEW_CLIENT), NEW_CLIENT)
                self.assertEqual(check.status, OK)
                self.assertIn("OAuth token present", check.detail)

    def test_no_client_file_configured_warns(self):
        """A token with nothing to pair it to fails every sync — say so."""
        for service in ("gmail", "calendar"):
            with self.subTest(service=service):
                check = self._check(
                    service,
                    _token(NEW_CLIENT),
                    GoogleOAuthClientNotConfigured("none found"),
                )
                self.assertEqual(check.status, WARN)
                self.assertIn("no OAuth client file is configured", check.detail)

    def test_legacy_token_without_client_id_does_not_warn(self):
        """Nothing to compare is not evidence of a problem — no false positive."""
        for service in ("gmail", "calendar"):
            with self.subTest(service=service):
                check = self._check(service, _token(None), NEW_CLIENT)
                self.assertEqual(check.status, OK)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

from rebalance.web import auth_log_page


class WebAuthLogTests(unittest.TestCase):
    def test_sleuth_file_source_sync_renders_green_success_badge(self) -> None:
        entries = [
            {
                "ts": "2026-06-09T05:56:48.784693+00:00",
                "device": "example-mac.local",
                "source": "sleuth",
                "event": "sync_succeeded",
                "detail": {
                    "workspace": "neochrome",
                    "source_mode": "file-source",
                    "returned": 28,
                    "total": 28,
                    "updated": 19,
                },
            }
        ]
        # GH-101: the page now also needs the TOTAL, so it can say when it truncated
        # instead of letting the row cap read as the whole log.
        with patch("rebalance.web.read_log_with_total", return_value=(entries, len(entries))):
            response = auth_log_page()

        html = response.body.decode("utf-8")
        self.assertIn("✓ file source synced", html)
        self.assertIn("source_mode</b>: file-source", html)
        self.assertIn("workspace</b>: neochrome", html)

    def test_watched_repos_reduced_renders_warn_badge(self) -> None:
        entries = [
            {
                "ts": "2026-06-26T12:00:00+00:00",
                "device": "example-mac.local",
                "source": "github",
                "event": "watched_repos_reduced",
                "detail": {
                    "removed": [{"repo": "BinoidCBD/LTVera-Pandas", "last_buckets": ["project"]}],
                    "info_churn": [],
                },
            }
        ]
        # GH-101: the page now also needs the TOTAL, so it can say when it truncated
        # instead of letting the row cap read as the whole log.
        with patch("rebalance.web.read_log_with_total", return_value=(entries, len(entries))):
            response = auth_log_page()

        html = response.body.decode("utf-8")
        self.assertIn("⚠ watched repos reduced", html)  # the warn badge label
        self.assertIn("BinoidCBD/LTVera-Pandas", html)  # the dropped repo surfaces

    def test_project_auto_promoted_renders_ok_badge(self) -> None:
        entries = [
            {
                "ts": "2026-07-10T12:00:00+00:00",
                "device": "example-mac.local",
                "source": "registry",
                "event": "project_auto_promoted",
                "detail": {
                    "repo": "Claude-AI-Tools-Ventura-County/clio",
                    "project_name": "clio",
                    "commit_count": 3,
                    "threshold": 3,
                },
            }
        ]
        # GH-101: the page now also needs the TOTAL, so it can say when it truncated
        # instead of letting the row cap read as the whole log.
        with patch("rebalance.web.read_log_with_total", return_value=(entries, len(entries))):
            response = auth_log_page()

        html = response.body.decode("utf-8")
        self.assertIn("✓ project auto-added", html)  # the ok badge label
        self.assertIn("Claude-AI-Tools-Ventura-County/clio", html)


if __name__ == "__main__":
    unittest.main()

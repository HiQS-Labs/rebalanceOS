"""Security tests for Reminder Graph page (GH-107).

Pins: Reminder text containing `</script>` must not break out of the inline
<script> element on the Reminder Graph page.
"""

from __future__ import annotations

import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rebalance import web
from rebalance.ingest.sleuth_grouping import ReminderGroup


class SleuthGraphScriptBreakoutTests(unittest.TestCase):
    def test_reminder_containing_script_closing_tag_is_escaped(self) -> None:
        """A reminder containing </script> must not break out of inline script."""
        malicious_text = "Task payload </script><script>alert('xss')</script>"
        reminder = {
            "reminder_id": "rem-123",
            "task_text": malicious_text,
            "original_channel_name": "general",
            "state": "active",
            "github_urls": [],
        }
        group = ReminderGroup(
            label="General",
            kind="channel",
            reminders=[reminder],
        )

        # The route opens the DB read-only through the shared gateway, which
        # cannot open ":memory:" — give it a real (empty) file instead. The
        # reads themselves are patched; only the open must succeed.
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            db_file = Path(handle.name)
        self.addCleanup(db_file.unlink, missing_ok=True)
        sqlite3.connect(db_file).close()

        with (
            mock.patch.object(web, "resolve_db", return_value=str(db_file)),
            mock.patch(
                "rebalance.ingest.sleuth_grouping.load_client_mapping",
                return_value={},
            ),
            mock.patch(
                "rebalance.ingest.sleuth_grouping.grouped_reminders_from_db",
                return_value=[group],
            ),
            mock.patch(
                "rebalance.ingest.sleuth_grouping.load_active_reminders",
                return_value=[reminder],
            ),
        ):
            resp = web.sleuth_graph_page()

        html = resp.body.decode("utf-8")

        # Find the inline script block defining var elements
        match = re.search(r"<script>\s*\(function\(\)\s*\{([^<]+(?:<(?!\/script>)[^<]+)*)\}\)\(\);?\s*</script>", html)
        self.assertIsNotNone(match, "Inline cytoscape script block not found")
        script_body = match.group(1)

        # Extract the elements JSON literal
        elem_match = re.search(r"var elements = (\[.*?\]);", script_body, re.DOTALL)
        self.assertIsNotNone(elem_match, "elements JSON literal not found in script body")
        raw_elements_json = elem_match.group(1)

        # The JSON literal inside <script> must NOT contain raw unescaped </script>
        self.assertNotIn("</script>", raw_elements_json)
        self.assertIn(r"<\/", raw_elements_json)

        # The serialized JSON must still be valid JSON and unescape back to original text
        parsed = json.loads(raw_elements_json)
        found_task = False
        for node in parsed:
            data = node.get("data", {})
            if data.get("full_text") == malicious_text:
                found_task = True
                break
        self.assertTrue(found_task, "Parsed JSON did not preserve original task text")


if __name__ == "__main__":
    unittest.main()

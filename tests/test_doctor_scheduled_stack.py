"""GH-36 — the scheduled stack must run from the same checkout as this code.

The real incident: after the repo migrated, all seventeen launchd jobs kept
running the retiring clone's code for days. The interactive CLI verified
current while the dashboard rendered pre-campaign output. This pins the
tripwire that makes that drift loud.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rebalance.doctor import OK, WARN, _check_scheduled_stack_checkout

REPO_ROOT = Path(__file__).resolve().parents[1]

PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
  <key>Label</key><string>com.rebalance-os.{name}</string>
  <key>ProgramArguments</key>
  <array><string>{script}</string></array>
</dict></plist>
"""


def _write(agents: Path, name: str, script: str) -> None:
    (agents / f"com.rebalance-os.{name}.plist").write_text(PLIST.format(name=name, script=script), encoding="utf-8")


class ScheduledStackCheckoutTests(unittest.TestCase):
    def test_job_in_another_clone_warns_and_names_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp)
            _write(agents, "pulse-server", "/Users/x/Documents/rebalance-OS/scripts/pulse_server.sh")
            _write(agents, "vault-sync", str(REPO_ROOT / "scripts" / "vault_sync.sh"))
            checks = _check_scheduled_stack_checkout(agents)
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].status, WARN)
        self.assertIn("pulse-server", checks[0].detail)
        self.assertNotIn("vault-sync", checks[0].detail)

    def test_all_jobs_in_this_checkout_is_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp)
            _write(agents, "vault-sync", str(REPO_ROOT / "scripts" / "vault_sync.sh"))
            _write(agents, "github-sync", str(REPO_ROOT / "scripts" / "github_sync.sh"))
            checks = _check_scheduled_stack_checkout(agents)
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].status, OK)

    def test_non_rebalance_paths_are_ignored(self) -> None:
        # A job whose script lives outside any rebalance checkout (e.g. a
        # system python invoking a repo script is caught by the script arg,
        # not the interpreter) must not false-positive on the interpreter.
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp)
            _write(agents, "misc", "/usr/local/bin/some-tool.sh")
            checks = _check_scheduled_stack_checkout(agents)
        self.assertEqual(checks[0].status, OK)

    def test_missing_agents_dir_is_silent(self) -> None:
        self.assertEqual([], _check_scheduled_stack_checkout(Path("/nonexistent/LaunchAgents")))


class DeclaredRuntimeRootTests(unittest.TestCase):
    """A dedicated runtime clone (declared in ~/.config/rebalance/runtime-root)
    becomes the expectation for EVERY checkout's doctor — dev checkouts no
    longer read their own location as the required home."""

    def test_declared_root_overrides_running_checkout(self) -> None:
        from unittest.mock import patch

        from rebalance import doctor

        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "rebalance-runtime"
            (runtime / "scripts").mkdir(parents=True)
            root_file = Path(tmp) / "runtime-root"
            root_file.write_text(str(runtime) + "\n", encoding="utf-8")

            agents = Path(tmp) / "agents"
            agents.mkdir()
            # Job in the declared runtime clone: OK even though it is not in
            # the checkout running this test.
            _write(agents, "pulse-server", str(runtime / "scripts" / "pulse_server.sh"))
            with patch.object(doctor, "RUNTIME_ROOT_FILE", root_file):
                checks = _check_scheduled_stack_checkout(agents)
            self.assertEqual(checks[0].status, OK)
            self.assertIn("declared runtime root", checks[0].detail)

            # Job in THIS checkout now counts as drift — the declaration wins.
            _write(agents, "vault-sync", str(REPO_ROOT / "scripts" / "vault_sync.sh"))
            with patch.object(doctor, "RUNTIME_ROOT_FILE", root_file):
                checks = _check_scheduled_stack_checkout(agents)
            self.assertEqual(checks[0].status, WARN)
            self.assertIn("vault-sync", checks[0].detail)

    def test_missing_declaration_falls_back_to_running_checkout(self) -> None:
        from unittest.mock import patch

        from rebalance import doctor

        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp) / "agents"
            agents.mkdir()
            _write(agents, "vault-sync", str(REPO_ROOT / "scripts" / "vault_sync.sh"))
            with patch.object(doctor, "RUNTIME_ROOT_FILE", Path(tmp) / "absent"):
                checks = _check_scheduled_stack_checkout(agents)
            self.assertEqual(checks[0].status, OK)
            self.assertIn("this checkout", checks[0].detail)


if __name__ == "__main__":
    unittest.main()

"""Behavioural tests for scripts/stack.sh (GH-59 Phase 1).

The script is the single control plane for the launchd fleet, so its failure
mode is unloading jobs and not bringing them back — precisely the silent outage
GH-59 exists to fix. These tests pin the four properties that make it safe to
run:

1. its managed set IS SCHEDULER.md, byte for byte the same list doctor parses;
2. anything outside that set is never unloaded or deleted (the three preserved
   3-Eyes plists depend on this);
3. `down` is non-destructive — only `purge` removes a plist;
4. job lookup is an exact match, so `health-check` cannot pick up
   `health-check-triage`'s launchctl row.

They run without touching the real fleet: HOME is redirected to a tmpdir,
STACK_LAUNCHCTL_OUTPUT supplies a fixed `launchctl list` table, and
STACK_LAUNCHCTL_BIN replaces launchctl with a recording stub. All three are
required. Redirecting HOME alone is NOT enough and an earlier draft of this
file proved it the hard way: `launchctl unload <path>` resolves the job from the
Label inside the file, so a fixture plist labelled com.rebalance-os.vault-sync
in a temp HOME unloaded the REAL vault-sync on the developer's machine. The stub
is the actual isolation boundary; the tmpdir only keeps the files tidy.
"""

from __future__ import annotations

import os
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STACK = REPO / "scripts" / "stack.sh"
PREFIX = "com.rebalance-os."

# A launchctl table covering the collision case: health-check and
# health-check-triage differ only by suffix, and their rows disagree.
#
# The TRIAGE ROW IS DELIBERATELY FIRST. A substring match for "health-check"
# hits both rows; if the longer label sorts second, a `grep … | head -1` picks
# the right row by luck and the collision stays invisible. Ordering it first
# makes both shapes of the bug — two rows into a one-row parse, and head -1
# taking the wrong one — produce a wrong answer. Verified by reintroducing each
# variant and watching this test fail.
LAUNCHCTL_FIXTURE = "\n".join(
    [
        "PID\tStatus\tLabel",
        f"-\t99\t{PREFIX}health-check-triage",
        f"-\t0\t{PREFIX}health-check",
        f"4242\t0\t{PREFIX}pulse-server",
        f"-\t1\t{PREFIX}github-sync",
        f"-\t0\t{PREFIX}3eyes.selfcheck",
    ]
)


def make_launchctl_stub(home: Path) -> Path:
    """A launchctl that records its arguments instead of touching the fleet."""
    stub = home / "launchctl-stub.sh"
    stub.write_text(
        '#!/bin/bash\nprintf "%s\\n" "$*" >> "$HOME/launchctl-calls.log"\nexit 0\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return stub


def run_stack(*args: str, home: Path, extra_env: dict[str, str] | None = None):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["STACK_LAUNCHCTL_OUTPUT"] = LAUNCHCTL_FIXTURE
    env["STACK_LAUNCHCTL_BIN"] = str(make_launchctl_stub(home))
    # Redirecting HOME also moves the canonical app-data path, so database
    # resolution fails and validate_environment aborts BEFORE the target-root
    # guard runs. Without this the guard tests pass vacuously — they see a
    # non-zero exit from the wrong check. Point the DB somewhere resolvable.
    db = home / "rebalance.db"
    db.touch()
    env["REBALANCE_DB"] = str(db)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(STACK), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO),
    )


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class StackScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.agents = self.home / "Library" / "LaunchAgents"
        self.agents.mkdir(parents=True)
        self.addCleanup(self._tmp.cleanup)

    def write_plist(self, label_suffix: str, root: str | None = None) -> Path:
        # Default to THIS checkout: a fixture bound elsewhere now trips the
        # target-root guard, which every destructive command honours since the
        # branch review. Tests about teardown should not be testing the guard.
        root = root if root is not None else str(REPO)
        path = self.agents / f"{PREFIX}{label_suffix}.plist"
        path.write_text(
            "<?xml version='1.0' encoding='UTF-8'?>\n"
            "<plist version='1.0'><dict>\n"
            f"  <key>Label</key><string>{PREFIX}{label_suffix}</string>\n"
            "  <key>ProgramArguments</key><array>\n"
            f"    <string>{root}/scripts/{label_suffix.replace('-', '_')}.sh</string>\n"
            "  </array>\n"
            "</dict></plist>\n",
            encoding="utf-8",
        )
        return path

    # -- 1. the managed set is SCHEDULER.md ---------------------------------

    def test_managed_set_matches_doctors_policy_parse(self):
        """stack.sh and doctor must agree on the job list, or `down` has a
        different idea of 'managed' than `doctor` has of 'required'."""
        import sys

        sys.path.insert(0, str(REPO / "src"))
        from rebalance.doctor import _scheduler_policy_jobs

        expected = set(_scheduler_policy_jobs(REPO / "SCHEDULER.md"))
        self.assertTrue(expected, "SCHEDULER.md policy table parsed as empty")

        out = strip_ansi(run_stack("status", home=self.home).stdout)
        table = out.split("BOUND TO", 1)[1]
        table = table.split("managed:", 1)[0]
        seen = {line.split()[0] for line in table.splitlines() if line.strip() and not line.startswith("-")}
        self.assertEqual(seen, expected)

    def test_status_reports_the_full_policy_count(self):
        import sys

        sys.path.insert(0, str(REPO / "src"))
        from rebalance.doctor import _scheduler_policy_jobs

        count = len(_scheduler_policy_jobs(REPO / "SCHEDULER.md"))
        out = strip_ansi(run_stack("status", home=self.home).stdout)
        self.assertIn(f"managed: {count}", out)

    # -- 2. unmanaged plists are shown but never touched --------------------

    def test_unmanaged_plists_are_listed_separately(self):
        self.write_plist("3eyes.selfcheck")
        out = strip_ansi(run_stack("status", home=self.home).stdout)
        head, _, tail = out.partition("Unmanaged")
        self.assertTrue(tail, "unmanaged section missing from status output")
        self.assertNotIn("3eyes.selfcheck", head)
        self.assertIn("3eyes.selfcheck", tail)

    def test_purge_refuses_to_delete_an_unmanaged_plist(self):
        """The negative control. The three deferred 3-Eyes plists are kept on
        disk deliberately; a glob over com.rebalance-os.* would eat them."""
        preserved = self.write_plist("3eyes.selfcheck")
        managed = self.write_plist("vault-sync")

        result = run_stack("purge", home=self.home)
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertTrue(
            preserved.exists(),
            "purge deleted an unmanaged plist — 3-Eyes preservation is broken",
        )
        self.assertFalse(managed.exists(), "purge failed to remove a managed plist")
        self.assertNotIn("3eyes", strip_ansi(result.stdout))

    # -- 3. down is non-destructive ----------------------------------------

    def test_down_unloads_but_keeps_the_plist(self):
        """`restart` is down-then-up. If `down` deleted plists, a failed `up`
        would leave the machine with no agents at all."""
        managed = self.write_plist("vault-sync")
        result = run_stack("down", home=self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            managed.exists(),
            "down deleted a plist — a failed restart would strand the fleet",
        )
        self.assertIn("plists kept", strip_ansi(result.stdout))

    # -- 4. exact-match job lookup -----------------------------------------

    def test_health_check_does_not_absorb_the_triage_row(self):
        """A substring grep matches both labels, returns two launchctl rows,
        and reports garbage for each. Regression pin for defect #5."""
        out = strip_ansi(run_stack("status", home=self.home).stdout)
        rows = {
            line.split()[0]: line.split()
            for line in out.splitlines()
            if line.strip().startswith(("health-check", "pulse-server", "github-sync"))
        }

        self.assertIn("health-check", rows)
        self.assertIn("health-check-triage", rows)
        # health-check's fixture row is exit 0; triage's is 99. A substring
        # match collapses them and loses one of the two.
        self.assertEqual(rows["health-check"][2], "0")
        self.assertEqual(rows["health-check-triage"][2], "99")
        self.assertIn("ERROR", " ".join(rows["health-check-triage"]))
        self.assertNotIn("ERROR", " ".join(rows["health-check"]))

    def test_running_and_failing_states_are_distinguished(self):
        out = strip_ansi(run_stack("status", home=self.home).stdout)
        for line in out.splitlines():
            fields = line.split()
            if fields[:1] == ["pulse-server"]:
                self.assertEqual(fields[1], "4242")
                self.assertIn("RUNNING", line)
            if fields[:1] == ["github-sync"]:
                self.assertIn("ERROR (1)", line)

    # -- 5. the target-root guard ------------------------------------------

    def test_status_reports_a_foreign_binding_on_the_owning_row(self):
        """`up` derives its root from its own location, so running it from the
        wrong checkout migrates the whole fleet. status must make that visible
        before anyone runs up — and on the RIGHT job's row: asserting the string
        appears somewhere in the output would pass even if it were attributed to
        the wrong job."""
        self.write_plist("vault-sync", root="/somewhere/else")
        out = strip_ansi(run_stack("status", home=self.home).stdout)
        self.assertIn(f"Target root: {REPO}", out)

        rows = [ln for ln in out.splitlines() if ln.startswith("vault-sync ")]
        self.assertEqual(len(rows), 1, f"expected one vault-sync row, got {rows}")
        self.assertIn("/somewhere/else", rows[0])

        others = [ln for ln in out.splitlines() if "/somewhere/else" in ln and not ln.startswith("vault-sync ")]
        self.assertFalse(others, f"foreign binding leaked onto other rows: {others}")

    def test_up_refuses_when_the_fleet_is_bound_elsewhere(self):
        self.write_plist("vault-sync", root="/somewhere/else")
        result = run_stack("up", home=self.home)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("bound to a different checkout", strip_ansi(result.stderr))

    def test_unreadable_binding_counts_as_a_conflict(self):
        """bound_root returns empty when no <string> looks like a checkout path.
        Treating unknown as "ours" would make the migration guard fail OPEN,
        which is the one direction a safety check must never fail."""
        path = self.agents / f"{PREFIX}vault-sync.plist"
        path.write_text(
            "<?xml version='1.0'?><plist version='1.0'><dict>\n"
            "<key>Label</key><string>com.rebalance-os.vault-sync</string>\n"
            "<key>Program</key><string>/usr/local/bin/python</string>\n"
            "</dict></plist>\n",
            encoding="utf-8",
        )
        result = run_stack("up", home=self.home)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("binding unreadable", strip_ansi(result.stderr))

    def test_status_survives_a_plist_with_no_string_values(self):
        """`set -o pipefail` + a grep that matches nothing used to abort the
        whole script from inside bound_root's command substitution."""
        path = self.agents / f"{PREFIX}vault-sync.plist"
        path.write_text(
            "<?xml version='1.0'?><plist version='1.0'><dict>\n<key>Nice</key><integer>5</integer>\n</dict></plist>\n",
            encoding="utf-8",
        )
        result = run_stack("status", home=self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("managed:", strip_ansi(result.stdout))

    def test_restart_preflights_before_tearing_anything_down(self):
        """restart is down-then-up, and up can abort in preflight. If the
        preflight ran after the teardown, a failing check would leave the machine
        with zero agents — the outage this script exists to prevent."""
        self.write_plist("vault-sync", root="/somewhere/else")
        result = run_stack("restart", home=self.home)

        self.assertNotEqual(result.returncode, 0, "restart should refuse a foreign binding")
        calls_log = self.home / "launchctl-calls.log"
        calls = calls_log.read_text().splitlines() if calls_log.exists() else []
        self.assertFalse(
            [c for c in calls if c.startswith("unload ")],
            f"restart unloaded jobs before its preflight failed: {calls}",
        )
        self.assertTrue(
            (self.agents / f"{PREFIX}vault-sync.plist").exists(),
            "restart removed a plist despite aborting",
        )

    # -- 6. the tests cannot reach the real fleet ---------------------------

    def test_teardown_only_unloads_plists_inside_the_sandbox(self):
        """Isolation pin. `launchctl unload <path>` reads the Label from the
        file, so an unstubbed run here would unload the developer's real jobs —
        which is exactly what happened before STACK_LAUNCHCTL_BIN existed. Assert
        every unload target is under this test's HOME."""
        self.write_plist("vault-sync")
        self.write_plist("3eyes.selfcheck")
        run_stack("down", home=self.home)

        calls = (self.home / "launchctl-calls.log").read_text().splitlines()
        unloads = [c for c in calls if c.startswith("unload ")]
        self.assertTrue(unloads, "down never called launchctl unload")
        for call in unloads:
            target = call.split(" ", 1)[1]
            self.assertTrue(
                target.startswith(str(self.home)),
                f"unload escaped the test sandbox: {target}",
            )
        self.assertFalse(
            [c for c in unloads if "3eyes" in c],
            "down tried to unload an unmanaged 3-Eyes job",
        )

    # -- 7. destructive commands honour the binding guard too ---------------

    def test_down_refuses_a_fleet_bound_elsewhere(self):
        """`up` refusing to ADOPT a foreign fleet while `down` was free to STOP
        it was the wrong way round: unloading jobs this clone does not own is
        the worse outcome of the two."""
        self.write_plist("vault-sync", root="/somewhere/else")
        result = run_stack("down", home=self.home)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("bound to a different checkout", strip_ansi(result.stderr))
        calls_log = self.home / "launchctl-calls.log"
        calls = calls_log.read_text().splitlines() if calls_log.exists() else []
        self.assertFalse([c for c in calls if c.startswith("unload ")], calls)

    def test_purge_refuses_a_fleet_bound_elsewhere(self):
        plist = self.write_plist("vault-sync", root="/somewhere/else")
        result = run_stack("purge", home=self.home)

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(plist.exists(), "purge deleted a plist it did not own")

    def test_force_still_allows_a_deliberate_teardown(self):
        """The guard must be an interlock, not a wall — --force is the escape
        hatch, and it has to actually work."""
        self.write_plist("vault-sync", root="/somewhere/else")
        result = run_stack("down", "--force", home=self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.home / "launchctl-calls.log").read_text().splitlines()
        self.assertTrue([c for c in calls if c.startswith("unload ")])

    # -- 8. up validates every template before unloading anything ------------

    def test_up_unloads_nothing_when_a_template_will_not_render(self):
        """`rb_install_launchd_job` unloads the old job before writing the new
        plist, so a template that fails to lint used to leave that job down —
        and under `restart`, every job processed before it as well. Preflight
        now renders and lints the whole policy set first."""
        policy = self.home / "POLICY.md"
        policy.write_text(
            "| Job (label suffix) | Cadence | Wrapper |\n"
            "|---|---|---|\n"
            "| `vault-sync` | hourly | `scripts/vault_sync.sh` |\n"
            "| `no-such-job` | hourly | — |\n",
            encoding="utf-8",
        )
        self.write_plist("vault-sync")

        result = run_stack("up", home=self.home, extra_env={"STACK_POLICY_DOC": str(policy)})

        self.assertNotEqual(result.returncode, 0, "up accepted a missing template")
        self.assertIn("no-such-job", strip_ansi(result.stderr))
        calls_log = self.home / "launchctl-calls.log"
        calls = calls_log.read_text().splitlines() if calls_log.exists() else []
        self.assertFalse(
            [c for c in calls if c.startswith("unload ")],
            f"up unloaded a job before discovering the bad template: {calls}",
        )

    def test_usage_lists_every_dispatcher_command(self):
        result = run_stack("nonsense-command", home=self.home)
        self.assertEqual(result.returncode, 2)
        usage = strip_ansi(result.stdout + result.stderr)
        for cmd in ("up", "down", "restart", "status", "doctor", "verify", "purge"):
            self.assertIn(cmd, usage)


if __name__ == "__main__":
    unittest.main()

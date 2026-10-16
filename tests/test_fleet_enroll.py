"""GH-325 — fleet enrollment: one clone resolver, enroll/repair command, doctor rows.

Every case runs against a temp collector config dir and a temp rbos.config, so
nothing touches this Mac's real fleet configuration.
"""

from __future__ import annotations

import json
import os
import tempfile
import stat
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rebalance.cli import app
from rebalance.doctor import FAIL, OK, WARN, _check_pulse_fleet
from rebalance.ingest import config as config_module
from rebalance.lib.git_ops import (
    collector_clone,
    discover_pulse_clone,
    fleet_settings,
    read_collector_config,
    set_collector_values,
)


class _FleetFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.gp = self.root / "gp"
        self.gp.mkdir()
        self._env = patch.dict(os.environ, {"GIT_PULSE_CONFIG_DIR": str(self.gp), "HOME": str(self.home)})
        self._env.start()
        self._orig_config = config_module.CONFIG_PATH
        config_module.CONFIG_PATH = self.root / "rbos.config"

    def tearDown(self) -> None:
        config_module.CONFIG_PATH = self._orig_config
        self._env.stop()
        self._tmp.cleanup()

    def clone(self, path: Path) -> Path:
        (path / ".git").mkdir(parents=True)
        return path

    def collector(self, body: str) -> Path:
        path = self.gp / "config.sh"
        path.write_text(body)
        return path

    def rbos(self, **values: object) -> None:
        config_module.CONFIG_PATH.write_text(json.dumps(values))

    def rbos_values(self) -> dict:
        return json.loads(config_module.CONFIG_PATH.read_text())


class CollectorCloneTests(_FleetFixture):
    def test_effective_forms_resolve(self) -> None:
        cases = {
            "": self.gp / "repo",
            "$CONFIG_DIR/repo": self.gp / "repo",
            "${CONFIG_DIR}/repo": self.gp / "repo",
            "$HOME/x": self.home / "x",
            "${HOME}/x": self.home / "x",
            "~/x": self.home / "x",
            "/abs/x": Path("/abs/x"),
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(collector_clone({"sync_repo_dir": raw}, self.gp), expected)

    def test_other_expressions_rejected(self) -> None:
        for raw in ("$OTHER/x", "$HOMEDIR/x"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                collector_clone({"sync_repo_dir": raw}, self.gp)

    def test_fleet_settings_accepts_home_path(self) -> None:
        clone = self.clone(self.home / "pulse")
        self.collector('device_id="mac-a"\nfleet_mode=true\nsync_repo_dir="$HOME/pulse"\n')
        cfg = {"pulse_fleet_enabled": True, "pulse_target_path": str(clone), "pulse_device_id": "mac-a"}
        self.assertEqual(fleet_settings(cfg), {"device_id": "mac-a", "sync_subdir": "sync"})


class SetCollectorValuesTests(_FleetFixture):
    def test_replaces_duplicates_appends_missing_and_backs_up(self) -> None:
        original = '# keep me\nrepos=("a b")\nsync_repo_dir="/old"\nfleet_mode=false\nfleet_mode=false\n'
        path = self.collector(original)
        path.chmod(0o600)
        set_collector_values({"fleet_mode": "true", "sync_repo_dir": "/new dir", "fleet_sync_subdir": "sync"})
        text = path.read_text()
        self.assertIn("# keep me", text)
        self.assertIn('repos=("a b")', text)
        self.assertEqual(text.count("fleet_mode=true"), 2)
        self.assertNotIn("fleet_mode=false", text)
        self.assertEqual(
            read_collector_config(),
            {"sync_repo_dir": "/new dir", "fleet_mode": "true", "fleet_sync_subdir": "sync"},
        )
        self.assertEqual((self.gp / "config.sh.bak-gh325").read_text(), original)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.gp / "config.sh.bak-gh325").stat().st_mode), 0o600)
        set_collector_values({"fleet_mode": "false"})
        self.assertEqual((self.gp / "config.sh.bak-gh325").read_text(), original)

    def test_backup_failure_leaves_original_and_no_partial_backup(self) -> None:
        path = self.collector("fleet_mode=false\n")
        original = path.read_bytes()
        for operation in ("os.fsync", "os.link"):
            with (
                self.subTest(operation=operation),
                patch("rebalance.lib.git_ops." + operation, side_effect=OSError("fixture failure")),
            ):
                with self.assertRaises(OSError):
                    set_collector_values({"fleet_mode": "true"})
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse((self.gp / "config.sh.bak-gh325").exists())
            self.assertEqual(list(self.gp.glob(".config.sh-*")), [])

    def test_replace_failure_keeps_complete_backup_and_original_mode(self) -> None:
        path = self.collector("fleet_mode=false\n")
        path.chmod(0o640)
        original = path.read_bytes()
        with patch.object(Path, "replace", side_effect=OSError("fixture replace failure")):
            with self.assertRaises(OSError):
                set_collector_values({"fleet_mode": "true"})
        self.assertEqual(path.read_bytes(), original)
        backup = self.gp / "config.sh.bak-gh325"
        self.assertEqual(backup.read_bytes(), original)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o640)
        self.assertEqual(list(self.gp.glob(".config.sh-*")), [])
        set_collector_values({"fleet_mode": "true"})
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
        self.assertEqual(backup.read_bytes(), original)


class DiscoverPulseCloneTests(_FleetFixture):
    def test_no_collector_uses_target_without_device_id(self) -> None:
        target = self.clone(self.root / "mini-clone")
        self.assertEqual(discover_pulse_clone({"pulse_target_path": str(target)}), target)

    def test_nothing_configured_is_none(self) -> None:
        self.assertIsNone(discover_pulse_clone({}))

    def test_two_different_clones_refuse(self) -> None:
        a = self.clone(self.root / "a")
        b = self.clone(self.root / "b")
        self.collector(f'sync_repo_dir="{a}"\n')
        with self.assertRaises(ValueError):
            discover_pulse_clone({"pulse_target_path": str(b)})

    def test_unresolved_expression_refuses(self) -> None:
        self.collector('sync_repo_dir="$OTHER/repo"\n')
        with self.assertRaises(ValueError):
            discover_pulse_clone({"pulse_target_path": str(self.clone(self.root / "p"))})


class FleetEnrollCliTests(_FleetFixture):
    def run_cli(self, *args: str):
        return CliRunner().invoke(app, ["config", "fleet-enroll", *args])

    def snapshot(self) -> tuple[bytes, bytes]:
        return (self.gp / "config.sh").read_bytes(), config_module.CONFIG_PATH.read_bytes()

    def test_preview_writes_nothing(self) -> None:
        clone = self.clone(self.home / "pulse")
        self.collector('device_id="mac-a"\nsync_repo_dir="$HOME/pulse"\n')
        self.rbos(pulse_target_path=str(clone), pulse_filename="README.md")
        before = self.snapshot()
        result = self.run_cli()
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Preview only", result.output)
        self.assertEqual(self.snapshot(), before)

    def test_apply_writes_literal_path_and_rerun_is_byte_identical(self) -> None:
        clone = self.clone(self.home / "pulse")
        self.collector('device_id="mac-a"\nsync_repo_dir="$HOME/pulse"\n')
        self.rbos(pulse_target_path="~/pulse", pulse_filename="README.md")
        result = self.run_cli("--apply")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(read_collector_config()["sync_repo_dir"], str(clone))
        values = self.rbos_values()
        self.assertEqual(values["pulse_target_path"], str(clone))
        self.assertEqual(values["pulse_device_id"], "mac-a")
        self.assertTrue(values["pulse_fleet_enabled"])
        self.assertNotIn("pulse_filename", values)
        before = self.snapshot()
        again = self.run_cli("--apply")
        self.assertIn("already enrolled", again.output)
        self.assertEqual(self.snapshot(), before)

    def test_empty_sync_repo_dir_with_target_elsewhere_converges(self) -> None:
        clone = self.clone(self.root / "Documents/GitHub/rebalance-git-pulse")
        self.collector('device_id="mac-mini"\nsync_repo_dir=""\n')
        self.rbos(pulse_target_path=str(clone))
        result = self.run_cli("--apply")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(read_collector_config()["sync_repo_dir"], str(clone))

    def test_config_dir_form_accepted(self) -> None:
        self.clone(self.gp / "repo")
        self.collector('device_id="mac-a"\nsync_repo_dir="$CONFIG_DIR/repo"\n')
        self.rbos()
        result = self.run_cli("--apply")
        self.assertEqual(result.exit_code, 0, result.output)

    def test_refusals_write_nothing(self) -> None:
        a = self.clone(self.root / "a")
        b = self.clone(self.root / "b")
        cases = {
            "two clones": ('device_id="mac-a"\nsync_repo_dir="' + str(a) + '"\n', {"pulse_target_path": str(b)}),
            "missing device_id": ('sync_repo_dir="' + str(a) + '"\n', {}),
            "unsafe sync_subdir": (
                'device_id="mac-a"\nsync_repo_dir="' + str(a) + '"\n',
                {"sync_subdir": "../escape"},
            ),
        }
        for name, (collector_body, rbos_values) in cases.items():
            with self.subTest(name):
                self.collector(collector_body)
                self.rbos(**rbos_values)
                before = self.snapshot()
                result = self.run_cli("--apply")
                self.assertEqual(result.exit_code, 1, result.output)
                self.assertEqual(self.snapshot(), before)

    def test_print_clone_exit_codes(self) -> None:
        self.assertEqual(self.run_cli("--print-clone").exit_code, 3)
        target = self.clone(self.root / "p")
        self.rbos(pulse_target_path=str(target))
        found = self.run_cli("--print-clone")
        self.assertEqual(found.exit_code, 0)
        self.assertEqual(found.output.strip(), str(target))
        self.collector('sync_repo_dir="$OTHER/repo"\n')
        self.assertEqual(self.run_cli("--print-clone").exit_code, 2)
        self.collector(f'sync_repo_dir="{self.clone(self.root / "other")}"\n')
        self.assertEqual(self.run_cli("--print-clone").exit_code, 2)

    def test_invalid_existing_settings_refuse_all_admission_without_writes(self) -> None:
        clone = self.clone(self.home / "pulse")
        path = self.collector(f'device_id="mac-a"\nsync_repo_dir="{clone}"\n')
        original_collector = path.read_bytes()
        for payload in (b'{"fixture":', b"[1,2,3]", b"\xff"):
            config_module.CONFIG_PATH.write_bytes(payload)
            for args in ((), ("--apply",), ("--print-clone",)):
                with self.subTest(payload=payload, args=args):
                    result = self.run_cli(*args)
                    self.assertEqual(result.exit_code, 2 if args == ("--print-clone",) else 1, result.output)
                    self.assertIn("Cannot read settings", result.output)
                    self.assertEqual(config_module.CONFIG_PATH.read_bytes(), payload)
                    self.assertEqual(path.read_bytes(), original_collector)
        with self.assertRaises(ValueError):
            config_module.set_pulse_config(github_login="fixture")
        self.assertEqual(config_module.CONFIG_PATH.read_bytes(), b"\xff")

    def test_set_pulse_rejects_bad_timezone_before_any_setting_changes(self) -> None:
        self.rbos(github_login="fixture-before")
        before = config_module.CONFIG_PATH.read_bytes()
        result = CliRunner().invoke(
            app, ["config", "set-pulse", "--github-login", "fixture-after", "--timezone", "America/Los_Angelesx"]
        )
        self.assertEqual(result.exit_code, 2, result.output)
        self.assertIn("IANA timezone", result.output)
        self.assertEqual(config_module.CONFIG_PATH.read_bytes(), before)
        valid = CliRunner().invoke(app, ["config", "set-pulse", "--timezone", "UTC"])
        self.assertEqual(valid.exit_code, 0, valid.output)
        self.assertEqual(self.rbos_values()["pulse_timezone"], "UTC")

    def test_partial_apply_and_missing_postcondition_report_recovery(self) -> None:
        clone = self.clone(self.home / "pulse")
        body = f'device_id="mac-a"\nsync_repo_dir="{clone}"\nfleet_mode=false\n'
        path = self.collector(body)
        self.rbos(github_login="fixture-before")
        before = config_module.CONFIG_PATH.read_bytes()
        with patch.object(config_module, "set_pulse_config", side_effect=OSError("fixture second writer failure")):
            result = self.run_cli("--apply")
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Enrollment incomplete", result.output)
        self.assertIn("Recovery backup", result.output)
        self.assertIn("write was attempted", result.output)
        self.assertNotEqual(path.read_text(), body)
        self.assertEqual(config_module.CONFIG_PATH.read_bytes(), before)
        path.write_text(body)
        with patch("rebalance.lib.git_ops.fleet_settings", return_value=None):
            missing = self.run_cli("--apply")
        self.assertEqual(missing.exit_code, 1, missing.output)
        self.assertIn("fleet settings missing after enrollment", missing.output)


class DoctorPulseFleetTests(_FleetFixture):
    def rows(self) -> list:
        return _check_pulse_fleet()

    def test_no_collector_and_fleet_off_is_silent(self) -> None:
        self.assertEqual(self.rows(), [])

    def test_fleet_on_without_collector_names_installer(self) -> None:
        self.rbos(pulse_fleet_enabled=True, pulse_target_path=str(self.clone(self.root / "p")))
        [row] = self.rows()
        self.assertEqual(row.status, FAIL)
        self.assertIn("install.sh", row.hint)

    def test_installed_but_unenrolled_warns_with_preview(self) -> None:
        self.collector('device_id="mac-a"\nfleet_mode=true\n')
        [row] = self.rows()
        self.assertEqual(row.status, WARN)
        self.assertIn("not enrolled", row.detail)
        self.assertIn("rebalance config fleet-enroll", row.hint)
        self.assertNotIn("--apply", row.hint)

    def test_invalid_enrollment_fails_with_apply_hint(self) -> None:
        clone = self.clone(self.root / "p")
        self.collector('device_id="mac-a"\nfleet_mode=true\nsync_repo_dir="$OTHER/x"\n')
        self.rbos(pulse_fleet_enabled=True, pulse_target_path=str(clone), pulse_device_id="mac-a")
        [row] = self.rows()
        self.assertEqual(row.status, FAIL)
        self.assertIn("fleet-enroll --apply", row.hint)

    def test_enrolled_ok_and_ignored_filename_warns(self) -> None:
        clone = self.clone(self.root / "p")
        self.collector(f'device_id="mac-a"\nfleet_mode=true\nsync_repo_dir="{clone}"\n')
        self.rbos(
            pulse_fleet_enabled=True,
            pulse_target_path=str(clone),
            pulse_device_id="mac-a",
            pulse_filename="README.md",
        )
        enrolled, filename = self.rows()
        self.assertEqual(enrolled.status, OK)
        self.assertEqual(filename.status, WARN)
        self.assertIn("README.md", filename.detail)
        self.assertIn("fleet-enroll --apply", filename.hint)


if __name__ == "__main__":
    unittest.main()

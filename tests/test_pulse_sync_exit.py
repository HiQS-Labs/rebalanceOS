"""Exit semantics for the pulse scheduler wrapper (GH-282)."""

import contextlib
import io
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "pulse_sync.sh"


def _embedded_python() -> str:
    """Return the Python payload executed by the shell wrapper."""
    script = SCRIPT.read_text()
    start = "if rb_run_python_stdin <<'PY' >> \"$LOG_FILE\" 2>&1\n"
    return script.split(start, 1)[1].split("\nPY\nthen", 1)[0]


def _run_pulse_payload(pulse_result: dict | Exception) -> tuple[int, dict | None, str]:
    """Run the wrapper's Python payload with publish_pulse stubbed."""
    rebalance = types.ModuleType("rebalance")
    ingest = types.ModuleType("rebalance.ingest")
    pulse_mod = types.ModuleType("rebalance.ingest.pulse")
    paths = types.ModuleType("rebalance.paths")

    if isinstance(pulse_result, Exception):

        def _failing_publish(*args, **kwargs):
            raise pulse_result

        pulse_mod.publish_pulse = _failing_publish
    else:
        pulse_mod.publish_pulse = lambda *args, **kwargs: dict(pulse_result)

    paths.resolve_database_path = lambda: "/tmp/rebalance.db"

    modules = {
        "rebalance": rebalance,
        "rebalance.ingest": ingest,
        "rebalance.ingest.pulse": pulse_mod,
        "rebalance.paths": paths,
    }
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    with (
        patch.dict(sys.modules, modules),
        contextlib.redirect_stdout(stdout_buf),
        contextlib.redirect_stderr(stderr_buf),
    ):
        with unittest.TestCase().assertRaises(SystemExit) as raised:
            exec(compile(_embedded_python(), str(SCRIPT), "exec"), {})

    stdout_val = stdout_buf.getvalue()
    stderr_val = stderr_buf.getvalue()

    lines = stdout_val.splitlines()
    json_res = None
    for idx, line in enumerate(lines):
        if line.strip() == "{":
            try:
                json_res = json.loads("\n".join(lines[idx:]))
                break
            except json.JSONDecodeError:
                pass

    return raised.exception.code, json_res, stderr_val


class PulseSyncExitTests(unittest.TestCase):
    def test_clean_success_exits_zero(self) -> None:
        payload = {
            "ok": True,
            "git": {"committed": True, "pushed": True},
        }
        code, res, _ = _run_pulse_payload(payload)
        self.assertEqual(code, 0)
        self.assertIsNotNone(res)

    def test_no_change_exits_zero(self) -> None:
        payload = {
            "ok": True,
            "git": {"committed": False, "pushed": False, "reason": "no content change"},
        }
        code, res, _ = _run_pulse_payload(payload)
        self.assertEqual(code, 0)
        self.assertIsNotNone(res)

    def test_config_error_exits_one(self) -> None:
        payload = {
            "ok": False,
            "error": "pulse config missing keys: ['github_login']",
        }
        code, res, _ = _run_pulse_payload(payload)
        self.assertEqual(code, 1)

    def test_git_delivery_error_exits_two(self) -> None:
        payload = {
            "ok": True,
            "git": {"git_error": "push timeout after 120s", "pending": True},
        }
        code, res, _ = _run_pulse_payload(payload)
        self.assertEqual(code, 2)

    def test_lock_deferred_exits_75(self) -> None:
        # A deferred result even if carrying git_error must exit 75
        payload = {
            "ok": True,
            "git": {"deferred": True, "git_error": "publisher busy for /path/to/repo"},
        }
        code, res, _ = _run_pulse_payload(payload)
        self.assertEqual(code, 75)

    def test_render_or_python_runtime_crash_exits_70_with_traceback(self) -> None:
        code, res, stderr = _run_pulse_payload(ValueError("template rendering failed"))
        self.assertEqual(code, 70)
        self.assertIn("uncaught error during pulse sync", stderr)
        self.assertIn("Traceback", stderr)


if __name__ == "__main__":
    unittest.main()

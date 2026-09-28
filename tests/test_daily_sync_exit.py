"""Exit semantics for the daily scheduler wrapper (GH-146)."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
COMMON = REPO / "scripts" / "lib" / "scheduler_common.sh"


def _embedded_python() -> str:
    """Return the Python payload executed by rb_refresh in scheduler_common.sh."""
    script = COMMON.read_text()
    start = 'rb_run_python_stdin "$scopes" "$days" "$strict" <<\'PY\' >> "${LOG_FILE:-/dev/null}" 2>&1\n'
    if start not in script:
        raise ValueError("Could not find start marker in scheduler_common.sh")
    extracted = script.split(start, 1)[1].split("\nPY\n", 1)[0]
    if not extracted.strip():
        raise ValueError("Extracted Python payload is empty")
    return extracted


def _run_refresh_payload(payload: dict) -> tuple[int, dict]:
    """Run the wrapper's Python payload with refresh_index replaced by a fixture."""
    from rebalance.ingest.index_ops import classify_sync_outcome as real_classify

    rebalance = types.ModuleType("rebalance")
    ingest = types.ModuleType("rebalance.ingest")
    index_ops = types.ModuleType("rebalance.ingest.index_ops")
    paths = types.ModuleType("rebalance.paths")
    index_ops.refresh_index = lambda _db_path, **_kw: payload
    index_ops.classify_sync_outcome = real_classify
    paths.resolve_database_path = lambda: "/tmp/rebalance.db"
    modules = {
        "rebalance": rebalance,
        "rebalance.ingest": ingest,
        "rebalance.ingest.index_ops": index_ops,
        "rebalance.paths": paths,
    }
    output = io.StringIO()
    with (
        patch.dict(sys.modules, modules),
        patch.object(sys, "argv", ["fake_script"]),
        contextlib.redirect_stdout(output),
    ):
        with unittest.TestCase().assertRaises(SystemExit) as raised:
            exec(compile(_embedded_python(), str(COMMON), "exec"), {})

    lines = output.getvalue().splitlines()
    json_start = next(index for index, line in enumerate(lines) if line == "{")
    return raised.exception.code, json.loads("\n".join(lines[json_start:]))


class DailySyncExitTests(unittest.TestCase):
    def test_transient_only_errors_exit_zero_and_preserve_errors(self) -> None:
        payload = {
            "errors": [{"scope": "calendar", "error": "request timed out"}],
            "results": [{"scope": "github", "commits": 3}],
        }

        exit_code, result = _run_refresh_payload(payload)

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["sync_outcome"], "degraded")
        self.assertEqual(result["errors"], payload["errors"])

    def test_github_rate_limit_payload_exits_zero(self) -> None:
        payload = {
            "errors": [{"scope": "github", "error": "Rate limited fetching /user"}],
            "results": [{"scope": "vault", "notes": 12}],
        }

        exit_code, result = _run_refresh_payload(payload)

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["sync_outcome"], "degraded")

    def test_fatal_error_exits_one(self) -> None:
        payload = {
            "errors": [{"scope": "migrations", "error": "unable to open database file"}],
            "results": [],
        }

        exit_code, result = _run_refresh_payload(payload)

        self.assertEqual(exit_code, 1)
        self.assertEqual(result["sync_outcome"], "fatal")

    def test_clean_run_exits_zero(self) -> None:
        exit_code, result = _run_refresh_payload({"errors": [], "results": [{"scope": "vault"}]})

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["sync_outcome"], "complete")


class ClassifySyncOutcomeDirectTests(unittest.TestCase):
    """Direct unit tests for rebalance.ingest.index_ops.classify_sync_outcome."""

    def test_no_errors_is_complete(self) -> None:
        from rebalance.ingest.index_ops import classify_sync_outcome

        outcome, code = classify_sync_outcome({"results": [{"scope": "vault"}]})
        self.assertEqual(outcome, "complete")
        self.assertEqual(code, 0)

    def test_embedding_deferred_by_guard_is_degraded_not_skipped(self) -> None:
        """GH-296: the collector ingested, then the guard deferred its embedding step.

        The work that ran must never be reported as skipped (no exit 75) nor as a
        failure (no exit 1): the run is partial.
        """
        from rebalance.ingest.index_ops import classify_sync_outcome

        outcome, code = classify_sync_outcome(
            {"results": [{"scope": "vault", "ingest": {"new_files": 2}, "embedding_deferred": "refusing to start"}]}
        )
        self.assertEqual((outcome, code), ("degraded", 0))

    def test_no_embedding_deferral_stays_complete(self) -> None:
        from rebalance.ingest.index_ops import classify_sync_outcome

        outcome, code = classify_sync_outcome({"results": [{"scope": "vault", "embedding_deferred": None}]})
        self.assertEqual((outcome, code), ("complete", 0))

    def test_migration_error_is_fatal(self) -> None:
        from rebalance.ingest.index_ops import classify_sync_outcome

        outcome, code = classify_sync_outcome(
            {
                "errors": [{"scope": "migrations", "error": "locked"}],
                "results": [{"scope": "vault"}],
            }
        )
        self.assertEqual(outcome, "fatal")
        self.assertEqual(code, 1)

    def test_partial_error_with_success_is_degraded(self) -> None:
        from rebalance.ingest.index_ops import classify_sync_outcome

        outcome, code = classify_sync_outcome(
            {
                "errors": [{"scope": "github", "error": "rate limit"}],
                "results": [{"scope": "vault"}],
            }
        )
        self.assertEqual(outcome, "degraded")
        self.assertEqual(code, 0)

    def test_all_failed_or_skipped_is_fatal(self) -> None:
        from rebalance.ingest.index_ops import classify_sync_outcome

        outcome, code = classify_sync_outcome(
            {
                "errors": [{"scope": "github", "error": "timeout"}],
                "results": [{"scope": "github", "skipped": True}],
            }
        )
        self.assertEqual(outcome, "fatal")
        self.assertEqual(code, 1)


class ArgvMappingTests(unittest.TestCase):
    """Tests verifying rb_refresh maps sys.argv to refresh_index kwargs and respects strict mode."""

    def _execute_with_argv(self, argv: list[str], payload: dict) -> tuple[int, dict]:
        from rebalance.ingest.index_ops import classify_sync_outcome as real_classify

        captured_kwargs: dict = {}

        def fake_refresh(_db_path, **kw):
            captured_kwargs.update(kw)
            return payload

        rebalance = types.ModuleType("rebalance")
        ingest = types.ModuleType("rebalance.ingest")
        index_ops = types.ModuleType("rebalance.ingest.index_ops")
        paths = types.ModuleType("rebalance.paths")
        index_ops.refresh_index = fake_refresh
        index_ops.classify_sync_outcome = real_classify
        paths.resolve_database_path = lambda: "/tmp/rebalance.db"
        modules = {
            "rebalance": rebalance,
            "rebalance.ingest": ingest,
            "rebalance.ingest.index_ops": index_ops,
            "rebalance.paths": paths,
        }
        output = io.StringIO()
        with (
            patch.dict(sys.modules, modules),
            patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(output),
        ):
            with unittest.TestCase().assertRaises(SystemExit) as raised:
                exec(compile(_embedded_python(), str(COMMON), "exec"), {})

        return raised.exception.code, captured_kwargs

    def test_argv_maps_scopes_and_days(self) -> None:
        code, kwargs = self._execute_with_argv(
            ["script", "github, focus5", "7"],
            {"results": [{"scope": "github"}]},
        )
        self.assertEqual(code, 0)
        self.assertEqual(kwargs, {"scope": ["github", "focus5"], "artifact_sync_days": 7})

    def test_argv_maps_empty_args_to_no_kwargs(self) -> None:
        code, kwargs = self._execute_with_argv(
            ["script", "", ""],
            {"results": [{"scope": "all"}]},
        )
        self.assertEqual(code, 0)
        self.assertEqual(kwargs, {})

    def test_argv_strict_mode_forces_exit_1_on_degraded(self) -> None:
        degraded_payload = {
            "errors": [{"scope": "github", "error": "rate limit"}],
            "results": [{"scope": "focus5"}],
        }
        # Non-strict (default): degraded returns exit 0
        code, _ = self._execute_with_argv(["script", "github,focus5", "7", "0"], degraded_payload)
        self.assertEqual(code, 0)

        # Strict mode (1): degraded returns exit 1 for alert visibility
        strict_code, _ = self._execute_with_argv(["script", "github,focus5", "7", "1"], degraded_payload)
        self.assertEqual(strict_code, 1)

    def test_argv_invalid_days_exits_2(self) -> None:
        code, kwargs = self._execute_with_argv(
            ["script", "github", "invalid_number"],
            {"results": [], "errors": []},
        )
        self.assertEqual(code, 2)
        self.assertEqual(kwargs, {})


class ShellExecutionTests(unittest.TestCase):
    """Direct subprocess execution tests for rb_refresh in scheduler_common.sh."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tempdir = tempfile.TemporaryDirectory()
        cls.stub_dir = Path(cls._tempdir.name) / "stub"
        (cls.stub_dir / "rebalance" / "ingest").mkdir(parents=True)
        (cls.stub_dir / "rebalance" / "paths").mkdir(parents=True)
        (cls.stub_dir / "rebalance" / "__init__.py").write_text("")
        (cls.stub_dir / "rebalance" / "paths" / "__init__.py").write_text(
            'def resolve_database_path(): return ":memory:"\n'
        )
        (cls.stub_dir / "rebalance" / "ingest" / "__init__.py").write_text("")
        (cls.stub_dir / "rebalance" / "ingest" / "index_ops.py").write_text(
            "import os\n"
            "def classify_sync_outcome(res):\n"
            '    outcome = res.get("sync_outcome", "complete")\n'
            '    return outcome, (0 if outcome != "fatal" else 1)\n'
            "\n"
            "def refresh_index(db, **kw):\n"
            '    mode = os.environ.get("TEST_OUTCOME", "complete")\n'
            '    if mode == "degraded":\n'
            '        return {"sync_outcome": "degraded", "errors": [{"scope": "github", "error": "rate limit"}], "results": []}\n'
            '    elif mode == "fatal":\n'
            '        return {"sync_outcome": "fatal", "errors": [{"scope": "all", "error": "fatal"}], "results": []}\n'
            '    return {"sync_outcome": "complete", "errors": [], "results": [{"scope": "all"}]}\n'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tempdir.cleanup()

    def _run_shell_refresh(
        self,
        outcome: str,
        scopes: str = "github",
        days: str = "7",
        strict: str = "0",
    ) -> tuple[int, str, str]:
        cmd = f"""
        set -eu
        export RB_PYTHON="{sys.executable}"
        source "{COMMON}"
        export PYTHONPATH="{self.stub_dir}:$PYTHONPATH"
        export TEST_OUTCOME="{outcome}"
        if rb_refresh "{scopes}" "{days}" "{strict}"; then code=0; else code=$?; fi
        echo "EXIT_CODE=$code"
        echo "OUTCOME=$RB_SYNC_OUTCOME"
        rb_log_sync_outcome "test-job" "$code"
        """
        res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
        lines = res.stdout.strip().splitlines()
        exit_code = int([line for line in lines if line.startswith("EXIT_CODE=")][0].split("=")[1])
        captured_outcome = [line for line in lines if line.startswith("OUTCOME=")][0].split("=")[1]
        logged_line = lines[-1]
        return exit_code, captured_outcome, logged_line

    def test_shell_degraded_strict_exits_1(self) -> None:
        code, outcome, log_line = self._run_shell_refresh("degraded", strict="1")
        self.assertEqual(code, 1)
        self.assertEqual(outcome, "degraded")
        self.assertIn("degraded; finished with non-zero exit (1) due to strict policy", log_line)

    def test_shell_degraded_nonstrict_exits_0(self) -> None:
        code, outcome, log_line = self._run_shell_refresh("degraded", strict="0")
        self.assertEqual(code, 0)
        self.assertEqual(outcome, "degraded")
        self.assertIn("degraded; partial errors or deferred steps recorded", log_line)

    def test_shell_fatal_exits_1(self) -> None:
        code, outcome, log_line = self._run_shell_refresh("fatal", strict="0")
        self.assertEqual(code, 1)
        self.assertEqual(outcome, "fatal")
        self.assertIn("failed fatally", log_line)

    def test_shell_complete_exits_0(self) -> None:
        code, outcome, log_line = self._run_shell_refresh("complete", strict="1")
        self.assertEqual(code, 0)
        self.assertEqual(outcome, "complete")
        self.assertIn("complete", log_line)

    def test_shell_invalid_days_exits_2(self) -> None:
        code, outcome, _ = self._run_shell_refresh("complete", days="not_an_int")
        self.assertEqual(code, 2)


class SchedulerInterpreterSeamTests(unittest.TestCase):
    """Direct tests for the RB_PYTHON interpreter seam and execution guards (GH-289)."""

    def test_default_resolution_unset(self) -> None:
        cmd = f"""
        set -eu
        unset RB_PYTHON || true
        source "{COMMON}"
        echo "RESOLVED_PYTHON=$PYTHON"
        """
        res = subprocess.run(
            ["env", "-u", "RB_PYTHON", "bash", "-c", cmd],
            capture_output=True,
            text=True,
            check=True,
        )
        expected = str(REPO / ".venv" / "bin" / "python")
        self.assertIn(f"RESOLVED_PYTHON={expected}", res.stdout)

    def test_default_resolution_empty(self) -> None:
        cmd = f"""
        set -eu
        export RB_PYTHON=""
        source "{COMMON}"
        echo "RESOLVED_PYTHON=$PYTHON"
        """
        res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
        expected = str(REPO / ".venv" / "bin" / "python")
        self.assertIn(f"RESOLVED_PYTHON={expected}", res.stdout)

    def test_custom_override_resolution(self) -> None:
        custom_python = "/custom/test/python"
        cmd = f"""
        set -eu
        export RB_PYTHON="{custom_python}"
        source "{COMMON}"
        echo "RESOLVED_PYTHON=$PYTHON"
        """
        res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
        self.assertIn(f"RESOLVED_PYTHON={custom_python}", res.stdout)

    def test_rb_run_python_stdin_missing_guard(self) -> None:
        missing_python = "/nonexistent/python/binary"
        cmd = f"""
        export RB_PYTHON="{missing_python}"
        source "{COMMON}"
        rb_run_python_stdin <<'PY'
print("hello")
PY
        """
        res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
        self.assertEqual(res.returncode, 127)
        self.assertIn(f"interpreter unavailable or not executable: {missing_python}", res.stderr)

    def test_rb_run_python_stdin_non_executable_guard(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp_path = Path(tmp.name)
            tmp_path.chmod(0o644)
            cmd = f"""
            export RB_PYTHON="{tmp_path}"
            source "{COMMON}"
            rb_run_python_stdin <<'PY'
print("hello")
PY
            """
            res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
            self.assertEqual(res.returncode, 127)
            self.assertIn(f"interpreter unavailable or not executable: {tmp_path}", res.stderr)

    def test_rb_run_python_stdin_bare_command_name(self) -> None:
        cmd = f"""
        export RB_PYTHON="python3"
        source "{COMMON}"
        rb_run_python_stdin <<'PY'
print("bare_cmd_ok")
PY
        """
        res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
        self.assertIn("bare_cmd_ok", res.stdout)

    def test_rb_refresh_missing_interpreter_logs_diagnostic(self) -> None:
        missing_python = "/nonexistent/python/binary"
        with tempfile.NamedTemporaryFile() as tmp_log:
            log_path = Path(tmp_log.name)
            cmd = f"""
            export RB_PYTHON="{missing_python}"
            export LOG_FILE="{log_path}"
            source "{COMMON}"
            if rb_refresh "" "" "0"; then code=0; else code=$?; fi
            echo "EXIT_CODE=$code"
            """
            res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
            lines = res.stdout.strip().splitlines()
            exit_code = int([line for line in lines if line.startswith("EXIT_CODE=")][0].split("=")[1])
            self.assertEqual(exit_code, 127)
            log_content = log_path.read_text()
            self.assertIn(f"interpreter unavailable or not executable: {missing_python}", log_content)

    def test_rb_refresh_non_executable_logs_diagnostic(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp_py, tempfile.NamedTemporaryFile() as tmp_log:
            py_path = Path(tmp_py.name)
            py_path.chmod(0o644)
            log_path = Path(tmp_log.name)
            cmd = f"""
            export RB_PYTHON="{py_path}"
            export LOG_FILE="{log_path}"
            source "{COMMON}"
            if rb_refresh "" "" "0"; then code=0; else code=$?; fi
            echo "EXIT_CODE=$code"
            """
            res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
            lines = res.stdout.strip().splitlines()
            exit_code = int([line for line in lines if line.startswith("EXIT_CODE=")][0].split("=")[1])
            self.assertEqual(exit_code, 127)
            log_content = log_path.read_text()
            self.assertIn(f"interpreter unavailable or not executable: {py_path}", log_content)


if __name__ == "__main__":
    unittest.main()

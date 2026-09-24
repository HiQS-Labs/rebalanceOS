"""Scheduler policy conformance tests (Phase 4).

SCHEDULER.md is the policy table for the launchd fleet; these tests enforce
its machine-checkable columns against the actual artifacts in ``scripts/``:

- every plist template renders cleanly (no leftover ``{{...}}``), parses, and
  carries the right label, cadence, RunAtLoad/KeepAlive, and program paths
- every wrapper script uses the shared runtime (``lib/scheduler_common.sh``)
  and encodes its policy scope / entry call verbatim
- every job installs through ONE flow (``lib/install_common.sh`` via ``stack.sh``),
  and that flow carries the job-specific steps the retired per-job installers did
- SCHEDULER.md documents every job with its cadence-defining tokens

Everything runs hermetically: templates are rendered with dummy paths and
parsed with ``plistlib`` — no ``launchctl``, no live LaunchAgents, no network.
"""

import os
import plistlib
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
SCHEDULER_MD = REPO / "SCHEDULER.md"

FAKE_ROOT = "/policy-test/repo"
FAKE_PYTHON = "/policy-test/venv/bin/python"
FAKE_HOME = "/policy-test/home"

WORKDAY_HOURS = list(range(6, 24))  # 06:00 through 23:xx


def _hourly(minute):
    return [{"Hour": h, "Minute": minute} for h in WORKDAY_HOURS]


# Mirror of the SCHEDULER.md job table. Keys are the label suffix
# (com.rebalance-os.<key>). Fields:
#   calendar      expected StartCalendarInterval entries (None = no schedule)
#   run_at_load / keep_alive   expected boolean plist keys (absent key = False)
#   wrapper       repo-relative wrapper script, or None for python-direct jobs
#   wrapper_must_contain       policy-bearing lines the wrapper must keep
#   args_must_contain          tokens required in rendered ProgramArguments
#   args_must_not_contain      tokens that must NOT appear (cost guards)
#   retention     log retention days passed to rb_job_init
#   doc_tokens    strings SCHEDULER.md must contain for this job
POLICY = {
    "daily-sync": {
        "calendar": [{"Hour": 6, "Minute": 30}],
        "run_at_load": True,
        "keep_alive": False,
        "wrapper": "scripts/daily_sync.sh",
        "wrapper_must_contain": [
            'rb_job_init "daily-sync" 30',
            "result = refresh_index(db_path)",
        ],
        "doc_tokens": ["daily 06:30", "refresh_index(db_path)"],
    },
    "obsidian-vault-embeddings": {
        "calendar": _hourly(15),
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": "scripts/obsidian_vault_embeddings.sh",
        "wrapper_must_contain": [
            'rb_job_init "obsidian-vault-embeddings" 14',
            'scope=["vault", "semantic"]',
        ],
        "doc_tokens": ["hourly at :15", '["vault", "semantic"]'],
    },
    "github-sync": {
        "calendar": _hourly(45),
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": "scripts/github_sync.sh",
        "wrapper_must_contain": [
            'rb_job_init "github-sync" 14',
            # Focus 5 piggybacks this hourly cadence (no standalone launchd job).
            'scope=["github", "focus5"]',
        ],
        "doc_tokens": ["hourly at :45", '["github", "focus5"]'],
    },
    "pulse-sync": {
        "calendar": _hourly(0),
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": "scripts/pulse_sync.sh",
        "wrapper_must_contain": [
            'rb_job_init "pulse-sync" 14',
            "publish_pulse(db_path, dry_run=False, push=push)",
        ],
        "doc_tokens": ["hourly at :00", "publish_pulse(db_path"],
    },
    "pulse-web-sync": {
        # :08/:38, not :00/:30 (GH-175). This is a derived read-only stage over
        # what pulse-sync writes at :00 — sharing that minute risked rendering
        # from half-written state, so the offset is correctness, not tidiness.
        "calendar": [{"Hour": h, "Minute": m} for h in WORKDAY_HOURS for m in (8, 38)],
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": "scripts/pulse_web_sync.sh",
        "wrapper_must_contain": [
            'rb_job_init "pulse-web-sync" 14',
            "scripts/pulse_web.py",
        ],
        "doc_tokens": ["every 30 min", "pulse_web.py"],
    },
    "pulse-server": {
        "calendar": None,
        "run_at_load": True,
        "keep_alive": True,
        "wrapper": "scripts/pulse_server.sh",
        "wrapper_must_contain": [
            'rb_job_mark_started "pulse-server"',
            "scripts/pulse_server.py",
        ],
        "doc_tokens": ["RunAtLoad + KeepAlive", "pulse_server.py"],
    },
    "pulse-warning-watch": {
        # Off the quarter hours (GH-175): on :00/:15/:30/:45 this collided with
        # pulse-sync, vault-sync, pulse-web-sync and github-sync in turn.
        "calendar": [{"Minute": m} for m in (7, 22, 37, 52)],
        "run_at_load": True,
        "keep_alive": False,
        "wrapper": None,
        "args_must_contain": [
            "scripts/pulse_warning_watch.py",
            "--url",
            "http://127.0.0.1:8767/",
        ],
        "doc_tokens": ["every 15 min", "pulse_warning_watch.py"],
    },
    "daily-work-synthesis": {
        "calendar": None,
        "interval": 900,
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": "scripts/daily_work_synthesis.sh",
        "wrapper_must_contain": [
            'rb_job_init "daily-work-synthesis" 14',
            "utils/daily_work_synthesis.py",
        ],
        "doc_tokens": ["every 15 min", "daily_work_synthesis.py"],
    },
    "health-check": {
        # :10, not :00 (GH-175) — pulse-sync owns :00.
        "calendar": [{"Minute": 10}],
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": None,
        "args_must_contain": ["scripts/health_issue_reporter.py", "--close"],
        # The hourly run is the cheap FAIL-only tier — LLM flags live only in
        # the 3x-daily triage job.
        "args_must_not_contain": ["--llm-triage"],
        "doc_tokens": ["hourly at :10", "--close"],
    },
    "health-check-triage": {
        # :25, not :00 (GH-175) — pulse-sync owns :00.
        "calendar": [
            {"Hour": 8, "Minute": 25},
            {"Hour": 14, "Minute": 25},
            {"Hour": 20, "Minute": 25},
        ],
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": None,
        "args_must_contain": [
            "scripts/health_issue_reporter.py",
            "--llm-triage",
            "--llm-daily-limit",
        ],
        "doc_tokens": ["08:25, 14:25, 20:25", "--llm-triage"],
    },
    "obsidian-rollover": {
        # 00:40, not 00:00 (GH-175) — midnight collided with hourly pulse-sync.
        "calendar": [{"Hour": 0, "Minute": 40}],
        # Loading must never fire the rollover — it would wipe Today's Notes.
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": "utils/obsidian_rollover.sh",
        "wrapper_must_contain": ["obsidian_daily_rollover.py"],
        "doc_tokens": ["daily 00:40", "obsidian_rollover.sh"],
    },
    "daily-synthesis": {
        # 18:20, not 18:00 (GH-175 — inherited from the obsidian-daily-sync half
        # this job absorbed). GH-74 merged the former obsidian-daily-sync (18:20)
        # and git-pulse-daily-synthesis (18:30) into one process, one job: the
        # ordering dependency between the two blocks is now guaranteed by code
        # (pulse block upserted before git-pulse block in the same run), not by
        # keeping two launchd fire times in sync.
        "calendar": [{"Hour": 18, "Minute": 20}],
        # Loading should not fire an off-schedule summary write.
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": "utils/daily_synthesis.sh",
        "wrapper_must_contain": ["daily_synthesis.py"],
        "doc_tokens": ["daily 18:20", "daily_synthesis.sh"],
    },
    "hiqs-digest": {
        # :05, not :00 (GH-175) — pulse-sync owns :00.
        # Local wall clock is deliberate: launchd resolves StartCalendarInterval against
        # the machine's own clock and handles DST itself, which is why this job owns the
        # fire time rather than the Slack-side consumer (AEGIS-Sleuth-Slackbot#158 is an
        # open DST defect in that scheduler).
        "calendar": [{"Hour": 13, "Minute": 5}, {"Hour": 17, "Minute": 5}],
        # Loading must never fire an off-schedule post into a team channel.
        "run_at_load": False,
        "keep_alive": False,
        "wrapper": "scripts/hiqs_digest.sh",
        "wrapper_must_contain": [
            'rb_job_init "hiqs-digest" 14',
            "utils/hiqs_digest.py",
        ],
        "doc_tokens": ["13:05, 17:05", "hiqs_digest.sh"],
    },
}

MAX_RUNTIME_SECONDS = {
    "daily-sync": 10800,
    "obsidian-vault-embeddings": 7200,
    "github-sync": 7200,
    "pulse-sync": 1800,
    "pulse-web-sync": 7200,
    "pulse-server": None,
    "pulse-warning-watch": 300,
    "daily-work-synthesis": 180,
    "health-check": 900,
    "health-check-triage": 1800,
    "obsidian-rollover": 300,
    "hiqs-digest": 14400,
    "daily-synthesis": 900,
}


def _label(job):
    return f"com.rebalance-os.{job}"


def _render(job):
    """Render a template the way install_common.sh does, with dummy paths."""
    text = (SCRIPTS / f"{_label(job)}.plist.template").read_text()
    return (
        text.replace("{{REBALANCE_DIR}}", FAKE_ROOT).replace("{{PYTHON}}", FAKE_PYTHON).replace("{{HOME}}", FAKE_HOME)
    )


def _parse(job):
    return plistlib.loads(_render(job).encode())


def _intervals(plist):
    """Normalize StartCalendarInterval (dict or array) to a list of dicts."""
    raw = plist.get("StartCalendarInterval")
    if raw is None:
        return None
    return [raw] if isinstance(raw, dict) else list(raw)


class TestPlistTemplates(unittest.TestCase):
    def test_every_policy_job_has_a_template(self):
        for job in POLICY:
            self.assertTrue(
                (SCRIPTS / f"{_label(job)}.plist.template").is_file(),
                f"missing template for {job}",
            )

    def test_no_unrendered_placeholders(self):
        for job in POLICY:
            self.assertNotIn("{{", _render(job), f"{job}: unrendered {{{{...}}}}")

    def test_labels_match_filenames(self):
        for job in POLICY:
            self.assertEqual(_parse(job)["Label"], _label(job))

    def test_cadence_matches_policy(self):
        for job, spec in POLICY.items():
            got = _intervals(_parse(job))
            self.assertEqual(
                got,
                spec["calendar"],
                f"{job}: StartCalendarInterval diverged from SCHEDULER.md policy",
            )
            self.assertEqual(
                _parse(job).get("StartInterval"),
                spec.get("interval"),
                f"{job}: StartInterval diverged from SCHEDULER.md policy",
            )

    def test_run_at_load_and_keep_alive(self):
        for job, spec in POLICY.items():
            plist = _parse(job)
            self.assertEqual(
                bool(plist.get("RunAtLoad", False)),
                spec["run_at_load"],
                f"{job}: RunAtLoad",
            )
            self.assertEqual(
                bool(plist.get("KeepAlive", False)),
                spec["keep_alive"],
                f"{job}: KeepAlive",
            )

    def test_managed_jobs_use_standard_launch_priority(self):
        for job in POLICY:
            self.assertNotIn(
                "ProcessType",
                _parse(job),
                f"{job}: launchd background priority can starve startup before guarded work begins",
            )

    def test_program_arguments_reference_real_files(self):
        for job in POLICY:
            for arg in _parse(job)["ProgramArguments"]:
                if not arg.startswith(FAKE_ROOT + "/"):
                    continue
                rel = arg[len(FAKE_ROOT) + 1 :]
                # Only executables must exist in the repo. Runtime artifacts
                # (temp/ logs, state files) are created on first run and are
                # gitignored — asserting them broke CI on clean checkouts.
                if not rel.endswith((".py", ".sh")):
                    continue
                self.assertTrue(
                    (REPO / rel).is_file(),
                    f"{job}: ProgramArguments references missing file {rel}",
                )

    def test_python_direct_jobs_carry_policy_args(self):
        for job, spec in POLICY.items():
            args = " ".join(_parse(job)["ProgramArguments"])
            for token in spec.get("args_must_contain", []):
                self.assertIn(token, args, f"{job}: missing arg {token!r}")
            for token in spec.get("args_must_not_contain", []):
                self.assertNotIn(token, args, f"{job}: forbidden arg {token!r}")

    def test_every_finite_job_is_outer_guarded_at_its_policy_limit(self):
        for job, seconds in MAX_RUNTIME_SECONDS.items():
            args = _parse(job)["ProgramArguments"]
            if seconds is None:
                self.assertNotIn("utils/job_guard.py", " ".join(args))
                continue
            self.assertGreaterEqual(len(args), 10, job)
            self.assertTrue(args[1].endswith("utils/job_guard.py"), job)
            self.assertEqual(args[args.index("--name") + 1], f"scheduler-{job}")
            self.assertEqual(args[args.index("--max-runtime-seconds") + 1], str(seconds))
            self.assertEqual(args[args.index("--lifecycle-job") + 1], job)
            self.assertIn("--", args)

    def test_documented_runtime_policy_is_complete_and_strict(self):
        rows = {}
        for line in SCHEDULER_MD.read_text().splitlines():
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) != 7 or not cells[0].startswith("`"):
                continue
            job = cells[0].strip("`")
            self.assertNotIn(job, rows, f"duplicate scheduler policy row: {job}")
            raw = cells[6]
            rows[job] = None if raw == "none" else int(raw)
        self.assertEqual(rows, MAX_RUNTIME_SECONDS)
        self.assertTrue(all(value is None or value > 0 for value in rows.values()))

    def test_no_secrets_in_templates(self):
        for job in POLICY:
            text = (SCRIPTS / f"{_label(job)}.plist.template").read_text()
            for line in text.splitlines():
                if "sk-ant-" in line and "YOUR-KEY" not in line and "..." not in line:
                    self.fail(f"{job}: template appears to contain a real API key")


class TestWrapperScripts(unittest.TestCase):
    def _wrapper_jobs(self):
        return {j: s for j, s in POLICY.items() if s["wrapper"]}

    def test_wrappers_exist_and_pass_bash_syntax(self):
        shell = list((SCRIPTS / "lib").glob("*.sh"))
        shell += [REPO / s["wrapper"] for s in self._wrapper_jobs().values()]
        shell.append(SCRIPTS / "stack.sh")
        for path in shell:
            self.assertTrue(path.is_file(), f"missing {path}")
            proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, f"{path}: {proc.stderr}")

    def test_scheduled_wrappers_use_shared_runtime(self):
        # scripts/-resident wrappers must source the shared lib; the
        # utils/ rollover wrapper predates it and is exec-only by design.
        for job, spec in self._wrapper_jobs().items():
            if not spec["wrapper"].startswith("scripts/"):
                continue
            text = (REPO / spec["wrapper"]).read_text()
            self.assertIn(
                "lib/scheduler_common.sh",
                text,
                f"{job}: wrapper does not source scheduler_common.sh",
            )

    def test_wrappers_encode_policy_entry_calls(self):
        for job, spec in self._wrapper_jobs().items():
            text = (REPO / spec["wrapper"]).read_text()
            for token in spec.get("wrapper_must_contain", []):
                self.assertIn(token, text, f"{job}: wrapper lost {token!r}")

    def test_wrappers_never_call_launchctl(self):
        # Job runtime must stay hermetic — install/uninstall is installer
        # territory.
        for job, spec in self._wrapper_jobs().items():
            text = (REPO / spec["wrapper"]).read_text()
            self.assertNotIn("launchctl", text, f"{job}: wrapper calls launchctl")


class TestSchedulerCommonRuntime(unittest.TestCase):
    """Run the shared runtime in a throwaway tree — no venv, no real repo."""

    def _make_tree(self, tmp, body):
        import shutil

        repo = Path(tmp) / "repo"
        (repo / "scripts" / "lib").mkdir(parents=True)
        shutil.copy(
            SCRIPTS / "lib" / "scheduler_common.sh",
            repo / "scripts" / "lib" / "scheduler_common.sh",
        )
        wrapper = repo / "scripts" / "job.sh"
        wrapper.write_text(
            '#!/bin/bash\nset -euo pipefail\nsource "$(cd "$(dirname "$0")" && pwd)/lib/scheduler_common.sh"\n' + body
        )
        wrapper.chmod(0o755)
        return repo, wrapper

    def test_init_creates_dated_log_and_preserves_exit_zero(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            repo, wrapper = self._make_tree(tmp, 'rb_job_init "fake-job" 14\nlog "hello"\nrb_trim_logs\n')
            proc = subprocess.run([str(wrapper)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            logs = list((repo / "temp" / "logs").glob("fake_job_*.log"))
            self.assertEqual(len(logs), 1)
            self.assertIn("hello", logs[0].read_text())

    def test_failure_exit_code_survives_lifecycle_trap(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            _, wrapper = self._make_tree(tmp, 'rb_job_init "fake-job" 14\nexit 3\n')
            proc = subprocess.run([str(wrapper)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 3)

    def test_outer_guard_child_suppresses_inner_lifecycle_events(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            repo, wrapper = self._make_tree(tmp, 'rb_job_init "fake-job" 14\nexit 3\n')
            env = os.environ.copy()
            env["REBALANCE_SCHEDULER_LIFECYCLE_CHILD"] = "1"
            proc = subprocess.run([str(wrapper)], capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 3)
            self.assertFalse(
                (repo / "temp" / "logs" / "auth_activity.jsonl").exists(),
                "guarded child duplicated its outer lifecycle events",
            )


def _install(label, *, root, home, wrapper="", env=None):
    """Run rb_install_launchd_job hermetically.

    ``runtime-root`` under the sandbox HOME points REBALANCE_DIR at *root*, so
    temp/ writes and the opt-in config lookup never touch this checkout. plutil
    and launchctl are stubs. The launchctl stub records its calls and models
    registration: a label is loaded while ``$HOME/stub-state/<label>`` exists.
    ``load`` creates the marker, ``unload`` removes it, and ``list`` tests it.
    ``STUB_NEVER_REGISTER=<label>`` makes a load silently not register, and
    ``STUB_STUCK=<label>`` makes an unload silently fail.
    """
    (home / ".config" / "rebalance").mkdir(parents=True, exist_ok=True)
    (home / ".config" / "rebalance" / "runtime-root").write_text(f"{root}\n")
    (home / "Library" / "LaunchAgents").mkdir(parents=True, exist_ok=True)
    stubs = home / "stub-bin"
    stubs.mkdir(exist_ok=True)
    (stubs / "plutil").write_text("#!/bin/bash\nexit 0\n")
    (home / "stub-state").mkdir(exist_ok=True)
    (stubs / "launchctl").write_text(
        "#!/bin/bash\n"
        'printf "%s\\n" "$*" >> "$HOME/launchctl-calls.log"\n'
        'state="$HOME/stub-state"\n'
        'case "$1" in\n'
        '  list) [ -f "$state/$2" ]; exit $? ;;\n'
        '  load) l="$(basename "$2" .plist)"; [ "${STUB_NEVER_REGISTER:-}" = "$l" ] || touch "$state/$l" ;;\n'
        '  unload) l="$(basename "$2" .plist)"; [ "${STUB_STUCK:-}" = "$l" ] || rm -f "$state/$l" ;;\n'
        "esac\n"
        "exit 0\n"
    )
    for stub in stubs.iterdir():
        stub.chmod(0o755)
    run_env = {
        **os.environ,
        "HOME": str(home),
        "PATH": f"{stubs}:{os.environ['PATH']}",
        "STACK_LAUNCHCTL_BIN": str(stubs / "launchctl"),
        **(env or {}),
    }
    script = f'set -euo pipefail; source "{SCRIPTS}/lib/install_common.sh"; rb_install_launchd_job "$1" "$2"'
    return subprocess.run(
        ["bash", "-c", script, "install", label, wrapper],
        capture_output=True,
        text=True,
        env=run_env,
    )


class TestInstallFlow(unittest.TestCase):
    """GH-255: one install path. The 13 per-job installers had drifted from
    ``stack.sh up`` — each ran steps the fleet path skipped. Those steps now live
    in install_common.sh; these tests pin that every path gets them."""

    def setUp(self):
        import tempfile

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name) / "home"
        self.root = Path(tmp.name) / "root"
        self.home.mkdir()
        venv_python = self.root / ".venv" / "bin" / "python"
        venv_python.parent.mkdir(parents=True)
        venv_python.write_text("#!/bin/sh\n")
        venv_python.chmod(0o755)
        self.agents = self.home / "Library" / "LaunchAgents"

    def test_no_per_job_installers_remain(self):
        leftovers = sorted(p.name for p in SCRIPTS.glob("install_*scheduler.sh"))
        self.assertEqual(leftovers, [], "install through `stack.sh install <job>`, not a per-job script")

    def test_stack_script_is_executable_in_git(self):
        """The one documented entry point must be 100755 in the index — a local
        chmod does not fix a fresh clone (four installers once shipped 100644)."""
        out = subprocess.run(
            ["git", "ls-files", "-s", "--", "scripts/stack.sh"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertTrue(out.startswith("100755"), f"scripts/stack.sh not executable in git: {out!r}")

    def test_every_log_directory_in_the_plist_is_created(self):
        """launchd does not create StandardOutPath parents; `stack.sh up` never
        did either, so four jobs logged nowhere on a fresh machine."""
        logging_elsewhere = [
            job
            for job in POLICY
            if any(
                str(_parse(job).get(k, "")).startswith(f"{FAKE_HOME}/Library/Logs/")
                for k in ("StandardOutPath", "StandardErrorPath")
            )
        ]
        self.assertTrue(logging_elsewhere, "expected at least one job logging under ~/Library/Logs")
        for job in logging_elsewhere:
            proc = _install(_label(job), root=self.root, home=self.home)
            if proc.returncode == 3:  # opt-in job skipped before any write
                continue
            self.assertEqual(proc.returncode, 0, f"{job}: {proc.stderr}")
            self.assertTrue((self.home / "Library" / "Logs" / "rebalance-os").is_dir(), job)
            self.assertTrue((self.root / "temp" / "logs").is_dir(), job)

    LEGACY = "com.rebalance-os.vault-sync"

    def _seed_legacy(self, bound_to):
        """An installed, loaded vault-sync plist bound to *bound_to*."""
        self.agents.mkdir(parents=True, exist_ok=True)
        plist = self.agents / f"{self.LEGACY}.plist"
        plist.write_text(f"<plist><string>{bound_to}/scripts/vault_sync.sh</string></plist>")
        (self.home / "stub-state").mkdir(parents=True, exist_ok=True)
        (self.home / "stub-state" / self.LEGACY).touch()
        return plist

    def test_retired_vault_sync_is_unloaded_and_removed(self):
        legacy = self._seed_legacy(self.root)
        proc = _install(_label("obsidian-vault-embeddings"), root=self.root, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(legacy.exists())
        calls = (self.home / "launchctl-calls.log").read_text().splitlines()
        self.assertIn("unload " + str(legacy), calls)
        self.assertIn("Retired com.rebalance-os.vault-sync", proc.stdout)
        # Retirement happens only after the successor loaded (review: a failed
        # replacement must not leave neither job running).
        successor_load = calls.index("load " + str(self.agents / f"{_label('obsidian-vault-embeddings')}.plist"))
        self.assertLess(successor_load, calls.index("unload " + str(legacy)))

    def test_legacy_survives_a_successor_that_never_registers(self):
        legacy = self._seed_legacy(self.root)
        proc = _install(
            _label("obsidian-vault-embeddings"),
            root=self.root,
            home=self.home,
            env={"STUB_NEVER_REGISTER": _label("obsidian-vault-embeddings")},
        )
        self.assertNotEqual(proc.returncode, 0, "an unregistered job must not report success")
        self.assertIn("did not appear in launchctl list", proc.stderr)
        self.assertTrue(legacy.exists(), "the working legacy job was retired before its successor was up")
        self.assertTrue((self.home / "stub-state" / self.LEGACY).exists())

    def test_legacy_bound_to_another_checkout_is_left_alone(self):
        legacy = self._seed_legacy("/some/other/checkout")
        proc = _install(_label("obsidian-vault-embeddings"), root=self.root, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(legacy.exists())
        self.assertNotIn("unload " + str(legacy), (self.home / "launchctl-calls.log").read_text())
        self.assertIn("left retired com.rebalance-os.vault-sync alone", proc.stderr)

    def test_legacy_that_will_not_unload_keeps_its_plist_and_fails(self):
        legacy = self._seed_legacy(self.root)
        proc = _install(
            _label("obsidian-vault-embeddings"), root=self.root, home=self.home, env={"STUB_STUCK": self.LEGACY}
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(legacy.exists(), "deleting a still-loaded job's plist hides it from every tool")
        self.assertIn("still loaded", proc.stderr)

    def test_lapsed_opt_in_job_is_unloaded_and_removed(self):
        """Installed earlier, config since deleted: SKIPPED must not leave it scheduled."""
        label = _label("daily-work-synthesis")
        self.agents.mkdir(parents=True, exist_ok=True)
        dest = self.agents / f"{label}.plist"
        dest.write_text("<plist/>")
        (self.home / "stub-state" / label).parent.mkdir(parents=True, exist_ok=True)
        (self.home / "stub-state" / label).touch()
        proc = _install(label, root=self.root, home=self.home)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertFalse(dest.exists())
        self.assertFalse((self.home / "stub-state" / label).exists())

    def test_no_template_carries_a_secret_shaped_key(self):
        """The dropped-secret warning compares key presence only. A template that
        carried a secret-shaped key (even as a placeholder) would silence it and
        wipe the hand-added value, so the invariant is enforced here, not in prose."""
        import re

        for job in POLICY:
            # Commented-out examples document where to add a key; they are not live.
            text = re.sub(r"<!--.*?-->", "", (SCRIPTS / f"{_label(job)}.plist.template").read_text(), flags=re.S)
            self.assertIsNone(
                re.search(r"<key>[A-Z0-9_]*(API_KEY|TOKEN|SECRET)</key>", text),
                f"{job}: secret-shaped key in a tracked template",
            )

    def test_opt_in_job_is_skipped_without_its_config(self):
        proc = _install(_label("daily-work-synthesis"), root=self.root, home=self.home)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("SKIPPED", proc.stdout)
        self.assertFalse((self.agents / f"{_label('daily-work-synthesis')}.plist").exists())
        self.assertFalse((self.home / "launchctl-calls.log").exists(), "a skipped job must not touch launchd")

    def test_opt_in_job_installs_once_configured(self):
        (self.root / "temp").mkdir()
        (self.root / "temp" / "daily-work-synthesis.json").write_text("{}")
        proc = _install(_label("daily-work-synthesis"), root=self.root, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.agents / f"{_label('daily-work-synthesis')}.plist").is_file())

    def test_render_check_ignores_the_opt_in_gate(self):
        """Preflight must still prove the opt-in template renders."""
        proc = _install(_label("daily-work-synthesis"), root=self.root, home=self.home, env={"RB_RENDER_CHECK": "1"})
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_reinstall_warns_about_a_hand_added_secret(self):
        self.agents.mkdir(parents=True, exist_ok=True)
        dest = self.agents / f"{_label('hiqs-digest')}.plist"
        dest.write_text(
            "<dict><key>EnvironmentVariables</key><dict><key>GEMINI_API_KEY</key><string>x</string></dict></dict>"
        )
        proc = _install(_label("hiqs-digest"), root=self.root, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("hand-added GEMINI_API_KEY", proc.stderr)

    def test_secret_warning_ignores_a_key_that_only_appears_in_a_template_comment(self):
        """health-check's template names GEMINI_API_KEY inside an XML comment; a
        plain grep saw it as present and would drop a hand-added key silently."""
        self.agents.mkdir(parents=True, exist_ok=True)
        dest = self.agents / f"{_label('health-check')}.plist"
        dest.write_text("<dict><key>GEMINI_API_KEY</key><string>x</string></dict>")
        proc = _install(_label("health-check"), root=self.root, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("hand-added GEMINI_API_KEY", proc.stderr)

    def test_fresh_install_has_no_secret_warning(self):
        proc = _install(_label("hiqs-digest"), root=self.root, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("hand-added", proc.stderr)


class TestSchedulerDoc(unittest.TestCase):
    def test_policy_doc_exists_and_documents_every_job(self):
        self.assertTrue(SCHEDULER_MD.is_file(), "SCHEDULER.md missing")
        doc = SCHEDULER_MD.read_text()
        for job, spec in POLICY.items():
            self.assertIn(f"`{job}`", doc, f"SCHEDULER.md missing job {job}")
            for token in spec["doc_tokens"]:
                self.assertIn(token, doc, f"SCHEDULER.md: job {job} missing token {token!r}")


if __name__ == "__main__":
    unittest.main()

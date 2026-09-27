"""GH-23: real Git boundaries, never the operator's repositories."""

import json
from pathlib import Path

from test_pulse_self_repair import _git, _make_repos

from rebalance.ingest.pulse import _commit_and_push_if_changed
from rebalance.ingest.sleuth_reminders import _refresh_file_source
from rebalance.ingest.sync_snapshot import commit_and_push_sync
from rebalance.lib.git_ops import git_pull_rebase_safe


def test_reminder_refresh_never_changes_index_or_worktree(tmp_path: Path):
    remote, local = _make_repos(tmp_path)
    source = local / "reminders.json"
    source.write_text(json.dumps({"reminders": [], "revision": 1}))
    _git(["add", "reminders.json"], cwd=local)
    _git(["commit", "-m", "old export"], cwd=local)
    _git(["push"], cwd=local)
    peer = tmp_path / "peer"
    _git(["clone", str(remote), str(peer)], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=peer)
    _git(["config", "user.email", "test@example.invalid"], cwd=peer)
    (peer / "reminders.json").write_text(json.dumps({"reminders": [], "revision": 2}))
    _git(["add", "reminders.json"], cwd=peer)
    _git(["commit", "-m", "new export"], cwd=peer)
    _git(["push"], cwd=peer)
    before = source.read_bytes()
    result = _refresh_file_source(source)
    assert source.read_bytes() == before
    assert _git(["status", "--porcelain"], cwd=local).stdout == ""
    assert result == ("ok", {"reminders": [], "revision": 2})


def test_foreign_staged_content_is_preserved_not_committed(tmp_path: Path):
    _remote, local = _make_repos(tmp_path)
    (local / "authored.txt").write_text("precious staged work\n")
    _git(["add", "authored.txt"], cwd=local)
    head = _git(["rev-parse", "HEAD"], cwd=local).stdout
    result = _commit_and_push_if_changed(local, "pulse.md", "new page\n", push=True, commit_message="page")
    assert result.get("git_error")
    assert _git(["rev-parse", "HEAD"], cwd=local).stdout == head
    assert _git(["diff", "--cached", "--name-only"], cwd=local).stdout == "authored.txt\n"


def test_existing_rebase_is_not_aborted(tmp_path: Path):
    _remote, local = _make_repos(tmp_path)
    state = local / ".git" / "rebase-merge"
    state.mkdir()
    (state / "sentinel").write_text("other transaction")
    result = git_pull_rebase_safe(local)
    assert result.returncode != 0
    assert (state / "sentinel").read_text() == "other transaction"


def test_snapshot_commit_excludes_reminder_export(tmp_path: Path):
    remote, local = _make_repos(tmp_path)
    for source in ("calendar", "email"):
        directory = local / "sync" / source
        directory.mkdir(parents=True)
        (directory / "device.json").write_text(
            json.dumps({"device_id": "device", "source": source, "generated_at": "2026-09-24T12:00:00Z", "rows": []})
        )
        (directory / "latest.json").write_text(
            json.dumps({"device_id": "device", "snapshot_file": "device.json", "generated_at": "2026-09-24T12:00:00Z"})
        )
    reminder = local / "sync/sleuth/reminders.json"
    reminder.parent.mkdir()
    reminder.write_text("foreign export\n")
    result = commit_and_push_sync(local, "sync", device_id="device", generated_at="2026-09-24T12:00:00Z")
    assert result.get("pushed") is True
    assert "sync/sleuth/reminders.json" not in _git(["ls-tree", "-r", "--name-only", "HEAD"], cwd=remote).stdout
    assert reminder.read_text() == "foreign export\n"


def test_offline_page_retry_does_not_grow_backlog(tmp_path: Path):
    remote, local = _make_repos(tmp_path)
    offline = tmp_path / "offline"
    remote.rename(offline)
    first = _commit_and_push_if_changed(
        local, "pulse.md", "pending\n", push=True, replaceable=True, commit_message="pending"
    )
    head = _git(["rev-parse", "HEAD"], cwd=local).stdout
    retry = _commit_and_push_if_changed(
        local, "pulse.md", "next hourly page\n", push=True, replaceable=True, commit_message="next"
    )
    assert first.get("pending") and retry.get("pending")
    assert _git(["rev-parse", "HEAD"], cwd=local).stdout == head
    assert (local / "pulse.md").read_text() == "pending\n"
    offline.rename(remote)
    delivered = _commit_and_push_if_changed(
        local, "pulse.md", "next hourly page\n", push=True, replaceable=True, commit_message="next"
    )
    assert delivered["pushed"]
    assert _git(["show", "HEAD:pulse.md"], cwd=remote).stdout == "next hourly page\n"


def _collector_env(tmp_path, local):
    import os

    config = tmp_path / "config"
    config.mkdir()
    (config / "config.sh").write_text(
        f'repos=("{local}")\nsync_repo_dir="{local}"\ndevice_id="test-device"\nhostname="test-device"\n'
    )
    return {**os.environ, "GIT_PULSE_CONFIG_DIR": str(config)}, config


def test_shell_collector_defers_to_python_lock(tmp_path: Path):
    import subprocess
    from rebalance.lib.git_ops import git_publish_lock

    _remote, local = _make_repos(tmp_path)
    env, config = _collector_env(tmp_path, local)
    script = Path(__file__).parents[1] / "experimental/git-pulse/collect.sh"
    before = _git(["rev-parse", "HEAD"], cwd=local).stdout
    with git_publish_lock(local):
        blocked = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, timeout=15)
    assert blocked.returncode == 75, blocked.stderr
    assert not (config / "last-run").exists()
    assert _git(["rev-parse", "HEAD"], cwd=local).stdout == before
    done = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    assert (config / "last-run").exists()
    assert _git(["rev-parse", "HEAD"], cwd=local).stdout == _git(["rev-parse", "@{u}"], cwd=local).stdout


def test_peer_pointer_conflict_preserves_both_snapshots(tmp_path: Path):
    remote, local = _make_repos(tmp_path)
    peer = tmp_path / "peer"
    _git(["clone", str(remote), str(peer)], cwd=tmp_path)
    _git(["config", "user.name", "Peer"], cwd=peer)
    _git(["config", "user.email", "peer@example.invalid"], cwd=peer)

    def snapshot(repo, device, stamp):
        for source in ("calendar", "email"):
            directory = repo / "sync" / source
            directory.mkdir(parents=True)
            (directory / f"{device}.json").write_text(
                json.dumps(
                    {"schema_version": 1, "source": source, "device_id": device, "generated_at": stamp, "rows": []}
                )
            )
            (directory / "latest.json").write_text(
                json.dumps({"device_id": device, "generated_at": stamp, "snapshot_file": f"{device}.json"})
            )

    snapshot(peer, "peer", "2026-09-24T12:00:00Z")
    assert commit_and_push_sync(peer, "sync", device_id="peer", generated_at="2026-09-24T12:00:00Z")["pushed"]
    snapshot(local, "local", "2026-09-24T04:30:00-07:00")
    result = commit_and_push_sync(local, "sync", device_id="local", generated_at="2026-09-24T04:30:00-07:00")
    assert result["pushed"], result
    for source in ("calendar", "email"):
        assert (local / f"sync/{source}/local.json").exists()
        assert (local / f"sync/{source}/peer.json").exists()
        assert json.loads((local / f"sync/{source}/latest.json").read_text())["device_id"] == "peer"


def test_shell_lock_covers_push_and_releases_on_exit(tmp_path: Path):
    import subprocess
    import time
    from rebalance.lib.git_ops import git_publish_lock, GitPublishLockBusy
    import pytest

    remote, local = _make_repos(tmp_path)
    env, config = _collector_env(tmp_path, local)
    marker = tmp_path / "pushing"
    release = tmp_path / "release"
    hook = remote / "hooks/pre-receive"
    hook.write_text(f'#!/bin/sh\ntouch "{marker}"\nwhile [ ! -e "{release}" ]; do sleep 0.1; done\n')
    hook.chmod(0o700)
    script = Path(__file__).parents[1] / "experimental/git-pulse/collect.sh"
    proc = subprocess.Popen(["bash", str(script)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 15
        while not marker.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.exists(), "collector did not reach push"
        with pytest.raises(GitPublishLockBusy):
            with git_publish_lock(local):
                pass
        assert not (config / "last-run").exists()
    finally:
        release.touch()
        stdout, stderr = proc.communicate(timeout=15)
    assert proc.returncode == 0, stdout + stderr
    with git_publish_lock(local):
        assert (config / "last-run").exists()


def test_conflict_preserves_commit_and_leaves_no_owned_rebase(tmp_path: Path):
    remote, local = _make_repos(tmp_path)
    peer = tmp_path / "peer"
    _git(["clone", str(remote), str(peer)], cwd=tmp_path)
    _git(["config", "user.name", "Peer"], cwd=peer)
    _git(["config", "user.email", "peer@example.invalid"], cwd=peer)
    assert _commit_and_push_if_changed(peer, "pulse.md", "peer authored content\n", push=True, commit_message="peer")[
        "pushed"
    ]
    result = _commit_and_push_if_changed(
        local, "pulse.md", "precious local content\n", push=True, commit_message="local"
    )
    assert result.get("pending") and result.get("git_error")
    assert (local / "pulse.md").read_text() == "precious local content\n"
    assert not (local / ".git/rebase-merge").exists()
    assert _git(["show", "HEAD:pulse.md"], cwd=local).stdout == "precious local content\n"
    assert _git(["show", "HEAD:pulse.md"], cwd=remote).stdout == "peer authored content\n"


def test_offline_append_only_log_retains_new_days(tmp_path: Path):
    remote, local = _make_repos(tmp_path)
    remote.rename(tmp_path / "offline")
    for day in ("Monday", "Tuesday"):
        result = _commit_and_push_if_changed(
            local, "daily.md", lambda current, day=day: current + day + "\n", push=True, commit_message=day
        )
        assert result.get("pending")
    assert _git(["show", "HEAD:daily.md"], cwd=local).stdout == "Monday\nTuesday\n"


def test_replaceable_page_peer_race_delivers_without_authored_resolution(tmp_path: Path):
    remote, local = _make_repos(tmp_path)
    peer = tmp_path / "peer"
    _git(["clone", str(remote), str(peer)], cwd=tmp_path)
    _git(["config", "user.name", "Peer"], cwd=peer)
    _git(["config", "user.email", "peer@example.invalid"], cwd=peer)
    assert _commit_and_push_if_changed(peer, "pulse.md", "peer page\n", push=True, commit_message="peer")["pushed"]
    result = _commit_and_push_if_changed(
        local, "pulse.md", "current generated page\n", push=True, replaceable=True, commit_message="page"
    )
    assert result["pushed"], result
    assert _git(["show", "HEAD:pulse.md"], cwd=remote).stdout == "current generated page\n"
    assert not (local / ".git/rebase-merge").exists()


def test_malformed_pointer_defers_without_discarding_payload(tmp_path: Path, monkeypatch):
    from test_sync_snapshot import _seed_calendar, _seed_email
    from rebalance.ingest.index_ops import _refresh_sync

    _remote, local = _make_repos(tmp_path)
    database = tmp_path / "source.db"
    _seed_calendar(database, [])
    _seed_email(database, [])
    pointer = local / "sync/calendar/latest.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text('{"device_id": "a"')
    monkeypatch.setattr("rebalance.ingest.config.get_pulse_config", lambda: {"pulse_target_path": str(local)})
    monkeypatch.setattr("rebalance.ingest.config.get_sync_subdir", lambda: "sync")
    monkeypatch.setattr("rebalance.ingest.sync_snapshot.get_device_id", lambda: "device")
    result = _refresh_sync(database, dry_run=False)
    assert result["deferred"] and result["error"]
    assert pointer.read_text() == '{"device_id": "a"'
    assert json.loads((local / "sync/calendar/device.json").read_text())["device_id"] == "device"


def test_owned_filename_is_literal_not_a_git_glob(tmp_path: Path):
    remote, local = _make_repos(tmp_path)
    (local / "page-authored.md").write_text("unrelated private draft\n")
    result = _commit_and_push_if_changed(local, "page*.md", "generated\n", push=True, commit_message="literal path")
    assert result["pushed"], result
    assert "page-authored.md" not in _git(["ls-tree", "-r", "--name-only", "HEAD"], cwd=remote).stdout
    assert (local / "page-authored.md").read_text() == "unrelated private draft\n"


def test_publish_git_paths_handles_timeout_as_git_error(tmp_path: Path, monkeypatch):
    import subprocess
    from rebalance.lib.git_ops import publish_git_paths, run_git

    _remote, local = _make_repos(tmp_path)
    (local / "pulse.md").write_text("content\n")

    def mock_run_git(repo_path, *args, **kwargs):
        if args and args[0] == "push":
            raise subprocess.TimeoutExpired(cmd=["git", "push"], timeout=120.0)
        return run_git(repo_path, *args, **kwargs)

    monkeypatch.setattr("rebalance.lib.git_ops.run_git", mock_run_git)
    result = publish_git_paths(local, ["pulse.md"], "test message", push=True)
    assert result.get("pushed") is False
    assert result.get("pending") is True
    assert "git operation failed" in result.get("git_error", "")
    assert "timed out after 120.0 seconds" in result.get("git_error", "")


def test_publish_git_paths_custom_timeout_env(tmp_path: Path, monkeypatch):
    from rebalance.lib.git_ops import _default_git_timeout

    assert _default_git_timeout(120.0) == 120.0
    monkeypatch.setenv("REBALANCE_GIT_TIMEOUT", "45.5")
    assert _default_git_timeout(120.0) == 45.5
    monkeypatch.setenv("REBALANCE_GIT_TIMEOUT", "invalid")
    assert _default_git_timeout(120.0) == 120.0


def test_rebase_timeout_aborts_cleanly_leaving_no_rebase_merge(tmp_path: Path, monkeypatch):
    import subprocess
    from test_pulse_self_repair import _git
    from rebalance.lib.git_ops import git_pull_rebase_safe, run_git

    remote, local = _make_repos(tmp_path)
    (local / "file.txt").write_text("local content\n")
    _git(["add", "file.txt"], cwd=local)
    _git(["commit", "-m", "local commit"], cwd=local)

    # Make conflicting remote commit
    peer = tmp_path / "peer"
    _git(["clone", str(remote), str(peer)], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=peer)
    _git(["config", "user.email", "test@example.invalid"], cwd=peer)
    (peer / "file.txt").write_text("remote conflicting content\n")
    _git(["add", "file.txt"], cwd=peer)
    _git(["commit", "-m", "remote commit"], cwd=peer)
    _git(["push"], cwd=peer)

    # Monkeypatch run_git so that rebase --continue raises TimeoutExpired
    orig_run_git = run_git

    def flaky_run_git(repo_path, *args, **kwargs):
        if "rebase" in args and "--continue" in args:
            raise subprocess.TimeoutExpired(cmd=["git", "rebase", "--continue"], timeout=0.1)
        return orig_run_git(repo_path, *args, **kwargs)

    monkeypatch.setattr("rebalance.lib.git_ops.run_git", flaky_run_git)

    # Resolver that always tries to continue
    res = git_pull_rebase_safe(local, resolve_conflicts=lambda: True)
    assert res.returncode != 0
    assert not (local / ".git" / "rebase-merge").exists()
    assert not (local / ".git" / "rebase-apply").exists()


def test_publish_pulse_timezone_resolution(tmp_path: Path, monkeypatch):
    from rebalance.ingest.db import db_connection, ensure_baseline_schema
    from rebalance.ingest.pulse import publish_pulse

    remote, local = _make_repos(tmp_path)
    database = tmp_path / "test.db"
    with db_connection(database) as conn:
        ensure_baseline_schema(conn)

    monkeypatch.setattr(
        "rebalance.ingest.pulse.get_pulse_config",
        lambda: {
            "github_login": "testuser",
            "pulse_target_path": str(local),
            "pulse_timezone": "America/Los_Angeles",
        },
    )
    monkeypatch.setattr("rebalance.ingest.pulse.get_github_token", lambda: None)
    result = publish_pulse(database, dry_run=True)
    assert result["ok"] is True
    assert result["timezone"] == "America/Los_Angeles"

    # Test missing timezone falls back to local_tz with note in snapshot
    monkeypatch.setattr(
        "rebalance.ingest.pulse.get_pulse_config",
        lambda: {
            "github_login": "testuser",
            "pulse_target_path": str(local),
            "pulse_timezone": None,
        },
    )
    unset_result = publish_pulse(database, dry_run=True)
    assert unset_result["ok"] is True
    assert any("pulse_timezone unset in config" in note for note in unset_result["notes"])

    # Test invalid timezone returns config error (ok=False)
    monkeypatch.setattr(
        "rebalance.ingest.pulse.get_pulse_config",
        lambda: {
            "github_login": "testuser",
            "pulse_target_path": str(local),
            "pulse_timezone": "Invalid/Timezone_Name",
        },
    )
    invalid_result = publish_pulse(database, dry_run=True)
    assert invalid_result["ok"] is False
    assert "invalid pulse_timezone" in invalid_result["error"]

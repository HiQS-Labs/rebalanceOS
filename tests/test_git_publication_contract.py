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

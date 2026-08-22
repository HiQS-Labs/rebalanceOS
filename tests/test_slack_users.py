"""Tests for the Slack user resolver's cache and best-effort live lookup."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Barrier, Thread
from unittest.mock import patch

from rebalance.ingest import config, slack_users


def _reset_cache() -> None:
    slack_users._cache.update({"path": None, "mtime": None, "users": {}})


def test_cache_hit_avoids_payload_and_api(tmp_path: Path) -> None:
    cache = tmp_path / "slack_users.json"
    cache.write_text(json.dumps({"users": {"U1": "Cached Name"}}), encoding="utf-8")
    with (
        patch.object(slack_users, "SLACK_USERS_PATH", cache),
        patch.object(slack_users, "_fetch_slack_user", side_effect=AssertionError("API called")),
    ):
        _reset_cache()
        assert slack_users.resolve_slack_user("U1", payload={"display_name": "New Name"}) == "Cached Name"


def test_export_payload_cache_miss_writes_through(tmp_path: Path) -> None:
    cache = tmp_path / "nested" / "slack_users.json"
    with patch.object(slack_users, "SLACK_USERS_PATH", cache):
        _reset_cache()
        assert slack_users.resolve_slack_user("U2", payload={"user_profile": {"display_name": "Ada"}}) == "Ada"
        written = json.loads(cache.read_text(encoding="utf-8"))
        assert written["users"] == {"U2": "Ada"}
        assert "automatically" in written["_README"]


def test_configured_token_resolves_via_slack_api_and_caches(tmp_path: Path, monkeypatch) -> None:
    cache = tmp_path / "slack_users.json"
    config_path = tmp_path / "rbos.config"
    config_path.write_text(json.dumps({"slack_bot_token": "xoxb-test"}), encoding="utf-8")

    class Response:
        def read(self) -> bytes:
            return b'{"ok": true, "user": {"profile": {"display_name": "Grace"}}}'

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

    captured: dict[str, str] = {}

    def fake_urlopen(request: object, timeout: int) -> Response:
        captured["authorization"] = request.get_header("Authorization")  # type: ignore[attr-defined]
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        assert timeout == 10
        return Response()

    monkeypatch.setenv(config.KEYRING_DISABLE_ENV_VAR, "1")
    with (
        patch.object(config, "CONFIG_PATH", config_path),
        patch.object(slack_users, "SLACK_USERS_PATH", cache),
        patch.object(slack_users, "urlopen", side_effect=fake_urlopen),
    ):
        _reset_cache()
        assert slack_users.resolve_slack_user("U3") == "Grace"
        assert captured == {
            "authorization": "Bearer xoxb-test",
            "url": "https://slack.com/api/users.info?user=U3",
        }
        assert slack_users.load_user_map() == {"U3": "Grace"}


def test_unresolved_user_falls_back_to_raw_id_without_writing_cache(tmp_path: Path) -> None:
    cache = tmp_path / "slack_users.json"
    with (
        patch.object(slack_users, "SLACK_USERS_PATH", cache),
        patch.object(config, "get_slack_bot_token", return_value=None),
    ):
        _reset_cache()
        assert slack_users.format_slack_mentions("Ping <@U4>") == "Ping @U4"
        assert not cache.exists()


def test_resolved_multiword_names_compact_sleuth_reminders(tmp_path: Path) -> None:
    cache = tmp_path / "slack_users.json"
    cache.write_text(json.dumps({"users": {"U5": "Ada Lovelace"}}), encoding="utf-8")
    with patch.object(slack_users, "SLACK_USERS_PATH", cache):
        _reset_cache()
        assert (
            slack_users.compact_sleuth_reminder(
                "<@U5> - please follow up on <https://example.com|this>\n> Ship the resolver"
            )
            == "Ship the resolver"
        )


def test_concurrent_cache_misses_preserve_both_resolved_users(tmp_path: Path) -> None:
    cache = tmp_path / "slack_users.json"
    barrier = Barrier(2)
    results: dict[str, str | None] = {}

    def resolve(user_id: str, name: str) -> None:
        results[user_id] = slack_users.resolve_slack_user(user_id, payload={"display_name": name})

    original_write = slack_users._write_user_map

    def synchronized_write(users: dict[str, str]) -> None:
        # Both resolvers must read the empty map before either write begins;
        # this deterministically exercises the stale-snapshot race.
        barrier.wait()
        original_write(users)

    with patch.object(slack_users, "SLACK_USERS_PATH", cache):
        with patch.object(slack_users, "_write_user_map", side_effect=synchronized_write):
            _reset_cache()
            first = Thread(target=resolve, args=("U6", "Ada"))
            second = Thread(target=resolve, args=("U7", "Grace"))
            first.start()
            second.start()
            first.join()
            second.join()

        assert results == {"U6": "Ada", "U7": "Grace"}
        assert slack_users.load_user_map() == {"U6": "Ada", "U7": "Grace"}

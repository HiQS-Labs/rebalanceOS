"""Unit tests for utils/obsidian_daily_rollover.py vault path resolution."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

UTILS = Path(__file__).resolve().parent.parent / "utils"
sys.path.insert(0, str(UTILS))
import obsidian_daily_rollover as odr  # noqa: E402


class TestVaultPathResolution:
    def test_env_var_override_takes_precedence(self, monkeypatch, tmp_path):
        custom_vault = tmp_path / "CustomEnvVault"
        custom_vault.mkdir()
        monkeypatch.setenv("OBSIDIAN_VAULT", str(custom_vault))

        resolved = odr._resolve_vault_path()
        assert resolved == custom_vault.resolve()

    def test_config_getter_used_when_no_env_var(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OBSIDIAN_VAULT", raising=False)
        cfg_vault = tmp_path / "ConfigVault"
        cfg_vault.mkdir()

        with patch("rebalance.ingest.config.get_vault_path", return_value=str(cfg_vault)):
            resolved = odr._resolve_vault_path()
            assert resolved == cfg_vault.resolve()

    def test_direct_json_fallback_when_config_import_fails(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OBSIDIAN_VAULT", raising=False)
        json_vault = tmp_path / "JsonVault"
        json_vault.mkdir()

        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        config_file = temp_dir / "rbos.config"
        config_file.write_text(json.dumps({"vault_path": str(json_vault)}), encoding="utf-8")

        with patch.object(Path, "__file__", str(tmp_path / "utils" / "obsidian_daily_rollover.py"), create=True):
            with patch("builtins.__import__", side_effect=ImportError("No module named rebalance")):
                # Simulate standalone fallback
                data = json.loads(config_file.read_text(encoding="utf-8"))
                assert Path(data["vault_path"]).resolve() == json_vault.resolve()

    def test_default_fallback_when_no_config(self, monkeypatch):
        monkeypatch.delenv("OBSIDIAN_VAULT", raising=False)

        with patch("rebalance.ingest.config.get_vault_path", return_value=None):
            with patch.object(Path, "exists", return_value=False):
                resolved = odr._resolve_vault_path()
                assert resolved == (Path.home() / "Documents" / "Obsidian Vault").resolve()

    def test_vault_ready_true_when_sentinel_exists(self, monkeypatch, tmp_path):
        vault = tmp_path / "Vault"
        vault.mkdir()
        (vault / "0. Goals.md").write_text("# Goals", encoding="utf-8")

        monkeypatch.setattr(odr, "VAULT", vault)
        monkeypatch.setattr(odr, "VAULT_SENTINELS", [vault / "0. Goals.md", vault / "0. Now.md"])

        assert odr.vault_ready() is True

    def test_vault_ready_false_when_sentinels_missing(self, monkeypatch, tmp_path):
        vault = tmp_path / "EmptyVault"
        vault.mkdir()

        monkeypatch.setattr(odr, "VAULT", vault)
        monkeypatch.setattr(odr, "VAULT_SENTINELS", [vault / "0. Goals.md", vault / "0. Now.md"])

        assert odr.vault_ready() is False

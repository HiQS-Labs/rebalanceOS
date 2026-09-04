"""GH-161: `_read_config()` must return a dict for ANY file contents.

The bug it locks: `json.loads` happily parses a list, number, string, or null.
The old reader returned that verbatim, and ~40 getters then called `.get(...)`
on it — raising `AttributeError: 'list' object has no attribute 'get'` from a
frame that names nothing about the real cause (a hand-edited config).

Every payload here parses as valid JSON, so the old `except JSONDecodeError`
could never have caught any of them. Witnessed failing at HEAD before the fix:
all four non-object payloads raised, `[1,2,3]` reproducing the reported trace.
"""

import pytest

from rebalance.ingest import config as config_module


@pytest.fixture
def config_path(tmp_path, monkeypatch):
    """Point the resolver at a scratch file and reset the warn-once memo."""
    path = tmp_path / "rbos.config"
    monkeypatch.setattr(config_module, "CONFIG_PATH", path)
    monkeypatch.setattr(config_module, "_WARNED_BAD_CONFIG", set(), raising=False)
    return path


# Valid JSON, wrong shape — the whole point of the bug.
NON_OBJECT_PAYLOADS = ["[1,2,3]", "42", '"x"', "null", "true", "[]"]


@pytest.mark.parametrize("payload", NON_OBJECT_PAYLOADS)
def test_valid_json_of_the_wrong_shape_reads_as_an_empty_dict(config_path, payload):
    config_path.write_text(payload, encoding="utf-8")
    assert config_module._read_config() == {}


@pytest.mark.parametrize("payload", NON_OBJECT_PAYLOADS)
def test_a_getter_survives_valid_json_of_the_wrong_shape(config_path, payload):
    """The reported symptom: the AttributeError reached the operator, not a value."""
    config_path.write_text(payload, encoding="utf-8")
    assert config_module.get_vault_path() is None


def test_malformed_json_still_reads_as_an_empty_dict(config_path):
    config_path.write_text("{oops", encoding="utf-8")
    assert config_module._read_config() == {}


def test_a_missing_file_reads_as_an_empty_dict(config_path):
    assert not config_path.exists()
    assert config_module._read_config() == {}


# --- Negative controls: the guard must not eat valid config ------------------


def test_an_empty_object_reads_as_an_empty_dict(config_path):
    config_path.write_text("{}", encoding="utf-8")
    assert config_module._read_config() == {}


def test_a_real_config_still_resolves(config_path):
    """A guard that discarded everything would pass every test above."""
    config_path.write_text('{"vault_path": "/tmp/vault"}', encoding="utf-8")
    assert config_module._read_config() == {"vault_path": "/tmp/vault"}
    assert config_module.get_vault_path() == "/tmp/vault"


# --- The discard must be loud, but only once (GH-115/GH-116 failure mode) ----


def test_a_discarded_config_warns_on_stderr(config_path, capsys):
    config_path.write_text("[1,2,3]", encoding="utf-8")
    config_module._read_config()
    err = capsys.readouterr().err
    assert str(config_path) in err
    assert "list" in err


def test_the_warning_fires_once_per_path_not_once_per_getter(config_path, capsys):
    """~40 getters call this. Forty identical lines is the same as none."""
    config_path.write_text("[1,2,3]", encoding="utf-8")
    for _ in range(5):
        config_module._read_config()
    assert capsys.readouterr().err.count("warning: ignoring") == 1


def test_a_valid_config_warns_about_nothing(config_path, capsys):
    config_path.write_text('{"vault_path": "/tmp/vault"}', encoding="utf-8")
    config_module._read_config()
    assert capsys.readouterr().err == ""

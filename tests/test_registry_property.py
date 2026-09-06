"""Property coverage for project-registry parsing failures (GH-160)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from hypothesis import given, strategies as st
from pydantic import ValidationError
import pytest

from rebalance.ingest.registry import Registry, RegistryLoadError, read_registry


def _registry_markdown(yaml_block: str) -> str:
    return f"```yaml\n{yaml_block}\n```\n"


@given(st.text())
def test_registry_loader_never_leaks_yaml_errors(yaml_block: str) -> None:
    """Hand-edited YAML either loads or reports the one named loader error."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "registry.md"
        path.write_text(_registry_markdown(yaml_block), encoding="utf-8")
        try:
            loaded = read_registry(path)
        except RegistryLoadError:
            return
        assert isinstance(loaded, Registry)


@pytest.mark.parametrize(
    ("yaml_block", "expected_cause"),
    [
        ("active_projects: [unterminated", yaml.YAMLError),
        ("active_projects: definitely-not-a-list", ValidationError),
    ],
)
def test_registry_loader_wraps_parse_and_schema_failures(
    yaml_block: str, expected_cause: type[Exception]
) -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "registry.md"
        path.write_text(_registry_markdown(yaml_block), encoding="utf-8")

        with pytest.raises(RegistryLoadError) as error:
            read_registry(path)

    assert str(path) in str(error.value)
    assert isinstance(error.value.__cause__, expected_cause)


def test_registry_loader_preserves_a_valid_registry() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "registry.md"
        path.write_text(_registry_markdown("active_projects:\n  - name: Example"), encoding="utf-8")

        loaded = read_registry(path)

    assert [project.name for project in loaded.active_projects] == ["Example"]

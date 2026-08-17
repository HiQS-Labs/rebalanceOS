"""GH-42 — embedder must fail the model load, not abort the process, when
Metal is unavailable.

mlx aborts (SIGABRT) rather than raising when it can't reach a GPU device,
e.g. headless/sandboxed/virtualized macOS sessions. The fix is to probe for
Metal out-of-process (rebalance.lib.metal_probe.metal_available, shared with
tests/conftest.py's GH-250 skip marker) before ever calling into
mlx_embeddings, and raise a normal, catchable exception instead.
"""

from unittest.mock import patch

import pytest

from rebalance.ingest import embedder
from rebalance.ingest.embedder import MLXUnavailableError, _load_model


@pytest.fixture(autouse=True)
def _reset_embedder_state():
    embedder._cached_model = None
    embedder._cached_tokenizer = None
    embedder._cached_model_name = None
    embedder._cache_limit_set = False
    yield


def test_load_model_raises_catchable_error_when_metal_unavailable():
    """No Metal device -> a normal exception, never a crash."""
    with patch.object(embedder, "metal_available", return_value=False):
        with pytest.raises(MLXUnavailableError):
            _load_model("test_model")


def test_load_model_never_imports_mlx_embeddings_when_metal_unavailable():
    """The abort lives inside mlx_embeddings.load(); never call it without Metal."""
    with (
        patch.object(embedder, "metal_available", return_value=False),
        patch("mlx_embeddings.load") as mock_load,
    ):
        with pytest.raises(MLXUnavailableError):
            _load_model("test_model")
        mock_load.assert_not_called()


def test_instrument_embedding_pass_skips_mlx_when_metal_unavailable():
    """The telemetry hook must not touch mlx.core when there is no Metal device."""
    embedder._current_entry_point = None
    with patch.object(embedder, "metal_available", return_value=False) as mock_available:
        embedder.instrument_embedding_pass("test_site")
    mock_available.assert_called_once()

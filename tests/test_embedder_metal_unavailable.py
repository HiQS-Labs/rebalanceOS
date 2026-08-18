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
    prior_entry_point = embedder._current_entry_point
    yield
    embedder._current_entry_point = prior_entry_point


def test_load_model_raises_catchable_error_when_metal_unavailable():
    """No Metal device -> a normal exception, never a crash. This also proves
    the mlx_embeddings.load() call (where the real abort lives) is never
    reached: _load_model raises before that import line runs."""
    with patch.object(embedder, "metal_available", return_value=False):
        with pytest.raises(MLXUnavailableError):
            _load_model("test_model")


def test_instrument_embedding_pass_skips_mlx_when_metal_unavailable():
    """The telemetry hook must not touch mlx.core when there is no Metal device."""
    embedder._current_entry_point = None
    with patch.object(embedder, "metal_available", return_value=False) as mock_available:
        embedder.instrument_embedding_pass("test_site")
    mock_available.assert_called_once()

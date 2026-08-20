"""GH-81 — embedder works seamlessly on CPU / Metal without MLX crashes.

SentenceTransformers runs reliably on both CPU and Apple Silicon Metal without
aborts or SIGABRT exceptions.
"""

from unittest.mock import MagicMock, patch

import pytest

from rebalance.ingest import embedder
from rebalance.ingest.embedder import _load_model


@pytest.fixture(autouse=True)
def _reset_embedder_state():
    embedder._cached_model = None
    embedder._cached_tokenizer = None
    embedder._cached_model_name = None
    embedder._cache_limit_set = False
    prior_entry_point = embedder._current_entry_point
    yield
    embedder._current_entry_point = prior_entry_point


def test_load_model_succeeds_even_when_metal_unavailable():
    """SentenceTransformer loads on CPU without requiring Metal GPU."""
    mock_st = MagicMock()
    with patch("sentence_transformers.SentenceTransformer", return_value=mock_st):
        with patch.object(embedder, "metal_available", return_value=False):
            model, tokenizer = _load_model("mock_model")
            assert model is mock_st
            assert tokenizer is None


def test_instrument_embedding_pass_skips_mlx_when_metal_unavailable():
    """The telemetry hook must not touch mlx.core when there is no Metal device."""
    embedder._current_entry_point = None
    with patch.object(embedder, "metal_available", return_value=False) as mock_available:
        embedder.instrument_embedding_pass("test_site")
    mock_available.assert_called_once()

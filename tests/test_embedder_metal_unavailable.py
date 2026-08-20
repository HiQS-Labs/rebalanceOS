"""GH-81 — embedder works seamlessly on CPU / Metal without MLX crashes.

SentenceTransformers runs reliably on both CPU and Apple Silicon Metal without
aborts or SIGABRT exceptions.
"""

import importlib.util
import sys
from unittest.mock import MagicMock, patch

import pytest

from rebalance.ingest import embedder
from rebalance.ingest.embedder import _load_model


def test_mlx_is_introspectable_by_find_spec():
    """Whatever is registered as `mlx` must survive `importlib.util.find_spec`.

    conftest substitutes a stub module for mlx wherever the real package is
    absent (CI, or a venv without the `embeddings` extra). A `types.ModuleType`
    has `__spec__ = None`, and find_spec raises ValueError on such an entry
    rather than returning None. `transformers` — pulled in by
    sentence-transformers since GH-81 — calls exactly this at import time via
    `is_mlx_available()`, so a spec-less stub takes down every test that
    imports the embedder. Assert the property directly, on real mlx and stub
    alike, so the next import-time prober does not rediscover it in CI.
    """
    assert "mlx" in sys.modules, "conftest should register mlx (real or stub)"
    assert importlib.util.find_spec("mlx") is not None
    assert importlib.util.find_spec("mlx.core") is not None


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

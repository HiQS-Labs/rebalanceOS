"""GH-81 — the embedder's model-loading seam, on CPU and with MLX absent.

Scope, stated precisely because an earlier version of this docstring did not:
most tests here mock `SentenceTransformer` and therefore verify only the
*wiring* — that `_load_model` returns the model, that it does not require Metal,
that telemetry does not reach into `mlx.core` when there is no device. They do
NOT prove the real library loads or runs; a mocked test would pass against a
completely broken sentence-transformers install.

`test_real_model_loads_and_embeds_on_this_machine` is the one that proves it,
un-mocked, against the real model. It is skipped when the model is not already
in the local HuggingFace cache so neither CI nor a fresh clone is made to
download ~130 MB mid-suite — which means the un-mocked coverage exists on
developer machines (macOS/Metal, the platform this product targets) and is
absent in CI by design. Do not "fix" that by deleting the guard.
"""

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebalance.ingest import embedder
from rebalance.ingest.embedder import DEFAULT_MODEL, _load_model


def _model_is_cached(model_name: str) -> bool:
    """True when HuggingFace already has this model on disk (no download needed)."""
    cache = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    return (cache / f"models--{model_name.replace('/', '--')}").is_dir()


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


@pytest.mark.skipif(
    not _model_is_cached(DEFAULT_MODEL),
    reason=f"{DEFAULT_MODEL} is not in the local HF cache; refusing to download ~130MB mid-suite",
)
def test_real_model_loads_and_embeds_on_this_machine():
    """The un-mocked one: load the real model and produce a real vector.

    Every other test in this module mocks `SentenceTransformer`, so none of them
    can tell a working install from a broken one. This is the test that would
    catch a wrong model name, a sentence-transformers API change, a torch/Metal
    load failure, or a dimension drift between `EMBEDDING_DIM` and what the model
    actually emits.

    Asserting the dimension matters beyond "it ran": `EMBEDDING_DIM` is baked
    into the vec0 table declarations in `db/schema.py`, so a model whose true
    output width disagrees with that constant produces a database that rejects
    every insert.
    """
    from rebalance.ingest.embedder import EMBEDDING_DIM, _embed_batch

    model, tokenizer = _load_model(DEFAULT_MODEL)
    assert model is not None

    vectors = _embed_batch(model, tokenizer, ["a real sentence to embed", "and a second one"])

    assert len(vectors) == 2, "one vector per input text"
    assert all(len(v) == EMBEDDING_DIM for v in vectors), (
        f"{DEFAULT_MODEL} must emit {EMBEDDING_DIM}-dim vectors to match the vec0 "
        f"schema; got {[len(v) for v in vectors]}"
    )
    assert any(x != 0.0 for x in vectors[0]), "an all-zero vector means the embed silently no-opped"


def test_load_model_succeeds_even_when_metal_unavailable():
    """Wiring only (mocked): `_load_model` must not require a Metal device.

    Proves the CPU fallback path is reachable. Does NOT prove the real library
    loads — see `test_real_model_loads_and_embeds_on_this_machine` for that.
    """
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

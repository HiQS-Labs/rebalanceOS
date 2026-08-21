"""Local LLM synthesis tests for querier (GH-108).

Pins:
- When mlx-lm is not installed, local synthesis degrades gracefully with a named
  remediation error pointing at the 'local-llm' extra.
- When mlx-lm is present, local synthesis correctly generates responses.
"""

from __future__ import annotations

import sys
import unittest
from unittest import mock

import rebalance.ingest.querier as querier_module
from rebalance.ingest.querier import _synthesize, _synthesize_with_fallback


class QuerierLocalLLMTests(unittest.TestCase):
    def setUp(self) -> None:
        # Reset cached model state between tests
        querier_module._cached_chat_model = None
        querier_module._cached_chat_tokenizer = None
        querier_module._cached_chat_model_name = None

    def tearDown(self) -> None:
        querier_module._cached_chat_model = None
        querier_module._cached_chat_tokenizer = None
        querier_module._cached_chat_model_name = None

    def test_synthesize_raises_named_runtime_error_when_mlx_lm_missing(self) -> None:
        """When mlx-lm is not installed, _synthesize raises a RuntimeError mentioning local-llm."""
        with mock.patch.dict(sys.modules, {"mlx_lm": None}):
            with self.assertRaises(RuntimeError) as ctx:
                _synthesize("Summarize project activity")
            self.assertIn("mlx-lm is not installed", str(ctx.exception))
            self.assertIn("local-llm", str(ctx.exception))

    def test_synthesize_with_fallback_returns_named_failure_when_mlx_lm_missing(self) -> None:
        """When mlx-lm is not installed, _synthesize_with_fallback returns a formatted error."""
        with (
            mock.patch("rebalance.ingest.config.get_gemini_api_key", return_value=None),
            mock.patch.dict(sys.modules, {"mlx_lm": None}),
        ):
            synthesis, model_used = _synthesize_with_fallback("Test prompt")
            self.assertIn("[Local LLM synthesis failed:", synthesis)
            self.assertIn("local-llm", synthesis)
            self.assertIn("(failed)", model_used)

    def test_synthesize_succeeds_when_mlx_lm_available(self) -> None:
        """When mlx-lm is present, _synthesize generates text and cleans up stop tokens."""
        mock_model = mock.MagicMock()
        mock_tokenizer = mock.MagicMock()
        mock_load = mock.MagicMock(return_value=(mock_model, mock_tokenizer))
        mock_generate = mock.MagicMock(return_value="Project is on track.</answer>")

        mock_mlx = mock.MagicMock()
        mock_mlx.load = mock_load
        mock_mlx.generate = mock_generate

        with mock.patch.dict(sys.modules, {"mlx_lm": mock_mlx}):
            result = _synthesize("Test prompt")

        self.assertEqual(result, "Project is on track.")
        mock_load.assert_called_once_with(querier_module.DEFAULT_CHAT_MODEL)
        mock_generate.assert_called_once_with(
            mock_model,
            mock_tokenizer,
            prompt="Test prompt",
            max_tokens=512,
        )

    def test_synthesize_with_fallback_succeeds_when_mlx_lm_available(self) -> None:
        """_synthesize_with_fallback succeeds on local Qwen path when mlx-lm is available."""
        mock_model = mock.MagicMock()
        mock_tokenizer = mock.MagicMock()
        mock_load = mock.MagicMock(return_value=(mock_model, mock_tokenizer))
        mock_generate = mock.MagicMock(return_value="Summary generated locally")

        mock_mlx = mock.MagicMock()
        mock_mlx.load = mock_load
        mock_mlx.generate = mock_generate

        with (
            mock.patch("rebalance.ingest.config.get_gemini_api_key", return_value=None),
            mock.patch.dict(sys.modules, {"mlx_lm": mock_mlx}),
        ):
            synthesis, model_used = _synthesize_with_fallback("Test prompt")

        self.assertEqual(synthesis, "Summary generated locally")
        self.assertEqual(model_used, querier_module.DEFAULT_CHAT_MODEL)


if __name__ == "__main__":
    unittest.main()

import json
from typing import Any

def _json_dumps(value: Any) -> str:
    """Returns a deterministic, sorted, ensure_ascii=False JSON string."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------------------
# Parsing JSON out of freeform model output (GH-5 Phase 1)
# ---------------------------------------------------------------------------
#
# Canonical home for "the model was asked for JSON and mostly complied".
# Two failure shapes recur regardless of provider, and each one silently threw
# away a good answer before this existed:
#
#   1. A markdown fence around the object, despite a JSON response-format
#      request. `format: "json"` / `responseMimeType` are requests, not
#      guarantees.
#   2. Valid JSON followed by unfenced prose ("{...}\nHere is why..."), which
#      raises "Extra data" from json.loads and discards the whole reply.
#
# `utils/3-eyes/three_eyes/classify.py` keeps its own copy of this logic
# deliberately. 3-Eyes is a standalone package that runs from its own launchd
# shim under a limited PYTHONPATH and is designed to degrade gracefully when
# the repo venv is absent — importing `rebalance.lib` would break it in exactly
# the conditions it exists to survive. Equivalence between the two copies is
# proven by a golden-fixture test (tests/test_json_ops.py), not by a shared
# import. Change one, change both, and the fixture will tell you if you didn't.


def strip_code_fences(text: str) -> str:
    """Strip a surrounding markdown code fence, if present.

    Drops the opening fence line (with its optional language tag) and anything
    from the closing fence onward. Text with no leading fence is returned
    stripped but otherwise untouched.
    """
    text = (text or "").strip()
    if not text.startswith("```"):
        return text
    # Drop the opening fence (with optional language tag) and any closing fence.
    text = text.split("\n", 1)[-1] if "\n" in text else ""
    if "```" in text:
        text = text.rsplit("```", 1)[0]
    return text.strip()


def first_json_object(text: str) -> dict | None:
    """Decode the first balanced ``{...}`` object in *text*, ignoring trailing prose.

    Uses ``json.JSONDecoder.raw_decode``, which stops cleanly at the end of the
    first value instead of demanding that the whole string be JSON. Brace-counting
    by hand would mis-handle a ``}`` inside a string literal; the decoder does not.
    """
    start = (text or "").find("{")
    if start < 0:
        return None
    try:
        parsed, _ = json.JSONDecoder().raw_decode(text[start:])
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def parse_llm_json(text: str, *, drop_nulls: bool = True) -> dict | None:
    """Parse a model reply as a JSON object, tolerating fences and trailing prose.

    Returns the parsed object, or ``None`` when the reply genuinely is not a JSON
    object — never raises on malformed input, because every caller's correct
    response to "the model didn't comply" is a fallback, not a traceback.

    With *drop_nulls* (the default), keys whose value is an explicit JSON ``null``
    are removed. This matters for callers that use ``setdefault`` to fill missing
    fields: ``setdefault`` only fills a *missing* key, so ``{"severity": null}``
    would survive as ``None`` and render as the literal string "None" in
    operator-facing output.
    """
    text = strip_code_fences(text)
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        # Valid JSON followed by unfenced prose raises "Extra data". Retry on just
        # the first balanced {...} rather than discarding a good answer because
        # the model kept talking.
        parsed = first_json_object(text)
        if parsed is None:
            return None
    if not isinstance(parsed, dict):
        return None
    return {k: v for k, v in parsed.items() if v is not None} if drop_nulls else parsed

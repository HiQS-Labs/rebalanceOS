"""Hermetic contract tests for the opt-in GH-210 Terra Daily canary."""

from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "utils" / "daily_work_synthesis.py"
SPEC = importlib.util.spec_from_file_location("daily_work_synthesis", MODULE_PATH)
assert SPEC and SPEC.loader
dws = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dws)


def packet(*, first=False, monday=False):
    return {
        "evidence": [{"id": "clio:1"}],
        "first_cycle_today": first,
        "first_cycle_monday": monday,
        "unclosed_loops": {"summary_line": "- **Unclosed Loops**: 1 open PR"},
        "cpu_health": {"summary_line": "- **Machine CPU Health**: clean"},
    }


def result(**overrides):
    value = {
        "focus": "Testing the canary.",
        "trajectory": ["One thread is active.", "Codex is synthesizing."],
        "velocity": "Nominal — one active thread.",
        "operational_horizon": "Finish the canary.",
        "coaching_nudge": "Keep the current thread bounded.",
        "coaching_trigger": "1 active repository in the current window",
        "evidence_ids": ["clio:1"],
        "confidence": 0.8,
        "abstain": False,
        "yesterday_arc": None,
        "weekly_horizon": None,
    }
    value.update(overrides)
    return value


def test_default_is_disabled_and_pins_terra_low():
    cfg = dws.default_config()
    assert cfg["enabled"] is False
    assert cfg["model"] == "gpt-5.6-terra"
    assert cfg["reasoning_effort"] == "low"
    assert cfg["max_calls_per_day"] > 0
    assert cfg["max_estimated_cost_usd_per_day"] > 0


def test_scrub_masks_secret_values_and_emails():
    text = dws.scrub("token=abc123 contact dev@example.com")
    assert "abc123" not in text
    assert "dev@example.com" not in text
    assert "[REDACTED]" in text and "[EMAIL]" in text


def test_recent_prompt_rows_is_bounded_and_time_filtered(tmp_path, monkeypatch):
    log = tmp_path / ".claude" / "prompt-log.jsonl"
    log.parent.mkdir()
    log.write_text(
        "\n".join(
            [
                '{"timestamp":"2026-09-12T16:00:00Z","prompt":"old","agent":"agy","repo":"x"}',
                '{"timestamp":"2026-09-13T01:30:00Z","prompt":"new","agent":"codex","repo":"y"}',
            ]
        )
        + "\n"
    )
    monkeypatch.setattr(dws.Path, "home", classmethod(lambda cls: tmp_path))
    cutoff = datetime.fromisoformat("2026-09-13T00:00:00+00:00")
    rows = dws.recent_prompt_rows(cutoff, limit=1)
    assert [row["prompt"] for row in rows] == ["new"]


def test_validator_rejects_unknown_evidence_id():
    with pytest.raises(ValueError, match="unknown evidence"):
        dws.validate_result(result(evidence_ids=["invented:9"]), packet())


def test_validator_rejects_empty_citation_on_non_abstention():
    with pytest.raises(ValueError, match="must cite"):
        dws.validate_result(result(evidence_ids=[]), packet())


def test_validator_rejects_unrated_velocity():
    with pytest.raises(ValueError, match="allowed rating"):
        dws.validate_result(result(velocity="Fast enough."), packet())


def test_validator_enforces_exactly_once_horizon_fields():
    with pytest.raises(ValueError, match="yesterday_arc cadence"):
        dws.validate_result(result(), packet(first=True))
    dws.validate_result(
        result(yesterday_arc="Previous work landed.", weekly_horizon="Protect Monday."),
        packet(first=True, monday=True),
    )


def test_cost_is_conservative_and_cache_aware():
    usage = {
        "input_tokens": 1000,
        "cached_input_tokens": 800,
        "output_tokens": 100,
        "reasoning_output_tokens": 20,
    }
    expected = (200 * 2.0 + 800 * 0.2 + 120 * 12.0) / 1_000_000
    assert dws.estimated_cost(usage) == pytest.approx(expected)


def test_prompt_allows_apparent_focus_without_claiming_completion():
    prompt = dws.build_prompt(packet())
    assert "may establish an apparent current focus" in prompt
    assert "not proof of execution or completion" in prompt


def test_renderer_preserves_daily_sections_and_adds_receipt():
    cfg = dws.default_config()
    now = datetime.fromisoformat("2026-09-12T12:12:00-07:00")
    text = dws.render(result(), packet(), now, 3, {"input_tokens": 10, "output_tokens": 2}, 0.001, 1.2, cfg)
    for heading in (
        "Synthesis (Cycle 3)",
        "**Focus**",
        "**Trajectory",
        "**Velocity**",
        "**Operational Horizon**",
        "**Unclosed Loops**",
        "**Machine CPU Health**",
        "**Coaching Nudge**",
        "**Model Receipt**",
    ):
        assert heading in text

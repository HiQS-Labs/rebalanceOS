"""Synthetic red controls for the campaign comparator, independent of private history."""

import copy
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("comparison", Path(__file__).with_name("compare_replay.py"))
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def bundles():
    original = dict(
        source={"sha256": "fixture", "bytes": 1},
        as_of_utc="frozen",
        prompts=[dict(id="fixture-1", ordinal=1, text="issue 12", start=True, refs=[])],
        journeys=[dict(id="fixture-1", prompts=["fixture-1"])],
        orphans=[],
        coverage=dict(
            eligible_prompts=1,
            starts=1,
            journeys=1,
            orphans=0,
            devices=1,
            scanned=1,
            out_of_window=0,
            malformed=0,
            unresolved_or_other_repo=0,
            byte_cap_hit=False,
        ),
    )
    before = copy.deepcopy(original)
    before["prompts"][0]["refs"] = [["example/repo", "issue", 12]]
    return original, before, copy.deepcopy(before)


def test_nonempty_comparison():
    records, private = comparison.compare(*bundles())
    assert len(records) == 1 and records[0]["prior_changed"] and records[0]["final_refs"] == 1
    assert "issue 12" in private
    assert "issue 12" not in str(records)


@pytest.mark.parametrize("mutation", ["empty", "source", "start", "membership", "coverage"])
def test_invariants_reject_corrupted_input(mutation):
    original, before, after = bundles()
    if mutation == "empty":
        after["prompts"] = []
    elif mutation == "source":
        after["source"]["sha256"] = "changed"
    elif mutation == "start":
        after["prompts"][0]["start"] = False
    elif mutation == "membership":
        after["journeys"][0]["prompts"] = []
    else:
        after["coverage"]["eligible_prompts"] = 0
    with pytest.raises(AssertionError):
        comparison.compare(original, before, after)

"""Synthetic controls for the retained-metadata composition experiment."""

import importlib.util
from pathlib import Path

import pytest


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


ROOT = Path(__file__).resolve().parents[2]
JR = module(ROOT / "utils/CLIO/journey_replay.py", "jr_control")
FACTS = module(Path(__file__).with_name("replay_saved_facts.py"), "facts_control")
AS_OF = JR.parse_iso("2026-09-16T04:25:38Z")


def snapshot():
    return dict(
        retrieved_at_utc="2026-09-16T14:37:54Z",
        prs=[],
        issues=[
            dict(
                number=10,
                url="https://github.com/HiQS-Labs/XYZ-forge/issues/10",
                createdAt="2026-09-09T04:25:38Z",
                closedAt="2026-09-16T04:25:38Z",
            )
        ],
    )


def test_time_boundary_dedup_and_identity():
    value = snapshot()
    value["issues"] *= 2
    events = FACTS.saved_events(JR, value, AS_OF)
    assert len(events) == 1
    assert events[0]["event"] == "created_at"
    assert events[0]["ref"] == (JR.REPO, "issue", 10)
    assert events[0]["fetched_at"] != events[0]["timestamp"]


def test_wrong_number_rejected():
    value = snapshot()
    value["issues"][0]["number"] = 20
    with pytest.raises(ValueError, match="identity mismatch"):
        FACTS.saved_events(JR, value, AS_OF)


def test_wrong_kind_rejected():
    value = snapshot()
    value["issues"][0]["url"] = "https://github.com/HiQS-Labs/XYZ-forge/pull/10"
    with pytest.raises(ValueError, match="identity mismatch"):
        FACTS.saved_events(JR, value, AS_OF)


def test_foreign_repository_abstains():
    value = snapshot()
    value["issues"][0]["url"] = "https://github.com/example/other/issues/10"
    assert FACTS.saved_events(JR, value, AS_OF) == []


def delivery_snapshot():
    value = snapshot()
    value["prs"] = [
        dict(
            number=20,
            url="https://github.com/HiQS-Labs/XYZ-forge/pull/20",
            mergedAt="2026-09-15T12:00:00Z",
            state="MERGED",
            closingIssuesReferences=[
                dict(
                    number=10,
                    url="https://github.com/HiQS-Labs/XYZ-forge/issues/10",
                    repository=dict(name="XYZ-forge", owner=dict(login="HiQS-Labs")),
                )
            ],
        )
    ]
    return value


def test_delivery_requires_api_relationship_and_preserves_open_issue():
    value = delivery_snapshot()
    value["issues"][0]["state"] = "OPEN"
    links, gaps = FACTS.saved_delivery_links(JR, value, AS_OF)
    assert len(links) == 1 and not gaps
    assert links[0]["issue"] == (JR.REPO, "issue", 10)
    assert links[0]["pr"] == (JR.REPO, "pr", 20)
    assert links[0]["source_field"] == "closingIssuesReferences"
    assert links[0]["fetched_at"] != links[0]["merged_at"]
    assert value["issues"][0]["state"] == "OPEN"
    value["prs"][0]["closingIssuesReferences"] = []
    value["prs"][0]["body"] = "Closes #10"
    assert FACTS.saved_delivery_links(JR, value, AS_OF)[0] == []


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_number",
        "wrong_kind",
        "foreign_repository",
        "conflicting_repository",
        "cutoff",
        "unmerged",
        "missing_refs",
    ],
)
def test_delivery_abstains_on_unsafe_identity_or_time(mutation):
    value = delivery_snapshot()
    pr = value["prs"][0]
    target = pr["closingIssuesReferences"][0]
    if mutation == "wrong_number":
        target["number"] = 99
    elif mutation == "wrong_kind":
        target["url"] = target["url"].replace("/issues/", "/pull/")
    elif mutation == "foreign_repository":
        target["url"] = "https://github.com/Other/repo/issues/10"
    elif mutation == "conflicting_repository":
        target["repository"]["name"] = "other"
    elif mutation == "cutoff":
        pr["mergedAt"] = AS_OF.isoformat()
    elif mutation == "unmerged":
        pr["mergedAt"] = None
    else:
        del pr["closingIssuesReferences"]
    assert FACTS.saved_delivery_links(JR, value, AS_OF)[0] == []


def test_shared_delivery_dedup_and_conflict():
    from copy import deepcopy

    value = delivery_snapshot()
    target = deepcopy(value["prs"][0]["closingIssuesReferences"][0])
    target |= dict(number=11, url=target["url"].replace("/10", "/11"))
    value["prs"][0]["closingIssuesReferences"].append(target)
    value["prs"] *= 2
    links, _ = FACTS.saved_delivery_links(JR, value, AS_OF)
    assert len(links) == 2 and len({tuple(link["pr"]) for link in links}) == 1
    conflict = deepcopy(value["prs"][0])
    conflict["closingIssuesReferences"] = []
    value["prs"].append(conflict)
    links, gaps = FACTS.saved_delivery_links(JR, value, AS_OF)
    assert not links and gaps


@pytest.mark.parametrize("mutation", ["embedded_url", "open_state", "early_retrieval", "null_target"])
def test_review_delivery_blockers(mutation):
    value = delivery_snapshot()
    if mutation == "embedded_url":
        value["prs"][0]["url"] = "https://evil.test/?next=" + value["prs"][0]["url"]
    elif mutation == "open_state":
        value["prs"][0]["state"] = "OPEN"
    elif mutation == "early_retrieval":
        value["retrieved_at_utc"] = "2026-09-14T00:00:00Z"
    else:
        value["prs"][0]["closingIssuesReferences"] = [None]
    links, gaps = FACTS.saved_delivery_links(JR, value, AS_OF)
    assert not links and gaps


def test_event_conflicting_duplicate_fails_closed():
    from copy import deepcopy

    value = delivery_snapshot()
    extra = deepcopy(value["prs"][0])
    extra["mergedAt"] = "2026-09-15T13:00:00Z"
    value["prs"].append(extra)
    with pytest.raises(ValueError, match="conflicting"):
        FACTS.saved_events(JR, value, AS_OF)


def test_event_embedded_url_fails_closed():
    value = snapshot()
    value["issues"][0]["url"] = "https://evil.test/?next=" + value["issues"][0]["url"]
    with pytest.raises(ValueError, match="identity"):
        FACTS.saved_events(JR, value, AS_OF)


def test_event_incoherent_merge_state_fails_closed():
    value = delivery_snapshot()
    value["prs"][0]["state"] = "OPEN"
    with pytest.raises(ValueError, match="state conflicts"):
        FACTS.saved_events(JR, value, AS_OF)


def test_delivery_render_preserves_original_and_compares_same_facts():
    value = delivery_snapshot()
    raw = b'{"timestamp":"2026-09-15T10:00:00Z","repo":"hiqs-labs/xyz-forge","session_id":"synthetic","prompt":"See https://github.com/HiQS-Labs/XYZ-forge/issues/10"}\n'
    rows, _ = JR.load_prompts(raw, "fixture", AS_OF, {JR.REPO}, explicit_links_only=True)
    journeys, parents, orphans = JR.group(rows)
    events = FACTS.saved_events(JR, value, AS_OF)
    bundle = dict(prompts=rows, journeys=journeys, parents=parents, orphans=orphans, events=events, coverage={})
    links, gaps = FACTS.saved_delivery_links(JR, value, AS_OF)
    updated = bundle | dict(issue_evidence=True, delivery_links=links, delivery_gaps=gaps, review_cases=[10])
    result = JR.render(updated)
    assert result.startswith(JR.render(bundle))
    assert bundle["orphans"] == [rows[0]["id"]]
    comparison = result.split("## E —")[1]
    history, plain = comparison.split("#### B —")
    for event in events:
        assert event["id"] in history and event["id"] in plain
    assert links[0]["id"] in history and links[0]["id"] in plain
    assert "Operator judgment: pending" in plain

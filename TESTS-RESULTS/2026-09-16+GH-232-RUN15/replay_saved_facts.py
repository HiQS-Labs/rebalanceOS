"""Campaign-only composition of a private strict replay and retained GitHub metadata.

No fetching or index writes. Uses the existing replay renderer/private publisher.
"""

import argparse
import importlib.util
import json
from datetime import timedelta
from pathlib import Path

from rebalance.lib.json_ops import _json_dumps


def artifact_identity(jr, item, kind):
    """A snapshot URL is an entire canonical artifact URL, not free-form prose."""
    url = item.get("url")
    if (
        not isinstance(url, str)
        or not jr.REF.fullmatch(url)
        or type(item.get("number")) is not int
        or item["number"] <= 0
    ):
        return None
    refs = jr.qualified_references(url)
    return refs[0] if len(refs) == 1 and refs[0] == (jr.REPO, kind, item["number"]) else None


def saved_events(jr, snapshot, as_of):
    events = {}
    records = {}
    retrieved = jr.parse_iso(snapshot.get("retrieved_at_utc"))
    if retrieved is None:
        raise ValueError("snapshot retrieval time missing")
    for key in ("issues", "prs"):
        for item in snapshot[key]:
            identity = jr.qualified_references(item["url"])
            if len(identity) == 1 and identity[0][0] != jr.REPO:
                continue
            expected_kind = "issue" if key == "issues" else "pr"
            identity = artifact_identity(jr, item, expected_kind)
            if identity is None:
                raise ValueError("snapshot artifact identity mismatch")
            repo, kind, number = identity
            signature = tuple(item.get(field) for field in ("createdAt", "closedAt", "mergedAt", "state"))
            if identity in records and records[identity] != signature:
                raise ValueError("conflicting snapshot artifact records")
            records[identity] = signature
            for source_field, event in [
                ("createdAt", "created_at"),
                ("closedAt", "closed_at"),
                ("mergedAt", "merged_at"),
            ]:
                stamp = jr.parse_iso(item.get(source_field))
                if stamp and as_of - timedelta(days=7) <= stamp < as_of:
                    if retrieved < stamp:
                        raise ValueError("snapshot retrieval precedes event")
                    if kind == "pr" and event == "merged_at" and item.get("state") != "MERGED":
                        raise ValueError("snapshot merge state conflicts with event")
                    eid = f"gh:{repo}:{kind}:{number}:{event}:{stamp.isoformat()}"
                    events[eid] = dict(
                        id=eid,
                        timestamp=stamp.isoformat(),
                        kind="recorded event",
                        event=event,
                        ref=(repo, kind, number),
                        url=item["url"],
                        fetched_at=snapshot["retrieved_at_utc"],
                    )
    return sorted(events.values(), key=lambda e: (e["timestamp"], e["id"]))


def saved_delivery_links(jr, snapshot, as_of):
    """Observed API relations, not parsed closing words or historical causation."""
    if not jr.parse_iso(snapshot.get("retrieved_at_utc")):
        raise ValueError("snapshot retrieval time missing")
    links, gaps, records = {}, [], {}
    for item in snapshot["prs"]:
        key = artifact_identity(jr, item, "pr")
        if key is None:
            gaps.append("PR identity conflict; relationship excluded")
            continue
        signature = _json_dumps(
            dict(
                mergedAt=item.get("mergedAt"),
                state=item.get("state"),
                closingIssuesReferences=item.get("closingIssuesReferences"),
            )
        )
        records.setdefault(key, []).append((signature, item))
    for pr, duplicates in sorted(records.items()):
        if len({signature for signature, _ in duplicates}) != 1:
            gaps.append(f"PR #{pr[2]} conflicting snapshots; relationships excluded")
            continue
        item = duplicates[0][1]
        merged = jr.parse_iso(item.get("mergedAt"))
        if not merged or not as_of - timedelta(days=7) <= merged < as_of:
            continue
        if item.get("state") != "MERGED" or jr.parse_iso(snapshot["retrieved_at_utc"]) < merged:
            gaps.append(f"PR #{pr[2]} inconsistent merge state or retrieval time; relationship excluded")
            continue
        targets = item.get("closingIssuesReferences")
        if not isinstance(targets, list):
            gaps.append(f"PR #{pr[2]} closing-issue metadata unavailable")
            continue
        for target in targets:
            if not isinstance(target, dict):
                gaps.append(f"PR #{pr[2]} malformed closing-issue metadata; relationship excluded")
                continue
            issue = artifact_identity(jr, target, "issue")
            repository = target.get("repository", {})
            if not isinstance(repository, dict) or not isinstance(repository.get("owner"), dict):
                gaps.append(f"PR #{pr[2]} repository metadata unavailable; relationship excluded")
                continue
            qualified_repo = f"{repository.get('owner', {}).get('login', '')}/{repository.get('name', '')}".lower()
            if issue is None or qualified_repo != jr.REPO:
                gaps.append(f"PR #{pr[2]} closing-issue identity conflict; relationship excluded")
                continue
            lid = f"gh-link:{pr[0]}:pr:{pr[2]}:issue:{issue[2]}"
            links[lid] = dict(
                id=lid,
                pr=pr,
                issue=issue,
                merged_at=merged.isoformat(),
                fetched_at=snapshot["retrieved_at_utc"],
                source_field="closingIssuesReferences",
                pr_url=item["url"],
                issue_url=target["url"],
            )
    return sorted(links.values(), key=lambda link: link["id"]), sorted(set(gaps))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("runtime", "bundle", "snapshot", "capture", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--delivery-links", action="store_true", help="Compose observed API closing-issue relations.")
    p.add_argument("--review-cases", action="store_true", help="Append the three frozen A/B usefulness cases.")
    a = p.parse_args()
    spec = importlib.util.spec_from_file_location("jr", a.runtime)
    jr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jr)
    assert a.bundle.stat().st_size <= jr.MAX_BYTES, "bundle byte cap exceeded"
    assert a.snapshot.stat().st_size <= jr.MAX_BYTES, "snapshot byte cap exceeded"
    bundle = json.loads(a.bundle.read_text())
    assert bundle["prompts"], "empty replay"
    assert bundle["coverage"]["reference_policy"] == "explicit URLs only", "strict replay required"
    snapshot = json.loads(a.snapshot.read_text())
    assert snapshot["issues"] or snapshot["prs"], "empty retained snapshot"
    assert len(snapshot["issues"]) + len(snapshot["prs"]) <= jr.MAX_ROWS, "snapshot row cap exceeded"
    as_of = jr.parse_iso(bundle["as_of_utc"])
    assert jr.parse_iso(snapshot["historical_cutoff_utc"]) == as_of, "snapshot cutoff mismatch"
    events = saved_events(jr, snapshot, as_of)
    assert events, "no retained facts"
    bundle["events"] = events
    bundle["coverage"] |= dict(
        github_events=len(events),
        github_status="retained snapshot experiment",
        snapshot_retrieved_at=snapshot["retrieved_at_utc"],
    )
    if a.delivery_links:
        links, gaps = saved_delivery_links(jr, snapshot, as_of)
        bundle |= dict(delivery_links=links, delivery_gaps=gaps, issue_evidence=True)
    if a.review_cases:
        assert a.delivery_links, "review requires verified delivery composition"
        bundle["review_cases"] = [508, 568, 623]
    raw, meta = jr.snapshot(a.capture)
    assert meta == bundle["source"], "capture mismatch"
    jr.publish(a.output, raw, bundle, a.capture, meta)
    linked = {tuple(r) for row in bundle["prompts"] for r in row["refs"]}
    print(
        _json_dumps(
            dict(
                saved_events=len(events),
                explicitly_referenced_events=sum(tuple(e["ref"]) in linked for e in events),
                deployment="unknown",
                source="retained metadata only",
            )
        )
    )


if __name__ == "__main__":
    main()

"""Private frozen-input preservation check; emits only safe aggregate receipts."""

import argparse
import importlib.util
import json
from copy import deepcopy
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("replay", args.runtime)
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    original = json.loads(args.evidence.read_text())
    assert len(original["prompts"]) == 288, "frozen input missing or changed"
    assert len(original["journeys"]) == 9 and len(original["orphans"]) == 212
    assert original["as_of_utc"] == "2026-09-16T04:25:38+00:00"
    raw, meta = replay.snapshot(args.capture)
    assert meta["sha256"] == original["source"]["sha256"]
    updated = deepcopy(original) | dict(issue_evidence=True)
    before = replay.render(original)
    preview = replay.render(updated)
    assert preview.startswith(before), "existing preview changed"
    assert {k: v for k, v in updated.items() if k != "issue_evidence"} == original
    mentions = [r for r in original["prompts"] if (replay.REPO, "issue", 568) in replay.qualified_references(r["text"])]
    assert len(mentions) == 3
    assert sum(r["id"] in original["orphans"] for r in mentions) == 2
    section = preview.split("## D — Explicit issue evidence")[1]
    target = section.split("### hiqs-labs/xyz-forge#568\n")[1].split("\n### ")[0]
    assert all(r["id"] in target for r in mentions)
    assert target.count("Unassigned —") == 2
    replay.publish(args.output, raw, updated, args.capture, meta)
    assert args.output.stat().st_mode & 0o777 == 0o700
    assert all(p.stat().st_mode & 0o777 == 0o600 for p in args.output.iterdir())
    print(
        json.dumps(
            dict(
                eligible=288,
                journeys=9,
                unassigned=212,
                issue_568_mentions=3,
                issue_568_unassigned=2,
                original_bundle_unchanged=True,
                original_preview_prefix_unchanged=True,
                private_permissions=True,
            )
        )
    )


if __name__ == "__main__":
    main()

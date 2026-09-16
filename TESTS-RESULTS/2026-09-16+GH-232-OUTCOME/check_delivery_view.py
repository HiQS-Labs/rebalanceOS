"""Compare two private replay bundles; emit only public-safe aggregate receipts."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    args = parser.parse_args()
    before = json.loads((args.before / 'evidence.json').read_text())
    after = json.loads((args.after / 'evidence.json').read_text())
    assert before['prompts'] and len(before['prompts']) == 288
    for key in ('prompts', 'journeys', 'parents', 'orphans', 'source', 'as_of_utc', 'events', 'coverage'):
        assert before[key] == after[key], f'{key} changed'
    links = after['delivery_links']
    assert len(links) == 8 and not after['delivery_gaps']
    pairs = {(link['pr'][2], link['issue'][2]) for link in links}
    assert pairs == {(535, 508), (540, 536), (557, 556), (577, 561),
                     (581, 568), (640, 623), (641, 609), (641, 626)}
    assert all(link['source_field'] == 'closingIssuesReferences' for link in links)
    assert not any(link['issue'][2] in (567, 589, 608) for link in links)
    # Original chat views precede the opt-in issue section and remain byte-identical.
    old_preview = (args.before / 'preview.md').read_text()
    new_preview = (args.after / 'preview.md').read_text()
    assert old_preview.split('## D —')[0] == new_preview.split('## D —')[0]
    assert new_preview.count('#### A — Compact history') == 3
    assert new_preview.count('#### B — Plain issue evidence list') == 3
    assert args.after.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in args.after.iterdir())
    print(json.dumps(dict(original_preserved=True, saved_events=len(after['events']),
                          closing_relationships=len(links), review_cases=after['review_cases'],
                          open_direct_shared_controls=True, private_permissions=True,
                          operator_feedback='pending', deployment='unknown')))


if __name__ == '__main__':
    main()

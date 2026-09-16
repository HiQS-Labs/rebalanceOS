"""Campaign-only composition of a private strict replay and retained GitHub metadata.

No fetching or index writes. Uses the existing replay renderer/private publisher.
"""
import argparse
import importlib.util
import json
from datetime import timedelta
from pathlib import Path

from rebalance.lib.json_ops import _json_dumps


def saved_events(jr, snapshot, as_of):
    events = {}
    for key in ('issues', 'prs'):
        for item in snapshot[key]:
            identity = jr.qualified_references(item['url'])
            if len(identity) != 1 or identity[0][0] != jr.REPO:
                continue
            repo, kind, number = identity[0]
            expected_kind = 'issue' if key == 'issues' else 'pr'
            if kind != expected_kind or item['number'] != number:
                raise ValueError('snapshot artifact identity mismatch')
            for source_field, event in [('createdAt', 'created_at'), ('closedAt', 'closed_at'),
                                        ('mergedAt', 'merged_at')]:
                stamp = jr.parse_iso(item.get(source_field))
                if stamp and as_of - timedelta(days=7) <= stamp < as_of:
                    eid = f'gh:{repo}:{kind}:{number}:{event}:{stamp.isoformat()}'
                    events[eid] = dict(id=eid, timestamp=stamp.isoformat(), kind='recorded event',
                                       event=event, ref=(repo, kind, number), url=item['url'],
                                       fetched_at=snapshot['retrieved_at_utc'])
    return sorted(events.values(), key=lambda e: (e['timestamp'], e['id']))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'bundle', 'snapshot', 'capture', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    spec = importlib.util.spec_from_file_location('jr', a.runtime)
    jr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jr)
    bundle = json.loads(a.bundle.read_text())
    assert bundle['prompts'], 'empty replay'
    assert bundle['coverage']['reference_policy'] == 'explicit URLs only', 'strict replay required'
    snapshot = json.loads(a.snapshot.read_text())
    as_of = jr.parse_iso(bundle['as_of_utc'])
    assert jr.parse_iso(snapshot['historical_cutoff_utc']) == as_of, 'snapshot cutoff mismatch'
    events = saved_events(jr, snapshot, as_of)
    assert events, 'no retained facts'
    bundle['events'] = events
    bundle['coverage'] |= dict(github_events=len(events), github_status='retained snapshot experiment',
                               snapshot_retrieved_at=snapshot['retrieved_at_utc'])
    raw, meta = jr.snapshot(a.capture)
    assert meta == bundle['source'], 'capture mismatch'
    jr.publish(a.output, raw, bundle, a.capture, meta)
    linked = {tuple(r) for row in bundle['prompts'] for r in row['refs']}
    print(_json_dumps(dict(saved_events=len(events),
                          explicitly_referenced_events=sum(tuple(e['ref']) in linked for e in events),
                          deployment='unknown', source='retained metadata only')))


if __name__ == '__main__':
    main()

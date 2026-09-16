"""Compare three retained replay bundles; public counts, private source-linked review.

Run with PYTHONPATH=src. Output files must be new. This is campaign analysis, not a collector.
"""
import argparse
import json
import os
from pathlib import Path

from rebalance.lib.json_ops import _json_dumps


def compare(baseline, before, after):
    assert baseline['prompts'] and before['prompts'] and after['prompts'], 'empty input'
    assert baseline['source'] == before['source'] == after['source'], 'source changed'
    assert baseline['as_of_utc'] == before['as_of_utc'] == after['as_of_utc'], 'window changed'
    identity = lambda b: [{k: v for k, v in p.items() if k != 'refs'} for p in b['prompts']]
    assert identity(baseline) == identity(before) == identity(after), 'prompt identity/start drift'
    membership = lambda b: [(j['id'], j['prompts']) for j in b['journeys']]
    assert membership(baseline) == membership(before) == membership(after), 'journey membership drift'
    assert baseline['orphans'] == before['orphans'] == after['orphans'], 'assignment drift'
    for key in ('eligible_prompts', 'starts', 'journeys', 'orphans', 'devices', 'scanned',
                'out_of_window', 'malformed', 'unresolved_or_other_repo', 'byte_cap_hit'):
        assert baseline['coverage'].get(key) == before['coverage'].get(key) == after['coverage'].get(key), key
    records, private = [], ['# Private reference review', '', 'Assistant diagnostic review, not human accuracy labels.', '']
    for original, previous, current in zip(baseline['prompts'], before['prompts'], after['prompts']):
        old, prev, new = (set(map(tuple, x['refs'])) for x in (original, previous, current))
        if old == prev == new:
            continue
        case = len(records) + 1
        records.append(dict(case=case, prior_changed=old != prev, changed_now=prev != new,
                            added=len(new-prev), removed=len(prev-new), retained=len(prev & new),
                            retained_prior_additions=len((prev-old) & new), final_refs=len(new)))
        private += [f'## Case {case} — source ordinal {current["ordinal"]}',
                    f'ID: {current["id"]}', f'Original: {sorted(old)}', f'Before: {sorted(prev)}',
                    f'After: {sorted(new)}', '', current['text'], '']
    assert records, 'no changed cases to review'
    return records, '\n'.join(private)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'before', 'after', 'public_output', 'private_output'):
        p.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    args = p.parse_args()
    bundles = [json.loads(path.read_text()) for path in (args.baseline, args.before, args.after)]
    records, private = compare(*bundles)
    assert not args.public_output.exists() and not args.private_output.exists(), 'output exists'
    with args.private_output.open('x') as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(private)
    with args.public_output.open('x') as f:
        for record in records:
            f.write(_json_dumps(record) + '\n')
    print(_json_dumps(dict(review_cases=len(records), prior_cases=sum(r['prior_changed'] for r in records),
                          changed_now=sum(r['changed_now'] for r in records),
                          added=sum(r['added'] for r in records), removed=sum(r['removed'] for r in records),
                          invariants='passed')))


if __name__ == '__main__':
    main()

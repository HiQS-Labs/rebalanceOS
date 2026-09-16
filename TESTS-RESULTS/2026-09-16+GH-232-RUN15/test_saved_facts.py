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
JR = module(ROOT / 'utils/CLIO/journey_replay.py', 'jr_control')
FACTS = module(Path(__file__).with_name('replay_saved_facts.py'), 'facts_control')
AS_OF = JR.parse_iso('2026-09-16T04:25:38Z')


def snapshot():
    return dict(retrieved_at_utc='2026-09-16T14:37:54Z', prs=[], issues=[dict(
        number=10, url='https://github.com/HiQS-Labs/XYZ-forge/issues/10',
        createdAt='2026-09-09T04:25:38Z', closedAt='2026-09-16T04:25:38Z')])


def test_time_boundary_dedup_and_identity():
    value = snapshot()
    value['issues'] *= 2
    events = FACTS.saved_events(JR, value, AS_OF)
    assert len(events) == 1
    assert events[0]['event'] == 'created_at'
    assert events[0]['ref'] == (JR.REPO, 'issue', 10)
    assert events[0]['fetched_at'] != events[0]['timestamp']


def test_wrong_number_rejected():
    value = snapshot()
    value['issues'][0]['number'] = 20
    with pytest.raises(ValueError, match='identity mismatch'):
        FACTS.saved_events(JR, value, AS_OF)


def test_wrong_kind_rejected():
    value = snapshot()
    value['issues'][0]['url'] = 'https://github.com/HiQS-Labs/XYZ-forge/pull/10'
    with pytest.raises(ValueError, match='identity mismatch'):
        FACTS.saved_events(JR, value, AS_OF)


def test_foreign_repository_abstains():
    value = snapshot()
    value['issues'][0]['url'] = 'https://github.com/example/other/issues/10'
    assert FACTS.saved_events(JR, value, AS_OF) == []

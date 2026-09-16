"""Synthetic, nonempty replay fixtures; never reads operator history."""
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("journey_replay", Path(__file__).parents[1] / "utils/CLIO/journey_replay.py")
jr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(jr)
AS_OF = jr.parse_iso("2026-09-16T00:00:00Z")


def row(prompt="/start-task #10", **extra):
    return dict(timestamp="2026-09-15T10:00:00Z", repo="verified-clone", agent="codex",
                machine="device-a", session_id="chat-a", prompt=prompt) | extra


def load(*rows, explicit_links_only=False):
    raw = b"\n".join(json.dumps(r).encode() for r in rows) + b"\n"
    return jr.load_prompts(raw, "fixture", AS_OF, {"verified-clone"}, explicit_links_only=explicit_links_only)


@pytest.mark.parametrize("text", ["/start-task #10", "/express #10", "Please start the fix", "Let's start GH10", "hotfix: repair loader", "[$start-task](skill.md) #10"])
def test_starts(text):
    assert jr.is_start(text)


@pytest.mark.parametrize("text", ['"/start-task #10"', "`/express`", "> /start-task #10", "Do not start", "Please start if tests pass", "How do I /start-task?", "Example: /express", "keep going", "not yet /express"])
def test_nonstarts(text):
    assert not jr.is_start(text)


@pytest.mark.parametrize("text,kind,number", [
    ("issue 626", "issue", 626), ("Issue #626", "issue", 626),
    ("PR 553", "pr", 553), ("check PR #553", "pr", 553),
    ("pull request 553", "pr", 553), ("/start-task on 567 now", "issue", 567),
    ("/start-task 567", "issue", 567),
])
def test_typed_references_require_verified_context(text, kind, number):
    assert jr.references(text, True) == [(jr.REPO, kind, number)]
    assert jr.references(text, False) == []


@pytest.mark.parametrize("text", ["567", "phase 2", "version 567.2", "/start-task on PR 2 phase",
                                       "issue 626abc", "issue 626.5"])
def test_numbers_are_not_implicitly_issues(text):
    refs = jr.references(text, True)
    assert all(kind != "issue" for _, kind, _ in refs)


def test_qualified_pr_and_issue_do_not_get_duplicate_types():
    assert jr.references("PR #553 and issue #626", True) == [
        (jr.REPO, "issue", 626), (jr.REPO, "pr", 553)]
    assert jr.references("https://github.com/Other/Repo/pull/553", True) == [("other/repo", "pr", 553)]
    assert jr.references("/start-task on PR 2 phase", True) == []
    assert jr.references("PR #2 phase", True) == []


def test_scope_and_negative_join_control(monkeypatch):
    def check():
        refs = jr.references("Other/repo#10 and #10", False)
        assert (jr.REPO, "issue", 10) not in refs
    check()
    original = jr.references
    monkeypatch.setattr(jr, "references", lambda text, context: original(text, True))
    with pytest.raises(AssertionError):
        check()  # deliberately broken bare-number join is caught


@pytest.mark.parametrize('text,expected', [
    ('PR **#519** and PR `#520`', [(jr.REPO, 'pr', 519), (jr.REPO, 'pr', 520)]),
    ('CLOSED PR **#566**', [(jr.REPO, 'pr', 566)]),
    ('PR #519 then PR **#519**', [(jr.REPO, 'pr', 519)]),
    ('Join XYZ AgentChorus #123456 to discuss PR #519', [(jr.REPO, 'pr', 519)]),
    ('Join XYZ agent2agent #123456 to discuss issue #12', [(jr.REPO, 'issue', 12)]),
    ('Issue #123456', [(jr.REPO, 'issue', 123456)]),
])
def test_formatting_and_chat_ids(text, expected):
    assert jr.references(text, True) == expected


@pytest.mark.parametrize('text', [
    'Join XYZ AgentChorus **#123456** to discuss PR #519',
    'Join XYZ agent2agent `#123456` to discuss PR #519',
])
def test_formatted_chat_ids_are_not_issues(text):
    assert jr.references(text, True) == [(jr.REPO, 'pr', 519)]


@pytest.mark.parametrize('url', [
    'https://github.com/HiQS-Labs/XYZ-forge/issues/123.5',
    'https://github.com/HiQS-Labs/XYZ-forge/pull/123-invalid',
])
def test_invalid_artifact_url_is_not_a_prefix_match(url):
    assert jr.references(url, False) == []


@pytest.mark.parametrize('ending', ['#issuecomment-123', '?view=1', ')', '.'])
def test_valid_artifact_url_delimiters(ending):
    assert jr.references('https://github.com/HiQS-Labs/XYZ-forge/issues/123' + ending, False) == [
        (jr.REPO, 'issue', 123)]


def test_explicit_links_mode_keeps_uncertainty_out_of_joins():
    raw = (json.dumps(row('/start-task #10; Catalog PR 8; Other/project#25; '
                          'https://github.com/HiQS-Labs/XYZ-forge/pull/520')).encode() + b'\n')
    rows, _ = jr.load_prompts(raw, 'fixture', AS_OF, {'verified-clone'}, explicit_links_only=True)
    assert rows[0]['refs'] == [(jr.REPO, 'pr', 520)]
    assert {x['number'] for x in rows[0]['unresolved_refs']} == {10, 8, 25}
    assert all(x['repository'] is None for x in rows[0]['unresolved_refs'])
    assert jr.group(rows)[0][0]['issues'] == []


def test_explicit_links_mode_requires_no_checkout_guess():
    raw = (json.dumps(row('https://github.com/Other/project/issues/25', repo='verified-clone')).encode() + b'\n')
    rows, _ = jr.load_prompts(raw, 'fixture', AS_OF, {'verified-clone'}, explicit_links_only=True)
    assert rows[0]['refs'] == [('other/project', 'issue', 25)]
    assert rows[0]['unresolved_refs'] == []


def test_unresolved_mentions_cannot_attach_events():
    raw = json.dumps(row('/start-task #10; Catalog PR 8')).encode() + b'\n'
    rows, _ = jr.load_prompts(raw, 'fixture', AS_OF, {'verified-clone'}, explicit_links_only=True)
    journeys, parents, orphans = jr.group(rows)
    bundle = dict(prompts=rows, journeys=journeys, parents=parents, orphans=orphans, coverage={},
                  events=[dict(timestamp='2026-09-15T11:00:00Z', id='fixture-event',
                               ref=(jr.REPO, 'pr', 8), event='merged_at', url='fixture-merge')])
    assert 'fixture-merge' not in jr.render(bundle)
    rows[0]['refs'] = [(jr.REPO, 'pr', 8)]  # Deliberately restore the wrong join.
    assert 'fixture-merge' in jr.render(bundle)


def test_grouping_same_input_and_no_bridge():
    rows, _ = load(row(), row("continue", timestamp="2026-09-15T11:00:00Z"),
                   row(session_id="chat-b", machine="device-b"),
                   row("/start-task #10 and #11", session_id="chat-c"),
                   row("unassigned", session_id=None))
    journeys, parents, orphans = jr.group(rows)
    assert len(journeys) == 3 and len(orphans) == 1
    assert len(parents[f"{jr.REPO}#10"]) == 2
    assert len(parents) == 2  # ambiguous third segment is NOT a bridge
    assert sum(len(j["prompts"]) for j in journeys) + len(orphans) == len(rows)


def test_qualified_next_task_preserves_original_and_separates_events():
    rows, _ = load(row('/start-task https://github.com/HiQS-Labs/XYZ-forge/issues/10'),
                   row('Next task: https://github.com/HiQS-Labs/XYZ-forge/issues/20',
                       timestamp='2026-09-15T11:00:00Z'),
                   row('continue', timestamp='2026-09-15T12:00:00Z'))
    original = jr.group(rows)
    journeys, parents, orphans = jr.group(rows, qualified_transitions=True)
    assert len(original[0]) == 1 and len(journeys) == 2
    assert journeys[0]['prompts'] == [rows[0]['id']]
    assert journeys[1]['prompts'] == [rows[1]['id'], rows[2]['id']]
    assert journeys[0]['issues'] == [(jr.REPO, 'issue', 10)]
    assert journeys[1]['issues'] == [(jr.REPO, 'issue', 20)]
    assert not rows[1]['start']  # Candidate boundaries do not rewrite captured intent.
    assert jr.group(rows) == original
    bundle = dict(prompts=rows, journeys=journeys, parents=parents, orphans=orphans,
                  coverage={}, events=[dict(timestamp='2026-09-15T13:00:00Z', id='event-20',
                      ref=(jr.REPO, 'issue', 20), event='closed_at', url='fixture-close-20')])
    preview = jr.render(bundle)
    first, second = preview.split('### ')[1:3]
    assert 'fixture-close-20' not in first and 'fixture-close-20' in second
    original_bundle = bundle | dict(journeys=original[0], parents=original[1], orphans=original[2],
                                   candidate_view=dict(journeys=journeys, parents=parents, orphans=orphans))
    candidate_sections = jr.render(original_bundle).split('### Candidate ')[1:3]
    assert 'fixture-close-20' not in candidate_sections[0]
    assert 'fixture-close-20' in candidate_sections[1]
    # Disable the optional detector to witness that the boundary assertion constrains it.
    assert len(jr.group(rows, qualified_transitions=False)[0]) != len(journeys)


@pytest.mark.parametrize('text', [
    'Next task: issue #20',
    'Next task: https://github.com/Other/project/issues/20',
    'Next task: https://github.com/HiQS-Labs/XYZ-forge/pull/20',
    'Next task: https://github.com/HiQS-Labs/XYZ-forge/issues/20?',
    'Next task: do not start https://github.com/HiQS-Labs/XYZ-forge/issues/20',
    '"Next task: https://github.com/HiQS-Labs/XYZ-forge/issues/20"',
    'Next task: https://github.com/HiQS-Labs/XYZ-forge/issues/20 and issue #30',
    'Next task: https://github.com/HiQS-Labs/XYZ-forge/issues/20 and https://github.com/Other/project/issues/30',
    'Next: https://github.com/HiQS-Labs/XYZ-forge/issues/20',
    'Next task: https://github.com/HiQS-Labs/XYZ-forge/issues/10',
    'And then do same for: https://github.com/HiQS-Labs/XYZ-forge/issues/20',
])
def test_unclear_transitions_abstain(text):
    rows, _ = load(row('/start-task https://github.com/HiQS-Labs/XYZ-forge/issues/10'),
                   row(text, timestamp='2026-09-15T11:00:00Z'), explicit_links_only=True)
    assert jr.group(rows, qualified_transitions=True) == jr.group(rows)


def test_transition_needs_a_known_unambiguous_prior_task():
    for initial in ('/start-task now', '/start-task #10 and #30'):
        rows, _ = load(row(initial), row('Next task: start https://github.com/HiQS-Labs/XYZ-forge/issues/20',
                                         timestamp='2026-09-15T11:00:00Z'), explicit_links_only=True)
        assert jr.group(rows, qualified_transitions=True) == jr.group(rows)


def test_transition_view_excludes_guesses_without_explicit_links_flag():
    rows, _ = load(row('/start-task https://github.com/HiQS-Labs/XYZ-forge/issues/10'),
                   row('Next task: https://github.com/HiQS-Labs/XYZ-forge/issues/20',
                       timestamp='2026-09-15T11:00:00Z'),
                   row('Catalog PR 8 is mentioned only', timestamp='2026-09-15T12:00:00Z'))
    original = jr.group(rows)
    candidate = jr.group(rows, qualified_transitions=True)
    bundle = dict(prompts=rows, journeys=original[0], parents=original[1], orphans=original[2],
                  coverage={}, candidate_view=dict(journeys=candidate[0], parents=candidate[1], orphans=candidate[2]),
                  events=[dict(timestamp='2026-09-15T13:00:00Z', id='foreign-guess', ref=(jr.REPO,'pr',8),
                               event='merged_at', url='should-not-join-candidate')])
    assert 'should-not-join-candidate' not in jr.render(bundle).split('## C —')[1]
    assert all((jr.REPO, 'pr', 8) not in j['issues'] for j in candidate[0])
    assert jr.group(rows) == original


def test_bare_prior_issue_cannot_qualify_a_transition():
    rows, _ = load(row('/start-task #10'), row('Next task: https://github.com/HiQS-Labs/XYZ-forge/issues/20',
                                              timestamp='2026-09-15T11:00:00Z'))
    assert len(jr.group(rows, qualified_transitions=True)[0]) == 1


def test_repeated_start_new_attempt_and_no_lookahead():
    before, _ = load(row(), row("continue", timestamp="2026-09-15T11:00:00Z"))
    after, _ = load(row(), row("continue", timestamp="2026-09-15T11:00:00Z"),
                    row("/express #10", timestamp="2026-09-15T12:00:00Z"))
    assert [(r["start"], r["id"]) for r in before] == [(r["start"], r["id"]) for r in after[:2]]
    assert jr.group(after)[0][0] == jr.group(before)[0][0]
    assert len(jr.group(after)[0]) == 2


def test_bad_rows_duplicates_and_window():
    rows, counts = load(row(), row(), [], row(timestamp="bad"), row(machine=12),
                        row(timestamp="2026-09-01T00:00:00Z"), row(repo="unknown", prompt="start #9"))
    assert len(rows) == 1
    assert counts["duplicates"] == 1 and counts["malformed"] == 3
    assert counts["out_of_window"] == 1 and counts["unresolved_or_other_repo"] == 1
    with pytest.raises(ValueError, match="no eligible"):
        load(row(timestamp="2026-09-01T00:00:00Z"))


def test_snapshot_and_mutation_control(tmp_path):
    source = tmp_path / "capture"
    source.write_bytes(b'{}\npartial')
    raw, meta = jr.snapshot(source)
    assert raw == b'{}\n' and meta["partial_tail"]
    jr.verify_prefix(source, meta)
    source.write_bytes(b'[]\npartial')
    with pytest.raises(ValueError, match="prefix changed"):
        jr.verify_prefix(source, meta)


def test_github_readonly_events_and_absence(tmp_path):
    db = tmp_path / "fixture.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE github_items(repo_full_name,item_type,number,created_at,closed_at,merged_at,fetched_at)")
    conn.execute("INSERT INTO github_items VALUES(?,?,?,?,?,?,?)",
                 (jr.REPO, "pr", 12, "2026-09-15T10:00:00Z", None, "2026-09-15T12:00:00Z", "2026-09-16T01:00:00Z"))
    conn.execute("INSERT INTO github_items VALUES(?,?,?,?,?,?,?)",
                 ("other/repo", "pr", 12, "2026-09-15T10:00:00Z", None, None, "later"))
    conn.commit()
    conn.close()
    original = db.read_bytes()
    events, status = jr.github_events(db, AS_OF)
    assert status == "available" and len(events) == 2
    assert events[1]["event"] == "merged_at" and events[1]["kind"] == "recorded event"
    assert db.read_bytes() == original
    assert jr.github_events(tmp_path / "absent", AS_OF)[1].startswith("unavailable")
    assert not (tmp_path / "absent").exists()


def test_intent_control_and_private_publish(tmp_path, monkeypatch):
    rows, _ = load(row("/start-task #10; create and merge a PR"))
    journeys, parents, orphans = jr.group(rows)
    bundle = dict(prompts=rows, journeys=journeys, parents=parents, orphans=orphans, events=[], coverage={})
    def check():
        assert all(r["kind"] == "intent" for r in bundle["prompts"])
        assert bundle["events"] == []
    check()
    rows[0]["kind"] = "completed"
    with pytest.raises(AssertionError):
        check()
    rows[0]["kind"] = "intent"
    source = tmp_path / "source"
    source.write_bytes(b'{}\n')
    raw, meta = jr.snapshot(source)
    out = tmp_path / "out"
    jr.publish(out, raw, bundle, source, meta)
    assert (out / "preview.md").read_text() == jr.render(bundle)
    assert (out / "capture.jsonl").stat().st_mode & 0o777 == 0o600
    assert out.stat().st_mode & 0o777 == 0o700
    sentinel = (out / "preview.md").read_bytes()
    with pytest.raises(ValueError, match="exists"):
        jr.publish(out, raw, bundle, source, meta)
    assert (out / "preview.md").read_bytes() == sentinel
    monkeypatch.setattr(jr, "render", lambda _: (_ for _ in ()).throw(ValueError("render failed")))
    with pytest.raises(ValueError, match="render failed"):
        jr.publish(tmp_path / "new", raw, bundle, source, meta)
    assert not (tmp_path / "new").exists()


def test_caps_explicit(tmp_path, monkeypatch):
    monkeypatch.setattr(jr, "MAX_ROWS", 1)
    rows, coverage = load(row(), row(session_id="other"))
    assert len(rows) == 1 and coverage["row_cap_hit"] == 1
    monkeypatch.setattr(jr, "MAX_BYTES", 3)
    source = tmp_path / "source"
    source.write_bytes(b'{}\n{}\n')
    assert jr.snapshot(source)[1]["byte_cap_hit"]


def test_canonical_markdown_contract():
    raw = b'''Personal notes are not input.
<!-- clio:id:chat-one:2026-09-15T10:00:00Z -->
## XYZ-FORGE
2026-09-15 03:00 PDT
device-a \xc2\xb7 branch \xc2\xb7 codex

> "/start-task #10
> keep the source intact"

## Personal heading
Do not ingest me
'''
    decoded = jr.markdown_rows(raw)
    rows, _ = jr.load_prompts(decoded, "fixture", AS_OF, {"xyz-forge"})
    assert len(rows) == 1 and rows[0]["start"]
    assert rows[0]["text"] == "/start-task #10\nkeep the source intact"
    assert rows[0]["device"] == "device-a" and rows[0]["agent"] == "codex"
    assert rows[0]["timestamp"] == "2026-09-15T10:00:00+00:00"
    assert b'Personal heading' not in decoded

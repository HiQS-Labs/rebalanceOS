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


def load(*rows):
    raw = b"\n".join(json.dumps(r).encode() for r in rows) + b"\n"
    return jr.load_prompts(raw, "fixture", AS_OF, {"verified-clone"})


@pytest.mark.parametrize("text", ["/start-task #10", "/express #10", "Please start the fix", "Let's start GH10", "hotfix: repair loader", "[$start-task](skill.md) #10"])
def test_starts(text):
    assert jr.is_start(text)


@pytest.mark.parametrize("text", ['"/start-task #10"', "`/express`", "> /start-task #10", "Do not start", "Please start if tests pass", "How do I /start-task?", "Example: /express", "keep going", "not yet /express"])
def test_nonstarts(text):
    assert not jr.is_start(text)


def test_scope_and_negative_join_control(monkeypatch):
    def check():
        refs = jr.references("Other/repo#10 and #10", False)
        assert (jr.REPO, "issue", 10) not in refs
    check()
    original = jr.references
    monkeypatch.setattr(jr, "references", lambda text, context: original(text, True))
    with pytest.raises(AssertionError):
        check()  # deliberately broken bare-number join is caught


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

#!/bin/bash
# Fixture harness for utils/CLIO/clio-codex-tail.sh (GH-139 Phase 2).
#
# Exercises the at-least-once contract against a synthetic rollout tree:
# start-now default, explicit backfill, restart-no-duplicates (tailer run
# twice with NO exporter in between), truncated final record, rotation
# rescan, overlapping invocations, and a busy append lock.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TAILER="$ROOT/utils/CLIO/clio-codex-tail.sh"
FIXTURE="$ROOT/test/fixtures/clio/codex-rollout.jsonl"
INSTALL_DOC="$ROOT/utils/CLIO/INSTALL.md"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/clio-codex-tail.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || fail "python3 is required to run this harness"
command -v jq >/dev/null 2>&1 || fail "jq is required to run this harness"

# Install the shared writer (extracted from INSTALL.md) into a throwaway HOME.
setup_home() { # $1 = case dir; echoes the home path
  home="$1/home"
  mkdir -p "$home/.claude/hooks" "$home/.zcode"
  awk '/^cat > ~\/\.claude\/hooks\/clio-capture\.sh << .EOF.$/{f=1;next} f&&/^EOF$/{exit} f' \
    "$INSTALL_DOC" > "$home/.claude/hooks/clio-capture.sh"
  [ -s "$home/.claude/hooks/clio-capture.sh" ] || fail "could not extract the shared writer"
  chmod +x "$home/.claude/hooks/clio-capture.sh"
  printf '%s\n' "$home"
}

new_session_file() { # $1 = CODEX_HOME; echoes the rollout path
  seedir="$1/sessions/2026/08/31"
  mkdir -p "$seedir"
  printf '%s\n' "$seedir/rollout-2026-08-31T10-00-00-abc.jsonl"
}

log_count() { [ -f "$1" ] && wc -l < "$1" | tr -d ' ' || echo 0; }

# -- 1. start-now default: pre-existing rollout history is NOT imported -------
home=$(setup_home "$TMP/start-now")
rollout=$(new_session_file "$TMP/start-now/codex")
cp "$FIXTURE" "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/start-now/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=0 deferred_files=0" ] \
  || fail "start-now: expected zero delivered rows, got: $out"
[ "$(log_count "$home/.claude/prompt-log.jsonl")" = "0" ] \
  || fail "start-now: history import happened despite the default"

# -- 1b. first sighting ends in a PARTIAL record: completion delivered once ---
home=$(setup_home "$TMP/partial-first")
rollout=$(new_session_file "$TMP/partial-first/codex")
cp "$FIXTURE" "$rollout"
printf '%s' '{"payload":{"type":"user_message","message":"This is the fifth mock user prompt, present but unterminated at first sighting, long enough to clear the threshold."},"timestamp":"2099-08-27T19:25:00.000Z","type":"event_msg"}' >> "$rollout"
HOME="$home" CODEX_HOME="$TMP/partial-first/codex" "$TAILER" >/dev/null
[ "$(log_count "$home/.claude/prompt-log.jsonl")" = "0" ] \
  || fail "partial first sighting: a partial record was captured pre-completion"
printf '\n' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/partial-first/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=1 deferred_files=0" ] \
  || fail "partial first sighting: completion was not delivered, got: $out"
[ "$(log_count "$home/.claude/prompt-log.jsonl")" = "1" ] \
  || fail "partial first sighting: expected exactly 1 row after completion"

# -- 2. explicit backfill imports the pre-existing rows -----------------------
home=$(setup_home "$TMP/backfill")
rollout=$(new_session_file "$TMP/backfill/codex")
cp "$FIXTURE" "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" CLIO_TAIL_BACKFILL=1 "$TAILER")
[ "$out" = "clio-codex-tail: delivered=2 deferred_files=0" ] \
  || fail "backfill: expected the two user prompts delivered, got: $out"
log="$home/.claude/prompt-log.jsonl"
[ "$(log_count "$log")" = "2" ] || fail "backfill: expected 2 JSONL rows"
grep -qF '"agent":"codex"' "$log" || fail "backfill: agent not stamped"
grep -qF '"timestamp":"2026-08-27T19:16:03Z"' "$log" \
  || fail "backfill: sub-second timestamp not normalized to UTC seconds"
grep -qF '"repo":"mock-repo"' "$log" || fail "backfill: repo not derived from session cwd"
grep -qF 'Injected AGENTS-style context' "$log" \
  && fail "backfill: response_item content leaked into the log" || true
grep -qF '"timestamp":"2026-08-27T19:16:20Z"' "$log" \
  && fail "backfill: agent_message was captured" || true

# -- 3. restart-no-duplicates: tailer runs twice, NO exporter in between ------
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=0 deferred_files=0" ] \
  || fail "restart: expected an idle second run, got: $out"
[ "$(log_count "$log")" = "2" ] || fail "restart: duplicate rows appeared"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$(log_count "$log")" = "2" ] || fail "restart x2: duplicate rows appeared"
ids=$(jq -r '(.session_id + ":" + .timestamp)' "$log" | sort -u | wc -l | tr -d ' ')
[ "$ids" = "2" ] || fail "restart: JSONL contains duplicate IDs"

# -- 4. live append: only the new prompt is delivered -------------------------
printf '%s\n' '{"payload":{"type":"user_message","message":"This is the third mock user prompt, appended live after the first tailer pass, long enough to clear the capture threshold."},"timestamp":"2026-08-27T19:20:00.000Z","type":"event_msg"}' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=1 deferred_files=0" ] \
  || fail "live append: expected 1 new row, got: $out"
[ "$(log_count "$log")" = "3" ] || fail "live append: expected 3 JSONL rows"

# -- 5. truncated final record: retried, never written half -------------------
printf '%s' '{"payload":{"type":"user_message","message":"This is the fourth mock user prompt, deliberately left unfinished on the writes' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$(log_count "$log")" = "3" ] \
  || fail "truncated record: a partial record was written"
printf '%s with no trailing newline."},"timestamp":"2026-08-27T19:21:00.000Z","type":"event_msg"}\n' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=1 deferred_files=0" ] \
  || fail "truncated record: completion was not delivered on the next run"
[ "$(log_count "$log")" = "4" ] || fail "truncated record: expected 4 JSONL rows"

# -- 6. rotation: replaced file rescans; IDs suppress duplicates --------------
cp "$FIXTURE" "$rollout.new" && mv "$rollout.new" "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$(log_count "$log")" = "4" ] \
  || fail "rotation: rescan duplicated rows (expected suppression by ID)"
ids=$(jq -r '(.session_id + ":" + .timestamp)' "$log" | sort -u | wc -l | tr -d ' ')
[ "$ids" = "4" ] || fail "rotation: duplicate IDs in the JSONL"

# -- 7. overlapping invocations: a busy tailer lock is a silent no-op ---------
lock="$home/.claude/prompt-log-codex-tail.lock"
mkdir "$lock"
before=$(log_count "$log")
HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER" || fail "busy tailer lock: invocation must exit 0"
[ "$(log_count "$log")" = "$before" ] || fail "busy tailer lock: rows changed"
rmdir "$lock"

# -- 8. busy append lock: the chunk is deferred, cursor NOT advanced ----------
applock="$home/.claude/prompt-log.lock"
mkdir "$applock"
date +%s > "$applock/born"
printf '%s\n' '{"payload":{"type":"user_message","message":"This is the fifth mock user prompt, written while the append lock is held by another writer, long enough to clear the threshold."},"timestamp":"2026-08-27T19:22:00.000Z","type":"event_msg"}' >> "$rollout"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=0 deferred_files=1" ] \
  || fail "append lock busy: expected the file to be deferred, got: $out"
[ "$(log_count "$log")" = "4" ] || fail "append lock busy: a row was written anyway"
rm -rf "$applock"
out=$(HOME="$home" CODEX_HOME="$TMP/backfill/codex" "$TAILER")
[ "$out" = "clio-codex-tail: delivered=1 deferred_files=0" ] \
  || fail "append lock freed: the deferred chunk was not delivered"
[ "$(log_count "$log")" = "5" ] || fail "append lock freed: expected 5 JSONL rows"

# -- 9. GH-199: discovery boundary, provenance and migration -----------------
python3 - "$TAILER" "$INSTALL_DOC" <<'PYTEST'
import json, os, subprocess, sys, tempfile
from pathlib import Path

tailer, install_doc = map(Path, sys.argv[1:])
marker = "cat > ~/.claude/hooks/clio-capture.sh << 'EOF'\n"
writer_text = install_doc.read_text().split(marker, 1)[1].split('\nEOF', 1)[0] + '\n'
SINCE = '2026-09-08T20:00:00.500000+00:00'
OLD = '2026-09-08T20:00:00.499999Z'
NEW = '2026-09-08T20:00:00.500001Z'

def meta(sid='root', source='vscode', **extra):
    return {'type':'session_meta', 'payload':{'id':sid, 'cwd':'/fixture/'+sid, 'source':source, **extra}}

def prompt(label, ts=NEW):
    return {'type':'event_msg', 'timestamp':ts, 'payload':{'type':'user_message', 'message':label+' '+('x'*120)}}

def encoded(rows):
    return ''.join(json.dumps(row)+'\n' for row in rows).encode()

with tempfile.TemporaryDirectory(prefix='clio-discovery-') as tmp:
    root = Path(tmp)
    def setup(name, sessions=True):
        home = root/name/'home'; hooks = home/'.claude/hooks'; hooks.mkdir(parents=True)
        writer = hooks/'clio-capture.sh'; writer.write_text(writer_text); writer.chmod(0o755)
        tree = root/name/'codex/sessions'
        if sessions: tree.mkdir(parents=True)
        env = {**os.environ, 'HOME':str(home), 'CODEX_HOME':str(tree.parent)}
        env.pop('CLIO_TAIL_BACKFILL', None)
        return home, tree, env

    def run(case, **extra):
        p = subprocess.run([str(tailer)], env={**case[2], **extra}, capture_output=True, text=True, timeout=30)
        assert p.returncode == 0, p.stderr
        log = case[0]/'.claude/prompt-log.jsonl'
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    def pin(case):
        state = case[0]/'.claude/prompt-log-codex-tail.state'
        state.write_text('# capture_since\t'+SINCE+'\n')
        return state

    def labels(rows):
        return [r['prompt'].split()[0] for r in rows]

    # A complete prompt exists before the first discovery of its new file.
    c = setup('first'); assert run(c) == []; pin(c)
    f = c[1]/'rollout-new.jsonl'; f.write_bytes(encoded([meta(), prompt('first')]))
    before = f.read_bytes()
    assert labels(run(c)) == ['first'], 'completed first prompt lost before discovery'
    assert labels(run(c)) == ['first'], 'restart duplicated first prompt'
    assert f.read_bytes() == before, 'source was modified'

    # Initial history remains excluded; polling can initialize without a tree.
    c = setup('absent', sessions=False); assert run(c) == []
    assert (c[0]/'.claude/prompt-log-codex-tail.state').read_text().startswith('# capture_since\t')
    pin(c); c[1].mkdir(parents=True)
    f = c[1]/'rollout-late.jsonl'; f.write_bytes(encoded([meta(),prompt('history',OLD),prompt('late')]))
    assert labels(run(c)) == ['late']
    original = f.read_bytes(); replacement = f.with_suffix('.new'); replacement.write_bytes(original); replacement.replace(f)
    assert labels(run(c)) == ['late'], 'rotation imported skipped history'
    f.write_bytes(b''); assert labels(run(c)) == ['late']
    f.write_bytes(original); assert labels(run(c)) == ['late'], 'truncation imported skipped history'

    # Full-precision, inclusive comparison and validation, with distinct IDs.
    c = setup('times'); pin(c)
    for sid,ts in [('before',OLD),('equal',SINCE),('after',NEW),('offset','2026-09-08T13:00:00.500000-07:00'),('invalid','2026-99-99T20:00:00Z'),('naive','2026-09-08T20:00:01'),('missing','')]:
        (c[1]/('rollout-'+sid+'.jsonl')).write_bytes(encoded([meta(sid),prompt(sid,ts)]))
    assert sorted(labels(run(c))) == ['after','equal','offset']

    # Completing an old partial does not bypass eligibility; a new one survives.
    c = setup('partials'); pin(c)
    for sid,ts in [('old',OLD),('new',NEW)]:
        (c[1]/('rollout-'+sid+'.jsonl')).write_bytes(encoded([meta(sid),prompt(sid,ts)]).rstrip(b'\n'))
    assert run(c) == []
    for f in c[1].glob('*.jsonl'):
        with f.open('ab') as h: h.write(b'\n')
    assert labels(run(c)) == ['new'], 'partial completion bypassed cutoff or was lost'

    # Empty first sighting must retain the cutoff when its first data arrives.
    c = setup('empty'); pin(c); f = c[1]/'rollout-empty.jsonl'; f.touch(); assert run(c) == []
    f.write_bytes(encoded([meta(),prompt('history',OLD),prompt('eligible')]))
    assert labels(run(c)) == ['eligible']

    # The FIRST metadata controls child identity even after parent context appears.
    c = setup('provenance'); pin(c)
    f = c[1]/'rollout-child.jsonl'
    child = meta('child', {'subagent':{'thread_spawn':{'parent_thread_id':'parent'}}})
    f.write_bytes(encoded([child,prompt('inherited'),meta('parent'),prompt('copied')]))
    for sid, m in [('string',meta('string','subagent')),('parent',meta('parent-id',parent_thread_id='parent'))]:
        (c[1]/('rollout-'+sid+'.jsonl')).write_bytes(encoded([m,meta('copied-'+sid),prompt('copied-'+sid)]))
    r = c[1]/'rollout-root.jsonl'; r.write_bytes(encoded([meta('genuine'),prompt('root')]))
    assert labels(run(c)) == ['root'], 'child context leaked or all roots rejected'
    with f.open('ab') as h: h.write(encoded([prompt('child-later','2026-09-08T20:01:00Z')]))
    with r.open('ab') as h: h.write(encoded([meta('resumed','cli'),prompt('resume','2026-09-08T20:01:00Z')]))
    rows = run(c)
    assert labels(rows) == ['root','resume'] and [v['session_id'] for v in rows] == ['genuine','resumed']
    assert [v['repo'] for v in rows] == ['genuine','resumed']
    assert labels(run(c,CLIO_TAIL_BACKFILL='1')) == ['root','resume']

    # New root parsing defers until complete first metadata, never cached guesses.
    c = setup('metadata'); pin(c); f = c[1]/'rollout-meta.jsonl'; data=encoded([meta()]); f.write_bytes(data[:20]); assert run(c)==[]
    with f.open('ab') as h: h.write(data[20:]+encoded([prompt('complete')]))
    assert labels(run(c)) == ['complete']

    # A legacy pending chunk retries unchanged; reset never imports skipped A.
    c = setup('legacy'); f=c[1]/'rollout-legacy.jsonl'
    prefix=encoded([meta(),prompt('A','2026-09-08T18:00:00Z')]); whole=prefix+encoded([prompt('B','2026-09-08T19:00:00Z')]); f.write_bytes(whole)
    state=c[0]/'.claude/prompt-log-codex-tail.state'
    state.write_text(f'{f}\t{f.stat().st_ino}\t{len(prefix)}\troot\t/fixture/root\n')
    real_writer=c[0]/'.claude/hooks/clio-capture.sh'; saved=real_writer.read_text(); real_writer.write_text('#!/bin/bash\nexit 3\n')
    assert run(c)==[]; assert '\t'+str(len(prefix))+'\t' in state.read_text()
    real_writer.write_text(saved)
    assert labels(run(c))==['B'], 'legacy pending row was discarded'
    replacement=f.with_suffix('.new'); replacement.write_bytes(whole); replacement.replace(f)
    assert labels(run(c))==['B'], 'legacy reset imported skipped A'
    f.write_bytes(b''); assert labels(run(c))==['B']; f.write_bytes(whole)
    assert labels(run(c))==['B'], 'legacy truncation imported skipped A'

    # Explicit backfill still imports root history; it never imports child copies.
    c=setup('backfill-child'); pin(c)
    (c[1]/'rollout-root.jsonl').write_bytes(encoded([meta(),prompt('old-root',OLD)]))
    (c[1]/'rollout-child.jsonl').write_bytes(encoded([child,meta('parent'),prompt('old-child',OLD)]))
    assert labels(run(c,CLIO_TAIL_BACKFILL='1'))==['old-root']

print('PASS: GH-199 first discovery, history/rotation, precision, partials, child/root resume, legacy retry, backfill')
PYTEST

echo "PASS: codex tailer"

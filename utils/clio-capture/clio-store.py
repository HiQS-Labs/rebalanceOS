#!/usr/bin/env python3
"""CLIO's local history store. Stdlib only; no network or background process."""
import argparse
import contextlib
import fcntl
import hashlib
import html
import json
import os
from pathlib import Path
import plistlib
import re
import sqlite3
import sys
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import uuid

APP_ID = 0x434C494F
VERSION = 1
FIELDS = ('timestamp', 'repo', 'branch', 'machine', 'agent', 'session_id',
          'prompt', 'checkout', 'repo_slug', 'source_event_id')
RESERVED = set(FIELDS) | {'record_id', 'legacy_id', 'origin_id', 'origin_kind',
                          'references', 'extras', 'clio_version'}
MAX_FLEET_BYTES = 64 * 1024 * 1024
MAX_ARCHIVES = 128
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
FLEET_WAIT_SECONDS = 7200
CONFIG = Path(os.environ.get('CLIO_CONFIG', str(Path.home() / '.claude/clio-storage.json')))


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def instant(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timestamp must include a timezone')
    return parsed.astimezone(timezone.utc)


def utc(value=None):
    value = value or datetime.now(timezone.utc)
    return value.isoformat(timespec='microseconds').replace('+00:00', 'Z')


def atomic(path, data, exclusive=False):
    """One-file publication; never expose an incomplete replacement."""
    path = Path(path).expanduser().absolute()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def diagnostic(message):
    # Callers pass content-free descriptions, never input or SQL parameter values.
    path = Path.home() / '.claude/prompt-log-errors.log'
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a') as stream:
        stream.write(utc() + ' clio-store: ' + message + '\n')


def config():
    if not CONFIG.exists():
        return {}
    value = json.loads(CONFIG.read_text())
    if not isinstance(value, dict) or not value.get('db') or not value.get('owner'):
        raise ValueError('invalid storage configuration')
    return value


def database(path, writable=False):
    path = Path(path).expanduser().absolute()
    # Existing-file rw permits WAL housekeeping across SQLite runtimes.
    # query_only below protects event data; rw never creates a missing DB.
    mode = 'rw'
    conn = sqlite3.connect('file:' + quote(str(path), safe='/') + '?mode=' + mode,
                           uri=True, timeout=0.5)
    conn.row_factory = sqlite3.Row
    try:
        if not writable:
            conn.execute('PRAGMA query_only=ON')
        if conn.execute('PRAGMA application_id').fetchone()[0] != APP_ID:
            raise ValueError('not a CLIO database')
        if conn.execute('PRAGMA user_version').fetchone()[0] != VERSION:
            raise ValueError('unsupported CLIO schema version')
        return conn
    except Exception:
        conn.close()
        raise


def initialize(path):
    path = Path(path).expanduser().absolute()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        with contextlib.closing(database(path)) as conn:
            return conn.execute('SELECT owner FROM metadata').fetchone()[0]
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        owner = str(uuid.uuid4())
        with contextlib.closing(sqlite3.connect(path, timeout=0.5)) as conn:
            conn.executescript('''
                PRAGMA journal_mode=WAL;
                BEGIN IMMEDIATE;
                CREATE TABLE metadata(owner TEXT NOT NULL);
                CREATE TABLE events(
                    record_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL,
                    repo TEXT, machine TEXT, agent TEXT, session_id TEXT,
                    repo_slug TEXT, origin_id TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE INDEX event_time ON events(timestamp,record_id);
                CREATE INDEX event_repo ON events(repo,timestamp,record_id);
                CREATE INDEX event_machine ON events(machine,timestamp,record_id);
                CREATE INDEX event_agent ON events(agent,timestamp,record_id);
                CREATE INDEX event_session ON events(session_id,timestamp,record_id);
                CREATE INDEX event_slug ON events(repo_slug,timestamp,record_id);
                CREATE INDEX event_origin ON events(origin_id,timestamp,record_id);
                CREATE TABLE device_imports(
                    owner TEXT NOT NULL, digest TEXT NOT NULL, generated_at TEXT NOT NULL,
                    source TEXT NOT NULL, rows INTEGER NOT NULL, received_at TEXT NOT NULL,
                    PRIMARY KEY(owner,digest));
                CREATE TABLE sources(
                    source TEXT PRIMARY KEY, path TEXT NOT NULL, inode TEXT NOT NULL,
                    origin_id TEXT NOT NULL, offset INTEGER NOT NULL DEFAULT 0,
                    lines INTEGER NOT NULL DEFAULT 0, prefix_hash TEXT NOT NULL);
                CREATE TABLE source_lines(
                    source TEXT NOT NULL, line INTEGER NOT NULL, raw_hash TEXT NOT NULL,
                    record_id TEXT, reason TEXT, quarantine BLOB,
                    PRIMARY KEY(source,line));
            ''')
            conn.execute('INSERT INTO metadata VALUES (?)', (owner,))
            conn.execute('PRAGMA application_id=' + str(APP_ID))
            conn.execute('PRAGMA user_version=' + str(VERSION))
            conn.commit()
    except BaseException:
        # Only this invocation created the exclusive target; allow a clean retry.
        path.unlink()
        raise
    return owner


def normalize(row, owner=None, kind='legacy-adopted'):
    if not isinstance(row, dict):
        raise ValueError('record must be an object')
    versioned = row.get('clio_version') == VERSION
    if not versioned and {'record_id', 'legacy_id', 'origin_id', 'origin_kind'}.intersection(row):
        raise ValueError('identity fields require a versioned record')
    if 'clio_version' in row and not versioned:
        raise ValueError('unsupported record version')
    result = {}
    for field in FIELDS:
        value = row.get(field, '')
        value = '' if value is None else value
        if not isinstance(value, str):
            raise ValueError('invalid field type')
        result[field] = value
    if not result['prompt'].strip():
        raise ValueError('empty prompt')
    result['timestamp'] = utc(instant(result['timestamp']))
    result['origin_id'] = row.get('origin_id') if versioned else owner
    result['origin_kind'] = row.get('origin_kind') if versioned else kind
    if not isinstance(result['origin_id'], str) or not result['origin_id']:
        raise ValueError('missing origin identity')
    if result['origin_kind'] not in ('captured', 'legacy-adopted'):
        raise ValueError('invalid origin kind')
    extras = row.get('extras', {})
    if not isinstance(extras, dict) or RESERVED.intersection(extras):
        raise ValueError('extras shadow reserved fields')
    extras = dict(extras)
    for key, value in row.items():
        if key not in RESERVED:
            if key in extras and extras[key] != value:
                raise ValueError('conflicting extra metadata')
            extras[key] = value
    references = row.get('references', [])
    if not isinstance(references, list):
        raise ValueError('references must be a list')
    for ref in references:
        if not isinstance(ref, dict) or ref.get('relation') not in ('mentioned', 'task-context'):
            raise ValueError('invalid reference relation')
        if ref.get('type') in ('issue', 'pr'):
            segment = 'issues' if ref['type'] == 'issue' else 'pull'
            if not re.fullmatch(r'https://github\.com/[\w.-]+/[\w.-]+/' + segment + r'/[1-9][0-9]*', ref.get('url', '')):
                raise ValueError('reference requires a qualified GitHub URL')
        elif ref.get('type') == 'ledger':
            if not re.fullmatch(r'[\w.-]+/[\w.-]+', ref.get('repo_slug', '')) or not isinstance(ref.get('row_id'), str) or not ref['row_id']:
                raise ValueError('ledger reference requires repository and row identity')
        else:
            raise ValueError('invalid reference type')
    result.update(extras=extras, references=references, clio_version=VERSION)
    record_id = 'clio1-' + digest(encode(identity_payload(result)).encode())
    if versioned and row.get('record_id') != record_id:
        raise ValueError('record identity does not match payload')
    result['record_id'] = record_id
    result['legacy_id'] = result['session_id'] + ':' + result['timestamp'].replace('.000000Z', 'Z')
    return result


def identity_payload(row):
    # Tailer event identity is immutable; checkout/device labels are observations
    # made at delivery time. Retain the first committed observation on replay.
    payload = dict(row)
    if (payload.get('extras', {}).get('ide') == 't3-code'
            and payload.get('source_event_id', '').startswith('t3:')):
        return {key: payload[key] for key in ('origin_id', 'source_event_id', 'clio_version')}
    if payload.get('source_event_id'):
        for key in ('repo', 'branch', 'machine', 'checkout', 'repo_slug'):
            payload.pop(key, None)
    return payload


def insert(conn, row, replay=False, restore_labels=False):
    """The only event writer, shared by import, capture and recovery."""
    payload = encode(row)
    prior = conn.execute('SELECT payload FROM events WHERE record_id=?', (row['record_id'],)).fetchone()
    if prior:
        if prior[0] != payload and not (replay and row.get('source_event_id')
                and identity_payload(json.loads(prior[0])) == identity_payload(row)):
            raise ValueError('identity payload conflict')
        if restore_labels and prior[0] != payload:
            # Only trusted own-origin reconciliation calls this after archiving
            # all previous observations. Immutable identity must agree above.
            if not replay or not row.get('source_event_id'):
                raise ValueError('label restoration requires a replay identity')
            conn.execute('UPDATE events SET repo=?,machine=?,repo_slug=?,payload=? WHERE record_id=?',
                         (row['repo'], row['machine'], row['repo_slug'], payload, row['record_id']))
        return False
    conn.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)',
                 tuple(row[k] for k in ('record_id', 'timestamp', 'repo', 'machine',
                       'agent', 'session_id', 'repo_slug', 'origin_id')) + (payload,))
    return True


def pending_dir(path):
    path = Path(path).expanduser().absolute()
    return path.with_name(path.name + '.pending')


def capture(path, owner, value):
    row = normalize(value, owner, 'captured')
    pending = pending_dir(path) / (row['record_id'] + '.json')
    atomic(pending, encode(row).encode())
    try:
        with contextlib.closing(database(path, True)) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            insert(conn, row, replay=True)
        pending.unlink(missing_ok=True)
        return {'record_id': row['record_id'], 'state': 'committed'}
    except (sqlite3.Error, OSError, ValueError):
        diagnostic('capture queued durably; run drain or the scheduled SQLite exporter')
        return {'record_id': row['record_id'], 'state': 'pending'}


@contextlib.contextmanager
def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a') as stream:
        deadline = time.monotonic() + 0.5
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError('maintenance lock busy')
                time.sleep(0.01)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def drain(path, limit=100):
    folder = pending_dir(path)
    if not folder.exists():
        return {'drained': 0, 'pending': 0}
    count = 0
    with lock(folder / '.drain.lock'):
        for source in sorted(folder.glob('clio1-*.json'))[:limit]:
            row = normalize(json.loads(source.read_text()))
            with contextlib.closing(database(path, True)) as conn, conn:
                conn.execute('BEGIN IMMEDIATE')
                insert(conn, row, replay=True)
            source.unlink(missing_ok=True)
            count += 1
    return {'drained': count, 'pending': len(list(folder.glob('clio1-*.json')))}


def check_deadline(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError('cutover budget exceeded; retain legacy mode and retry offline')


def import_jsonl(path, source_path, source_id=None, max_records=1000, deadline=None):
    source_path = Path(source_path).expanduser().resolve()
    source_id = source_id or str(source_path)
    with source_path.open('rb') as stream, contextlib.closing(database(path, True)) as conn:
        stat = os.fstat(stream.fileno())
        inode = str(stat.st_dev) + ':' + str(stat.st_ino)
        owner = conn.execute('SELECT owner FROM metadata').fetchone()[0]
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            prior = conn.execute('SELECT * FROM sources WHERE source=?', (source_id,)).fetchone()
            if prior and (prior['path'] != str(source_path) or prior['inode'] != inode):
                raise ValueError('source replaced; use an explicit new --source identity')
            offset, number = (prior['offset'], prior['lines']) if prior else (0, 0)
            prefix = hashlib.sha256()
            remaining = offset
            while remaining:
                check_deadline(deadline)
                block = stream.read(min(remaining, 1024 * 1024))
                if not block:
                    raise ValueError('source shrank')
                prefix.update(block)
                remaining -= len(block)
            if prior and prefix.hexdigest() != prior['prefix_hash']:
                raise ValueError('source prefix changed')
            if not prior:
                conn.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?)',
                             (source_id, str(source_path), inode, owner, 0, 0, prefix.hexdigest()))
            else:
                owner = prior['origin_id']
            added = duplicates = rejected = 0
            for _ in range(max_records):
                check_deadline(deadline)
                raw = stream.readline()
                if not raw or not raw.endswith(b'\n'):
                    break
                number += 1
                row, reason = None, None
                try:
                    row = normalize(json.loads(raw), owner)
                except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
                    reason = 'invalid JSON or record fields'
                if row:
                    if insert(conn, row):
                        added += 1
                    else:
                        duplicates += 1
                else:
                    rejected += 1
                conn.execute('INSERT INTO source_lines VALUES (?,?,?,?,?,?)',
                             (source_id, number, digest(raw), row['record_id'] if row else None,
                              reason, raw if reason else None))
                prefix.update(raw)
                offset += len(raw)
            conn.execute('UPDATE sources SET offset=?,lines=?,prefix_hash=? WHERE source=?',
                         (offset, number, prefix.hexdigest(), source_id))
        return {'source': source_id, 'added': added, 'duplicates': duplicates,
                'quarantined': rejected, 'lines': number, 'offset': offset,
                'remaining_bytes': os.fstat(stream.fileno()).st_size - offset}


def verify_import(path, source_id, deadline=None):
    with contextlib.closing(database(path)) as conn:
        conn.execute('BEGIN')
        source = conn.execute('SELECT * FROM sources WHERE source=?', (source_id,)).fetchone()
        if source is None:
            source_id = str(Path(source_id).expanduser().resolve())
            source = conn.execute('SELECT * FROM sources WHERE source=?', (source_id,)).fetchone()
        if not source or not source['lines']:
            raise ValueError('no nonempty imported source to verify')
        with Path(source['path']).open('rb') as stream:
            stat = os.fstat(stream.fileno())
            if source['inode'] != str(stat.st_dev) + ':' + str(stat.st_ino):
                raise ValueError('source replaced')
            prefix = hashlib.sha256()
            count = quarantined = 0
            for evidence in conn.execute('SELECT * FROM source_lines WHERE source=? ORDER BY line', (source_id,)):
                check_deadline(deadline)
                raw = stream.readline()
                count += 1
                if not raw.endswith(b'\n') or digest(raw) != evidence['raw_hash']:
                    raise ValueError('source occurrence mismatch')
                prefix.update(raw)
                if evidence['record_id']:
                    expected = normalize(json.loads(raw), source['origin_id'])
                    stored = conn.execute('SELECT payload FROM events WHERE record_id=?',
                                          (evidence['record_id'],)).fetchone()
                    if not stored or encode(expected) != stored[0]:
                        raise ValueError('missing or corrupt imported event')
                else:
                    if raw != evidence['quarantine']:
                        raise ValueError('quarantine mismatch')
                    quarantined += 1
            if count != source['lines'] or prefix.hexdigest() != source['prefix_hash'] or stream.tell() != source['offset']:
                raise ValueError('source accounting mismatch')
            pending = stat.st_size - stream.tell()
            if pending:
                raise ValueError('source still has unaccounted bytes')
        return {'verified': True, 'source': source_id, 'occurrences': count,
                'quarantined': quarantined, 'prefix_hash': prefix.hexdigest()}


def activate(path, source_path, fresh=False, capture_only=False):
    """Explicit pilot operation. Does not install hooks or schedule jobs."""
    if CONFIG.exists():
        raise ValueError('already activated; preserve configuration for rollback')
    writer = Path.home() / '.claude/hooks/clio-capture.sh'
    helper = writer.with_name('clio-store.py')
    if not writer.exists() or 'CLIO_SQLITE_V1' not in writer.read_text() or not helper.exists():
        raise ValueError('install the SQLite-aware shared writer and helper first')
    with contextlib.closing(database(path)) as conn:
        owner = conn.execute('SELECT owner FROM metadata').fetchone()[0]
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('database integrity check failed')
    append_lock = Path.home() / '.claude/prompt-log.lock'
    append_lock.mkdir()  # Refuse busy/stale locks; never remove another writer's lock.
    try:
        deadline = time.monotonic() + 5
        (append_lock / 'born').write_text(str(int(time.time())))
        source_path = Path(source_path).expanduser().resolve()
        if fresh:
            if source_path.exists():
                raise ValueError('fresh activation requires no legacy source')
        else:
            result = import_jsonl(path, source_path, max_records=100, deadline=deadline)
            if result['remaining_bytes']:
                raise ValueError('backlog remains; run online import before activation')
            verify_import(path, str(source_path), deadline=deadline)
            backup = source_path.with_name(source_path.name + '.pre-sqlite-' + str(time.time_ns()))
            with source_path.open('rb') as src, backup.open('xb') as dst:
                while block := src.read(1024 * 1024):
                    check_deadline(deadline)
                    dst.write(block)
                dst.flush()
                os.fsync(dst.fileno())
        check_deadline(deadline)
        cfg = {'db': str(Path(path).expanduser().absolute()), 'owner': owner}
        if capture_only:
            cfg['capture_only'] = True
        atomic(CONFIG, (encode(cfg) + '\n').encode())
    finally:
        (append_lock / 'born').unlink(missing_ok=True)
        append_lock.rmdir()
    return {'activated': True, 'config': str(CONFIG), 'owner': owner}


def query(path, args):
    conditions, values = [], []
    for key, column in [('repo', 'repo'), ('device', 'machine'), ('agent', 'agent'),
                        ('session', 'session_id'), ('record_id', 'record_id'),
                        ('repo_slug', 'repo_slug'), ('origin', 'origin_id')]:
        value = getattr(args, key, None)
        if value is not None:
            conditions.append(column + '=?')
            values.append(value)
    for key, operation in [('since', '>='), ('until', '<=')]:
        value = getattr(args, key, None)
        if value:
            conditions.append('timestamp' + operation + '?')
            values.append(utc(instant(value)))
    if args.text is not None:
        conditions.append("instr(json_extract(payload,'$.prompt'),?)>0")
        values.append(args.text)
    if args.reference:
        conditions.append("EXISTS (SELECT 1 FROM json_each(events.payload,'$.references') r WHERE json_extract(r.value,'$.url')=? OR (json_extract(r.value,'$.repo_slug')||':'||json_extract(r.value,'$.row_id'))=?)")
        values.extend([args.reference, args.reference])
    sql = 'SELECT payload FROM events' + (' WHERE ' + ' AND '.join(conditions) if conditions else '')
    sql += ' ORDER BY timestamp DESC,record_id DESC LIMIT ? OFFSET ?'
    values.extend([args.limit, args.offset])
    with contextlib.closing(database(path)) as conn:
        rows = [json.loads(row[0]) for row in conn.execute(sql, values)]
        plan = [list(row) for row in conn.execute('EXPLAIN QUERY PLAN ' + sql, values)] if args.explain else None
    result = {'records': rows, 'limit': args.limit, 'offset': args.offset,
              'pending': len(list(pending_dir(path).glob('clio1-*.json')))}
    cfg = config()
    if cfg.get('fleet') and Path(cfg['db']).resolve() == Path(path).expanduser().resolve():
        result['fleet'] = cfg['fleet'].get('last_result', {'configured': True, 'state': 'not_reconciled'})
        result['note_status'] = cfg.get('view', {}).get('last_note_status')
    if plan is not None:
        result['query_plan'] = plan
    return result


def active_config(conn, path):
    cfg = config()
    if (not cfg or Path(cfg['db']).expanduser().resolve() != Path(path).expanduser().resolve()
            or cfg['owner'] != conn.execute('SELECT owner FROM metadata').fetchone()[0]):
        raise ValueError('operation requires the activated database and owner')
    return cfg


def existing_destination(explicit=None):
    """Read the installed job, never evaluate shell text or rewrite its schedule."""
    plist = Path.home() / 'Library/LaunchAgents/com.claude.prompt-log-to-md.plist'
    detected = None
    if plist.exists():
        job = plistlib.loads(plist.read_bytes())
        args = job.get('ProgramArguments', [])
        if args and args[0] in ('/bin/bash', '/bin/sh'):
            args = args[1:]
        if (not 1 <= len(args) <= 2 or not isinstance(args[0], str)
                or Path(args[0]).name != 'prompt-log-to-md.sh'
                or len(args) == 2 and (not isinstance(args[1], str) or args[1].startswith('-'))):
            raise ValueError('unsupported exporter job arguments; inspect the existing job before migration')
        detected = Path(args[1]).expanduser() if len(args) == 2 else Path.home() / '.claude/prompt-log.md'
        if not detected.is_absolute():
            raise ValueError('exporter job destination must be absolute')
    target = Path(explicit).expanduser().resolve() if explicit else detected
    target = (target or Path.home() / '.claude/prompt-log.md').resolve()
    if detected and target != detected.resolve():
        raise ValueError('explicit destination differs from the existing exporter job')
    return target


def legacy_coverage(conn, raw):
    """Match the shipped legacy renderer, refusing unaccounted body edits/history."""
    text = raw.decode('utf-8')
    markers = list(re.finditer(r'(?m)^[ \t]*<!-- CLIO:ENTRIES -->[ \t]*\r?\n', text))
    if len(markers) != 1:
        raise ValueError('expected one standalone historical marker; preserve and inspect the note')
    header, body = text[:markers[0].end()], text[markers[0].end():]
    entries = list(re.finditer(r'(?m)^<!-- clio:id:([^\r\n]+) -->\r?\n', body))
    if (body[:entries[0].start()] if entries else body).strip():
        raise ValueError('unrecognized content below the historical marker')
    candidates = {}
    for item in conn.execute('SELECT payload FROM events'):
        row = json.loads(item[0])
        candidates.setdefault(row['legacy_id'], []).append(row)
    for i, entry in enumerate(entries):
        block = body[entry.end():entries[i + 1].start() if i + 1 < len(entries) else len(body)]
        lines = block.split('\n')
        shown = lines[1].strip() if len(lines) > 1 else ''
        try:
            instant(shown)  # UTC/ISO fallback from the legacy exporter.
        except ValueError:
            # Historical %Z is a display label, not the current host's zone or
            # event identity. Validate its shape without interpreting ambiguous PDT/etc.
            local = re.fullmatch(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ([A-Za-z0-9_+:/-]+)', shown)
            try:
                if not local:
                    raise ValueError()
                datetime.strptime(local[1], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError('unrecognized historical timestamp display; preserve and reconcile the note') from None
        matched = False
        for row in candidates.get(entry[1], []):
            context = row['machine'] + (' · ' + row['branch'] if row['branch'] else '')
            context += ' · ' + (row['agent'] or 'claude-code')
            prompt = '> "' + row['prompt'].replace('\n', '\n> ') + '"'
            heading = row['repo'].translate(str.maketrans('abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
            headings = {'## ' + heading} if row['repo'] else {'## ', '## UNKNOWN'}
            if (len(lines) >= 5 and lines[0] in headings
                    and lines[2] == context and lines[3] == ''
                    and '\n'.join(lines[4:]).rstrip('\n') == prompt):
                matched = True
                break
        if not matched:
            raise ValueError('historical entry absent or different in SQLite; import every device source first')
    return header, len(entries)


def checked_view(conn, path, target):
    cfg = active_config(conn, path)
    view = cfg.get('view')
    if not view or Path(view['path']) != target:
        raise ValueError('run migrate-view for the existing destination before exporting')
    if digest(Path(view['backup']).read_bytes()) != view['backup_sha256']:
        raise ValueError('historical backup changed; publication refused')
    fleet = cfg.get('fleet', {})
    repair = fleet.get('repair_generated_note', False)
    if repair and (digest(view['header'].encode()) != fleet.get('header_sha256')
                   or view.get('coverage') != fleet.get('coverage')):
        raise ValueError('fleet header or coverage changed; publication refused')
    if not target.exists():
        if not repair:
            raise ValueError('registered note is missing; publication refused')
        view.pop('waiting_since', None)
        return cfg, None
    if repair and target.stat().st_size > MAX_FLEET_BYTES:
        raise ValueError('note exceeds fleet repair size bound; preserved in place')
    original = target.read_bytes()
    current = digest(original)
    if current in view['accepted_hashes']:
        view.pop('waiting_since', None)
    if current not in view['accepted_hashes']:
        if not repair:
            raise ValueError('note changed outside this publisher; preserve and reconcile edits before exporting')
        if not original.startswith(view['header'].encode()):
            raise ValueError('personal header changed; publication refused')
        text = original.decode('utf-8')
        ids = re.findall(r'^<!-- clio:record:(clio1-[0-9a-f]{64}) -->$', text, re.M)
        known = {item['record_id']: item for item in
                 (json.loads(r[0]) for r in conn.execute('SELECT payload FROM events'))}
        unknown = set(ids).difference(known)
        if unknown:
            now = instant(utc())
            waiting = instant(view.setdefault('waiting_since', utc(now)))
            # Future timestamps expire, rather than extending a clock rollback.
            if 0 <= (now - waiting).total_seconds() < FLEET_WAIT_SECONDS:
                atomic(CONFIG, (encode(cfg) + '\n').encode())
                raise ValueError('waiting_for_history; note preserved until bounded expiry')
        else:
            view.pop('waiting_since', None)
        peer = not unknown and peer_render_coverage(known, original, view['header']) is not None
        archive = None if peer else preserve_recovery(path, original, 'conflict', '.md')
        view['last_note_repair'] = {'at': utc(), 'state': 'peer_generated' if peer else 'archived_conflict',
                                    'digest': current, 'archive': str(archive) if archive else None}
        view.pop('waiting_since', None)
    return cfg, current


def peer_render_coverage(known, original, header):
    """Return the coverage banner under which this renderer reproduces the note exactly, else None."""
    text = original.decode('utf-8')
    ids = re.findall(r'^<!-- clio:record:(clio1-[0-9a-f]{64}) -->$', text, re.M)
    match = re.search(r'^UTC cutoff: (.+)$', text, re.M)
    if set(ids).difference(known) or len(ids) != len(set(ids)) or not match:
        return None
    try:
        cutoff = utc(instant(match[1]))
        if cutoff == match[1] and instant(cutoff) <= instant(utc()) + timedelta(minutes=5):
            for coverage in ('verified', 'archived-not-reconciled'):
                if render_markdown([known[i] for i in ids], cutoff, header, coverage)[0] == original:
                    return coverage
    except (ValueError, OverflowError):
        pass
    return None


def migrate_view(path, markdown=None, publishers_paused=False, archive_unreconciled_note=False, join_fleet_note=False):
    if join_fleet_note and (publishers_paused or archive_unreconciled_note):
        raise ValueError('--join-fleet-note registers a peer-rendered note; it excludes the single-publisher migration flags')
    if not publishers_paused and not join_fleet_note:
        raise ValueError('pause all shared-note publishers and designate one owner before --publishers-paused')
    target = existing_destination(markdown)
    with lock(str(Path(path).expanduser().absolute()) + '.project.lock'):
        with contextlib.closing(database(path)) as conn:
            conn.execute('BEGIN')
            cfg = active_config(conn, path)
            if cfg.get('view'):
                checked_view(conn, path, target)
                return {'registered': True, 'already_registered': True, 'markdown': str(target)}
            safe_output(conn, path, target, historical=True)
            original = target.read_bytes()
            if join_fleet_note:
                # Another device already renders this note from the shared fleet history:
                # register it only when this replica reproduces it byte for byte.
                if not cfg.get('fleet'):
                    raise ValueError('configure and reconcile the fleet before joining its note')
                text = original.decode('utf-8')
                markers = list(re.finditer(r'(?m)^[ \t]*<!-- CLIO:ENTRIES -->[ \t]*\r?\n', text))
                if len(markers) != 1:
                    raise ValueError('expected one standalone historical marker; preserve and inspect the note')
                header, count = text[:markers[0].end()], None
                known = {item['record_id']: item for item in
                         (json.loads(r[0]) for r in conn.execute('SELECT payload FROM events'))}
                ids = re.findall(r'^<!-- clio:record:(clio1-[0-9a-f]{64}) -->$', text, re.M)
                if set(ids).difference(known):
                    raise ValueError('note holds records not yet in this replica; reconcile after the next delivery and retry')
                coverage = peer_render_coverage(known, original, header)
                if coverage is None:
                    raise ValueError('note is not an exact fleet rendering; preserve and inspect it')
            elif archive_unreconciled_note:
                # Explicit operator acceptance: preserve all original bytes, but do
                # not claim archived entries were reconciled into SQLite.
                text = original.decode('utf-8')
                marker = re.search(r'(?m)^[ \t]*<!-- CLIO:ENTRIES -->[ \t]*\r?\n', text)
                if not marker:
                    raise ValueError('historical header marker missing; preserve and inspect the note')
                header, count = text[:marker.end()], None
            else:
                header, count = legacy_coverage(conn, original)
            if not join_fleet_note:
                coverage = 'archived-not-reconciled' if archive_unreconciled_note else 'verified'
            folder = Path(path).expanduser().resolve().parent / (Path(path).name + '.view-backups')
            folder.mkdir(mode=0o700, parents=True, exist_ok=True)
            backup_path = folder / (str(uuid.uuid4()) + '.md')
            fd = os.open(backup_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'wb') as backup_file:
                backup_file.write(original)
                backup_file.flush()
                os.fsync(backup_file.fileno())
            directory = os.open(folder, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            fingerprint = digest(original)
            if digest(backup_path.read_bytes()) != fingerprint or digest(target.read_bytes()) != fingerprint:
                raise ValueError('backup or note changed during migration; no view registered')
            cfg['view'] = {'path': str(target), 'header': header, 'backup': str(backup_path),
                           'backup_sha256': fingerprint, 'accepted_hashes': [fingerprint],
                           'legacy_entries': count, 'coverage': coverage}
            atomic(CONFIG, (encode(cfg) + '\n').encode())
    return {'registered': True, 'markdown': str(target), 'backup': str(backup_path), 'covered_entries': count, 'coverage': coverage}


def safe_output(conn, path, output, historical=False):
    target = Path(output).expanduser().resolve()
    forbidden = {Path(path).expanduser().resolve(), CONFIG.resolve()}
    sources = {Path(row[0]).resolve() for row in conn.execute('SELECT path FROM sources')}
    sources.add((Path.home() / '.claude/prompt-log.jsonl').resolve())
    forbidden.update(sources)
    forbidden.update(Path(row[0]).resolve() for row in conn.execute('SELECT source FROM device_imports')
                     if not row[0].startswith('git-blob:'))
    if any(target.parent == source.parent and target.name.startswith(source.name + '.pre-sqlite-')
           for source in sources):
        raise ValueError('output would overwrite a preserved activation source backup')
    base = Path(path).expanduser().resolve()
    cfg = config()
    view = cfg.get('view', {})
    if view.get('backup'):
        forbidden.add(Path(view['backup']).resolve())
    forbidden.update(Path(str(base) + suffix) for suffix in ('-wal', '-shm', '.project.lock'))
    if target in forbidden or target == pending_dir(path).resolve() or pending_dir(path).resolve() in target.parents:
        raise ValueError('output would overwrite storage, configuration or source history')
    if not historical and target == (Path.home() / '.claude/prompt-log.md').resolve():
        raise ValueError('preserve the historical shared Markdown; choose a new output')
    if not historical and target.exists() and any(line.strip() == '<!-- CLIO:ENTRIES -->'
                               for line in target.read_text().splitlines()):
        raise ValueError('preserve the historical shared Markdown; choose a new output')
    return target


def render_markdown(rows, cutoff, header='', coverage='verified'):
    cutoff_dt = instant(cutoff)
    cutoff_text, since = utc(cutoff_dt), utc(cutoff_dt - timedelta(hours=168))
    all_rows = sorted(rows, key=lambda row: (row['timestamp'], row['record_id']))
    recent = [row for row in reversed(all_rows) if since <= row['timestamp'] <= cutoff_text]
    lines = ['# CLIO — recent 168 hours', '', 'UTC cutoff: ' + cutoff_text,
             'Window starts: ' + since, 'Records: ' + str(len(recent)),
             'Imported history remains in SQLite. This view covers imported/local records only.', '']
    if coverage == 'archived-not-reconciled':
        lines.extend(['Earlier note content is preserved in a verified backup, not fully reconciled into SQLite.', ''])
    if not recent:
        lines.extend(['No prompts in this window.', ''])
    for row in recent:
        esc = lambda value: html.escape(value or 'unknown', quote=False)
        lines.extend(['<!-- clio:record:' + row['record_id'] + ' -->',
                      '## ' + esc(row['repo']), row['timestamp'] + ' (UTC)',
                      ' · '.join(esc(row[key]) for key in ('machine', 'branch', 'agent')),
                      'Session: ' + esc(row['session_id']),
                      'Checkout: ' + esc(row['checkout']),
                      'Repository: ' + esc(row['repo_slug']),
                      'Origin: ' + esc(row['origin_id']) + ' (' + row['origin_kind'] + ')',
                      'Record: ' + row['record_id'], ''])
        lines.extend('> ' + html.escape(line, quote=False) for line in row['prompt'].split('\n'))
        if row['extras']:
            lines.extend(['', 'Metadata: ' + html.escape(encode(row['extras']), quote=False)])
        if row['references']:
            lines.extend(['', 'References: ' + html.escape(encode(row['references']), quote=False)])
        lines.append('')
    data = ('\n'.join(lines) + '\n').encode()
    return header.encode() + (b'\n' if header else b'') + data, len(recent)


def project(path, markdown=None, jsonl=None, cutoff=None, jsonl_only=False):
    if jsonl_only and (not jsonl or markdown is not None):
        raise ValueError('JSONL-only projection requires JSONL and no Markdown destination')
    cutoff_dt = instant(cutoff) if cutoff else datetime.now(timezone.utc)
    if not cutoff and config().get('fleet'):
        cutoff_dt = datetime.fromtimestamp(int(cutoff_dt.timestamp()) // 300 * 300, timezone.utc)
    cutoff_text, since = utc(cutoff_dt), utc(cutoff_dt - timedelta(hours=168))
    with lock(str(Path(path).expanduser().absolute()) + '.project.lock'):
        with contextlib.closing(database(path)) as conn:
            conn.execute('BEGIN')
            cfg = config()
            view = cfg.get('view', {})
            if markdown is None and not jsonl_only:
                markdown = view.get('path')
                if not markdown:
                    raise ValueError('run migrate-view first, or provide --markdown for an explicit preview')
            if markdown is not None and view and Path(markdown).expanduser().absolute() == Path(view['path']):
                if Path(markdown).is_symlink():
                    raise ValueError('registered note became a symlink; publication refused')
            target = Path(markdown).expanduser().resolve() if markdown is not None else None
            registered = target == Path(view['path']) if view else False
            current = None
            if target is not None:
                target = safe_output(conn, path, target, historical=registered)
            all_rows = [json.loads(row[0]) for row in conn.execute('SELECT payload FROM events ORDER BY timestamp,record_id')]
            compat = safe_output(conn, path, jsonl) if jsonl else None
            if compat is not None and compat == target:
                raise ValueError('Markdown and JSONL outputs must differ')
            if compat:
                # Preserve the legacy UTC-second spelling for existing consumers.
                compatibility = [dict(row, timestamp=row['timestamp'].replace('.000000Z', 'Z')) for row in all_rows]
                atomic(compat, ''.join(encode(row) + '\n' for row in compatibility).encode())
            if jsonl_only:
                return {'jsonl': str(compat), 'history_rows': len(all_rows),
                        'markdown': None, 'note_publication': 'paused'}
            if registered:
                cfg, current = checked_view(conn, path, target)
                view = cfg['view']
            data, recent_count = render_markdown(all_rows, cutoff_text,
                                                   view['header'] if registered else '',
                                                   view.get('coverage', 'verified'))
            if registered:
                # Record both crash outcomes before replacing the note. A retry may
                # see either file, but never treats an unexpected edit as disposable.
                observed = digest(target.read_bytes()) if target.exists() else None
                if observed != current:
                    raise ValueError('note changed during projection; publication refused')
                cfg['view']['accepted_hashes'] = list(dict.fromkeys([value for value in (current, digest(data)) if value is not None]))
                atomic(CONFIG, (encode(cfg) + '\n').encode())
            atomic(target, data)
    return {'markdown': str(target), 'rows': recent_count, 'bytes': len(data),
            'cutoff': cutoff_text, 'history_rows': len(all_rows)}


def export_device(path, output, cutoff=None, origin=None):
    cfg = config()
    if origin is None and cfg.get('fleet') and Path(cfg['db']).resolve() == Path(path).expanduser().resolve():
        status = reconcile_fleet(path)
        if any(item['owner'] == cfg['owner'] and item['state'] == 'error' for item in status['origins']):
            raise ValueError('own committed history recovery failed; export refused')
    with lock(str(Path(path).expanduser().absolute()) + '.project.lock'):
        with contextlib.closing(database(path)) as conn:
            conn.execute('BEGIN')
            owner = conn.execute('SELECT owner FROM metadata').fetchone()[0]
            if origin is not None:
                owner = valid_origin(origin)
                if not conn.execute('SELECT 1 FROM events WHERE origin_id=? LIMIT 1', (owner,)).fetchone():
                    raise ValueError('bootstrap origin has no known history')
            target = safe_output(conn, path, output)
            rows = [row[0] for row in conn.execute('SELECT payload FROM events WHERE origin_id=? ORDER BY timestamp,record_id', (owner,))]
            payload = ''.join(row + '\n' for row in rows).encode()
            manifest = {'clio_snapshot': VERSION, 'owner': owner, 'generated_at': utc(instant(cutoff)) if cutoff else utc(),
                        'rows': len(rows), 'sha256': digest(payload)}
            atomic(target, (encode(manifest) + '\n').encode() + payload)
        return manifest

def snapshot_records(raw, expected_owner=None, deadline=None):
    line, payload = raw.split(b'\n', 1)
    manifest = json.loads(line)
    if (not isinstance(manifest, dict) or manifest.get('clio_snapshot') != VERSION
            or digest(payload) != manifest.get('sha256')):
        raise ValueError('invalid snapshot version or digest')
    if expected_owner is not None and manifest.get('owner') != expected_owner:
        raise ValueError('snapshot owner does not match its inventory path')
    instant(manifest['generated_at'])
    raw_rows = payload.splitlines()
    if type(manifest.get('rows')) is not int or len(raw_rows) != manifest['rows']:
        raise ValueError('snapshot row count mismatch')
    rows = []
    for raw_row in raw_rows:
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError('fleet reconciliation budget exhausted')
        row = normalize(json.loads(raw_row))
        if row['origin_id'] != manifest.get('owner'):
            raise ValueError('snapshot contains a foreign-owned record')
        rows.append(row)
    if len({row['record_id'] for row in rows}) != len(rows):
        raise ValueError('snapshot contains duplicate record identities')
    return manifest, rows


def import_snapshot(path, raw, source, expected_owner=None, trusted_own=False, cumulative=False, deadline=None):
    manifest, rows = snapshot_records(raw, expected_owner, deadline)
    added = labels = 0
    with contextlib.closing(database(path, True)) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        local_owner = conn.execute('SELECT owner FROM metadata').fetchone()[0]
        own = manifest['owner'] == local_owner
        if own and not trusted_own:
            raise ValueError('snapshot claims this store as origin; refuse self-import')
        prior = {r[0]: r[1] for r in conn.execute('SELECT record_id,payload FROM events WHERE origin_id=?', (manifest['owner'],))}
        ids = {row['record_id'] for row in rows}
        if cumulative and not own and set(prior).difference(ids):
            raise ValueError('cumulative snapshot regressed known history')
        restored = []
        for row in rows:
            old = prior.get(row['record_id'])
            if own and old is not None and old != encode(row):
                if not row.get('source_event_id') or identity_payload(json.loads(old)) != identity_payload(row):
                    raise ValueError('identity payload conflict')
                restored.append(json.loads(old))
        if restored:
            preserve_recovery(path, (encode(restored) + '\n').encode(), 'recovery', '.json')
        for row in rows:
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError('fleet reconciliation budget exhausted')
            added += insert(conn, row, replay=own, restore_labels=own)
        labels = len(restored)
        conn.execute('INSERT OR IGNORE INTO device_imports VALUES (?,?,?,?,?,?)',
                     (manifest['owner'], manifest['sha256'], manifest['generated_at'],
                      source, len(rows), utc()))
    return {'added': added, 'rows': len(rows), 'owner': manifest['owner'],
            'generated_at': manifest['generated_at'], 'label_restored': labels,
            'unsent': len(set(prior).difference(ids)) if own else 0}


def import_device(path, source):
    return import_snapshot(path, Path(source).read_bytes(), str(Path(source).resolve()))


def recovery_metrics(path):
    folder = Path(path).expanduser().absolute().with_name(Path(path).name + '.view-backups')
    archives = list(folder.glob('conflict-*')) + list(folder.glob('recovery-*'))
    return {'count': len(archives), 'bytes': sum(p.stat().st_size for p in archives)}


def preserve_recovery(path, data, kind, suffix):
    folder = Path(path).expanduser().absolute().with_name(Path(path).name + '.view-backups')
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    fingerprint = digest(data)
    target = folder / (kind + '-' + fingerprint + suffix)
    if target.exists() or target.is_symlink():
        if target.is_symlink() or digest(target.read_bytes()) != fingerprint:
            raise ValueError('recovery archive changed; preserved content not replaceable')
        return target
    metrics = recovery_metrics(path)
    if (len(data) > MAX_FLEET_BYTES or metrics['count'] >= MAX_ARCHIVES
            or metrics['bytes'] + len(data) > MAX_ARCHIVE_BYTES):
        raise ValueError('archive_budget_exhausted; current content preserved')
    try:
        atomic(target, data, exclusive=True)
    except FileExistsError:
        pass
    if target.is_symlink() or digest(target.read_bytes()) != fingerprint:
        raise ValueError('recovery archive verification failed')
    return target


def valid_origin(value):
    if str(uuid.UUID(value)) != value:
        raise ValueError('origin must be a canonical UUID')
    return value


def git_read(checkout, args, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('fleet reconciliation budget exhausted')
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_NAMESPACE'):
        env.pop(key, None)
    try:
        result = subprocess.run(['git', '--no-pager', '-C', str(checkout), *args],
                                capture_output=True, timeout=min(5, remaining), env=env)
    except subprocess.TimeoutExpired:
        raise TimeoutError('fleet Git read timed out') from None
    if result.returncode:
        raise ValueError('committed fleet snapshot unavailable')
    return result.stdout


def configure_fleet(path, checkout, origins, repair=False, discover=False):
    owners = [valid_origin(value) for value in origins or []]
    if (not owners and not discover) or len(owners) > 16 or len(set(owners)) != len(owners):
        raise ValueError('fleet inventory must contain 1 to 16 unique origins')
    checkout = Path(checkout).expanduser().resolve()
    root = git_read(checkout, ['rev-parse', '--show-toplevel'], time.monotonic() + 5).decode().strip()
    if Path(root).resolve() != checkout:
        raise ValueError('configure the fleet checkout root')
    with lock(str(Path(path).expanduser().absolute()) + '.project.lock'):
        with contextlib.closing(database(path)) as conn:
            cfg = active_config(conn, path)
            if discover and cfg['owner'] not in owners:
                owners.append(cfg['owner'])
                if len(owners) > 16:
                    raise ValueError('fleet inventory must contain 1 to 16 unique origins')
            if cfg['owner'] not in owners:
                raise ValueError('fleet inventory must include this owner')
            fleet = {'checkout': str(checkout), 'origins': sorted(owners), 'repair_generated_note': repair}
            if discover:
                # Opt-in: also import every committed devices/<uuid>/clio.jsonl at reconcile time.
                fleet['discover'] = True
            if repair:
                view = cfg.get('view', {})
                if not view or digest(Path(view['backup']).read_bytes()) != view['backup_sha256']:
                    raise ValueError('register and verify the existing note before enabling repair')
                if not Path(view['path']).read_bytes().startswith(view['header'].encode()):
                    raise ValueError('personal header differs; repair not enabled')
                fleet.update(header_sha256=digest(view['header'].encode()), coverage=view['coverage'])
            if (cfg.get('fleet', {}).get('discover', False) == discover
                    and all(cfg.get('fleet', {}).get(k) == v for k, v in fleet.items())):
                return {'configured': True, 'unchanged': True, 'fleet': cfg['fleet']}
            cfg['fleet'] = fleet
            atomic(CONFIG, (encode(cfg) + '\n').encode())
    return {'configured': True, 'fleet': fleet}


def reconcile_fleet(path):
    cfg = config()
    fleet = cfg.get('fleet')
    if not fleet:
        return {'configured': False}
    owners = [valid_origin(value) for value in fleet['origins']]
    if not 1 <= len(owners) <= 16 or len(set(owners)) != len(owners) or cfg['owner'] not in owners:
        raise ValueError('invalid configured fleet inventory')
    deadline = time.monotonic() + 30
    status = {'configured': True, 'at': utc(), 'revision': None, 'origins': [], 'partial': False}
    blobs = []
    try:
        head = git_read(fleet['checkout'], ['rev-parse', '--verify', 'HEAD^{commit}'], deadline).decode().strip()
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', head):
            raise ValueError('invalid committed revision')
        status['revision'] = head
        if fleet.get('discover'):
            listed = git_read(fleet['checkout'], ['ls-tree', '-r', '-z', '--name-only', head, '--', 'devices'], deadline)
            found = set()
            for name in listed.decode('utf-8', 'replace').split('\0'):
                match = re.fullmatch(r'devices/([0-9a-f-]{36})/clio\.jsonl', name)
                if match:
                    try:
                        found.add(valid_origin(match[1]))
                    except ValueError:
                        pass
            status['discovered'] = sorted(found.difference(owners))
            owners = sorted(set(owners) | found)
            if len(owners) > 16:
                raise ValueError('discovered fleet exceeds 16 origins')
        for owner in owners:
            spec = head + ':devices/' + owner + '/clio.jsonl'
            try:
                size = int(git_read(fleet['checkout'], ['cat-file', '-s', spec], deadline))
                if size > MAX_FLEET_BYTES:
                    raise ValueError('fleet snapshot exceeds size bound')
                blobs.append((owner, git_read(fleet['checkout'], ['cat-file', 'blob', spec], deadline)))
            except (ValueError, OSError, TimeoutError, subprocess.TimeoutExpired) as error:
                status['origins'].append({'owner': owner, 'state': 'missing' if isinstance(error, ValueError) and str(error) == 'committed fleet snapshot unavailable' else 'error', 'error': type(error).__name__})
    except (ValueError, OSError, TimeoutError, subprocess.TimeoutExpired) as error:
        status['origins'] = [{'owner': owner, 'state': 'error', 'error': type(error).__name__} for owner in owners]
    # Git reads precede the existing lock; no network operation holds this lock.
    with lock(str(Path(path).expanduser().absolute()) + '.project.lock'):
        with contextlib.closing(database(path)) as conn:
            latest = active_config(conn, path)
            if latest.get('fleet', {}) != fleet:
                raise ValueError('fleet configuration changed during reconciliation; retry')
            cfg = latest
        for owner, raw in blobs:
            try:
                result = import_snapshot(path, raw, 'git-blob:' + status['revision'] + ':' + owner,
                                         owner, trusted_own=owner == cfg['owner'], cumulative=True, deadline=deadline)
                result.update(state='accepted', committed_local_rows=result['rows'])
                if owner == cfg['owner'] and (result['added'] or result['label_restored']):
                    result['warning'] = 'own history restored; verify no duplicate live owner'
                status['origins'].append(result)
            except (ValueError, KeyError, TypeError, AttributeError, OverflowError, RecursionError, OSError, sqlite3.Error) as error:
                status['origins'].append({'owner': owner, 'state': 'error', 'error': type(error).__name__})
        status['partial'] = any(item['state'] != 'accepted' for item in status['origins'])
        status['archives'] = recovery_metrics(path)
        cfg['fleet']['last_result'] = status
        atomic(CONFIG, (encode(cfg) + '\n').encode())
    return status


def backup(path, output):
    output = Path(output).expanduser().absolute()
    # Never replace an existing backup or source.
    fd = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    with contextlib.closing(database(path)) as source, contextlib.closing(sqlite3.connect(output)) as target:
        source.backup(target)
    return {'backup': str(output)}


@contextlib.contextmanager
def t3_database(source):
    """T3 is an external source: never use CLIO's rw gateway for it."""
    uri = 'file:' + quote(str(Path(source).expanduser().resolve()), safe='/') + '?mode=ro'
    with contextlib.closing(sqlite3.connect(uri, uri=True, timeout=0.5)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA query_only=ON')
        conn.execute('BEGIN')
        required = {
            'orchestration_events': 'sequence,event_id,aggregate_kind,application_event_version,event_type,payload_json',
            'orchestration_v2_projection_threads': 'thread_id,project_id,payload_json',
            'orchestration_v2_projection_runs': 'run_id,thread_id,payload_json',
            'projection_projects': 'project_id,workspace_root',
            'orchestration_v2_projection_provider_sessions': 'payload_json',
        }
        for table, columns in required.items():
            conn.execute('SELECT ' + columns + ' FROM ' + table + ' LIMIT 0')
        yield conn


def configure_t3(path, source=None, disable=False):
    state_path = Path(str(Path(path).expanduser().absolute()) + '.t3.json')
    with lock(str(state_path) + '.lock'):
        with contextlib.closing(database(path)) as conn:
            active_config(conn, path)
        state = json.loads(state_path.read_text()) if state_path.exists() else None
        if disable:
            if state:
                state['enabled'] = False
                atomic(state_path, (encode(state) + '\n').encode())
            return {'configured': False}
        if source is None:
            raise ValueError('configure-t3 requires the T3 statev2.sqlite path or --disable')
        source = Path(source).expanduser().resolve()
        if state and state['source'] != str(source):
            raise ValueError('T3 source already registered; preserve its cursor before changing sources')
        with t3_database(source) as conn:
            if state:
                t3_boundary(conn, source, state)
            else:
                if conn.execute("SELECT 1 FROM orchestration_events WHERE aggregate_kind='thread' AND application_event_version NOT IN (1,2) LIMIT 1").fetchone():
                    raise ValueError('unsupported T3 thread event version')
                boundary = conn.execute('SELECT sequence,event_id FROM orchestration_events ORDER BY sequence DESC LIMIT 1').fetchone()
                info = source.stat()
                state = {'source': str(source), 'source_id': str(uuid.uuid4()),
                         'device': info.st_dev, 'inode': info.st_ino,
                         'sequence': boundary['sequence'] if boundary else 0,
                         'event_id': boundary['event_id'] if boundary else None}
        state['enabled'] = True
        atomic(state_path, (encode(state) + '\n').encode())
        return {'configured': True, 'source_id': state['source_id'], 'sequence': state['sequence']}


def t3_boundary(conn, source, state):
    info = Path(source).stat()
    if (info.st_dev, info.st_ino) != (state['device'], state['inode']):
        raise ValueError('T3 source replaced; preserve the registered cursor')
    if state['sequence']:
        boundary = conn.execute('SELECT event_id FROM orchestration_events WHERE sequence=?',
                                (state['sequence'],)).fetchone()
        if not boundary or boundary[0] != state['event_id']:
            raise ValueError('T3 source replaced or regressed; preserve the registered cursor')


def capture_t3(path, limit=1000):
    if not 1 <= limit <= 1000:
        raise ValueError('T3 page limit must be between 1 and 1000')
    state_path = Path(str(Path(path).expanduser().absolute()) + '.t3.json')
    with lock(str(state_path) + '.lock'):
        if not state_path.exists():
            return {'configured': False, 'scanned': 0, 'captured': 0}
        state = json.loads(state_path.read_text())
        if not state['enabled']:
            return {'configured': False, 'scanned': 0, 'captured': 0}
        with contextlib.closing(database(path)) as destination:
            cfg = active_config(destination, path)
            with t3_database(state['source']) as conn:
                t3_boundary(conn, state['source'], state)
                events = conn.execute('SELECT * FROM orchestration_events WHERE sequence>? ORDER BY sequence LIMIT ?',
                                      (state['sequence'], limit)).fetchall()
                messages = []
                for event in events:
                    if event['aggregate_kind'] != 'thread':
                        continue
                    version = event['application_event_version']
                    if version not in (1, 2):
                        raise ValueError('unsupported T3 thread event version')
                    if version != 2 or event['event_type'] != 'message.updated':
                        continue
                    message = json.loads(event['payload_json'])
                    if not isinstance(message, dict):
                        raise ValueError('invalid T3 message payload')
                    if (message.get('role') == 'user' and message.get('createdBy') == 'user'
                            and message.get('creationSource') in ('web', 'mobile')):
                        if not all(isinstance(message.get(key), str) and message[key]
                                   for key in ('id', 'threadId', 'createdAt')) or not isinstance(message.get('text'), str):
                            raise ValueError('invalid T3 human submission')
                        if message['text'].strip():
                            messages.append(message)
                rows = []
                unseen = []
                for message in messages:
                    identity = normalize({'timestamp': message['createdAt'], 'prompt': message['text'],
                                          'source_event_id': 't3:' + state['source_id'] + ':' + message['id'],
                                          'extras': {'ide': 't3-code'}}, cfg['owner'], 'captured')
                    prior = destination.execute('SELECT 1 FROM events WHERE record_id=?',
                                                (identity['record_id'],)).fetchone()
                    if prior:
                        continue
                    pending = pending_dir(path) / (identity['record_id'] + '.json')
                    if pending.exists():
                        frozen = normalize(json.loads(pending.read_text()))
                        if frozen['record_id'] != identity['record_id']:
                            raise ValueError('T3 pending receipt identity mismatch')
                        rows.append(frozen)
                    else:
                        unseen.append(message)
                rows.extend(t3_rows(conn, state, unseen))
                # Normalize the complete page before accepting any of it.
                rows = [normalize(row, cfg['owner'], 'captured') for row in rows]
                captured = 0
                for row in rows:
                    prior = destination.execute('SELECT payload FROM events WHERE record_id=?',
                                                (row['record_id'],)).fetchone()
                    pending = pending_dir(path) / (row['record_id'] + '.json')
                    if prior:
                        continue
                    if pending.exists():
                        row = json.loads(pending.read_text())
                    else:
                        captured += 1
                    capture(path, cfg['owner'], row)
                if events:
                    state.update(sequence=events[-1]['sequence'], event_id=events[-1]['event_id'])
                    atomic(state_path, (encode(state) + '\n').encode())
        return {'configured': True, 'scanned': len(events), 'captured': captured, 'sequence': state['sequence']}


def t3_rows(conn, state, messages):
    if not messages:
        return []
    threads = list({message['threadId'] for message in messages})
    marks = ','.join('?' for _ in threads)
    thread_rows = {row['thread_id']: row for row in conn.execute(
        'SELECT thread_id,project_id,payload_json FROM orchestration_v2_projection_threads WHERE thread_id IN (' + marks + ')', threads)}
    run_ids = list({message.get('runId') for message in messages if message.get('runId')})
    message_ids = [message['id'] for message in messages]
    runs = [json.loads(row[0]) for row in conn.execute(
        'SELECT payload_json FROM orchestration_v2_projection_runs WHERE run_id IN ('
        + ','.join('?' for _ in run_ids) + ') OR json_extract(payload_json,\'$.userMessageId\') IN ('
        + ','.join('?' for _ in message_ids) + ') LIMIT 2001', run_ids + message_ids)]
    if len(runs) > 2000:
        raise ValueError('T3 run attribution exceeds page bound')
    by_run = {run['id']: run for run in runs}
    by_message = {run['userMessageId']: run for run in runs}
    projects = list({row['project_id'] for row in thread_rows.values()})
    roots = dict(conn.execute('SELECT project_id,workspace_root FROM projection_projects WHERE project_id IN ('
                             + ','.join('?' for _ in projects) + ')', projects))
    instances = list({run['providerInstanceId'] for run in runs})
    sessions = [json.loads(row[0]) for row in conn.execute(
        'SELECT payload_json FROM orchestration_v2_projection_provider_sessions WHERE '
        "json_extract(payload_json,'$.providerInstanceId') IN (" + ','.join('?' for _ in instances) + ') LIMIT 1001', instances)]
    if len(sessions) > 1000:
        raise ValueError('T3 provider attribution exceeds page bound')
    drivers = {session['providerInstanceId']: session['driver']
               for session in sorted(sessions, key=lambda session: session.get('updatedAt', ''))}
    machine = os.uname().nodename.split('.')[0]
    try:
        computer_name = subprocess.run(['scutil', '--get', 'ComputerName'], capture_output=True,
                                       text=True, timeout=5)
        machine = computer_name.stdout.strip() if computer_name.returncode == 0 and computer_name.stdout.strip() else machine
    except (OSError, subprocess.TimeoutExpired):
        pass
    result = []
    for message in messages:
        run = by_run.get(message['runId']) if message.get('runId') else by_message.get(message['id'])
        if not run or not run.get('providerInstanceId') or run.get('threadId') != message['threadId']:
            raise ValueError('T3 submission run metadata unavailable; retry after projections recover')
        thread = thread_rows.get(message['threadId'])
        workspace = roots.get(thread['project_id'], '') if thread else ''
        details = json.loads(thread['payload_json']) if thread else {}
        checkout = (details.get('worktreePath') or workspace) if workspace else ''
        instance = run['providerInstanceId']
        driver = drivers.get(instance)
        result.append({'timestamp': message['createdAt'], 'repo': Path(workspace).name if workspace else '',
                       'branch': (details.get('branch') or '') if workspace else '',
                       'machine': machine,
                       'agent': {'claudeAgent': 'claude-code', 'antigravity': 'agy'}.get(driver, driver or instance),
                       'session_id': 't3:' + state['source_id'] + ':' + message['threadId'],
                       'prompt': message['text'], 'checkout': checkout,
                       'source_event_id': 't3:' + state['source_id'] + ':' + message['id'],
                       'extras': {'ide': 't3-code', 't3_message_id': message['id'],
                                  't3_thread_id': message['threadId'], 'provider_instance_id': instance,
                                  'driver': driver, 'model': run.get('modelSelection', {}).get('model'),
                                  'metadata_observed_at': utc(), 'metadata_basis': 'capture-time projections',
                                  'metadata_warning': None if workspace else 'project metadata unavailable'}})
    return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', help='default: activated DB, otherwise ~/.claude/prompt-log.sqlite3')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('init')
    imp = commands.add_parser('import-jsonl')
    imp.add_argument('input')
    imp.add_argument('--source')
    imp.add_argument('--max-records', type=int, default=1000)
    verify = commands.add_parser('verify-import')
    verify.add_argument('source')
    activation = commands.add_parser('activate')
    activation.add_argument('--source', default=str(Path.home() / '.claude/prompt-log.jsonl'))
    activation.add_argument('--fresh', action='store_true')
    activation.add_argument('--capture-only', action='store_true', help='capture and export full JSONL without changing the shared note')
    migration = commands.add_parser('migrate-view')
    migration.add_argument('--markdown')
    migration.add_argument('--publishers-paused', action='store_true')
    migration.add_argument('--archive-unreconciled-note', action='store_true',
                           help='accept historical gaps/repeated sections; archive the whole note without claiming SQLite parity')
    migration.add_argument('--join-fleet-note', action='store_true',
                           help='register a note another device already renders from the shared fleet history')
    scheduled = commands.add_parser('scheduled-export')
    scheduled.add_argument('markdown')
    scheduled.add_argument('--mode', default='export')
    commands.add_parser('capture')
    t3_setup = commands.add_parser('configure-t3', help='opt in to local T3 Code user-prompt capture')
    t3_setup.add_argument('source', nargs='?', help='T3 userdata/statev2.sqlite; starts at its current end')
    t3_setup.add_argument('--disable', action='store_true', help='stop scans and retain the cursor/history')
    t3_scan = commands.add_parser('capture-t3', help='capture one bounded page from the registered T3 source')
    t3_scan.add_argument('--limit', type=int, default=1000)
    recovery = commands.add_parser('drain')
    recovery.add_argument('--limit', type=int, default=100)
    reader = commands.add_parser('query')
    for flag in ('repo', 'device', 'agent', 'session', 'record-id', 'repo-slug', 'origin', 'since', 'until', 'text', 'reference'):
        reader.add_argument('--' + flag)
    reader.add_argument('--limit', type=int, default=20)
    reader.add_argument('--offset', type=int, default=0)
    reader.add_argument('--explain', action='store_true')
    projection = commands.add_parser('project')
    projection.add_argument('--markdown')
    projection.add_argument('--jsonl')
    projection.add_argument('--cutoff')
    projection.add_argument('--jsonl-only', action='store_true')
    exporter = commands.add_parser('export-device')
    exporter.add_argument('output')
    exporter.add_argument('--cutoff')
    exporter.add_argument('--origin', help='explicit one-time bootstrap of a known preserved origin')
    fleet = commands.add_parser('configure-fleet')
    fleet.add_argument('checkout')
    fleet.add_argument('--origin', action='append', default=[])
    fleet.add_argument('--discover-origins', action='store_true', help='also import every committed devices/<uuid>/clio.jsonl; this owner is implied')
    fleet.add_argument('--repair-generated-note', action='store_true', help='machine-owned body: archive unknown body edits before rebuilding; preserve personal header')
    commands.add_parser('reconcile-fleet')
    importer = commands.add_parser('import-device')
    importer.add_argument('input')
    copier = commands.add_parser('backup')
    copier.add_argument('output')
    args = parser.parse_args()
    try:
        cfg = {} if args.db and args.command != 'capture' else config()
        path = args.db or cfg.get('db') or str(Path.home() / '.claude/prompt-log.sqlite3')
        if hasattr(args, 'limit') and not 1 <= args.limit <= 1000:
            raise ValueError('limit must be between 1 and 1000')
        if getattr(args, 'offset', 0) < 0 or getattr(args, 'max_records', 1) < 1:
            raise ValueError('invalid pagination or import bound')
        if args.command == 'init':
            result = {'owner': initialize(path), 'db': str(Path(path).expanduser().absolute())}
        elif args.command == 'import-jsonl':
            result = import_jsonl(path, args.input, args.source, args.max_records)
        elif args.command == 'verify-import':
            result = verify_import(path, args.source)
        elif args.command == 'activate':
            result = activate(path, args.source, args.fresh, args.capture_only)
        elif args.command == 'migrate-view':
            result = migrate_view(path, args.markdown, args.publishers_paused, args.archive_unreconciled_note, args.join_fleet_note)
        elif args.command == 'configure-fleet':
            result = configure_fleet(path, args.checkout, args.origin, args.repair_generated_note, args.discover_origins)
        elif args.command == 'reconcile-fleet':
            result = reconcile_fleet(path)
        elif args.command == 'configure-t3':
            result = configure_t3(path, args.source, args.disable)
        elif args.command == 'capture-t3':
            result = capture_t3(path, args.limit)
        elif args.command == 'scheduled-export':
            destination = Path(args.markdown).expanduser()
            destination = destination.parent.resolve() / destination.name
            if args.mode != 'export':
                raise ValueError('legacy maintenance is unavailable in SQLite mode; use query, drain and project')
            with contextlib.closing(database(path)) as conn:
                activated = active_config(conn, path)
                capture_only = activated.get('capture_only') and not activated.get('view')
                if capture_only:
                    existing_destination(args.markdown)
                elif not activated.get('view'):
                    raise ValueError('register the existing note before scheduled publication')
                elif destination != Path(activated['view']['path']):
                    if destination.resolve() != Path(activated['view']['path']):
                        raise ValueError('scheduled destination differs from registered note')
                    destination = Path(activated['view']['path'])
            t3_result = None
            try:
                t3_result = capture_t3(path)
            except (ValueError, TypeError, KeyError, OSError, sqlite3.Error, TimeoutError) as error:
                diagnostic('T3 capture refused: ' + type(error).__name__ + '; cursor retained; run capture-t3')
                t3_result = {'configured': True, 'state': 'refused', 'error': type(error).__name__}
            if activated.get('fleet'):
                errors = []
                try:
                    recovery = drain(path)
                except (ValueError, OSError, sqlite3.Error, TimeoutError) as error:
                    recovery = {'pending': len(list(pending_dir(path).glob('clio1-*.json')))}
                    errors.append(type(error).__name__)
                try:
                    fleet_result = reconcile_fleet(path)
                except (ValueError, TypeError, KeyError, AttributeError, OverflowError, OSError, sqlite3.Error) as error:
                    fleet_result = {'configured': True, 'at': utc(), 'partial': True, 'error': type(error).__name__}
                # Compatibility output is independent of every note refusal.
                result = project(path, jsonl=Path.home() / '.claude/prompt-log-compat.jsonl', jsonl_only=True)
                note_status = {'state': 'paused' if capture_only else 'published'}
                if not capture_only:
                    try:
                        result.update(project(path, destination))
                    except (ValueError, OSError, sqlite3.Error, TimeoutError) as error:
                        note_status = {'state': 'waiting_for_history' if 'waiting_for_history' in str(error) else 'refused', 'error': type(error).__name__,
                                       'reason': ('archive_budget_exhausted' if 'archive_budget_exhausted' in str(error)
                                                  else 'header_changed' if 'header' in str(error)
                                                  else 'backup_changed' if 'backup' in str(error) else 'publication_guard')}
                with lock(str(Path(path).expanduser().absolute()) + '.project.lock'):
                    with contextlib.closing(database(path)) as conn:
                        latest = active_config(conn, path)
                        latest.get('view', {})['last_note_status'] = note_status
                        latest['fleet']['last_result'] = dict(fleet_result, archives=recovery_metrics(path))
                        atomic(CONFIG, (encode(latest) + '\n').encode())
                result.update(fleet=fleet_result, note_publication=note_status['state'], note_status=note_status, drain_errors=errors)
            else:
                recovery = drain(path)
                result = project(path, None if capture_only else destination,
                                 Path.home() / '.claude/prompt-log-compat.jsonl', jsonl_only=bool(capture_only))
            result['pending'] = recovery['pending']
            result['t3'] = t3_result
            if t3_result.get('state') == 'refused':
                print(encode(result))
                return 3
        elif args.command == 'capture':
            if not cfg or Path(cfg['db']).resolve() != Path(path).expanduser().resolve():
                raise ValueError('capture requires the activated database')
            result = capture(path, cfg['owner'], json.load(sys.stdin))
        elif args.command == 'drain':
            result = drain(path, args.limit)
        elif args.command == 'query':
            result = query(path, args)
        elif args.command == 'project':
            result = project(path, args.markdown, args.jsonl, args.cutoff, args.jsonl_only)
        elif args.command == 'export-device':
            result = export_device(path, args.output, args.cutoff, args.origin)
        elif args.command == 'import-device':
            result = import_device(path, args.input)
        else:
            result = backup(path, args.output)
        print(encode(result))
        return 0
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, OSError, sqlite3.Error) as error:
        # No raw input/parameters in diagnostics; private quarantine holds rejected source data.
        message = type(error).__name__ + ': ' + (str(error) if isinstance(error, (ValueError, sqlite3.Error)) else 'operation failed; source and pending receipts retained')
        print(message, file=sys.stderr)
        try:
            if args.command not in ('query', 'verify-import'):
                diagnostic(args.command + ': ' + message)
        except OSError:
            pass
        return 3


if __name__ == '__main__':
    sys.exit(main())

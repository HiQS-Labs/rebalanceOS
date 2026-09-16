#!/usr/bin/env python3
"""Opt-in GH-230 historical replay. No ingestion, model calls, or live publication."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from datetime import timedelta
from pathlib import Path

from rebalance.ingest.clio import filter_prompt_metadata
from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.lib.git_ops import parse_github_remote_url, run_git
from rebalance.lib.json_ops import _json_dumps
from rebalance.lib.redaction import redact_key_shaped_secrets
from rebalance.lib.time_ops import now_utc, parse_iso
from rebalance.paths import resolve_clio_prompt_log_path, resolve_database_path

REPO = "hiqs-labs/xyz-forge"
MAX_BYTES = 100_000_000
MAX_ROWS = 10_000
REF = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/(issues|pull)/([1-9]\d*)(?![\w-]|\.\d)\b|(?<![\w/])([\w.-]+/[\w.-]+)#([1-9]\d*)(?![\w-]|\.\d)\b", re.I)


def references(text, context):
    text = re.sub(r"\b(issue|pr|pull\s+request|AgentChorus|agent2agent)\s+(\*\*|`)(#?[1-9]\d*)\2",
                  r"\1 \3", text, flags=re.I)
    text = re.sub(r"\b(?:AgentChorus|agent2agent)\s+#\d+\b", " ", text, flags=re.I)
    refs = {(a.lower(), "pr" if b.lower() == "pull" else "issue", int(c)) if a else
            (d.lower(), "issue", int(e)) for a, b, c, d, e in REF.findall(text)}
    if context:
        # Consume typed refs before bare #N so PR #N does not also become issue #N.
        local = REF.sub(" ", text)
        number = r"([1-9]\d*)(?![\w]|\.\d)"
        def typed(match):
            if match[3]:  # "PR 2 phase" may be a phase ordinal, not a GitHub ID.
                return " "
            kind = "issue" if match[1].lower() == "issue" else "pr"
            refs.add((REPO, kind, int(match[2])))
            return " "
        local = re.sub(r"\b(issue|pr|pull\s+request)\s+#?" + number + r"(\s+phase\b)?", typed, local, flags=re.I)
        refs.update((REPO, "issue", int(n)) for n in re.findall(r"(?<![\w/])#" + number, local))
        # A bare command argument is scoped by the command, not arbitrary prose numbers.
        command = re.match(r"^\s*/start-task\s+(?:(?:on|for)\s+)?" + number, local, re.I)
        if command:
            refs.add((REPO, "issue", int(command[1])))
    return sorted(refs)


def qualified_references(text):
    """Typed qualified URLs only; neither prose scope nor shorthand supplies identity."""
    return sorted({(repo.lower(), 'pr' if kind.lower() == 'pull' else 'issue', int(number))
                   for repo, kind, number, _, _ in REF.findall(text) if repo})


def is_start(text):
    """Conservative command hints, not an intent classifier or proof of execution."""
    text = text.strip().lower()
    if any(x in text for x in ("?", "don't", "do not", "not yet", "if ", "example", "instead of")):
        return False
    if text.startswith(('"', "'", "`", ">")):
        return False
    # IDE skill links are normalized only at the command position.
    text = re.sub(r"^\[\$(start-task|express)\]\([^\n)]*\)", r"/\1", text)
    return bool(re.match(r"^(?:(?:ok[, ]+)?please\s+|ok[, ]+)?(?:/(?:start-task|express)\b|(?:let's\s+)?start\b|(?:fix|apply|implement)\s+(?:the\s+|a\s+)?hotfix\b|hotfix\s*:)", text))


def snapshot(path):
    with path.open("rb") as handle:
        size = os.fstat(handle.fileno()).st_size
        raw = handle.read(min(size, MAX_BYTES))
    end = raw.rfind(b"\n") + 1
    raw = raw[:end]
    if not raw:
        raise ValueError("no complete capture records")
    return raw, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                 "byte_cap_hit": size > MAX_BYTES, "partial_tail": end < min(size, MAX_BYTES)}


def verify_prefix(path, meta):
    with path.open("rb") as handle:
        raw = handle.read(meta["bytes"])
    if len(raw) != meta["bytes"] or hashlib.sha256(raw).hexdigest() != meta["sha256"]:
        raise ValueError("source prefix changed; refusing publication")


def markdown_rows(raw):
    """Decode only canonical exporter blocks, never free-form personal notes.

    Contract: utils/CLIO/prompt-log-to-md.sh:500. UTC is taken from the source
    marker, not the localized display timestamp. Unmarked legacy entries omitted.
    """
    text = raw.decode("utf-8")
    blocks = re.split(r"(?m)^<!-- clio:id:", text)[1:]
    rows = []
    for block in blocks:
        match = re.match(r"([^\n]+?):(\d{4}-\d{2}-\d{2}T[^\n ]+) -->\n## ([^\n]+)\n[^\n]*\n([^\n]*)\n\n(> .*?)(?=\n[^>]|\Z)", block, re.S)
        if not match:
            rows.append(b"null")  # counted as malformed, not silently accepted
            continue
        session, stamp, repo, metadata, quoted = match.groups()
        parts = metadata.split(" · ")
        prompt = "\n".join(line[2:] for line in quoted.splitlines())
        if not (prompt.startswith('"') and prompt.endswith('"')):
            rows.append(b"null")
            continue
        rows.append(_json_dumps(dict(session_id=session, timestamp=stamp, repo=repo,
                                    machine=parts[0] or None, agent=parts[-1] if len(parts) > 1 else None,
                                    prompt=prompt[1:-1])).encode())
    return b"\n".join(rows) + b"\n"


def load_prompts(raw, fingerprint, as_of, aliases, explicit_links_only=False):
    counts = Counter()
    rows, seen = [], set()
    for ordinal, line in enumerate(raw.splitlines(), 1):
        counts["scanned"] += 1
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get("prompt"), str):
                raise ValueError()
            stamp = parse_iso(row.get("timestamp"))
            if stamp is None:
                raise ValueError()
            if not as_of - timedelta(days=7) <= stamp < as_of:
                counts["out_of_window"] += 1
                continue
            for field in ("repo", "agent", "session_id", "machine"):
                if row.get(field) is not None and not isinstance(row[field], str):
                    raise ValueError()
        except (ValueError, TypeError, UnicodeError):
            counts["malformed"] += 1
            continue
        text = filter_prompt_metadata(row["prompt"])
        context = (row.get("repo") or "").casefold() in aliases
        refs = references(text, context)
        if not context and not any(r[0] == REPO for r in refs):
            counts["unresolved_or_other_repo"] += 1
            continue
        unresolved = []
        if explicit_links_only:
            # Only a typed, qualified URL establishes both repository and artifact type.
            # Shorthand and checkout-scoped prose stay review candidates, never join keys.
            explicit = set(qualified_references(text))
            unresolved = [dict(repository=None, kind_hint=kind, number=number,
                               reason='repository or artifact type requires review')
                          for repo, kind, number in refs if (repo, kind, number) not in explicit]
            refs = sorted(explicit)
        if len(rows) >= MAX_ROWS:
            counts["row_cap_hit"] = 1
            break
        identity = (row.get("machine"), row.get("agent"), row.get("session_id"), stamp.isoformat(), text)
        if identity in seen:
            counts["duplicates"] += 1
            continue
        seen.add(identity)
        counts["missing_session"] += not bool(row.get("session_id"))
        counts["missing_device"] += not bool(row.get("machine"))
        rows.append({"id": f"clio:{fingerprint}:{ordinal}", "ordinal": ordinal,
                     "timestamp": stamp.isoformat(), "text": text, "kind": "intent",
                     "session": row.get("session_id"), "device": row.get("machine"),
                     "agent": row.get("agent"), "refs": refs, "start": is_start(text)})
        if explicit_links_only:
            rows[-1]['unresolved_refs'] = unresolved
    if not rows:
        raise ValueError("no eligible seven-day prompts; coverage blocked")
    return sorted(rows, key=lambda r: (r["timestamp"], r["ordinal"])), dict(counts)


def group(rows, qualified_transitions=False):
    if qualified_transitions:
        rows = [row | {'refs': qualified_references(row['text'])} for row in rows]
    journeys, active, orphans = [], {}, []
    for row in rows:
        key = (row["device"], row["agent"], row["session"])
        if not row["session"]:
            orphans.append(row["id"])
            continue
        transition = False
        if qualified_transitions and key in active:
            # Exact new-task wording is a candidate boundary, never completion evidence.
            target = re.fullmatch(r"\s*next task:\s*(?:start\s+)?https://github\.com/"
                                 r"([\w.-]+/[\w.-]+)/issues/([1-9]\d*)\s*", row['text'], re.I)
            if target and target[1].lower() == REPO:
                issue = (REPO, 'issue', int(target[2]))
                old = [tuple(ref) for ref in active[key]['issues']]
                transition = len(old) == 1 and old[0] != issue and old[0][0] == REPO
        if row["start"] or transition:
            journey = {"id": row["id"], "prompts": [], "issues": []}
            if transition:
                journey['boundary'] = 'qualified new-task request; candidate only'
            journeys.append(journey)
            active[key] = journey
        if key not in active:
            orphans.append(row["id"])
            continue
        active[key]["prompts"].append(row["id"])
        refs = {tuple(x) for x in active[key]["issues"]}
        refs.update(tuple(x) for x in row["refs"] if x[2] > 0 and x[1] == "issue")
        active[key]["issues"] = sorted(refs)
    parents = {}
    for journey in journeys:
        refs = journey["issues"]
        # No bridging: any conflicting issue makes the segment ambiguous.
        parent = f"{REPO}#{refs[0][2]}" if len(refs) == 1 and refs[0][0] == REPO else journey["id"]
        parents.setdefault(parent, []).append(journey["id"])
    return journeys, parents, orphans


def github_events(database, as_of):
    """Read existing snapshots only. Unknown/absent source is not an empty success."""
    events = []
    try:
        with db_connection_readonly(database) as conn:
            conn.execute("PRAGMA query_only=ON")
            for offset in range(0, MAX_ROWS + 1, 1000):
                rows = conn.execute(
                    "SELECT item_type,number,created_at,closed_at,merged_at,fetched_at FROM github_items "
                    "WHERE lower(repo_full_name)=? ORDER BY item_type,number LIMIT 1000 OFFSET ?",
                    (REPO, offset)).fetchall()
                if offset == MAX_ROWS and rows:
                    return events, "incomplete: artifact row cap"
                for row in rows:
                    kind = "pr" if row["item_type"] in ("pr", "pull_request", "pull") else "issue"
                    for field in ("created_at", "closed_at", "merged_at"):
                        stamp = parse_iso(row[field])
                        if stamp and as_of - timedelta(days=7) <= stamp < as_of:
                            events.append({"id": f"gh:{REPO}:{kind}:{row['number']}:{field}:{stamp.isoformat()}",
                                           "timestamp": stamp.isoformat(), "kind": "recorded event",
                                           "event": field, "ref": (REPO, kind, row["number"]),
                                           "fetched_at": row["fetched_at"],
                                           "url": f"https://github.com/{REPO}/{'pull' if kind == 'pr' else 'issues'}/{row['number']}"})
                if len(rows) < 1000:
                    break
    except Exception as exc:
        return [], f"unavailable: {type(exc).__name__}"
    unique = {event["id"]: event for event in events}
    return sorted(unique.values(), key=lambda e: (e["timestamp"], e["id"])), "available" if events else "no events in window"


def render(bundle):
    rows = {r["id"]: r for r in bundle["prompts"]}
    lines = ["# XYZ Forge journey replay — private preview", "", "Requests are intent, not proof of completion.",
             "GitHub facts are retrospective snapshots; linking them does not prove a chat caused them.",
             "", "## Coverage", _json_dumps(bundle["coverage"]), "", "## A — Separate chat journeys"]
    for journey in bundle["journeys"]:
        lines += ["", f"### {journey['id']}"]
        refs = {tuple(ref) for pid in journey["prompts"] for ref in rows[pid]["refs"]}
        timeline = [(rows[pid]["timestamp"], f"intent [{pid}]: " +
                     redact_key_shaped_secrets(rows[pid]["text"]).replace("\n", " ")[:500]) for pid in journey["prompts"]]
        timeline += [(e["timestamp"], f"recorded event [{e['id']}]: {e['event']} {e['url']}")
                     for e in bundle["events"] if tuple(e["ref"]) in refs]
        lines += [f"- {stamp} — {text}" for stamp, text in sorted(timeline)]
        unresolved = sum(len(rows[pid].get('unresolved_refs', [])) for pid in journey['prompts'])
        if unresolved:
            lines += [f'- Unresolved reference candidates: {unresolved}; excluded from outcome joins.']
    lines += ["", "## B — Issue-linked parents (same child timelines)"]
    for parent, children in bundle["parents"].items():
        lines += [f"- {parent}"] + [f"  - {child}" for child in children]
    if 'candidate_view' in bundle:
        lines += ['', '## C — Qualified task-transition candidates',
                  'Original chat journeys above are preserved. A boundary does not attest completion.']
        for journey in bundle['candidate_view']['journeys']:
            lines += ['', f"### Candidate {journey['id']}",
                      f"- Boundary: {journey.get('boundary', 'original start hint')}",
                      '- Intent prompt IDs: ' + ', '.join(journey['prompts'])]
            refs = {ref for pid in journey['prompts'] for ref in qualified_references(rows[pid]['text'])}
            lines += [f"- {e['timestamp']} — recorded event: {e['event']} {e['url']}"
                      for e in bundle['events'] if tuple(e['ref']) in refs]
    lines += ["", f"Unassigned prompts: {len(bundle['orphans'])}", "", "## Review sample — first ten non-starts"]
    lines += [f"- {r['id']}: {redact_key_shaped_secrets(r['text']).replace(chr(10), ' ')[:320]}"
              for r in bundle["prompts"] if not r["start"]][:10]
    return "\n".join(lines) + "\n"


def publish(output, raw, bundle, source, meta):
    """Publish a new private run directory as one unit; never replace existing output."""
    if output.exists() or output.is_symlink():
        raise ValueError("output already exists; choose a new private run directory")
    markdown = render(bundle)  # validation/render failures leave prior output untouched
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix=".journey-", dir=output.parent) as stage:
        stage = Path(stage)
        for name, data in (("capture." + bundle.get("source_format", "jsonl"), raw), ("evidence.json", _json_dumps(bundle).encode()),
                           ("preview.md", markdown.encode())):
            with (stage / name).open("xb") as handle:
                os.fchmod(handle.fileno(), 0o600)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        verify_prefix(source, meta)
        os.rename(stage, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--source-format", choices=("jsonl", "md"), default="jsonl")
    parser.add_argument("--database", type=Path)
    parser.add_argument("--checkout", type=Path, action="append", default=[])
    parser.add_argument("--as-of", default=now_utc().isoformat())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument('--explicit-links-only', action='store_true',
                        help='Use only typed qualified GitHub URLs for joins; retain other mentions as unresolved.')
    parser.add_argument('--qualified-transitions', action='store_true',
                        help='Add a candidate view for exact qualified Next task requests; preserve original grouping.')
    args = parser.parse_args()
    as_of = parse_iso(args.as_of)
    if as_of is None:
        parser.error("invalid --as-of")
    aliases = {REPO}
    for checkout in args.checkout:
        remote = run_git(checkout, "remote", "get-url", "origin")
        if remote.returncode or (parse_github_remote_url(remote.stdout) or "").lower() != REPO:
            parser.error("checkout remote is not the trial repository")
        aliases.add(checkout.name.casefold())
    source = resolve_clio_prompt_log_path(args.source)
    raw, meta = snapshot(source)
    replay_input = markdown_rows(raw) if args.source_format == "md" else raw
    rows, counts = load_prompts(replay_input, meta["sha256"], as_of, aliases, args.explicit_links_only)
    journeys, parents, orphans = group(rows)
    events, status = github_events(resolve_database_path(args.database), as_of)
    coverage = counts | {"eligible_prompts": len(rows), "starts": sum(r["start"] for r in rows),
                        "journeys": len(journeys), "parents": len(parents), "orphans": len(orphans),
                        "github_events": len(events), "github_status": status,
                        "devices": len({r['device'] for r in rows if r['device']}),
                        "terra": "not called: guarded runner has no independent output seam",
                        "relay_marathon": "not attested", "byte_cap_hit": meta["byte_cap_hit"]}
    coverage['reference_policy'] = 'explicit URLs only' if args.explicit_links_only else 'checkout-context candidates'
    coverage['unresolved_reference_candidates'] = sum(len(r.get('unresolved_refs', [])) for r in rows)
    bundle = {"as_of_utc": as_of.isoformat(), "source": meta, "source_format": args.source_format, "coverage": coverage,
              "prompts": rows, "journeys": journeys, "parents": parents, "orphans": orphans, "events": events}
    if args.qualified_transitions:
        candidate_journeys, candidate_parents, candidate_orphans = group(rows, qualified_transitions=True)
        bundle['candidate_view'] = dict(journeys=candidate_journeys, parents=candidate_parents,
                                        orphans=candidate_orphans)
    publish(args.output, raw, bundle, source, meta)
    print(_json_dumps(coverage))  # no prompt text, session IDs, or private paths


if __name__ == "__main__":
    main()

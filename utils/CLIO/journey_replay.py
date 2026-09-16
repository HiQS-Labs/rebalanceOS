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
REF = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/(issues|pull)/(\d+)\b|(?<![\w/])([\w.-]+/[\w.-]+)#(\d+)\b", re.I)


def references(text, context):
    refs = {(a.lower(), "pr" if b == "pull" else "issue", int(c)) if a else
            (d.lower(), "issue", int(e)) for a, b, c, d, e in REF.findall(text)}
    if context:
        # Bare numbers are scoped ONLY by independently verified checkout identity.
        refs.update((REPO, "issue", int(n)) for n in re.findall(r"(?<![\w/])#(\d+)\b", text))
    return sorted(refs)


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


def load_prompts(raw, fingerprint, as_of, aliases):
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
    if not rows:
        raise ValueError("no eligible seven-day prompts; coverage blocked")
    return sorted(rows, key=lambda r: (r["timestamp"], r["ordinal"])), dict(counts)


def group(rows):
    journeys, active, orphans = [], {}, []
    for row in rows:
        key = (row["device"], row["agent"], row["session"])
        if not row["session"]:
            orphans.append(row["id"])
            continue
        if row["start"]:
            journey = {"id": row["id"], "prompts": [], "issues": []}
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
    lines += ["", "## B — Issue-linked parents (same child timelines)"]
    for parent, children in bundle["parents"].items():
        lines += [f"- {parent}"] + [f"  - {child}" for child in children]
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
    rows, counts = load_prompts(replay_input, meta["sha256"], as_of, aliases)
    journeys, parents, orphans = group(rows)
    events, status = github_events(resolve_database_path(args.database), as_of)
    coverage = counts | {"eligible_prompts": len(rows), "starts": sum(r["start"] for r in rows),
                        "journeys": len(journeys), "parents": len(parents), "orphans": len(orphans),
                        "github_events": len(events), "github_status": status,
                        "devices": len({r['device'] for r in rows if r['device']}),
                        "terra": "not called: guarded runner has no independent output seam",
                        "relay_marathon": "not attested", "byte_cap_hit": meta["byte_cap_hit"]}
    bundle = {"as_of_utc": as_of.isoformat(), "source": meta, "source_format": args.source_format, "coverage": coverage,
              "prompts": rows, "journeys": journeys, "parents": parents, "orphans": orphans, "events": events}
    publish(args.output, raw, bundle, source, meta)
    print(_json_dumps(coverage))  # no prompt text, session IDs, or private paths


if __name__ == "__main__":
    main()

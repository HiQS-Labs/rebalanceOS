#!/usr/bin/env python3
"""Twice-daily progress digest — producer half (GH-142).

Collects today's signal from rebalance.db, synthesizes it with Gemini, and publishes
one markdown file into the shared pulse repo. AEGIS Sleuth's snapshot-relay polls that
directory and posts new files to Slack (AEGIS-Sleuth-Slackbot#157) — this script never
talks to Slack itself.

Design contract (mirrors utils/daily_synthesis.py, which this is modeled on):
  * Deterministic first  — the three collectors own the FACTS. They are plain SQL and one
                           subprocess; no model is involved in deciding what happened.
  * Gemini-only prose    — synthesis returns None on no-key or failure and the caller
                           writes NOTHING. No fallback model ever reaches the channel.
                           Same rule as synthesize_pulse() (daily_synthesis.py:197).
  * Honest collectors    — a collector that fails records its error IN the facts rather
                           than returning empty. A digest that says "github: unavailable"
                           is correct; one that silently says "0 commits" is a lie, and
                           this repo has been bitten three times by jobs reporting
                           success while doing nothing (see #157).
  * generated_at         — stamped in the payload and rendered at the top of the post.
                           This is the ENTIRE observability design: launchd runs a missed
                           job on next wake, so a digest produced at 23:40 announces that
                           in the channel. There is deliberately no watchdog.
  * One file per slot    — hiqs-<date>-<slot>.md. The relay's seen-set is filename-keyed,
                           so two slots dedupe for free: no cursor, no watermark, and
                           both posts can cover midnight->now as specified.
  * Single write path    — reuses pulse._commit_and_push_if_changed rather than a second
                           write/commit/push implementation.

Semantic slot: source_filter=["github"] is REQUIRED, not tuning. A bake-off against live
data showed the unfiltered query returns near-duplicate vault prompt logs, because ~85%
of a day's index churn is vault writes. See AEGIS-Sleuth-Slackbot#157.

Requires the project venv (imports rebalance.*). Run via utils/hiqs_digest.sh so launchd
inherits Full Disk Access.

Usage:
  hiqs_digest.py                  # produce and publish (the launchd job)
  hiqs_digest.py --dry-run        # print what would be published; no write, no push
  hiqs_digest.py --facts-only     # print the collected facts as JSON; no LLM call
  hiqs_digest.py --slot 1305      # override the slot label (default: local HHMM)
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Where the digest lands inside pulse_target_path. Deliberately NOT a new config key —
# the pulse repo path is already configured; this is just a subdirectory in it.
DEFAULT_SUBDIR = os.environ.get("HIQS_DIGEST_SUBDIR", "digests")

# CB-1 from scripts/health_issue_reporter.py:31-38 — the hard kill switch, and the only
# breaker this job takes. The quota and per-run caps there guard up to 8 LLM calls a day;
# this job makes 2. Add them when a third caller shares the budget.
LLM_DISABLE_ENV = "HIQS_DIGEST_LLM_DISABLE"

SEMANTIC_SOURCES = ["github"]
SEMANTIC_QUERY = "what work shipped today"
SEMANTIC_TOP_K = 8

PROMPT_TEMPLATE = """You are writing a short progress update for an engineering team's Slack channel.

Below is a STRUCTURED snapshot of today's activity. Write a summary a teammate can skim in
about thirty seconds.

Cover all three, in this order, and nothing else:

1. SHIPPED — what actually landed today, grouped by repo or theme. Lead with merged work.
2. IN FLIGHT — one or two lines, only if `semantic.hits` shows themes that are NOT already
   covered by the shipped items. If it adds nothing new, omit this section entirely.
3. HEALTH — if `health.problem_count` is greater than zero, ONE line naming the problems.
   If it is zero, write nothing about health.

Hard rules:
- Do NOT invent anything. Every claim must trace to the data below.
- NEVER list a repository that shipped nothing. A repo with commits but no merged work is
  only worth a mention if it is the bulk of the day's activity.
- No preamble, no sign-off, no restating the counts (a footer already carries them).
- Twelve lines is the ceiling. If the data is sparse, three lines is the correct answer.
- If a whole section's data is missing or has an `error` key, say so in a few words. Never
  imply a quiet day when the truth is that a collector failed.

DATA:
{data}
"""


def log(msg: str) -> None:
    print(f"[hiqs-digest] {msg}", file=sys.stderr, flush=True)


def _scrub(text: str) -> str:
    """Replace the home directory with ~ so absolute paths don't ride into Slack."""
    home = str(Path.home())
    return text.replace(home, "~") if text else text


def _db_path() -> Path:
    default = Path.home() / "Library/Application Support/rebalance-os/rebalance.db"
    return Path(os.environ.get("REBALANCE_DB", default)).expanduser()


# --- Collectors ----------------------------------------------------------------
# Each returns a dict. On failure it returns {"error": "..."} rather than empty data,
# so the synthesizer can say "unavailable" instead of implying a quiet day.


def collect_github(db: Path, today: str) -> dict[str, Any]:
    """Today's GitHub activity, straight from the typed columns. No LLM, no parsing."""
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            repos = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT repo_full_name, commits, prs_opened, prs_merged,
                           issues_opened, issue_comments, reviews
                    FROM github_activity
                    WHERE scan_date = ?
                      AND (commits + prs_opened + prs_merged + issues_opened
                           + issue_comments + reviews) > 0
                    ORDER BY commits DESC, prs_merged DESC
                    """,
                    (today,),
                )
            ]
            commits = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT repo_full_name, message, author_login
                    FROM github_commits
                    WHERE date(committed_at) = ?
                    ORDER BY committed_at DESC
                    LIMIT 40
                    """,
                    (today,),
                )
            ]
            merged = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT repo_full_name, item_type, number, title
                    FROM github_items
                    WHERE date(merged_at) = ?
                    ORDER BY merged_at DESC
                    LIMIT 20
                    """,
                    (today,),
                )
            ]
            closed = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT repo_full_name, item_type, number, title
                    FROM github_items
                    WHERE date(closed_at) = ? AND merged_at IS NULL
                    ORDER BY closed_at DESC
                    LIMIT 20
                    """,
                    (today,),
                )
            ]
    except sqlite3.Error as e:
        return {"error": f"github collector failed: {e}"}

    # First line of each commit message is the subject; the body is noise for a digest.
    for c in commits:
        c["message"] = (c.get("message") or "").splitlines()[0][:140]

    return {
        "by_repo": repos,
        "commits": commits,
        "merged": merged,
        "closed_not_merged": closed,
    }


def collect_health() -> dict[str, Any]:
    """Non-ok checks from `rebalance doctor --json`. Everything green -> a one-word summary."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "rebalance", "doctor", "--json"],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return {"error": f"doctor failed to run: {e}"}

    if not result.stdout.strip():
        return {"error": f"doctor produced no output (exit {result.returncode})"}

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"doctor output was not JSON: {e}"}

    problems = [
        {
            "name": c.get("name"),
            "status": c.get("status"),
            "detail": _scrub((c.get("detail") or ""))[:200],
        }
        for c in payload.get("checks", [])
        if c.get("status") not in ("ok", None)
    ]
    return {
        "verdict": payload.get("verdict"),
        "problem_count": len(problems),
        "problems": problems,
    }


def collect_semantic(db: Path, today: str) -> dict[str, Any]:
    """Date-bounded semantic search over the BGE index, filtered to GitHub sources.

    source_filter is REQUIRED — see the module docstring. Titles are deduped because the
    index legitimately holds several near-identical chunks of the same document.
    """
    try:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from rebalance.ingest import semantic_index
    except ImportError as e:
        return {"error": f"semantic index unavailable: {e}"}

    try:
        rows = semantic_index.query(
            db,
            SEMANTIC_QUERY,
            top_k=SEMANTIC_TOP_K,
            updated_after=today,
            source_filter=SEMANTIC_SOURCES,
        )
    except Exception as e:  # noqa: BLE001 — any failure degrades this slot, never the run
        return {"error": f"semantic query failed: {e}"}

    seen: set[str] = set()
    hits: list[dict[str, Any]] = []
    for r in rows:
        title = (r.get("title") or r.get("source_id") or "").strip()
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        hits.append({"title": title[:160], "source_type": r.get("source_type")})

    return {"query": SEMANTIC_QUERY, "sources": SEMANTIC_SOURCES, "hits": hits}


def build_facts(db: Path, now: datetime) -> dict[str, Any]:
    today = now.strftime("%Y-%m-%d")
    return {
        "date": today,
        "generated_at": now.isoformat(timespec="seconds"),
        "window": "midnight to now, local time",
        "github": collect_github(db, today),
        "health": collect_health(),
        "semantic": collect_semantic(db, today),
    }


# --- Synthesis -----------------------------------------------------------------


def synthesize(facts: dict[str, Any]) -> str | None:
    """Gemini-only. Returns None if unavailable or failed — the caller then writes nothing.

    NO fallback model. A degraded summary posted to a team channel is worse than silence,
    because nobody can tell it apart from a good one.
    """
    if os.environ.get(LLM_DISABLE_ENV) == "1":
        log(f"SKIP: {LLM_DISABLE_ENV}=1 — refusing to synthesize.")
        return None

    try:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from rebalance.ingest.config import get_gemini_api_key
        from rebalance.ingest.querier import _synthesize_gemini
    except ImportError as e:
        log(f"SKIP: rebalance package not importable ({e}).")
        return None

    key = get_gemini_api_key()
    if not key:
        log("SKIP: no Gemini API key — refusing to write a fallback summary.")
        return None

    prompt = PROMPT_TEMPLATE.format(data=json.dumps(facts, indent=2, default=str))
    try:
        return _synthesize_gemini(prompt, api_key=key, thinking_budget=0, max_tokens=2048)
    except Exception as e:  # noqa: BLE001 — any failure means skip, never fall back
        log(f"SKIP: Gemini synthesis failed ({e}) — nothing written.")
        return None


# --- Render and publish --------------------------------------------------------


def render(summary: str, facts: dict[str, Any], now: datetime) -> str:
    """The published markdown. generated_at is rendered, not just stored — see docstring."""
    gh = facts.get("github", {})
    counts = []
    if "error" not in gh:
        counts.append(f"{len(gh.get('commits', []))} commits")
        counts.append(f"{len(gh.get('merged', []))} merged")
        counts.append(f"{len(gh.get('by_repo', []))} active repos")
    health = facts.get("health", {})
    if "error" not in health and health.get("problem_count"):
        counts.append(f"{health['problem_count']} health warnings")

    footer = " · ".join(counts) if counts else "no deterministic counts available"

    return (
        f"# Progress digest — {facts['date']}\n\n"
        f"_Generated {now:%Y-%m-%d %H:%M %Z}. Covers midnight to now._\n\n"
        f"{summary.strip()}\n\n"
        f"---\n"
        f"{footer}\n"
    )


def publish(content: str, now: datetime, slot: str, *, dry_run: bool, push: bool) -> dict[str, Any]:
    try:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from rebalance.ingest.config import get_pulse_config
        from rebalance.ingest.pulse import _commit_and_push_if_changed
    except ImportError as e:
        return {"ok": False, "reason": f"rebalance package not importable: {e}"}

    target_path = get_pulse_config().get("pulse_target_path")
    if not target_path:
        return {"ok": False, "reason": "pulse_target_path is not configured"}

    target_repo = Path(target_path).expanduser().resolve()
    if not (target_repo / ".git").exists():
        return {"ok": False, "reason": f"pulse_target_path is not a git repo: {target_repo}"}

    file_rel = f"{DEFAULT_SUBDIR}/hiqs-{now:%Y-%m-%d}-{slot}.md"

    if dry_run:
        log(f"DRY RUN — would write {file_rel} in the pulse repo:")
        print("-" * 72)
        print(content, end="")
        print("-" * 72)
        return {"ok": True, "dry_run": True, "file_rel": file_rel}

    result = _commit_and_push_if_changed(
        target_repo=target_repo,
        file_rel=file_rel,
        new_content=content,
        push=push,
        commit_message=f"hiqs-digest: {now:%Y-%m-%d} {slot}",
    )
    log(f"publish ({file_rel}): {result}")
    return {"ok": True, "file_rel": file_rel, **result}


# --- Orchestration -------------------------------------------------------------


def run(
    *,
    dry_run: bool = False,
    facts_only: bool = False,
    slot: str | None = None,
    push: bool = True,
    now: datetime | None = None,
) -> int:
    now = now or datetime.now().astimezone()
    slot = slot or now.strftime("%H%M")
    db = _db_path()

    if not db.exists():
        log(f"FATAL: database not found at {_scrub(str(db))}")
        return 1

    facts = build_facts(db, now)

    for name in ("github", "health", "semantic"):
        err = facts[name].get("error")
        if err:
            log(f"WARN: {err}")

    if facts_only:
        print(json.dumps(facts, indent=2, default=str))
        return 0

    # Every collector failing means there is nothing to summarize. Say so and exit
    # non-zero so the wrapper records job_failed, rather than publishing an empty digest.
    if all(facts[n].get("error") for n in ("github", "health", "semantic")):
        log("FATAL: every collector failed — nothing to publish.")
        return 1

    summary = synthesize(facts)
    if summary is None:
        log("Nothing written (no synthesis).")
        return 1

    result = publish(render(summary, facts, now), now, slot, dry_run=dry_run, push=push)
    if not result.get("ok"):
        log(f"FATAL: publish failed — {result.get('reason')}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="print the digest; write nothing")
    parser.add_argument("--facts-only", action="store_true", help="print collected facts as JSON; no LLM call")
    parser.add_argument("--slot", help="slot label for the filename (default: local HHMM)")
    parser.add_argument("--no-push", action="store_true", help="commit locally but do not push")
    args = parser.parse_args()
    return run(
        dry_run=args.dry_run,
        facts_only=args.facts_only,
        slot=args.slot,
        push=not args.no_push,
    )


if __name__ == "__main__":
    sys.exit(main())

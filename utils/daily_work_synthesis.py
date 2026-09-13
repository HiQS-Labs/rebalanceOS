#!/usr/bin/env python3
"""Opt-in Terra Low canary for the established 15-minute /daily contract (GH-210)."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from rebalance.lib.redaction import redact_key_shaped_secrets
from rebalance.paths import resolve_clio_prompt_log_path, resolve_database_path, resolve_project_root
from rebalance.lib.time_ops import now_utc, parse_iso, to_local


ROOT = resolve_project_root(Path(__file__))
SCHEMA = Path(__file__).with_suffix(".schema.json")
DEFAULT_CONFIG = ROOT / "temp" / "daily-work-synthesis.json"
REQUIRED_TEXT = ("focus", "velocity", "operational_horizon", "coaching_nudge", "coaching_trigger")
AUTH_RE = re.compile(r"(?i)\bauthorization\s*[:=]\s*(?:(?:bearer|basic|token)\s+)?[^\s,;]+")
LABELED_SECRET_RE = re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
ENTRY_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2}) .*?\] — Synthesis \(Cycle (\d+)\)", re.M)

# Dated list-price estimate only; Codex CLI does not expose billed cost.
PRICE_SOURCE_DATE = "2026-09-12"
PRICE_SOURCE = "https://developers.openai.com/api/docs/models/gpt-5.6-terra"
INPUT_PER_M = 2.00
CACHED_INPUT_PER_M = 0.20
OUTPUT_PER_M = 12.00


class TerraCallError(RuntimeError):
    """Invocation failure that preserves any provider usage already reported."""

    def __init__(self, message: str, usage: dict[str, int] | None = None, elapsed: float = 0.0):
        super().__init__(message)
        self.usage = usage or {}
        self.elapsed = elapsed


def default_config() -> dict[str, Any]:
    return {
        "enabled": False,
        "codex_executable": "codex",
        "model": "gpt-5.6-terra",
        "reasoning_effort": "low",
        "timeout_seconds": 120,
        "max_calls_per_day": 72,
        "max_estimated_cost_usd_per_day": 4.0,
        "reservation_usd_per_call": 0.06,
        "max_input_tokens_per_call": 50000,
        "max_output_tokens_per_call": 2000,
        "consecutive_failures_limit": 3,
        "max_packet_chars": 30000,
        "active_hour_start": 6,
        "active_hour_end": 23,
    }


def load_config(path: Path) -> dict[str, Any]:
    cfg = default_config()
    if path.exists():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("config must be a JSON object")
        cfg.update(loaded)
    return cfg


def scrub(value: Any, limit: int = 320) -> str:
    text = " ".join(str(value or "").split())
    text = AUTH_RE.sub("authorization=[REDACTED]", text)
    text = LABELED_SECRET_RE.sub(r"\1=[REDACTED]", text)
    text = redact_key_shaped_secrets(text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    return text[:limit]


def recent_prompt_rows(cutoff: datetime, limit: int = 16) -> list[dict[str, Any]]:
    """Read the live CLIO JSONL tail without mutating the persisted index."""
    path = resolve_clio_prompt_log_path()
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - 512_000))
            raw = handle.read().decode("utf-8", errors="ignore")
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in reversed(raw.splitlines()):
        try:
            row = json.loads(line)
            stamp = parse_iso(row.get("timestamp"))
            if stamp is None:
                continue
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if stamp < cutoff.astimezone(stamp.tzinfo):
            break
        if row.get("prompt"):
            rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def collect_packet(db_path: Path, now: datetime, log_dir: Path) -> dict[str, Any]:
    cutoff_dt = now.astimezone() - timedelta(hours=2)
    cutoff = cutoff_dt.isoformat()
    evidence: list[dict[str, Any]] = []

    rows: list[Any] = recent_prompt_rows(cutoff_dt)
    if not rows:
        try:
            from rebalance.ingest.clio import load_recent_clio_prompts

            rows = load_recent_clio_prompts(db_path, cutoff, limit=16)
        except Exception:
            rows = []
    for index, row in enumerate(rows):
        try:
            row_id = row.get("id") if isinstance(row, dict) else row["id"]
            evidence.append(
                {
                    "id": f"clio:{row_id or index}",
                    "kind": "intent",
                    "attested": False,
                    "observed_at": row["timestamp"],
                    "agent": scrub(row["agent"], 40),
                    "repo": scrub(row["repo"], 100),
                    "text": scrub(row["prompt"]),
                }
            )
        except (KeyError, TypeError):
            continue

    try:
        from rebalance.ingest.next_actions import load_ranked_next_actions

        ranked = load_ranked_next_actions(db_path)
        for action in ranked.ranked[:6] if ranked else []:
            evidence.append(
                {
                    "id": f"next:{action.rank}",
                    "kind": "ranked_next_action",
                    "attested": False,
                    "observed_at": ranked.computed_at,
                    "repo": scrub(action.project, 100),
                    "text": scrub(f"{action.title} — {action.why}"),
                }
            )
    except Exception:
        pass

    try:
        from rebalance.ingest.calendar import get_upcoming_events

        for event in get_upcoming_events(db_path, days_forward=1)[:8]:
            evidence.append(
                {
                    "id": f"calendar:{event.get('id', len(evidence))}",
                    "kind": "calendar",
                    "attested": True,
                    "observed_at": event.get("start_time"),
                    "text": scrub(event.get("summary")),
                }
            )
    except Exception:
        pass

    try:
        from rebalance.ingest.sleuth_grouping import grouped_reminders_from_db

        reminders = [r for group in grouped_reminders_from_db(db_path) for r in group.reminders]
        for reminder in reminders[:8]:
            evidence.append(
                {
                    "id": f"sleuth:{reminder.get('reminder_id')}",
                    "kind": "reminder",
                    "attested": True,
                    "observed_at": reminder.get("should_post_on"),
                    "text": scrub(reminder.get("task_text")),
                }
            )
    except Exception:
        pass

    try:
        from rebalance.ingest.apple_reminders import list_apple_reminders

        for reminder in list_apple_reminders(db_path, limit=8):
            evidence.append(
                {
                    "id": f"apple:{reminder.get('reminder_id')}",
                    "kind": "reminder",
                    "attested": True,
                    "observed_at": reminder.get("due_at"),
                    "text": scrub(reminder.get("title")),
                }
            )
    except Exception:
        pass

    loops_raw = _scanner_json("scan_unclosed_loops.py", ["--json", "--no-ledger-write"])
    cpu_raw = _scanner_json(
        "scan_runaway_cpu.py",
        ["--json", "--state-path", str(log_dir / "cpu-watch.json"), "--update-state"],
    )
    today_path = log_dir / f"{now:%Y-%m-%d}.log"
    previous_full = _tail(today_path, 2_000_000)
    previous = previous_full[-6000:]
    yesterday = _tail(log_dir / f"{now - timedelta(days=1):%Y-%m-%d}.log", 4000)
    loops = {
        "summary_line": loops_raw.get("summary_line", "scanner unavailable"),
        "counts": loops_raw.get("counts", {}),
    }
    cpu = {"summary_line": cpu_raw.get("summary_line", "scanner unavailable")}
    packet = {
        "contract": "daily-work-evidence-v1",
        "generated_at": now.isoformat(),
        "window_start": cutoff,
        "evidence": evidence,
        "unclosed_loops": loops or {"summary_line": "scanner unavailable", "counts": {}},
        "cpu_health": cpu or {"summary_line": "scanner unavailable"},
        "prior_daily_log": scrub(previous, 6000),
        "yesterday_log": scrub(yesterday, 4000),
        "first_cycle_today": not bool(ENTRY_RE.search(previous_full)),
        "first_cycle_monday": now.weekday() == 0 and "Weekly Operational Horizon" not in previous_full,
    }
    return packet


def _scanner_json(name: str, args: list[str]) -> dict[str, Any]:
    script = ROOT / ".agents" / "skills" / "daily" / "scripts" / name
    try:
        completed = subprocess.run(
            [os.environ.get("PYTHON", "python3"), str(script), *args],
            text=True,
            capture_output=True,
            timeout=45,
            cwd=ROOT,
        )
        return json.loads(completed.stdout) if completed.returncode == 0 else {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {}


def _tail(path: Path, chars: int) -> str:
    try:
        return path.read_text(encoding="utf-8")[-chars:]
    except OSError:
        return ""


def build_prompt(packet: dict[str, Any]) -> str:
    return (
        "Synthesize the supplied evidence packet into the established Rebalance /daily fields. "
        "Do not call tools or inspect files. Recent prompt/intent records may establish an apparent "
        "current focus and trajectory, but they are not proof of execution or completion; label those "
        "inferences accordingly. Ground every factual claim in supplied evidence IDs. Abstain only "
        "when neither recent intent nor attested evidence supports a focus. Keep each prose field "
        "concise. Velocity must begin Nominal, High, or Very High. "
        "Use exactly two trajectory bullets. Coaching trigger must be a falsifiable telemetry fact, "
        "not generic advice. Set yesterday_arc only when first_cycle_today is true and weekly_horizon "
        "only when first_cycle_monday is true; otherwise use null. Return JSON only. PACKET="
        + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
    )


def invoke_terra(prompt: str, cfg: dict[str, Any]) -> tuple[str, dict[str, int], float]:
    with tempfile.TemporaryDirectory(prefix="rebalance-daily-terra-") as workspace:
        command = [
            str(cfg["codex_executable"]),
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            "read-only",
            "--cd",
            workspace,
            "--model",
            str(cfg["model"]),
            "-c",
            f'model_reasoning_effort="{cfg["reasoning_effort"]}"',
            "--output-schema",
            str(SCHEMA),
            "--json",
            prompt,
        ]
        started = time.monotonic()
        completed = subprocess.run(command, text=True, capture_output=True, timeout=int(cfg["timeout_seconds"]))
        elapsed = round(time.monotonic() - started, 3)
    output = ""
    usage: dict[str, int] = {}
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "agent_message":
            output = event.get("text", "")
        if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message":
            output = event["item"].get("text", "")
        if event.get("type") == "turn.completed":
            usage = event.get("usage") or {}
    if completed.returncode:
        raise TerraCallError(f"codex exit {completed.returncode}: {completed.stderr[-300:]}", usage, elapsed)
    if not usage:
        raise TerraCallError("missing usage receipt", elapsed=elapsed)
    if not output:
        raise TerraCallError("missing structured output", usage, elapsed)
    return output, usage, elapsed


def validate_result(result: dict[str, Any], packet: dict[str, Any]) -> None:
    if not isinstance(result, dict):
        raise ValueError("result is not an object")
    for key in REQUIRED_TEXT:
        if not isinstance(result.get(key), str) or not result[key].strip():
            raise ValueError(f"missing {key}")
    if not isinstance(result.get("trajectory"), list) or len(result["trajectory"]) != 2:
        raise ValueError("trajectory must contain exactly two items")
    if not result["velocity"].startswith(("Nominal", "High", "Very High")):
        raise ValueError("velocity must begin with an allowed rating")
    known = {row["id"] for row in packet["evidence"]}
    cited = result.get("evidence_ids")
    if not isinstance(cited, list) or any(item not in known for item in cited):
        raise ValueError("unknown evidence id")
    if not result.get("abstain") and not cited:
        raise ValueError("non-abstaining result must cite evidence")
    if packet["first_cycle_today"] != bool(result.get("yesterday_arc")):
        raise ValueError("yesterday_arc cadence mismatch")
    if packet["first_cycle_monday"] != bool(result.get("weekly_horizon")):
        raise ValueError("weekly_horizon cadence mismatch")


def estimated_cost(usage: dict[str, int]) -> float:
    total = int(usage.get("input_tokens", 0))
    cached = int(usage.get("cached_input_tokens", 0))
    # Conservatively charge separately reported reasoning tokens again. Codex's
    # receipt does not establish whether they are a subset of output_tokens.
    output = int(usage.get("output_tokens", 0)) + int(usage.get("reasoning_output_tokens", 0))
    uncached = max(0, total - cached)
    return (uncached * INPUT_PER_M + cached * CACHED_INPUT_PER_M + output * OUTPUT_PER_M) / 1_000_000


def render(
    result: dict[str, Any],
    packet: dict[str, Any],
    now: datetime,
    cycle: int,
    usage: dict[str, int],
    cost: float,
    elapsed: float,
    cfg: dict[str, Any],
) -> str:
    start = now - timedelta(hours=2)
    loops = packet["unclosed_loops"].get("summary_line", "- **Unclosed Loops**: scanner unavailable")
    cpu = packet["cpu_health"].get("summary_line", "- **Machine CPU Health**: scanner unavailable")
    lines = [f"## [{now:%Y-%m-%d %H:%M %Z}] — Synthesis (Cycle {cycle})"]
    if result.get("yesterday_arc"):
        lines.append(f"- **🌅 Yesterday's Arc**: {result['yesterday_arc']}")
    if result.get("weekly_horizon"):
        lines.append(f"- **📅 Weekly Operational Horizon**: {result['weekly_horizon']}")
    lines.extend(
        [
            f"- **Focus**: {result['focus']}",
            f"- **Trajectory (2-Hour Window: {start:%H:%M} – {now:%H:%M %Z})**:",
            f"  - {result['trajectory'][0]}",
            f"  - {result['trajectory'][1]}",
            f"- **Velocity**: {result['velocity']}",
            f"- **Operational Horizon**: {result['operational_horizon']}",
            loops,
            cpu,
            f"- **Coaching Nudge**: {result['coaching_nudge']} `[Trigger: {result['coaching_trigger']}]`",
            f"- **Model Receipt**: `{cfg['model']}` / `{cfg['reasoning_effort']}`; "
            f"{usage.get('input_tokens', 0):,} input ({usage.get('cached_input_tokens', 0):,} cached), "
            f"{usage.get('output_tokens', 0):,} output; {elapsed:.2f}s; "
            f"estimated ${cost:.4f} at {PRICE_SOURCE_DATE} list price (not billed cost); "
            f"confidence {float(result.get('confidence', 0)):.2f}; evidence {', '.join(result.get('evidence_ids') or ['none'])}",
        ]
    )
    return "\n".join(lines) + "\n"


def read_receipts(path: Path) -> list[dict[str, Any]]:
    rows = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def run(config_path: Path, *, force: bool = False, dry_run: bool = False, now: datetime | None = None) -> int:
    now = now or to_local(now_utc())
    cfg = load_config(config_path)
    if not cfg["enabled"] and not force:
        print("daily work synthesis disabled")
        return 0
    if not force and not int(cfg["active_hour_start"]) <= now.hour <= int(cfg["active_hour_end"]):
        print("daily work synthesis outside active hours")
        return 0
    log_dir = ROOT / "temp" / "daily-log"
    receipt_path = log_dir / "terra-receipts" / f"{now:%Y-%m-%d}.jsonl"
    receipts = read_receipts(receipt_path)
    spent = sum(float(r.get("estimated_cost_usd", 0)) for r in receipts)
    failures = 0
    for row in reversed(receipts):
        if row.get("status") == "accepted":
            break
        failures += 1
    reason = None
    if len(receipts) >= int(cfg["max_calls_per_day"]):
        reason = "daily call budget exhausted"
    elif spent + float(cfg["reservation_usd_per_call"]) > float(cfg["max_estimated_cost_usd_per_day"]):
        reason = "daily estimated-cost budget exhausted"
    elif failures >= int(cfg["consecutive_failures_limit"]):
        reason = "failure circuit breaker open"
    if reason and not force:
        print(reason)
        return 0

    packet = collect_packet(resolve_database_path(), now, log_dir)
    encoded = json.dumps(packet, ensure_ascii=False)
    if len(encoded) > int(cfg["max_packet_chars"]):
        packet["evidence"] = packet["evidence"][:8]
        packet["prior_daily_log"] = packet["prior_daily_log"][-2000:]
        encoded = json.dumps(packet, ensure_ascii=False)
    if len(encoded) > int(cfg["max_packet_chars"]):
        append_jsonl(receipt_path, {"at": now.isoformat(), "status": "rejected", "reason": "packet ceiling"})
        return 1
    if dry_run:
        print(json.dumps({"evidence_count": len(packet["evidence"]), "packet_chars": len(encoded)}))
        return 0

    usage: dict[str, int] = {}
    elapsed = 0.0
    try:
        raw_output, usage, elapsed = invoke_terra(build_prompt(packet), cfg)
        result = json.loads(raw_output)
        validate_result(result, packet)
        if int(usage.get("input_tokens", 0)) > int(cfg["max_input_tokens_per_call"]):
            raise ValueError("input token ceiling exceeded")
        if int(usage.get("output_tokens", 0)) > int(cfg["max_output_tokens_per_call"]):
            raise ValueError("output token ceiling exceeded")
        cost = estimated_cost(usage)
        daily_path = log_dir / f"{now:%Y-%m-%d}.log"
        daily_path.parent.mkdir(parents=True, exist_ok=True)
        with daily_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            handle.seek(0)
            current = handle.read()
            if f"## [{now:%Y-%m-%d %H:%M %Z}]" in current:
                raise ValueError("cycle already appended")
            cycles = [int(n) for day, n in ENTRY_RE.findall(current) if day == f"{now:%Y-%m-%d}"]
            cycle = max(cycles, default=0) + 1
            entry = render(result, packet, now, cycle, usage, cost, elapsed, cfg)
            if not current:
                handle.write(f"# Daily Activity Log — {now:%Y-%m-%d}\n\n")
            elif not current.endswith("\n\n"):
                handle.write("\n")
            handle.write(entry + "\n")
        append_jsonl(
            receipt_path,
            {
                "at": now.isoformat(),
                "status": "accepted",
                "model": cfg["model"],
                "reasoning_effort": cfg["reasoning_effort"],
                "usage": usage,
                "estimated_cost_usd": round(cost, 8),
                "price_source": PRICE_SOURCE,
                "price_source_date": PRICE_SOURCE_DATE,
                "elapsed_seconds": elapsed,
                "evidence_count": len(packet["evidence"]),
                "cycle": cycle,
            },
        )
        print(f"accepted cycle {cycle}; estimated ${cost:.4f}")
        return 0
    except Exception as exc:
        if isinstance(exc, TerraCallError):
            usage = exc.usage
            elapsed = exc.elapsed
        rejected = {
            "at": now.isoformat(),
            "status": "rejected",
            "model": cfg["model"],
            "reasoning_effort": cfg["reasoning_effort"],
            "reason": scrub(exc, 500),
        }
        if usage:
            rejected.update(
                {
                    "usage": usage,
                    "estimated_cost_usd": round(estimated_cost(usage), 8),
                    "price_source": PRICE_SOURCE,
                    "price_source_date": PRICE_SOURCE_DATE,
                    "elapsed_seconds": elapsed,
                }
            )
        append_jsonl(receipt_path, rejected)
        print(f"daily work synthesis rejected: {scrub(exc, 300)}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return run(args.config, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())

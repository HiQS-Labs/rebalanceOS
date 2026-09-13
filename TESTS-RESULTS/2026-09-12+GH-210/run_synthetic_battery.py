#!/usr/bin/env python3
"""Run the GH-210 synthetic battery through isolated Terra and Muse CLIs."""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "p0-capability-schema.json"
MUSE = Path.home() / ".local/bin/muse"


def tail_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return (value or "")[-1000:]


def prompt_for(case: dict) -> str:
    evidence = json.dumps(case["evidence"], separators=(",", ":"))
    return (
        "Do not call tools or inspect files. Classify only the synthetic evidence below. "
        "Return only one JSON object with exactly these fields: primary_repo, phase, "
        "confidence, evidence_ids, abstain. phase must be planning, implementation, "
        "verification, or blocked; confidence must be 0 through 1. Cite only supplied "
        "evidence IDs. Use primary_repo unknown and abstain true when current primary "
        "focus is not supportable. Prompt-stated intent alone is not attested activity. "
        f"EVIDENCE={evidence}"
    )


def run(case: dict, engine: str, effort: str) -> dict:
    prompt = prompt_for(case)
    with tempfile.TemporaryDirectory(prefix=f"gh210-{engine}-{effort}-") as workspace:
        if engine == "terra":
            command = [
                "codex",
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
                "gpt-5.6-terra",
                "-c",
                f'model_reasoning_effort="{effort}"',
                "--output-schema",
                str(SCHEMA),
                "--json",
                prompt,
            ]
        else:
            command = [
                str(MUSE),
                "exec",
                "--json",
                "--no-session-log",
                "--disable-web-tools",
                "--no-foreign-personal-context",
                "--approval-mode",
                "never",
                "--approval-judge",
                "off",
                "--disable-write",
                "--disable-shell",
                "--no-parallel-tool-calls",
                "--max-model-steps",
                "1",
                "--workspace",
                workspace,
                "--model",
                "muse-spark-1.3",
                "--reasoning-effort",
                effort,
                prompt,
            ]
        started = time.monotonic()
        try:
            completed = subprocess.run(command, text=True, capture_output=True, timeout=60)
            elapsed = time.monotonic() - started
        except subprocess.TimeoutExpired as exc:
            return {
                "case_id": case["id"],
                "engine": engine,
                "effort": effort,
                "elapsed_seconds": 60.0,
                "exit_code": 124,
                "error": "timeout",
                "stdout_tail": tail_text(exc.stdout),
            }

    result = {
        "case_id": case["id"],
        "engine": engine,
        "effort": effort,
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": completed.returncode,
    }
    text_parts: list[str] = []
    for line in completed.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if engine == "terra":
            if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message":
                text_parts = [event["item"]["text"]]
            if event.get("type") == "turn.completed":
                result["usage"] = event.get("usage", {})
        else:
            payload = event.get("payload", {})
            if event.get("payload_type") == "run.terminal.completed":
                text_parts = [payload.get("text", "")]
            if event.get("payload_type") == "run.model.configured":
                result["returned_model"] = payload.get("model_id")
            status = payload.get("event", {})
            facets = status.get("details", {}).get("facets", [])
            for facet in facets:
                producer = facet.get("detail", {})
                if producer.get("request_id"):
                    result["request_id"] = producer["request_id"]
                    result["response_id"] = producer.get("response_id")
    raw = "".join(text_parts).strip()
    try:
        result["output"] = json.loads(raw)
    except json.JSONDecodeError:
        result["error"] = "invalid_json"
        result["raw_output"] = raw[-1000:]
    if completed.returncode and "error" not in result:
        result["error"] = "nonzero_exit"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    battery = json.loads((ROOT / "synthetic-battery.json").read_text())
    jobs = [
        (case, engine, effort)
        for engine in ("terra", "muse")
        for effort in ("low", "medium")
        for case in battery["cases"]
    ]
    random.Random(210).shuffle(jobs)
    args.output.write_text("")
    succeeded = True
    for case, engine, effort in jobs:
        row = run(case, engine, effort)
        with args.output.open("a") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
        print(
            json.dumps({key: row.get(key) for key in ("case_id", "engine", "effort", "exit_code", "error")}), flush=True
        )
        succeeded &= row.get("exit_code") == 0 and "output" in row
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())

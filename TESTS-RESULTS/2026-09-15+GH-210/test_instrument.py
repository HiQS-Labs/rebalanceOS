#!/usr/bin/env python3
"""Witness that the GH-210 scorer turns red for one deliberately corrupted result."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch

from run_comparison import parse_flash, parse_terra, run_one, sanitize_raw_text, valid_output


ROOT = Path(__file__).resolve().parent


def score(rows: list[dict], directory: Path, label: str) -> dict:
    primitive = directory / f"{label}.jsonl"
    summary = directory / f"{label}-summary.json"
    mismatches = directory / f"{label}-mismatches.jsonl"
    primitive.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )
    subprocess.run(
        [
            sys.executable, str(ROOT / "score_comparison.py"), "--input", str(primitive),
            "--output", str(summary), "--mismatches", str(mismatches),
        ],
        check=True,
        text=True,
        stdout=subprocess.DEVNULL,
    )
    return json.loads(summary.read_text(encoding="utf-8"))


def main() -> int:
    battery = json.loads((ROOT / "battery.json").read_text(encoding="utf-8"))
    battery_hash = hashlib.sha256((ROOT / "battery.json").read_bytes()).hexdigest()
    schema_hash = hashlib.sha256((ROOT / "schema.json").read_bytes()).hexdigest()
    rows = []
    sequence = 0
    for case in battery["cases"]:
        for arm in ("terra-low", "flash-low"):
            for attempt in (1, 2):
                sequence += 1
                rows.append(
                    {
                        "schema_version": 1,
                        "run_id": f"instrument-{case['id']}-{arm}-{attempt}",
                        "sequence": sequence,
                        "case_id": case["id"],
                        "arm": arm,
                        "attempt": attempt,
                        "exit_code": 0,
                        "wall_seconds": 1.0,
                        "battery_sha256": battery_hash,
                        "schema_sha256": schema_hash,
                        "provider_accepted": True,
                        "contract_valid": True,
                        "usage": {},
                        "output": {
                            key: case["expected"][key]
                            for key in ("project", "state", "completion_claimed", "evidence_ids", "abstain")
                        },
                    }
                )
    with tempfile.TemporaryDirectory(prefix="gh210-instrument-") as raw:
        directory = Path(raw)
        green = score(rows, directory, "green")
        corrupted = json.loads(json.dumps(rows))
        target = next(
            row for row in corrupted
            if row["case_id"] == "P01" and row["arm"] == "flash-low" and row["attempt"] == 1
        )
        target["output"]["state"] = "complete"
        target["output"]["completion_claimed"] = True
        red = score(corrupted, directory, "red")
    green_exact = green["arms"]["flash-low"]["strict_exact"]
    red_exact = red["arms"]["flash-low"]["strict_exact"]
    if green_exact != 48 or red_exact != 47:
        raise AssertionError(f"instrument did not constrain: green={green_exact}, red={red_exact}")
    if red["arms"]["flash-low"]["false_completion_claims"] != 1:
        raise AssertionError("corrupted false completion claim was not counted")
    malformed = json.loads(json.dumps(rows))
    malformed_target = next(
        row for row in malformed
        if row["case_id"] == "P01" and row["arm"] == "flash-low" and row["attempt"] == 1
    )
    malformed_target["output"] = []
    malformed_target["provider_accepted"] = False
    malformed_target["contract_valid"] = False
    with tempfile.TemporaryDirectory(prefix="gh210-malformed-") as raw:
        malformed_report = score(malformed, Path(raw), "malformed")
    if malformed_report["arms"]["flash-low"]["contract_valid"] != 47:
        raise AssertionError("malformed output did not fail closed")
    if valid_output([])[0] or valid_output({
        "project": "x", "state": [], "completion_claimed": False,
        "evidence_ids": [], "abstain": False,
    })[0]:
        raise AssertionError("runner validator accepted malformed output")
    flash_row = {}
    parse_flash(json.dumps({
        "status": "SUCCESS", "usage": [1], "structured_output": [],
    }), flash_row)
    if flash_row.get("usage") != {} or flash_row.get("usage_error") != "malformed_usage:list":
        raise AssertionError("Flash parser did not contain malformed usage")
    terra_row = {}
    parse_terra(
        json.dumps({"type": "turn.completed", "usage": "bad"}) + "\n" +
        json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "[]"}}),
        terra_row,
    )
    if terra_row.get("usage") != {} or terra_row.get("usage_error") != "malformed_usage:str":
        raise AssertionError("Terra parser did not contain malformed usage")
    flash_completed = CompletedProcess(
        args=[], returncode=0,
        stdout=json.dumps({"status": "SUCCESS", "usage": [1], "structured_output": []}),
        stderr="",
    )
    terra_completed = CompletedProcess(
        args=[], returncode=0,
        stdout=(
            json.dumps({"type": "turn.completed", "usage": "bad"}) + "\n" +
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "[]"}})
        ),
        stderr="",
    )
    case = battery["cases"][0]
    with patch("run_comparison.subprocess.run", return_value=flash_completed):
        integrated_flash = run_one(case, "flash-low", 1, 1)
    with patch("run_comparison.subprocess.run", return_value=terra_completed):
        integrated_terra = run_one(case, "terra-low", 1, 2)
    if integrated_flash.get("contract_valid") or integrated_terra.get("contract_valid"):
        raise AssertionError("integrated malformed outputs did not fail closed")
    if integrated_flash.get("usage_error") != "malformed_usage:list" or integrated_terra.get("usage_error") != "malformed_usage:str":
        raise AssertionError("integrated malformed usage was not retained")
    array_envelope = CompletedProcess(args=[], returncode=0, stdout="[]", stderr="")
    parse_exception = CompletedProcess(args=[], returncode=0, stdout="not-json", stderr="")
    with patch("run_comparison.subprocess.run", return_value=array_envelope):
        integrated_envelope = run_one(case, "flash-low", 1, 3)
    with patch("run_comparison.subprocess.run", return_value=parse_exception):
        integrated_parse = run_one(case, "flash-low", 1, 4)
    for integrated in (integrated_flash, integrated_terra, integrated_envelope, integrated_parse):
        json.dumps(integrated)
        if "raw_stdout" not in integrated or "raw_stderr" not in integrated:
            raise AssertionError("integrated failure lost complete raw receipt fields")
    sensitive_completed = CompletedProcess(
        args=[], returncode=0,
        stdout=json.dumps({
            "status": "SUCCESS",
            "token": "supersecret",
            "password": "alpha beta",
            "access_token": "access token value",
            "secret": ["containersecret", {"api_key": "escaped\"value"}],
            "response": f"Authorization: Bearer ABC123 {Path.home()}/private",
            "usage": {},
            "structured_output": {
                "project": f"{Path.home()}/project",
                "state": "planning",
                "completion_claimed": False,
                "evidence_ids": ["ev-001"],
                "abstain": False,
            },
        }),
        stderr='{"api_key":"another secret", "token":["stderrcontainer"], "path":"/private/var/tmp/out"}',
    )
    with patch("run_comparison.subprocess.run", return_value=sensitive_completed):
        sanitized_row = run_one(case, "flash-low", 1, 5)
    sanitized_text = json.dumps(sanitized_row, sort_keys=True)
    for forbidden in (
        "supersecret", "alpha beta", "containersecret", "escaped", "ABC123",
        "access token value", "another secret", "stderrcontainer", "/private/var/tmp/out", str(Path.home()),
    ):
        if forbidden in sanitized_text:
            raise AssertionError(f"published row leaked sensitive value/path: {forbidden}")
    raw_probe = sanitize_raw_text(
        '{"password":"space secret", "token":["nested secret"], "path":"' + str(Path.home()) + '/x"}\n'
        'Authorization: Bearer raw-secret\n',
        "",
    )
    for forbidden in ("space secret", "nested secret", "raw-secret", str(Path.home())):
        if forbidden in raw_probe:
            raise AssertionError(f"raw sanitizer leaked {forbidden}")
    multiline_probe = sanitize_raw_text(
        '{\n  "token": [\n    "multiline-container-secret"\n  ],\n  "ok": true\n}\n',
        "",
    )
    if "multiline-container-secret" in multiline_probe:
        raise AssertionError("multiline JSON container secret survived sanitization")
    timeout = TimeoutExpired(
        cmd=["agy"], timeout=45,
        output=b'{\n"token": [\n"timeout-container-secret"\n]\n}',
        stderr=b'Authorization: Bearer timeout-bearer',
    )
    with patch("run_comparison.subprocess.run", side_effect=timeout):
        timeout_row = run_one(case, "flash-low", 1, 6)
    timeout_text = json.dumps(timeout_row, sort_keys=True)
    if "timeout-container-secret" in timeout_text or "timeout-bearer" in timeout_text:
        raise AssertionError("timeout receipt leaked multiline/container credential")
    missing_usage_completed = CompletedProcess(
        args=[], returncode=0,
        stdout=json.dumps({
            "status": "SUCCESS",
            "structured_output": {
                "project": "example/atlas", "state": "planning",
                "completion_claimed": False, "evidence_ids": ["ev-001"], "abstain": False,
            },
        }),
        stderr="",
    )
    with patch("run_comparison.subprocess.run", return_value=missing_usage_completed):
        missing_usage_row = run_one(case, "flash-low", 1, 7)
    if not missing_usage_row.get("usage_missing"):
        raise AssertionError("Flash parser did not preserve explicit missing-usage signal")
    missing_rows = json.loads(json.dumps(rows))
    for index, row in enumerate(missing_rows):
        if (row["case_id"], row["arm"], row["attempt"]) == ("P01", "flash-low", 1):
            missing_rows[index] = missing_usage_row
            break
    with tempfile.TemporaryDirectory(prefix="gh210-missing-usage-") as raw:
        missing_report = score(missing_rows, Path(raw), "missing-usage")
    if missing_report["arms"]["flash-low"]["missing_usage_receipts"] != 1:
        raise AssertionError("scorer did not count parser-reported missing Flash usage")
    bad_usage = {"input_tokens": "bad", "output_tokens": True, "nested": {"x": 1}}
    flash_bad_usage = CompletedProcess(
        args=[], returncode=0,
        stdout=json.dumps({"status": "SUCCESS", "usage": bad_usage, "structured_output": []}),
        stderr="password: tail-secret-value",
    )
    terra_bad_usage = CompletedProcess(
        args=[], returncode=0,
        stdout=(
            json.dumps({"type": "turn.completed", "usage": bad_usage}) + "\n" +
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "[]"}})
        ),
        stderr="",
    )
    with patch("run_comparison.subprocess.run", return_value=flash_bad_usage):
        flash_bad_row = run_one(case, "flash-low", 1, 8)
    with patch("run_comparison.subprocess.run", return_value=terra_bad_usage):
        terra_bad_row = run_one(case, "terra-low", 1, 9)
    for bad_row in (flash_bad_row, terra_bad_row):
        if bad_row.get("usage") != {} or not str(bad_row.get("usage_error", "")).startswith("invalid_usage_values:"):
            raise AssertionError("invalid usage-object values were not rejected and reported")
    if "tail-secret-value" in json.dumps(flash_bad_row):
        raise AssertionError("sanitized diagnostic tail leaked a credential value")
    bad_usage_rows = json.loads(json.dumps(rows))
    bad_replacements = {
        ("P01", "flash-low", 1): flash_bad_row,
        ("P01", "terra-low", 1): terra_bad_row,
    }
    for index, row in enumerate(bad_usage_rows):
        key = (row["case_id"], row["arm"], row["attempt"])
        if key in bad_replacements:
            bad_usage_rows[index] = bad_replacements[key]
    with tempfile.TemporaryDirectory(prefix="gh210-bad-usage-") as raw:
        bad_usage_report = score(bad_usage_rows, Path(raw), "bad-usage")
    for arm in ("flash-low", "terra-low"):
        if bad_usage_report["arms"][arm]["invalid_usage_values"] != 3:
            raise AssertionError(f"{arm} scorer did not report all invalid usage values")
    integrated_rows = json.loads(json.dumps(rows))
    replacements = {
        ("P01", "flash-low", 1): integrated_flash,
        ("P01", "terra-low", 1): integrated_terra,
    }
    for index, row in enumerate(integrated_rows):
        key = (row["case_id"], row["arm"], row["attempt"])
        if key in replacements:
            integrated_rows[index] = replacements[key]
    with tempfile.TemporaryDirectory(prefix="gh210-integrated-") as raw:
        integrated_report = score(integrated_rows, Path(raw), "integrated")
    for arm in ("flash-low", "terra-low"):
        if integrated_report["arms"][arm]["contract_valid"] != 47:
            raise AssertionError(f"{arm} integrated malformed attempt left denominator")
        if integrated_report["arms"][arm]["malformed_usage_receipts"] != 1:
            raise AssertionError(f"{arm} integrated malformed usage was miscounted")
        if integrated_report["decision"]["eligible"][arm]:
            raise AssertionError(f"{arm} remained eligible after malformed integrated attempt")
    print("PASS: perfect fixture scored 48/48; deliberate corruption scored 47/48")
    print("PASS: deliberate false completion claim was counted exactly once")
    print("PASS: malformed output was retained and failed contract validation")
    print("PASS: runner validator rejected array envelopes and non-string states without raising")
    print("PASS: both parsers contained malformed usage receipts without raising")
    print("PASS: mocked end-to-end malformed attempts remained in denominators and failed eligibility")
    print("PASS: malformed envelopes and parsing exceptions retained complete raw receipt fields")
    print("PASS: recursive sanitization removed keyed secrets, bearer values, and local home paths")
    print("PASS: raw JSON/container/whitespace secrets and non-JSON bearer lines were redacted")
    print("PASS: multiline and timeout container secrets were redacted")
    print("PASS: missing Flash usage propagated through runner and scorer")
    print("PASS: invalid string/boolean/nested usage counters were rejected and reported for both arms")
    print("PASS: diagnostic tails derive from sanitized receipts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

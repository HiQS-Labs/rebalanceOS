#!/usr/bin/env python3
"""Deterministically score the frozen GH-210 paired comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
FIELDS = ("project", "state", "completion_claimed", "evidence_ids", "abstain")
ARMS = ("terra-low", "flash-low")


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return round(ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo), 3)


def normalize(field: str, value: Any) -> Any:
    return sorted(value) if field == "evidence_ids" and isinstance(value, list) else value


def evidence_correct(actual: Any, expected: dict[str, Any]) -> bool:
    if not isinstance(actual, list) or not all(isinstance(item, str) for item in actual):
        return False
    actual_set = sorted(actual)
    acceptable = expected.get("acceptable_evidence_sets") or [expected["evidence_ids"]]
    return any(actual_set == sorted(option) for option in acceptable)


def output_signature(row: dict[str, Any]) -> tuple[Any, ...] | None:
    if not row.get("contract_valid") or not isinstance(row.get("output"), dict):
        return None
    output = row["output"]
    return (
        output.get("project"), output.get("state"), output.get("completion_claimed"),
        tuple(sorted(output.get("evidence_ids") or [])), output.get("abstain"),
    )


def wilcoxon_exact(differences: list[float]) -> dict[str, Any]:
    nonzero = [value for value in differences if value != 0]
    if not nonzero:
        return {"n_nonzero": 0, "w_plus": 0.0, "p_two_sided": 1.0, "method": "exact"}
    ranked = sorted(enumerate(abs(value) for value in nonzero), key=lambda item: item[1])
    ranks = [0.0] * len(nonzero)
    cursor = 0
    while cursor < len(ranked):
        end = cursor + 1
        while end < len(ranked) and ranked[end][1] == ranked[cursor][1]:
            end += 1
        avg_rank = ((cursor + 1) + end) / 2
        for index in range(cursor, end):
            ranks[ranked[index][0]] = avg_rank
        cursor = end
    doubled = [int(round(rank * 2)) for rank in ranks]
    observed = sum(rank for rank, value in zip(doubled, nonzero) if value > 0)
    total = sum(doubled)
    counts = {0: 1}
    for rank in doubled:
        next_counts = dict(counts)
        for subtotal, count in counts.items():
            next_counts[subtotal + rank] = next_counts.get(subtotal + rank, 0) + count
        counts = next_counts
    distance = abs(observed - total / 2)
    extreme = sum(count for subtotal, count in counts.items() if abs(subtotal - total / 2) >= distance - 1e-12)
    p_value = extreme / (2 ** len(doubled))
    return {
        "n_nonzero": len(nonzero), "w_plus": observed / 2,
        "p_two_sided": round(min(1.0, p_value), 6), "method": "exact_with_midrank_ties",
    }


def baseline(case: dict[str, Any]) -> dict[str, Any]:
    evidence = sorted(case["evidence"], key=lambda item: item["minutes_ago"])
    current = evidence[0]
    text = current["text"].lower()
    repo = current.get("repo") or "unknown"
    if not current.get("attested") or not repo:
        state = "unknown"
    elif any(token in text for token in ("blocked", "unavailable", "inaccessible", "cannot continue")):
        state = "blocked"
    elif any(token in text for token in ("published", "merged", "deploy completed", "completed and")):
        state = "complete"
    elif any(token in text for token in ("test", "review", "check", "replay")):
        state = "verification"
    elif any(token in text for token in ("edited", "implementation", "source", "commit")):
        state = "implementation"
    else:
        state = "planning"
    abstain = state == "unknown"
    return {
        "project": "unknown" if abstain else repo,
        "state": state,
        "completion_claimed": state == "complete",
        "evidence_ids": [current["id"]],
        "abstain": abstain,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mismatches", type=Path, required=True)
    args = parser.parse_args()
    battery = json.loads((ROOT / "battery.json").read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in battery["cases"]}
    battery_hash = hashlib.sha256((ROOT / "battery.json").read_bytes()).hexdigest()
    schema_hash = hashlib.sha256((ROOT / "schema.json").read_bytes()).hexdigest()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) != 96:
        raise ValueError(f"expected 96 primitive rows, got {len(rows)}")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    per_case_arm: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    seen = set()
    for row in rows:
        if row.get("battery_sha256") != battery_hash or row.get("schema_sha256") != schema_hash:
            raise ValueError(f"frozen input hash mismatch in {row.get('run_id')}")
        key = (row["case_id"], row["arm"], row["attempt"])
        if key in seen:
            raise ValueError(f"duplicate primitive key {key}")
        seen.add(key)
        groups[row["arm"]].append(row)
        per_case_arm[(row["case_id"], row["arm"])].append(row)
    if set(groups) != set(ARMS) or any(len(groups[arm]) != 48 for arm in ARMS):
        raise ValueError({arm: len(group) for arm, group in groups.items()})
    mismatch_rows = []
    report: dict[str, Any] = {
        "schema_version": 1, "battery_id": battery["battery_id"], "primitive_rows": len(rows),
        "attempts_per_case_arm": battery["attempts_per_arm_case"], "arms": {},
    }
    case_scores: dict[str, dict[str, float]] = {arm: {} for arm in ARMS}
    for arm in ARMS:
        counts = defaultdict(int)
        latencies = []
        usage = defaultdict(int)
        for row in groups[arm]:
            expected = cases[row["case_id"]]["expected"]
            actual = row.get("output") if isinstance(row.get("output"), dict) else {}
            field_ok = {
                field: (
                    evidence_correct(actual.get(field), expected)
                    if field == "evidence_ids"
                    else normalize(field, actual.get(field)) == normalize(field, expected[field])
                )
                for field in FIELDS
            }
            exact = bool(row.get("contract_valid")) and all(field_ok.values())
            counts["strict_exact"] += exact
            counts["provider_accepted"] += bool(row.get("provider_accepted"))
            counts["contract_valid"] += bool(row.get("contract_valid"))
            counts["completed_calls"] += row.get("exit_code") == 0
            actual_ids = actual.get("evidence_ids")
            if not isinstance(actual_ids, list):
                actual_ids = []
            counts["unknown_evidence"] += any(
                item not in {ev["id"] for ev in cases[row["case_id"]]["evidence"]}
                for item in actual_ids if isinstance(item, str)
            )
            if expected["state"] != "complete" and actual.get("completion_claimed") is True:
                counts["false_completion_claims"] += 1
            for field, ok in field_ok.items():
                counts[f"field_{field}"] += ok
            if isinstance(row.get("wall_seconds"), (int, float)):
                latencies.append(float(row["wall_seconds"]))
            usage_row = row.get("usage")
            if row.get("usage_error"):
                counts["malformed_usage_receipts"] += 1
                if str(row["usage_error"]).startswith("invalid_usage_values:"):
                    details = str(row["usage_error"]).split(":", 1)[1]
                    counts["invalid_usage_values"] += len([item for item in details.split(",") if item])
            if row.get("usage_missing") or usage_row is None:
                counts["missing_usage_receipts"] += 1
                usage_row = {}
            elif not isinstance(usage_row, dict):
                counts["malformed_usage_receipts"] += 1
                usage_row = {}
            for key, value in usage_row.items():
                if type(value) is int and value >= 0:
                    usage[key] += value
                else:
                    counts["invalid_usage_values"] += 1
            if not exact:
                mismatch_rows.append({
                    "schema_version": 1, "case_id": row["case_id"], "arm": arm,
                    "attempt": row["attempt"], "expected": expected, "actual": actual,
                    "provider_accepted": row.get("provider_accepted"),
                    "contract_valid": row.get("contract_valid"), "error": row.get("error"),
                    "field_correct": field_ok,
                })
        consistent = 0
        for case_id in cases:
            pair = sorted(per_case_arm[(case_id, arm)], key=lambda item: item["attempt"])
            if len(pair) != 2:
                raise ValueError(f"{case_id}/{arm} expected two attempts")
            signatures = [output_signature(item) for item in pair]
            consistent += signatures[0] is not None and signatures[0] == signatures[1]
            counts["paired_failure_cases"] += any(signature is None for signature in signatures)
            expected = cases[case_id]["expected"]
            case_scores[arm][case_id] = statistics.mean(
                bool(item.get("contract_valid")) and all(
                    (
                        evidence_correct((item.get("output") or {}).get(field), expected)
                        if field == "evidence_ids"
                        else normalize(field, (item.get("output") or {}).get(field)) == normalize(field, expected[field])
                    )
                    for field in FIELDS
                )
                for item in pair
            )
        report["arms"][arm] = {
            "attempts": 48,
            "completed_calls": counts["completed_calls"],
            "provider_accepted": counts["provider_accepted"],
            "contract_valid": counts["contract_valid"],
            "malformed_usage_receipts": counts["malformed_usage_receipts"],
            "missing_usage_receipts": counts["missing_usage_receipts"],
            "invalid_usage_values": counts["invalid_usage_values"],
            "strict_exact": counts["strict_exact"],
            "strict_exact_rate": round(counts["strict_exact"] / 48, 6),
            "field_correct": {field: counts[f"field_{field}"] for field in FIELDS},
            "unknown_evidence_ids": counts["unknown_evidence"],
            "false_completion_claims": counts["false_completion_claims"],
            "two_attempt_consistent_cases": consistent,
            "paired_failure_cases": counts["paired_failure_cases"],
            "latency_seconds": {
                "p50": percentile(latencies, 0.50), "p95": percentile(latencies, 0.95),
                "max": round(max(latencies), 3) if latencies else None,
            },
            "usage_totals": dict(sorted(usage.items())),
        }
    differences = [
        case_scores["flash-low"][case_id] - case_scores["terra-low"][case_id]
        for case_id in sorted(cases)
    ]
    mean_delta = statistics.mean(differences)
    paired = wilcoxon_exact(differences)
    paired.update({
        "flash_minus_terra_mean_strict_delta": round(mean_delta, 6),
        "flash_better_cases": sum(value > 0 for value in differences),
        "terra_better_cases": sum(value < 0 for value in differences),
        "tied_cases": sum(value == 0 for value in differences),
    })
    report["paired_strict"] = paired
    baseline_exact = 0
    baseline_fields = defaultdict(int)
    for case in cases.values():
        actual = baseline(case)
        expected = case["expected"]
        field_ok = {
            field: (
                evidence_correct(actual[field], expected)
                if field == "evidence_ids"
                else normalize(field, actual[field]) == normalize(field, expected[field])
            )
            for field in FIELDS
        }
        baseline_exact += all(field_ok.values())
        for field, ok in field_ok.items():
            baseline_fields[field] += ok
    report["deterministic_baseline"] = {
        "cases": 24, "strict_exact": baseline_exact,
        "strict_exact_rate": round(baseline_exact / 24, 6),
        "field_correct": dict(baseline_fields),
    }
    eligible = {
        arm: (
            report["arms"][arm]["provider_accepted"] == 48
            and report["arms"][arm]["contract_valid"] == 48
            and report["arms"][arm]["unknown_evidence_ids"] == 0
            and report["arms"][arm]["false_completion_claims"] == 0
        )
        for arm in ARMS
    }
    quality_winner = None
    if all(eligible.values()) and abs(mean_delta) >= 0.10 and paired["p_two_sided"] < 0.05:
        quality_winner = "flash-low" if mean_delta > 0 else "terra-low"
    p95_terra = report["arms"]["terra-low"]["latency_seconds"]["p95"]
    p95_flash = report["arms"]["flash-low"]["latency_seconds"]["p95"]
    operational_lead = None
    if quality_winner is None and all(eligible.values()) and p95_terra and p95_flash:
        if p95_flash <= p95_terra * 0.75:
            operational_lead = "flash-low"
        elif p95_terra <= p95_flash * 0.75:
            operational_lead = "terra-low"
    report["decision"] = {
        "eligible": eligible, "quality_winner": quality_winner,
        "operational_lead": operational_lead,
        "production_replacement_authorized": False,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with args.mismatches.open("w", encoding="utf-8") as stream:
        for row in mismatch_rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

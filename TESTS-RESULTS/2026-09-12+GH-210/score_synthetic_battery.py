#!/usr/bin/env python3
"""Score the GH-210 synthetic battery and emit aggregate JSON."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parent


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def main() -> int:
    battery = json.loads((ROOT / "synthetic-battery.json").read_text())
    expected = {case["id"]: case["expected"] for case in battery["cases"]}
    schema = json.loads((ROOT / "p0-capability-schema.json").read_text())
    rows = [json.loads(line) for line in (ROOT / "synthetic-results.jsonl").read_text().splitlines() if line]
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["engine"], row["effort"])].append(row)
    if len(rows) != 48 or any(len(group) != 12 for group in groups.values()):
        sizes = {str(key): len(value) for key, value in groups.items()}
        raise ValueError(f"expected 48 rows and four groups of 12, got {len(rows)} / {sizes}")

    report = {"battery_id": battery["battery_id"], "rows": len(rows), "arms": {}}
    dimensions = ("primary_repo", "phase", "abstain")
    for (engine, effort), group in sorted(groups.items()):
        counts = defaultdict(int)
        mismatches = []
        for row in group:
            output = row.get("output", {})
            exp = expected[row["case_id"]]
            try:
                jsonschema.validate(output, schema)
                counts["schema_valid"] += 1
            except jsonschema.ValidationError:
                pass
            for dimension in dimensions:
                counts[dimension] += output.get(dimension) == exp[dimension]
            evidence_match = set(output.get("evidence_ids", [])) == set(exp["evidence_ids"])
            counts["evidence_ids"] += evidence_match
            exact = evidence_match and all(output.get(dimension) == exp[dimension]
                                           for dimension in dimensions)
            counts["exact"] += exact
            abstention_aware = evidence_match and output.get("abstain") == exp["abstain"]
            if exp["abstain"]:
                abstention_aware = abstention_aware and output.get("primary_repo") == "unknown"
            else:
                counts["phase_non_abstain_total"] += 1
                counts["phase_non_abstain"] += output.get("phase") == exp["phase"]
                abstention_aware = (abstention_aware
                                    and output.get("primary_repo") == exp["primary_repo"]
                                    and output.get("phase") == exp["phase"])
            counts["exact_abstention_aware"] += abstention_aware
            if not exact:
                mismatches.append({"case_id": row["case_id"], "expected": exp, "actual": output})
        latency = [row["elapsed_seconds"] for row in group]
        arm = {
            "attempts": len(group),
            "successes": sum(row["exit_code"] == 0 for row in group),
            "schema_valid": counts["schema_valid"],
            "exact": counts["exact"],
            "exact_abstention_aware_posthoc": counts["exact_abstention_aware"],
            "primary_repo_correct": counts["primary_repo"],
            "phase_correct": counts["phase"],
            "phase_correct_non_abstain": counts["phase_non_abstain"],
            "phase_non_abstain_total": counts["phase_non_abstain_total"],
            "abstain_correct": counts["abstain"],
            "evidence_ids_exact": counts["evidence_ids"],
            "latency_seconds": {
                "mean": round(statistics.mean(latency), 3),
                "p50": round(statistics.median(latency), 3),
                "p95_inclusive": round(percentile(latency, 0.95), 3),
                "max": round(max(latency), 3),
            },
            "mismatches": mismatches,
        }
        if engine == "terra":
            usage = [row["usage"] for row in group]
            input_tokens = sum(item.get("input_tokens", 0) for item in usage)
            cached_tokens = sum(item.get("cached_input_tokens", 0) for item in usage)
            output_tokens = sum(item.get("output_tokens", 0) for item in usage)
            reasoning_tokens = sum(item.get("reasoning_output_tokens", 0) for item in usage)
            estimated_cost = ((input_tokens - cached_tokens) * 2.00
                              + cached_tokens * 0.20 + output_tokens * 12.00) / 1_000_000
            arm["tokens"] = {
                "input_total": input_tokens,
                "input_cached": cached_tokens,
                "output": output_tokens,
                "reasoning_output_reported": reasoning_tokens,
            }
            arm["estimated_cost_usd"] = round(estimated_cost, 6)
            arm["estimated_cost_upper_if_reasoning_additional_usd"] = round(
                estimated_cost + reasoning_tokens * 12.00 / 1_000_000, 6)
            arm["cost_method"] = "Official 2026-09-12 list prices; assumes input total includes cached input."
        else:
            arm["tokens"] = "not exposed by Muse CLI JSONL"
            arm["estimated_cost_usd"] = None
            arm["cost_method"] = "not measured; no token or billed-cost receipt"
        report["arms"][f"{engine}-{effort}"] = arm

    for effort in ("low", "medium"):
        terra = report["arms"][f"terra-{effort}"]["tokens"]
        hypothetical_cost = ((terra["input_total"] - terra["input_cached"]) * 1.25
                             + terra["input_cached"] * 0.15
                             + terra["output"] * 4.25) / 1_000_000
        muse = report["arms"][f"muse-{effort}"]
        muse["counterfactual_same_terra_token_volume_usd"] = round(hypothetical_cost, 6)
        muse["counterfactual_cost_caveat"] = (
            "Price-only comparison, not Muse cost: Muse did not expose its token counts."
        )
    (ROOT / "synthetic-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

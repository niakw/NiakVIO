#!/usr/bin/env python3
"""Aggregate per-fixture ARCHI2 A/B comparison reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(args.input.rglob("comparison.json"))
    if not files:
        raise SystemExit("no ARCHI2 A/B comparison reports found")
    rows: list[dict[str, Any]] = [json.loads(path.read_text(encoding="utf-8")) for path in files]

    sums = {
        "baseline_verified_total": sum(int(row["baseline"]["verified_total"]) for row in rows),
        "candidate_verified_total": sum(int(row["candidate"]["verified_total"]) for row in rows),
        "baseline_verified_vf": sum(int(row["baseline"]["verified_vf"]) for row in rows),
        "candidate_verified_vf": sum(int(row["candidate"]["verified_vf"]) for row in rows),
        "baseline_identity_contradictions": sum(len(row["baseline"]["identity_contradiction_provider_ids"]) for row in rows),
        "candidate_identity_contradictions": sum(len(row["candidate"]["identity_contradiction_provider_ids"]) for row in rows),
        "baseline_enabled_compatible": sum(int((row.get("selection") or {}).get("baseline_enabled_compatible") or 0) for row in rows),
        "candidate_enabled_compatible": sum(int((row.get("selection") or {}).get("candidate_enabled_compatible") or 0) for row in rows),
    }
    sums["delta_verified_total"] = sums["candidate_verified_total"] - sums["baseline_verified_total"]
    sums["delta_verified_vf"] = sums["candidate_verified_vf"] - sums["baseline_verified_vf"]
    sums["delta_identity_contradictions"] = sums["candidate_identity_contradictions"] - sums["baseline_identity_contradictions"]
    sums["delta_enabled_compatible"] = sums["candidate_enabled_compatible"] - sums["baseline_enabled_compatible"]

    assessments = {str(row.get("assessment") or "unknown") for row in rows}
    if sums["delta_identity_contradictions"] > 0 or "safety_regression" in assessments:
        overall = "safety_regression"
    elif sums["delta_verified_total"] > 0 and sums["delta_verified_vf"] >= 0:
        overall = "improved"
    elif sums["delta_verified_total"] >= 0 and sums["delta_verified_vf"] > 0:
        overall = "improved"
    elif sums["delta_verified_total"] < 0 or sums["delta_verified_vf"] < 0:
        overall = "coverage_regression"
    elif assessments == {"neutral"}:
        overall = "neutral"
    else:
        overall = "mixed"

    payload = {
        "schema_version": 1,
        "overall_assessment": overall,
        "fixture_count": len(rows),
        "totals": sums,
        "fixtures": [
            {
                "title": (row.get("fixture") or {}).get("title") or (row.get("fixture") or {}).get("tmdbId"),
                "assessment": row.get("assessment"),
                "baseline_verified_total": row["baseline"]["verified_total"],
                "candidate_verified_total": row["candidate"]["verified_total"],
                "delta_verified_total": row["delta"]["verified_total"],
                "baseline_verified_vf": row["baseline"]["verified_vf"],
                "candidate_verified_vf": row["candidate"]["verified_vf"],
                "delta_verified_vf": row["delta"]["verified_vf"],
                "qualified_added": row["delta"]["qualified_added"],
                "qualified_lost": row["delta"]["qualified_lost"],
            }
            for row in rows
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# ARCHI2 A/B corpus audit",
        "",
        f"Overall assessment: **{overall}**",
        "",
        "| Metric | Pre-ARCHI2 | ARCHI2 | Delta |",
        "|---|---:|---:|---:|",
        f"| Enabled-compatible fixture/provider pairs | {sums['baseline_enabled_compatible']} | {sums['candidate_enabled_compatible']} | {sums['delta_enabled_compatible']:+d} |",
        f"| Verified provider/fixture pairs | {sums['baseline_verified_total']} | {sums['candidate_verified_total']} | {sums['delta_verified_total']:+d} |",
        f"| Verified VF provider/fixture pairs | {sums['baseline_verified_vf']} | {sums['candidate_verified_vf']} | {sums['delta_verified_vf']:+d} |",
        f"| Identity contradictions | {sums['baseline_identity_contradictions']} | {sums['candidate_identity_contradictions']} | {sums['delta_identity_contradictions']:+d} |",
        "",
        "| Fixture | Assessment | Verified A→B | VF A→B |",
        "|---|---|---:|---:|",
    ]
    for row in payload["fixtures"]:
        lines.append(
            f"| {row['title']} | {row['assessment']} | {row['baseline_verified_total']}→{row['candidate_verified_total']} ({row['delta_verified_total']:+d}) | "
            f"{row['baseline_verified_vf']}→{row['candidate_verified_vf']} ({row['delta_verified_vf']:+d}) |"
        )
    lines.append("")
    text = "\n".join(lines)
    args.markdown.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

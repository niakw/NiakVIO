#!/usr/bin/env python3
"""Compare two sanitized Nuvio client lab reports produced by one harness."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def provider_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in report.get("providers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def verdict_counts(report: dict[str, Any]) -> dict[str, dict[str, int]]:
    clients = [str(value) for value in report.get("clients") or []]
    output: dict[str, dict[str, int]] = {}
    for client in clients:
        counter: Counter[str] = Counter()
        for provider in report.get("providers") or []:
            row = (provider.get("clients") or {}).get(client) or {}
            counter[str(row.get("verdict") or "missing")] += 1
        output[client] = dict(sorted(counter.items()))
    return output


def metric(report: dict[str, Any], key: str) -> int:
    return int((report.get("policy") or {}).get(key) or 0)


def ids(report: dict[str, Any], key: str) -> list[str]:
    return [str(value) for value in (report.get("policy") or {}).get(key) or []]


def compare(baseline: dict[str, Any], candidate: dict[str, Any], selection: dict[str, Any] | None = None) -> dict[str, Any]:
    baseline_providers = provider_index(baseline)
    candidate_providers = provider_index(candidate)
    baseline_qualified = set(ids(baseline, "qualified_provider_ids"))
    candidate_qualified = set(ids(candidate, "qualified_provider_ids"))
    baseline_vf = set(ids(baseline, "qualified_vf_provider_ids"))
    candidate_vf = set(ids(candidate, "qualified_vf_provider_ids"))
    baseline_bad = set(ids(baseline, "identity_contradiction_provider_ids"))
    candidate_bad = set(ids(candidate, "identity_contradiction_provider_ids"))

    delta_total = metric(candidate, "verified_total") - metric(baseline, "verified_total")
    delta_vf = metric(candidate, "verified_vf") - metric(baseline, "verified_vf")
    delta_identity = metric(candidate, "identity_verified_total") - metric(baseline, "identity_verified_total")
    delta_bad = len(candidate_bad) - len(baseline_bad)

    if delta_bad > 0:
        assessment = "safety_regression"
    elif delta_total > 0 and delta_vf >= 0:
        assessment = "improved"
    elif delta_total >= 0 and delta_vf > 0:
        assessment = "improved"
    elif delta_total < 0 or delta_vf < 0:
        assessment = "coverage_regression"
    elif candidate_qualified != baseline_qualified or candidate_vf != baseline_vf:
        assessment = "mixed"
    else:
        assessment = "neutral"

    return {
        "schema_version": 1,
        "fixture": candidate.get("fixture") or baseline.get("fixture") or {},
        "clients": candidate.get("clients") or baseline.get("clients") or [],
        "assessment": assessment,
        "selection": selection or {},
        "baseline": {
            "verified_total": metric(baseline, "verified_total"),
            "verified_vf": metric(baseline, "verified_vf"),
            "identity_verified_total": metric(baseline, "identity_verified_total"),
            "qualified_provider_ids": sorted(baseline_qualified),
            "qualified_vf_provider_ids": sorted(baseline_vf),
            "identity_contradiction_provider_ids": sorted(baseline_bad),
            "verdict_counts": verdict_counts(baseline),
            "providers_reported": len(baseline_providers),
        },
        "candidate": {
            "verified_total": metric(candidate, "verified_total"),
            "verified_vf": metric(candidate, "verified_vf"),
            "identity_verified_total": metric(candidate, "identity_verified_total"),
            "qualified_provider_ids": sorted(candidate_qualified),
            "qualified_vf_provider_ids": sorted(candidate_vf),
            "identity_contradiction_provider_ids": sorted(candidate_bad),
            "verdict_counts": verdict_counts(candidate),
            "providers_reported": len(candidate_providers),
        },
        "delta": {
            "verified_total": delta_total,
            "verified_vf": delta_vf,
            "identity_verified_total": delta_identity,
            "identity_contradictions": delta_bad,
            "qualified_added": sorted(candidate_qualified - baseline_qualified),
            "qualified_lost": sorted(baseline_qualified - candidate_qualified),
            "vf_added": sorted(candidate_vf - baseline_vf),
            "vf_lost": sorted(baseline_vf - candidate_vf),
            "manifest_enabled_compatible": int((selection or {}).get("candidate_enabled_compatible") or 0)
            - int((selection or {}).get("baseline_enabled_compatible") or 0),
        },
    }


def markdown(report: dict[str, Any]) -> str:
    fixture = report.get("fixture") or {}
    baseline = report["baseline"]
    candidate = report["candidate"]
    delta = report["delta"]
    lines = [
        "# ARCHI2 A/B audit",
        "",
        f"Fixture: **{fixture.get('title') or fixture.get('tmdbId')}**",
        f"Assessment: **{report['assessment']}**",
        "",
        "| Metric | Pre-ARCHI2 | ARCHI2 | Delta |",
        "|---|---:|---:|---:|",
        f"| Enabled compatible providers | {report.get('selection', {}).get('baseline_enabled_compatible', 0)} | {report.get('selection', {}).get('candidate_enabled_compatible', 0)} | {delta['manifest_enabled_compatible']:+d} |",
        f"| Verified providers | {baseline['verified_total']} | {candidate['verified_total']} | {delta['verified_total']:+d} |",
        f"| Verified VF | {baseline['verified_vf']} | {candidate['verified_vf']} | {delta['verified_vf']:+d} |",
        f"| Identity-verified | {baseline['identity_verified_total']} | {candidate['identity_verified_total']} | {delta['identity_verified_total']:+d} |",
        f"| Identity contradictions | {len(baseline['identity_contradiction_provider_ids'])} | {len(candidate['identity_contradiction_provider_ids'])} | {delta['identity_contradictions']:+d} |",
        "",
        f"Qualified added: {', '.join(delta['qualified_added']) or 'none'}",
        f"Qualified lost: {', '.join(delta['qualified_lost']) or 'none'}",
        f"VF added: {', '.join(delta['vf_added']) or 'none'}",
        f"VF lost: {', '.join(delta['vf_lost']) or 'none'}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    baseline = load(args.baseline)
    candidate = load(args.candidate)
    selection = load(args.selection) if args.selection else None
    report = compare(baseline, candidate, selection)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

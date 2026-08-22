#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Report provider IDs newly declared by the three configured live upstreams.

This script is deliberately read-only with respect to published NiakVIO state. It
consumes staging/candidates.json produced by discover_candidates.py and emits a
human-review queue. Snapshot/LKG-only variants never count as a new upstream
provider: a weekly discovery must be observed in a live manifest before review.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def canonical(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def collect_catalog_ids(value: Any, out: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"id", "canonical_id", "providerId", "provider_id"}:
                text = canonical(child)
                if text:
                    out.add(text)
            collect_catalog_ids(child, out)
    elif isinstance(value, list):
        for child in value:
            collect_catalog_ids(child, out)


def known_provider_ids(catalog: dict[str, Any], manifest: dict[str, Any]) -> set[str]:
    known: set[str] = set()
    collect_catalog_ids(catalog, known)
    orders = catalog.get("manifestOrder") or {}
    if isinstance(orders, dict):
        for rows in orders.values():
            if isinstance(rows, list):
                known.update(canonical(row) for row in rows if canonical(row))
    for row in manifest.get("scrapers") or []:
        if isinstance(row, dict):
            provider_id = canonical(row.get("id") or row.get("name"))
            if provider_id:
                known.add(provider_id)
    return known


def score_candidate(variants: list[dict[str, Any]]) -> tuple[int, list[str]]:
    """Small review-priority score; never an activation decision."""
    score = 0
    reasons: list[str] = []
    metadata_rows = [row.get("metadata") for row in variants if isinstance(row.get("metadata"), dict)]
    joined = json.dumps(metadata_rows, ensure_ascii=False).casefold()
    sources = sorted({str(row.get("source") or "") for row in variants if row.get("source")})
    if len(sources) >= 2:
        score += 3
        reasons.append("declared_by_multiple_upstreams")
    if any(token in joined for token in ('"fr"', 'french', 'français', 'francais', 'vostfr', 'truefrench', 'vff')):
        score += 3
        reasons.append("french_signal")
    if any(token in joined for token in ('movie', 'tv', 'anime')):
        score += 2
        reasons.append("useful_media_types")
    if any(token in joined for token in ('2160', '4k', '1080', 'uhd', 'fhd')):
        score += 1
        reasons.append("quality_signal")
    if any(str(meta.get("description") or "").strip() for meta in metadata_rows):
        score += 1
        reasons.append("described_upstream")
    return score, reasons


def build_report(stage: dict[str, Any], catalog: dict[str, Any], manifest: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    configured_sources = set((sources.get("upstreams") or {}).keys())
    known = known_provider_ids(catalog, manifest)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in stage.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        source = str(row.get("source") or "")
        if source not in configured_sources:
            continue
        # Only a provider freshly observed in a live upstream manifest can be new.
        if str(row.get("manifest_origin") or "live") != "live":
            continue
        provider_id = canonical(row.get("canonical_id") or row.get("upstream_id"))
        if provider_id:
            grouped[provider_id].append(row)

    discoveries: list[dict[str, Any]] = []
    for provider_id, variants in grouped.items():
        if provider_id in known:
            continue
        score, reasons = score_candidate(variants)
        sources_seen = sorted({str(row.get("source") or "") for row in variants})
        metadata = next((row.get("metadata") for row in variants if isinstance(row.get("metadata"), dict)), {})
        discoveries.append({
            "canonical_id": provider_id,
            "upstream_ids": sorted({str(row.get("upstream_id") or provider_id) for row in variants}),
            "sources": sources_seen,
            "source_repositories": sorted({str(row.get("source_repository") or "") for row in variants if row.get("source_repository")}),
            "review_score": score,
            "review_reasons": reasons,
            "supported_types": metadata.get("supportedTypes") if isinstance(metadata.get("supportedTypes"), list) else [],
            "content_language": metadata.get("contentLanguage") if isinstance(metadata.get("contentLanguage"), list) else [],
            "description": str(metadata.get("description") or "")[:500],
            "automatic_import_allowed": False,
            "requires_human_review_and_native_proof": True,
        })
    discoveries.sort(key=lambda row: (-int(row["review_score"]), row["canonical_id"]))

    upstream_status = {}
    for key in sorted(configured_sources):
        upstream_status[key] = (stage.get("upstreams") or {}).get(key, {"status": "missing"})

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "weekly_upstream_provider_discovery_review_only",
        "configured_upstreams": sorted(configured_sources),
        "known_provider_count": len(known),
        "live_upstream_provider_count": len(grouped),
        "new_provider_count": len(discoveries),
        "new_providers": discoveries,
        "upstream_status": upstream_status,
        "policy": {
            "automatic_import_allowed": False,
            "automatic_activation_allowed": False,
            "live_manifest_required_for_new_provider": True,
            "p2p_exclusions_inherited_from_discovery": True,
            "native_reader_proof_required_before_future_promotion": True,
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Weekly upstream provider discovery",
        "",
        f"New live providers requiring review: **{report['new_provider_count']}**",
        f"Live upstream canonical providers observed: **{report['live_upstream_provider_count']}**",
        "",
    ]
    for key, status in report.get("upstream_status", {}).items():
        lines.append(f"- `{key}`: `{status.get('status', 'unknown')}`")
    if report.get("new_providers"):
        lines.extend(["", "## Review queue", ""])
        for row in report["new_providers"]:
            sources = ", ".join(row.get("sources") or [])
            reasons = ", ".join(row.get("review_reasons") or []) or "no extra ranking signal"
            lines.append(f"- **{row['canonical_id']}** — score {row['review_score']} — {sources} — {reasons}")
    else:
        lines.extend(["", "No new live upstream provider is absent from the NiakVIO catalog."])
    lines.extend(["", "Review only: this workflow never imports, enables, disables or publishes a provider."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging/candidates.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "provider_catalog.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--sources", type=Path, default=ROOT / "sources.json")
    parser.add_argument("--output", type=Path, default=ROOT / "health-output/weekly-provider-discovery.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "health-output/weekly-provider-discovery.md")
    args = parser.parse_args()

    report = build_report(load(args.stage), load(args.catalog), load(args.manifest), load(args.sources))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(
        "FIELD_WEEKLY_UPSTREAM_PROVIDER_DISCOVERY "
        f"upstreams={len(report['configured_upstreams'])} "
        f"live_providers={report['live_upstream_provider_count']} "
        f"new_providers={report['new_provider_count']} review_only=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Report upstream providers not yet represented in NiakVIO's canonical catalog.

This script is intentionally read-only with respect to provider_catalog.json,
manifest.json and providers/. It consumes an already staged discovery transaction,
compares only the three configured upstream sources against the canonical catalog,
and writes review artifacts. No candidate is imported, enabled or published here.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def norm(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for raw in value:
        item = str(raw or "").strip()
        if item and item not in out:
            out.append(item)
    return out


def interest(candidate: dict[str, Any]) -> tuple[int, list[str]]:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    canonical = candidate.get("canonical_metadata") if isinstance(candidate.get("canonical_metadata"), dict) else {}
    languages = {norm(v) for v in [*string_list(metadata.get("contentLanguage")), *string_list(canonical.get("contentLanguage"))]}
    types = {norm(v) for v in [*string_list(metadata.get("supportedTypes")), *string_list(canonical.get("supportedTypes"))]}
    formats = {norm(v) for v in [*string_list(metadata.get("formats")), *string_list(canonical.get("formats"))]}
    score = 0
    reasons: list[str] = []
    if "fr" in languages:
        score += 50
        reasons.append("French-capable")
    if "en" in languages:
        score += 10
        reasons.append("English-capable")
    media = sorted(types & {"movie", "tv", "anime"})
    if media:
        score += 10 * len(media)
        reasons.append("media=" + ",".join(media))
    direct_formats = sorted(formats & {"m3u8", "hls", "mp4", "mkv", "mpd", "dash"})
    if direct_formats:
        score += min(20, 5 * len(direct_formats))
        reasons.append("formats=" + ",".join(direct_formats))
    if metadata.get("enabled") is True:
        score += 5
        reasons.append("upstream-enabled")
    if not reasons:
        reasons.append("new non-P2P upstream declaration")
    return score, reasons


def build_report(stage: dict[str, Any], catalog: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    upstreams = sources.get("upstreams") if isinstance(sources.get("upstreams"), dict) else {}
    allowed_sources = set(upstreams)
    if len(allowed_sources) != 3:
        raise ValueError(f"expected exactly 3 configured upstream repositories, got {len(allowed_sources)}")

    known = {
        norm(row.get("canonicalId"))
        for row in catalog.get("providers") or []
        if isinstance(row, dict) and norm(row.get("canonicalId"))
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in stage.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        source = str(candidate.get("source") or "").strip()
        cid = norm(candidate.get("canonical_id") or candidate.get("upstream_id"))
        if source not in allowed_sources or not cid or cid in known:
            continue
        grouped[cid].append(candidate)

    providers: list[dict[str, Any]] = []
    for cid, variants in grouped.items():
        best = sorted(
            variants,
            key=lambda row: (
                -interest(row)[0],
                int(row.get("source_priority") or 999),
                str(row.get("source") or ""),
            ),
        )[0]
        score, reasons = interest(best)
        metadata = best.get("metadata") if isinstance(best.get("metadata"), dict) else {}
        canonical = best.get("canonical_metadata") if isinstance(best.get("canonical_metadata"), dict) else {}
        provider_sources = sorted({str(row.get("source") or "") for row in variants if row.get("source")})
        provider_repositories = sorted({
            str((upstreams.get(source) or {}).get("repository") or "")
            for source in provider_sources
            if str((upstreams.get(source) or {}).get("repository") or "")
        })
        providers.append({
            "canonicalId": cid,
            "displayName": str(metadata.get("name") or best.get("upstream_id") or cid),
            "interestScore": score,
            "interestReasons": reasons,
            "sources": provider_sources,
            "repositories": provider_repositories,
            "upstreamIds": sorted({str(row.get("upstream_id") or "") for row in variants if row.get("upstream_id")}),
            "supportedTypes": string_list(canonical.get("supportedTypes")) or string_list(metadata.get("supportedTypes")),
            "contentLanguage": string_list(canonical.get("contentLanguage")) or string_list(metadata.get("contentLanguage")),
            "formats": string_list(canonical.get("formats")) or string_list(metadata.get("formats")),
            "variantCount": len(variants),
            "reviewRequired": True,
            "automaticImportAllowed": False,
            "automaticActivationAllowed": False,
        })

    providers.sort(key=lambda row: (-int(row["interestScore"]), row["canonicalId"]))
    interesting = [row for row in providers if int(row["interestScore"]) >= 20]
    upstream_status = {
        key: (stage.get("upstreams") or {}).get(key, {})
        for key in sorted(allowed_sources)
    }
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "weekly_upstream_provider_discovery",
        "configuredUpstreams": sorted(allowed_sources),
        "knownCanonicalProviders": len(known),
        "newProviderCount": len(providers),
        "interestingProviderCount": len(interesting),
        "providers": providers,
        "upstreamStatus": upstream_status,
        "policy": {
            "upstreamsReadOnly": True,
            "niakvioCatalogMutationAllowed": False,
            "automaticImportAllowed": False,
            "automaticActivationAllowed": False,
            "manualReviewRequired": True,
            "p2pExcludedByDiscovery": True,
        },
    }


def markdown(report: dict[str, Any]) -> str:
    rows = report.get("providers") or []
    lines = [
        "# Weekly upstream provider discovery",
        "",
        f"Configured upstreams: **{len(report.get('configuredUpstreams') or [])}**",
        f"Known NiakVIO providers: **{report.get('knownCanonicalProviders', 0)}**",
        f"New upstream providers: **{report.get('newProviderCount', 0)}**",
        f"Interesting candidates: **{report.get('interestingProviderCount', 0)}**",
        "",
        "> Review only: this job never imports, enables or publishes a provider automatically.",
        "",
    ]
    if not rows:
        lines.append("No new non-P2P upstream provider is currently missing from the canonical catalog.")
        return "\n".join(lines) + "\n"
    lines.extend([
        "| Provider | Score | Sources | Types | Languages | Formats | Why review |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ])
    for row in rows:
        lines.append(
            "| {name} | {score} | {sources} | {types} | {languages} | {formats} | {why} |".format(
                name=str(row.get("displayName") or row.get("canonicalId") or "").replace("|", "\\|"),
                score=int(row.get("interestScore") or 0),
                sources=", ".join(row.get("sources") or []) or "-",
                types=", ".join(row.get("supportedTypes") or []) or "-",
                languages=", ".join(row.get("contentLanguage") or []) or "-",
                formats=", ".join(row.get("formats") or []) or "-",
                why="; ".join(row.get("interestReasons") or []).replace("|", "\\|"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging/candidates.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "provider_catalog.json")
    parser.add_argument("--sources", type=Path, default=ROOT / "sources.json")
    parser.add_argument("--output", type=Path, default=ROOT / "health-output/upstream-provider-discovery.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "health-output/upstream-provider-discovery.md")
    args = parser.parse_args()

    report = build_report(load_json(args.stage), load_json(args.catalog), load_json(args.sources))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(
        "FIELD_UPSTREAM_PROVIDER_DISCOVERY "
        f"upstreams={len(report['configuredUpstreams'])} "
        f"new={report['newProviderCount']} interesting={report['interestingProviderCount']} "
        "automatic_import=false automatic_activation=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

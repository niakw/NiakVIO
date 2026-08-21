#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Read-only scout for new providers declared by NiakVIO's configured upstreams.

This job never imports, enables, patches or publishes a provider. It compares the
three upstream manifests declared in sources.json with provider_catalog.json and
writes a review artifact containing only new, non-P2P candidates.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from discover_candidates import fetch_manifest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources.json"
CATALOG = ROOT / "provider_catalog.json"
DEFAULT_OUTPUT = ROOT / "health-output/weekly-provider-discovery.json"


def canonical_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return (cleaned[:120] or "provider").casefold().replace("_", "-")


def known_provider_ids(catalog: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    order = catalog.get("manifestOrder") or {}
    if isinstance(order, dict):
        for values in order.values():
            if isinstance(values, list):
                ids.update(canonical_id(value) for value in values if str(value).strip())
    providers = catalog.get("providers")
    if isinstance(providers, dict):
        ids.update(canonical_id(value) for value in providers)
    elif isinstance(providers, list):
        for row in providers:
            if isinstance(row, dict):
                raw = row.get("id") or row.get("canonicalId") or row.get("name")
                if raw:
                    ids.add(canonical_id(str(raw)))
    return ids


def excluded(entry: dict[str, Any], exclusions: dict[str, Any]) -> tuple[bool, str]:
    provider_id = canonical_id(str(entry.get("id") or entry.get("name") or ""))
    blocked_ids = {canonical_id(str(value)) for value in exclusions.get("provider_ids", [])}
    if provider_id in blocked_ids:
        return True, "excluded_provider_id"
    blob = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    for marker in exclusions.get("metadata_patterns", []):
        token = str(marker).casefold().strip()
        if token and token in blob:
            return True, f"excluded_metadata:{token}"
    return False, ""


def _text(entry: dict[str, Any]) -> str:
    return json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()


def candidate_signals(entry: dict[str, Any]) -> tuple[int, list[str]]:
    blob = _text(entry)
    score = 1
    reasons = ["new_upstream_provider"]

    if any(token in blob for token in ("vff", "vfq", "vostfr", '"fr"', "french", "français", "francais")):
        score += 5
        reasons.append("french_signal")
    if any(token in blob for token in ("anime", "animation")):
        score += 2
        reasons.append("anime_signal")
    if any(token in blob for token in ("2160", "4k", "uhd")):
        score += 2
        reasons.append("uhd_signal")
    elif "1080" in blob:
        score += 1
        reasons.append("1080p_signal")
    if entry.get("enabled") is not False:
        score += 1
        reasons.append("upstream_enabled")

    supported = entry.get("supportedTypes") or entry.get("types") or entry.get("catalogues") or []
    if isinstance(supported, str):
        supported = [supported]
    supported_blob = " ".join(str(value).casefold() for value in supported) if isinstance(supported, list) else ""
    recognized = [kind for kind in ("movie", "tv", "anime") if kind in supported_blob or kind in blob]
    if recognized:
        score += min(3, len(recognized))
        reasons.append("media:" + ",".join(recognized))
    return score, reasons


def collect_candidates(
    source_key: str,
    source_cfg: dict[str, Any],
    manifest: dict[str, Any],
    known: set[str],
    exclusions: dict[str, Any],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        raw_id = str(row.get("id") or row.get("name") or "").strip()
        if not raw_id:
            continue
        provider_id = canonical_id(raw_id)
        if provider_id in known:
            continue
        is_excluded, reason = excluded(row, exclusions)
        if is_excluded:
            continue
        score, signals = candidate_signals(row)
        result.append({
            "canonicalId": provider_id,
            "upstreamId": raw_id,
            "source": source_key,
            "sourceName": source_cfg.get("name", source_key),
            "repository": source_cfg.get("repository"),
            "score": score,
            "signals": signals,
            "upstreamEnabled": row.get("enabled") is not False,
            "supportedTypes": row.get("supportedTypes") or row.get("types") or [],
            "languages": row.get("languages") or row.get("language") or [],
            "quality": row.get("quality") or row.get("qualities") or [],
            "filename": row.get("filename"),
        })
    return result


def build_report(
    sources: dict[str, Any],
    catalog: dict[str, Any],
    manifests: dict[str, dict[str, Any]],
    manifest_urls: dict[str, str] | None = None,
    errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    known = known_provider_ids(catalog)
    exclusions = sources.get("exclusions") or {}
    upstreams = sources.get("upstreams") or {}
    candidates: list[dict[str, Any]] = []
    for source_key, source_cfg in upstreams.items():
        manifest = manifests.get(source_key)
        if not isinstance(source_cfg, dict) or not isinstance(manifest, dict):
            continue
        candidates.extend(collect_candidates(source_key, source_cfg, manifest, known, exclusions))
    candidates.sort(key=lambda row: (-int(row["score"]), str(row["canonicalId"]), str(row["source"])))
    return {
        "schemaVersion": 1,
        "mode": "read_only_upstream_provider_discovery",
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "configuredUpstreamCount": len(upstreams),
        "checkedUpstreamCount": len(manifests),
        "knownProviderCount": len(known),
        "candidateCount": len(candidates),
        "candidates": candidates,
        "upstreams": {
            key: {
                "repository": cfg.get("repository") if isinstance(cfg, dict) else None,
                "manifestUrl": (manifest_urls or {}).get(key),
                "declaredProviders": len((manifests.get(key) or {}).get("scrapers") or []),
                "error": (errors or {}).get(key),
            }
            for key, cfg in upstreams.items()
        },
        "policy": {
            "readOnly": True,
            "automaticImport": False,
            "automaticEnable": False,
            "automaticPublish": False,
            "p2pExcluded": True,
            "catalogSourceOfTruth": "provider_catalog.json",
            "upstreamSourceOfTruth": "sources.json",
            "reviewRequired": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--require-all-upstreams", action="store_true")
    args = parser.parse_args()

    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    upstreams = sources.get("upstreams") or {}
    manifests: dict[str, dict[str, Any]] = {}
    manifest_urls: dict[str, str] = {}
    errors: dict[str, str] = {}

    for source_key, source_cfg in upstreams.items():
        try:
            manifest, manifest_url = fetch_manifest(list(source_cfg.get("manifest_urls") or []))
            manifests[source_key] = manifest
            manifest_urls[source_key] = manifest_url
            print(f"[OK] {source_key}: {len(manifest.get('scrapers') or [])} declared providers")
        except Exception as exc:
            errors[source_key] = str(exc)
            print(f"[WARN] {source_key}: {exc}")

    report = build_report(sources, catalog, manifests, manifest_urls, errors)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "FIELD_WEEKLY_PROVIDER_DISCOVERY "
        f"upstreams={report['checkedUpstreamCount']}/{report['configuredUpstreamCount']} "
        f"known={report['knownProviderCount']} candidates={report['candidateCount']} "
        f"output={output.relative_to(ROOT) if ROOT in output.parents else output}"
    )
    if args.require_all_upstreams and errors:
        return 2
    if not manifests:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

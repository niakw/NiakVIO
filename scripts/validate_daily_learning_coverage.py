#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def validate_coverage(manifest: dict[str, Any], stage: dict[str, Any], health: dict[str, Any]) -> dict[str, Any]:
    published = {
        _norm(row.get("id"))
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and _norm(row.get("id"))
    }
    if not published:
        raise ValueError("published manifest contains no providers")

    candidate_by_key: dict[str, str] = {}
    for row in stage.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        provider_id = _norm(row.get("canonical_id") or row.get("upstream_id"))
        if key and provider_id:
            candidate_by_key[key] = provider_id

    observed: set[str] = set()
    result_count = 0
    for row in health.get("results") or []:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        provider_id = candidate_by_key.get(key)
        if provider_id:
            observed.add(provider_id)
            result_count += 1

    missing = sorted(published - observed)
    summary = {
        "schemaVersion": 1,
        "target": "published_providers_daily_learning_observation",
        "publishedProviderCount": len(published),
        "observedPublishedProviderCount": len(published & observed),
        "coverageRatio": round(len(published & observed) / len(published), 6),
        "healthResultCount": result_count,
        "missingPublishedProviders": missing,
        "extraObservedProviders": sorted(observed - published),
        "complete": not missing,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    summary = validate_coverage(_load(args.manifest), _load(args.stage), _load(args.health))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_DAILY_COVERAGE "
        f"published={summary['publishedProviderCount']} "
        f"observed={summary['observedPublishedProviderCount']} "
        f"ratio={summary['coverageRatio']:.6f} "
        f"missing={len(summary['missingPublishedProviders'])}"
    )
    if not summary["complete"]:
        raise SystemExit(
            "daily Learning did not observe every published provider: "
            + ", ".join(summary["missingPublishedProviders"][:20])
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

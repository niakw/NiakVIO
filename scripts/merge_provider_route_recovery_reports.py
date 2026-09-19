#!/usr/bin/env python3
"""Merge independently-proved provider recovery reports without sharing provider authority."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import current_provider_scope as current_scope  # noqa: E402
import recover_provider_routes_from_upstreams as recovery  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: object required")
    if int(value.get("schemaVersion") or 0) != recovery.PROOF_VERSION:
        raise SystemExit(
            f"{path}: proof version={value.get('schemaVersion')} expected={recovery.PROOF_VERSION}"
        )
    return value


def manifest_ids() -> set[str]:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    return {
        current_scope.cid(row.get("id"))
        for row in (manifest.get("scrapers") or [])
        if isinstance(row, dict) and current_scope.cid(row.get("id"))
    }


def merge(paths: list[Path], scope: str) -> dict[str, Any]:
    expected = current_scope.active_provider_ids() if scope == "active" else manifest_ids()
    rows: dict[str, dict[str, Any]] = {}
    source_files: dict[str, str] = {}
    for path in paths:
        value = load(path)
        providers = value.get("providers") if isinstance(value.get("providers"), list) else []
        for row in providers:
            if not isinstance(row, dict):
                continue
            provider_id = current_scope.cid(row.get("providerId"))
            if provider_id not in expected:
                continue
            if provider_id in rows:
                raise SystemExit(
                    f"duplicate provider proof for {provider_id}: {source_files[provider_id]} and {path}"
                )
            rows[provider_id] = row
            source_files[provider_id] = str(path)
    missing = expected - set(rows)
    extra = set(rows) - expected
    if missing or extra:
        raise SystemExit(
            f"individual recovery scope mismatch: missing={sorted(missing)} extra={sorted(extra)}"
        )
    ordered = [rows[provider_id] for provider_id in sorted(rows)]
    counts = Counter(str(row.get("status") or "unknown") for row in ordered)
    proven = [row for row in ordered if row.get("routes")]
    return {
        "schemaVersion": recovery.PROOF_VERSION,
        "method": "independent-provider-runtime-http-proof-aggregate",
        "scope": scope,
        "providerCount": len(ordered),
        "catalogueProviderCount": len(expected),
        "providersWithProvenRoutes": len(proven),
        "provenRouteCount": sum(len(row.get("routes") or []) for row in ordered),
        "simpleApiRecipeCount": sum(1 for row in ordered if isinstance(row.get("apiRecipe"), dict)),
        "statusCounts": dict(sorted(counts.items())),
        "staticCandidatesExecutable": False,
        "authorityIsolation": "one-provider-one-proof-job-no-cross-provider-domain-or-route-sharing",
        "providers": ordered,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--scope", choices=("active", "all"), default="active")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    paths: list[Path] = []
    for raw in args.inputs:
        if raw.is_dir():
            paths.extend(sorted(raw.rglob("*.json")))
        else:
            paths.append(raw)
    paths = [path for path in paths if path.is_file()]
    if not paths:
        raise SystemExit("no individual provider recovery reports found")

    report = merge(paths, args.scope)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_INDIVIDUAL_ROUTE_PROOFS_MERGED "
        f"scope={args.scope} providers={report['providerCount']} "
        f"proven={report['providersWithProvenRoutes']} routes={report['provenRouteCount']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

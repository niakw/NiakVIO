#!/usr/bin/env python3
"""Merge targeted route proof with historical evidence for current active providers.

Provider cardinality is never policy. The executable Repair scope is the set of
manifest rows that are enabled and whose current artifact lives in providers/.
Disabled-retained providers remain visible in manifest.json but are not Repair
obligations; provider-old entries are absent from the current catalogue.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

import provider_route_proof_lkg as route_lkg

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def pid(row: dict[str, Any]) -> str:
    return str(row.get("providerId") or "").strip().casefold().replace("_", "-")


def manifest_pid(row: dict[str, Any]) -> str:
    return str(row.get("id") or "").strip().casefold().replace("_", "-")


def normalize_typed_api_recipe(row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    out = copy.deepcopy(row)
    recipe = out.get("apiRecipe")
    if not isinstance(recipe, dict):
        return out, False
    if not recipe.get("movieRoute") or not recipe.get("episodeRoute"):
        return out, False
    if "directRoute" not in recipe and "directRequest" not in recipe:
        return out, False
    recipe = copy.deepcopy(recipe)
    recipe.pop("directRoute", None)
    recipe.pop("directRequest", None)
    out["apiRecipe"] = recipe
    return out, True


def eligible_bootstrap(seed: dict[str, Any], targeted: dict[str, Any]) -> dict[str, Any]:
    targeted_sources = {
        pid(row): route_lkg.source_identity(row.get("source"))
        for row in targeted.get("providers") or []
        if isinstance(row, dict) and pid(row)
    }
    providers: list[dict[str, Any]] = []
    for row in seed.get("providers") or []:
        if not isinstance(row, dict):
            continue
        key = pid(row)
        identity = route_lkg.source_identity(row.get("source"))
        if key and identity is not None and targeted_sources.get(key) == identity:
            providers.append(copy.deepcopy(row))
    return {"schemaVersion": 1, "providers": providers}


def current_active_ids(manifest: dict[str, Any]) -> list[str]:
    ids = [
        manifest_pid(row)
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
        and row.get("enabled") is not False
        and str(row.get("filename") or "").startswith("providers/")
        and manifest_pid(row)
    ]
    if not ids:
        raise SystemExit("current active provider scope is empty")
    if len(ids) != len(set(ids)):
        raise SystemExit("current active provider scope contains duplicate ids")
    return ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=Path("automation/provider-route-recovery-v5.json"))
    parser.add_argument("--targeted", type=Path, required=True)
    parser.add_argument("--lkg", type=Path, default=Path("automation/provider-route-proof-lkg.json"))
    parser.add_argument("--seed", type=Path, default=Path("automation/provider-route-proof-seed-v1.json"))
    parser.add_argument("--output", type=Path, default=Path("automation/provider-route-recovery-v6.json"))
    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    args = parser.parse_args()

    baseline = load(ROOT / args.baseline)
    targeted = load(ROOT / args.targeted)
    manifest = load(ROOT / args.manifest)
    catalogue_ids = current_active_ids(manifest)
    catalogue_set = set(catalogue_ids)

    baseline_rows = [
        row for row in baseline.get("providers") or []
        if isinstance(row, dict) and pid(row) in catalogue_set
    ]
    missing_baseline = sorted(catalogue_set - {pid(row) for row in baseline_rows})
    if missing_baseline:
        raise SystemExit("historical baseline missing current active providers: " + ",".join(missing_baseline))

    lkg_path = ROOT / args.lkg
    lkg = route_lkg.load(lkg_path, missing_ok=True)
    seed_path = ROOT / args.seed
    seed_stats = {"updatedProviders": 0, "sourceResets": 0, "retainedRows": 0}
    if seed_path.exists():
        seed = eligible_bootstrap(load(seed_path), targeted)
        if seed.get("providers"):
            lkg, seed_stats = route_lkg.merge_report_into_registry(lkg, seed)
    lkg, lkg_stats = route_lkg.merge_report_into_registry(lkg, targeted)
    route_lkg.write(lkg_path, lkg)
    lkg_providers = lkg.get("providers") if isinstance(lkg.get("providers"), dict) else {}

    rows = {pid(row): row for row in baseline_rows if pid(row)}
    targeted_rows = [row for row in targeted.get("providers") or [] if isinstance(row, dict) and pid(row)]
    targeted_ids = {pid(row) for row in targeted_rows}
    outside = sorted(targeted_ids - catalogue_set)
    if outside:
        raise SystemExit("targeted report contains providers outside current active scope: " + ",".join(outside))

    lkg_retained_rows = 0
    lkg_augmented_providers: list[str] = []
    for row in targeted_rows:
        key = pid(row)
        enriched, retained = route_lkg.augment_provider_row(row, lkg_providers.get(key))
        rows[key] = enriched
        if retained > 0:
            lkg_retained_rows += retained
            lkg_augmented_providers.append(key)

    if set(rows) != catalogue_set:
        missing = sorted(catalogue_set - set(rows))
        extra = sorted(set(rows) - catalogue_set)
        raise SystemExit(f"merged provider identity mismatch missing={missing} extra={extra}")

    merged_rows = []
    typed_recipe_sanitized = []
    for key in sorted(rows):
        normalized, changed = normalize_typed_api_recipe(rows[key])
        merged_rows.append(normalized)
        if changed:
            typed_recipe_sanitized.append(key)

    counts = Counter(str(row.get("status") or "unknown") for row in merged_rows)
    proven = [row for row in merged_rows if row.get("routes")]
    merged = dict(baseline)
    merged.update({
        "providerCount": len(catalogue_ids),
        "catalogueProviderCount": len(catalogue_ids),
        "scopeAuthority": "manifest.json enabled rows under providers/",
        "providersWithProvenRoutes": len(proven),
        "provenRouteCount": sum(len(row.get("routes") or []) for row in merged_rows),
        "simpleApiRecipeCount": sum(1 for row in merged_rows if isinstance(row.get("apiRecipe"), dict)),
        "statusCounts": dict(sorted(counts.items())),
        "providers": merged_rows,
        "portfolioRepair": {
            "version": 10,
            "targetedProviderCount": len(targeted_ids),
            "targetedProviders": sorted(targeted_ids),
            "preservedProviderCount": len(catalogue_ids) - len(targeted_ids),
            "preservedProvidersNotReprobed": sorted(set(rows) - targeted_ids),
            "targetedDurationMs": int(targeted.get("durationMs") or 0),
            "proofMethod": targeted.get("method"),
            "typedRecipeDirectRouteSanitizedCount": len(typed_recipe_sanitized),
            "typedRecipeDirectRouteSanitizedProviders": typed_recipe_sanitized,
            "routeProofBootstrapMatchedProviders": int(seed_stats.get("updatedProviders") or 0),
            "routeProofLkgUpdatedProviders": int(lkg_stats.get("updatedProviders") or 0),
            "routeProofLkgSourceResets": int(lkg_stats.get("sourceResets") or 0),
            "routeProofLkgRetainedRows": lkg_retained_rows,
            "routeProofLkgAugmentedProviders": sorted(set(lkg_augmented_providers)),
        },
    })
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_REPAIR_REPORT_V6_MERGED "
        f"active={len(catalogue_ids)} targeted={len(targeted_ids)} preserved={len(catalogue_ids)-len(targeted_ids)} "
        f"proven={merged['providersWithProvenRoutes']} routes={merged['provenRouteCount']} "
        f"recipes={merged['simpleApiRecipeCount']} typed_direct_sanitized={len(typed_recipe_sanitized)} "
        f"route_bootstrap={seed_stats.get('updatedProviders', 0)} "
        f"route_lkg_updated={lkg_stats.get('updatedProviders', 0)} "
        f"route_lkg_retained={lkg_retained_rows} route_lkg_augmented={len(set(lkg_augmented_providers))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Merge targeted route proof with historical evidence for current active providers.

Provider cardinality is never policy. The executable Repair scope is the active
Global+France projection union. Strict France-only identities are first-class
Repair obligations; disabled-retained and provider-old entries are not.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

import provider_route_proof_lkg as route_lkg
from current_provider_scope import projection_active_provider_ids

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "manifest.json"
CATALOGUE_PRESENCE_ONLY_POLICY = "catalogue-presence-only"


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


def publication_active_ids(
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    projection_ids_fn=projection_active_provider_ids,
) -> list[str]:
    """Resolve canonical Repair scope.

    The repository's default manifest is only the Global projection. Repair
    authority is the active Global+France union, including strict France-only
    providers. Explicit custom manifests remain supported for isolated tests.
    """
    if manifest_path.resolve() == DEFAULT_MANIFEST.resolve():
        ids = [str(value).strip().casefold().replace("_", "-") for value in projection_ids_fn()]
        ids = [value for value in ids if value]
        if not ids:
            raise SystemExit("current active Global+France provider scope is empty")
        if len(ids) != len(set(ids)):
            raise SystemExit("current active Global+France provider scope contains duplicate ids")
        return ids
    return current_active_ids(manifest)


def catalogue_presence_only_row(provider_id: str) -> dict[str, Any]:
    """Represent current catalogue membership without inventing route proof.

    This row exists solely so a targeted Repair report can retain exact current
    manifest cardinality when the historical route baseline predates activation
    of a provider. Downstream application must leave existing provider DATA
    untouched until that identity is actually reprobed.
    """
    return {
        "providerId": provider_id,
        "status": "current-active-not-in-historical-route-baseline",
        "routes": [],
        "routeData": [],
        "executionRoutes": [],
        "mergePolicy": CATALOGUE_PRESENCE_ONLY_POLICY,
        "preserveExistingRuntimePlan": True,
        "proofAuthority": False,
        "executionAuthority": False,
    }


def baseline_rows_for_catalogue(
    baseline: dict[str, Any], catalogue_ids: list[str]
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    catalogue_set = set(catalogue_ids)
    rows = {
        pid(row): copy.deepcopy(row)
        for row in baseline.get("providers") or []
        if isinstance(row, dict) and pid(row) in catalogue_set
    }
    missing = sorted(catalogue_set - set(rows))
    for provider_id in missing:
        rows[provider_id] = catalogue_presence_only_row(provider_id)
    return rows, missing


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
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest = load(manifest_path)
    catalogue_ids = publication_active_ids(manifest_path, manifest)
    catalogue_set = set(catalogue_ids)

    rows, missing_baseline = baseline_rows_for_catalogue(baseline, catalogue_ids)

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
        "scopeAuthority": "Global+France active projection union",
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
            "historicalBaselineMissingProviderCount": len(missing_baseline),
            "historicalBaselineMissingProviders": missing_baseline,
            "cataloguePresenceOnlyProviderCount": sum(
                1 for row in merged_rows
                if row.get("mergePolicy") == CATALOGUE_PRESENCE_ONLY_POLICY
            ),
            "cataloguePresenceOnlyPolicy": (
                "current manifest identity only; zero route/execution authority; "
                "application preserves existing runtime DATA until a fresh targeted probe replaces the row"
            ),
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
        f"baseline_missing={len(missing_baseline)} "
        f"presence_only={merged['portfolioRepair']['cataloguePresenceOnlyProviderCount']} "
        f"proven={merged['providersWithProvenRoutes']} routes={merged['provenRouteCount']} "
        f"recipes={merged['simpleApiRecipeCount']} typed_direct_sanitized={len(typed_recipe_sanitized)} "
        f"route_bootstrap={seed_stats.get('updatedProviders', 0)} "
        f"route_lkg_updated={lkg_stats.get('updatedProviders', 0)} "
        f"route_lkg_retained={lkg_retained_rows} route_lkg_augmented={len(set(lkg_augmented_providers))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

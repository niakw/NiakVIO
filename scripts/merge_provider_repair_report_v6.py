#!/usr/bin/env python3
"""Merge targeted route proof with the 96-provider baseline and exact-source LKG.

Already-green providers are deliberately not re-probed. Their baseline rows are
carried forward. Targeted providers use current proof first, augmented only by
live-positive route rows retained in the exact-source route-proof LKG. This keeps
variable successful upstream traces from erasing previously proven correlated
steps while source changes still reset historical evidence.

A small historical bootstrap may recover proof emitted before the durable LKG
existed. Bootstrap evidence is eligible only for a provider targeted now and only
when its exact source identity equals the current targeted source. It cannot
revive evidence after an upstream SHA change.

Before persistence, every carried/new simple API recipe passes the same typed-route
normalizer so obsolete generic directRoute DATA cannot outrank movie/tv routes.
The resulting report is a normal full proof-v5 census consumable by the existing
deterministic applier/materializer.
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


def normalize_typed_api_recipe(row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Remove obsolete generic direct execution when both semantic lanes exist.

    A legacy directRoute is unsafe once a recipe owns explicit movieRoute and
    episodeRoute: runtime direct-first execution can force the movie lane for TV.
    Preserve all proof rows and typed requests; only the redundant generic route
    and its paired request are removed. This applies equally to preserved and
    freshly targeted providers, so skip status cannot bypass DATA safety.
    """
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
    """Return only seed rows whose provider + exact source are targeted now."""
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=Path("automation/provider-route-recovery-v5.json"))
    parser.add_argument("--targeted", type=Path, required=True)
    parser.add_argument("--lkg", type=Path, default=Path("automation/provider-route-proof-lkg.json"))
    parser.add_argument("--seed", type=Path, default=Path("automation/provider-route-proof-seed-v1.json"))
    parser.add_argument("--output", type=Path, default=Path("automation/provider-route-recovery-v6.json"))
    args = parser.parse_args()
    baseline = load(ROOT / args.baseline)
    targeted = load(ROOT / args.targeted)
    if int(baseline.get("providerCount") or 0) != 96 or len(baseline.get("providers") or []) != 96:
        raise SystemExit("baseline route proof must contain 96 providers")

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

    rows = {pid(row): row for row in baseline.get("providers") or [] if isinstance(row, dict) and pid(row)}
    targeted_rows = [row for row in targeted.get("providers") or [] if isinstance(row, dict) and pid(row)]
    targeted_ids = {pid(row) for row in targeted_rows}
    lkg_retained_rows = 0
    lkg_augmented_providers: list[str] = []
    for row in targeted_rows:
        key = pid(row)
        enriched, retained = route_lkg.augment_provider_row(row, lkg_providers.get(key))
        rows[key] = enriched
        if retained > 0:
            lkg_retained_rows += retained
            lkg_augmented_providers.append(key)
    if len(rows) != 96:
        raise SystemExit(f"merged provider rows={len(rows)}, expected=96")

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
        "providerCount": 96,
        "catalogueProviderCount": 96,
        "providersWithProvenRoutes": len(proven),
        "provenRouteCount": sum(len(row.get("routes") or []) for row in merged_rows),
        "simpleApiRecipeCount": sum(1 for row in merged_rows if isinstance(row.get("apiRecipe"), dict)),
        "statusCounts": dict(sorted(counts.items())),
        "providers": merged_rows,
        "portfolioRepair": {
            "version": 9,
            "targetedProviderCount": len(targeted_ids),
            "targetedProviders": sorted(targeted_ids),
            "preservedProviderCount": 96 - len(targeted_ids),
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
        f"targeted={len(targeted_ids)} preserved={96-len(targeted_ids)} "
        f"proven={merged['providersWithProvenRoutes']} routes={merged['provenRouteCount']} "
        f"recipes={merged['simpleApiRecipeCount']} typed_direct_sanitized={len(typed_recipe_sanitized)} "
        f"route_bootstrap={seed_stats.get('updatedProviders', 0)} "
        f"route_lkg_updated={lkg_stats.get('updatedProviders', 0)} "
        f"route_lkg_retained={lkg_retained_rows} route_lkg_augmented={len(set(lkg_augmented_providers))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

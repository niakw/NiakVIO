#!/usr/bin/env python3
"""Merge a targeted route-proof repair census with the last full 96-provider census.

Already-green providers are deliberately not re-probed. Their last accepted proof
rows are carried forward, while targeted rows replace only their own provider ids.
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=Path("automation/provider-route-recovery-v5.json"))
    parser.add_argument("--targeted", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("automation/provider-route-recovery-v6.json"))
    args = parser.parse_args()
    baseline = load(ROOT / args.baseline)
    targeted = load(ROOT / args.targeted)
    if int(baseline.get("providerCount") or 0) != 96 or len(baseline.get("providers") or []) != 96:
        raise SystemExit("baseline route proof must contain 96 providers")

    rows = {pid(row): row for row in baseline.get("providers") or [] if isinstance(row, dict) and pid(row)}
    targeted_rows = [row for row in targeted.get("providers") or [] if isinstance(row, dict) and pid(row)]
    targeted_ids = {pid(row) for row in targeted_rows}
    for row in targeted_rows:
        rows[pid(row)] = row
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
            "version": 7,
            "targetedProviderCount": len(targeted_ids),
            "targetedProviders": sorted(targeted_ids),
            "preservedProviderCount": 96 - len(targeted_ids),
            "preservedProvidersNotReprobed": sorted(set(rows) - targeted_ids),
            "targetedDurationMs": int(targeted.get("durationMs") or 0),
            "proofMethod": targeted.get("method"),
            "typedRecipeDirectRouteSanitizedCount": len(typed_recipe_sanitized),
            "typedRecipeDirectRouteSanitizedProviders": typed_recipe_sanitized,
        },
    })
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_REPAIR_REPORT_V6_MERGED "
        f"targeted={len(targeted_ids)} preserved={96-len(targeted_ids)} "
        f"proven={merged['providersWithProvenRoutes']} routes={merged['provenRouteCount']} "
        f"recipes={merged['simpleApiRecipeCount']} typed_direct_sanitized={len(typed_recipe_sanitized)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

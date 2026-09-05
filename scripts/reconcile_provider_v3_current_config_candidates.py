#!/usr/bin/env python3
"""Reconcile Provider v3 replay candidates with the currently materialized config.

The live gate intentionally keeps failed/unexecuted candidate evidence for learning,
but a later repair pass must not blindly make those historical candidates executable
again after the Provider config has moved on.  This preflight reads the Provider model
embedded in every manifest JS plus explicit provider-overrides, rebuilds the next
candidate set from that current config, and preserves only independently live-validated
historical routes.

Nothing in this script marks a new route HTTP-proven.  New/current config routes remain
candidates until validate_provider_v3_routes_live.py traverses them successfully.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
OVERRIDES = ROOT / "provider-overrides.json"
MODEL_RE = re.compile(
    r"const\s+NIAKVIO_PROVIDER_MODEL\s*=\s*Object\.freeze\((\{.*?\})\);",
    re.DOTALL,
)
ROUTE_SUFFIXES = ("route", "routes", "path", "paths", "endpoint", "endpoints", "url", "urls")
ROUTE_EXCLUDED = {
    "base", "baseurl", "referer", "referrer", "origin", "host", "domain",
    "officialsite", "officialhub", "officialapi", "fixedapi",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique(values: Iterable[Any], limit: int = 256) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def compact_key(value: object) -> str:
    return str(value or "").strip().replace("-", "").replace("_", "").casefold()


def routeish_key(key: object) -> bool:
    compact = compact_key(key)
    return bool(compact and compact not in ROUTE_EXCLUDED and compact.endswith(ROUTE_SUFFIXES))


def iter_recipe_routes(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if routeish_key(key):
                if isinstance(child, str) and child.strip():
                    yield child.strip()
                elif isinstance(child, list):
                    for item in child:
                        if isinstance(item, str) and item.strip():
                            yield item.strip()
            if isinstance(child, (dict, list)):
                yield from iter_recipe_routes(child)
    elif isinstance(value, list):
        for child in value:
            if isinstance(child, (dict, list)):
                yield from iter_recipe_routes(child)


def read_embedded_model(root: Path, filename: str) -> dict[str, Any] | None:
    path = root / filename
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = MODEL_RE.search(text)
    if match is None:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def infer_role(route: str) -> str:
    value = str(route or "").casefold()
    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword|story)=", value):
        return "search"
    if re.search(r"/(?:player|embed|play)(?:[/?#.-]|$)", value):
        return "player"
    if re.search(r"/(?:source|sources|download|file)(?:[/?#.-]|$)", value):
        return "source"
    if re.search(r"/(?:episode|episodes)(?:[/?#.-]|$)", value):
        return "episode-index"
    if "/api" in value:
        return "api"
    return "detail"


def live_validated_reusable(row: dict[str, Any]) -> bool:
    if str(row.get("validationState") or "") != "live-validated":
        return False
    if row.get("reusable") is False:
        return False
    if row.get("fixtureSpecificValues"):
        return False
    if row.get("dynamicQueryResidue"):
        return False
    return True


def fresh_candidate_row(route: str) -> dict[str, Any]:
    return {
        "route": route,
        "role": infer_role(route),
        "method": "GET",
        "bodyFields": [],
        "formEncoded": False,
        "jsonEncoded": False,
        "refererRequired": False,
        "originRequired": False,
        "response": "unknown",
        "executedEvidence": False,
        "httpUsed": False,
        "evidence": "provider-current-config-route-data",
        "evidenceSources": ["provider-current-config-route-data"],
        "confidence": 0.85,
        "candidateCurrentConfig": True,
    }


def _effective_recipe(embedded: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(patch.get("api_recipe"), dict):
        return copy.deepcopy(patch["api_recipe"])
    if isinstance(embedded.get("apiRecipe"), dict):
        return copy.deepcopy(embedded["apiRecipe"])
    return None


def _declared_routes(embedded: dict[str, Any], patch: dict[str, Any], recipe: dict[str, Any] | None) -> list[str]:
    patch_learned = patch.get("learned_routes") if isinstance(patch.get("learned_routes"), list) else []
    override_has_route_plan = bool(patch_learned) or isinstance(patch.get("api_recipe"), dict)
    routes: list[Any] = []
    if patch_learned:
        routes.extend(patch_learned)
    if not override_has_route_plan:
        routes.extend(embedded.get("routes") if isinstance(embedded.get("routes"), list) else [])
    if isinstance(recipe, dict):
        routes.extend(iter_recipe_routes(recipe))
    return unique(routes, 256)


def _sync_effective_config(model: dict[str, Any], embedded: dict[str, Any], patch: dict[str, Any]) -> None:
    # The embedded model is the exact config in the JS that the next probe will run.
    for key in (
        "knownSite", "officialSite", "officialHub", "officialApi", "fixedApi",
        "identityInput", "sourceRuntimeFamily", "strategy", "supportedTypes",
    ):
        if key in embedded:
            model[key] = copy.deepcopy(embedded[key])

    mapping = {
        "official_site": "officialSite",
        "official_hub": "officialHub",
        "official_api": "officialApi",
    }
    for source, target in mapping.items():
        if source in patch:
            model[target] = copy.deepcopy(patch[source])
    if patch.get("official_site"):
        model["knownSite"] = patch["official_site"]
    fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
    if fixed.get("api"):
        model["fixedApi"] = fixed["api"]

    substitutions: dict[str, Any] = {}
    if isinstance(embedded.get("domainSubstitutions"), dict):
        substitutions.update(embedded["domainSubstitutions"])
    for key in ("domain_substitutions", "replacements", "runtime_domain_replacements"):
        value = patch.get(key)
        if isinstance(value, dict):
            substitutions.update(value)
    if substitutions:
        model["domainSubstitutions"] = substitutions


def reconcile(
    root: Path,
    manifest: dict[str, Any],
    knowledge: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    stats = {
        "providersSeen": 0,
        "providersReconciled": 0,
        "missingEmbeddedModel": 0,
        "currentConfigRoutes": 0,
        "liveValidatedRoutesPreserved": 0,
        "staleCandidatesSuppressed": 0,
        "recipesReconciled": 0,
    }

    for manifest_row in manifest.get("scrapers") or []:
        if not isinstance(manifest_row, dict):
            continue
        provider_id = str(manifest_row.get("id") or "").strip().casefold()
        filename = str(manifest_row.get("filename") or "").strip()
        if not provider_id or not filename:
            continue
        stats["providersSeen"] += 1
        static_row = providers.get(provider_id)
        if not isinstance(static_row, dict):
            continue
        embedded = read_embedded_model(root, filename)
        if not isinstance(embedded, dict):
            stats["missingEmbeddedModel"] += 1
            continue
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        _sync_effective_config(model, embedded, patch)

        recipe = _effective_recipe(embedded, patch)
        declared_routes = _declared_routes(embedded, patch, recipe)
        declared_set = set(declared_routes)
        stats["currentConfigRoutes"] += len(declared_routes)

        old_candidate_data = model.get("candidateRouteData") if isinstance(model.get("candidateRouteData"), list) else []
        old_route_data = model.get("routeData") if isinstance(model.get("routeData"), list) else []
        source_rows = [row for row in [*old_candidate_data, *old_route_data] if isinstance(row, dict)]
        by_route: dict[str, dict[str, Any]] = {}
        for source_row in source_rows:
            route = str(source_row.get("route") or "").strip()
            if not route:
                continue
            previous = by_route.get(route)
            if previous is None or live_validated_reusable(source_row):
                by_route[route] = source_row

        reconciled_data: list[dict[str, Any]] = []
        for route in declared_routes:
            row = copy.deepcopy(by_route.get(route) or fresh_candidate_row(route))
            row["route"] = route
            row["candidateCurrentConfig"] = True
            sources = list(row.get("evidenceSources") or [])
            if "provider-current-config-route-data" not in sources:
                sources.append("provider-current-config-route-data")
            row["evidenceSources"] = sources
            reconciled_data.append(row)

        preserved_live: list[str] = []
        for route, source_row in by_route.items():
            if route in declared_set or not live_validated_reusable(source_row):
                continue
            kept = copy.deepcopy(source_row)
            kept["candidateCurrentConfig"] = False
            kept["preservedByLiveValidation"] = True
            reconciled_data.append(kept)
            preserved_live.append(route)

        old_candidate_routes = unique(
            [*(model.get("candidateRoutes") or []), *[row.get("route") for row in old_candidate_data]],
            512,
        )
        reconciled_routes = unique([*declared_routes, *preserved_live], 256)
        suppressed = [route for route in old_candidate_routes if route not in set(reconciled_routes)]
        stats["staleCandidatesSuppressed"] += len(suppressed)
        stats["liveValidatedRoutesPreserved"] += len(preserved_live)

        model["candidateRouteData"] = reconciled_data
        model["candidateRoutes"] = reconciled_routes
        model["candidateReconciliation"] = {
            "version": 1,
            "source": "current-provider-js-plus-overrides",
            "currentConfigRouteCount": len(declared_routes),
            "liveValidatedRouteCountPreserved": len(preserved_live),
            "staleCandidateCountSuppressed": len(suppressed),
            "suppressedRoutes": suppressed[:64],
            "newRoutesRequireLiveProof": True,
        }
        if isinstance(recipe, dict):
            model["candidateApiRecipe"] = copy.deepcopy(recipe)
            stats["recipesReconciled"] += 1
        else:
            model.pop("candidateApiRecipe", None)
        static_row["model"] = model

        if isinstance(patch, dict):
            if isinstance(patch.get("learned_routes"), list):
                patch["candidate_learned_routes"] = unique([*patch["learned_routes"], *preserved_live], 256)
            elif "candidate_learned_routes" in patch:
                patch.pop("candidate_learned_routes", None)
            if isinstance(recipe, dict):
                patch["candidate_api_recipe"] = copy.deepcopy(recipe)
            elif "candidate_api_recipe" in patch:
                patch.pop("candidate_api_recipe", None)
            patch["candidate_config_reconciliation"] = {
                "version": 1,
                "current_config_route_count": len(declared_routes),
                "live_validated_route_count_preserved": len(preserved_live),
                "stale_candidate_count_suppressed": len(suppressed),
                "new_routes_require_live_proof": True,
            }

        stats["providersReconciled"] += 1

    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    args = parser.parse_args()

    root = args.root.resolve()
    manifest_path = args.manifest.resolve()
    knowledge_path = args.knowledge.resolve()
    overrides_path = args.overrides.resolve()
    manifest = load(manifest_path)
    knowledge = load(knowledge_path)
    overrides = load(overrides_path)
    stats = reconcile(root, manifest, knowledge, overrides)
    write(knowledge_path, knowledge)
    write(overrides_path, overrides)
    print(
        "FIELD_PROVIDER_CURRENT_CONFIG_RECONCILE "
        + " ".join(f"{key}={value}" for key, value in stats.items()),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

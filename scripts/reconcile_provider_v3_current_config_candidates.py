#!/usr/bin/env python3
"""Reconcile Provider v3 replay candidates with NiakVIO-owned current config.

Priority for executable candidate seeding is:
  explicit provider override > recognition seed > embedded Provider JS model
  > historical candidate evidence.

Historical failed/unexecuted candidates are not replayed merely because they still
exist in static knowledge. Independently live-validated reusable routes are retained.
Recognition seeds are durable config/recognition evidence, never HTTP proof by
 themselves; a seed route still has to pass validate_provider_v3_routes_live.py.
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
RECOGNITION_SEEDS = ROOT / "automation" / "provider-v3-recognition-seeds.json"
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
    if re.search(r"/(?:search|recherche|browser)(?:[/?#]|$)|[?&](?:s|q|query|keyword|story)=", value):
        return "search"
    if re.search(r"/(?:player|embed|play)(?:[/?#.-]|$)", value):
        return "player"
    if re.search(r"/(?:source|sources|download|file)(?:[/?#.-]|$)", value):
        return "source"
    if re.search(r"/(?:episode|episodes)(?:[/?#.-]|$)|/ep[-/{]", value):
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


def seed_request_map(seed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    requests = seed.get("requests") if isinstance(seed.get("requests"), list) else []
    for raw in requests:
        if not isinstance(raw, dict):
            continue
        route = str(raw.get("route") or "").strip()
        if route:
            out[route] = raw
    return out


def apply_seed_request_contract(row: dict[str, Any], seed_request: dict[str, Any] | None) -> None:
    if not isinstance(seed_request, dict):
        return
    for key in (
        "role", "method", "bodyFields", "formEncoded", "jsonEncoded",
        "refererRequired", "originRequired", "response", "confidence",
    ):
        if key in seed_request:
            row[key] = copy.deepcopy(seed_request[key])
    row["recognitionSeedEvidence"] = str(seed_request.get("evidence") or "niakvio-recognition-seed")
    row["recognitionSeedExecutedEvidence"] = bool(seed_request.get("executedEvidence"))
    # Static recognition DATA never upgrades to HTTP proof by itself.
    if not live_validated_reusable(row):
        row["executedEvidence"] = False
        row["httpUsed"] = False
        if str(row.get("validationState") or "") == "live-validated":
            row.pop("validationState", None)
    sources = list(row.get("evidenceSources") or [])
    if "provider-v3-recognition-seed" not in sources:
        sources.append("provider-v3-recognition-seed")
    row["evidenceSources"] = sources


def _effective_recipe(
    embedded: dict[str, Any],
    seed: dict[str, Any],
    patch: dict[str, Any],
) -> dict[str, Any] | None:
    if isinstance(patch.get("api_recipe"), dict):
        return copy.deepcopy(patch["api_recipe"])
    if isinstance(seed.get("apiRecipe"), dict):
        return copy.deepcopy(seed["apiRecipe"])
    if isinstance(embedded.get("apiRecipe"), dict):
        return copy.deepcopy(embedded["apiRecipe"])
    return None


def _declared_routes(
    embedded: dict[str, Any],
    seed: dict[str, Any],
    patch: dict[str, Any],
    recipe: dict[str, Any] | None,
) -> tuple[list[str], str]:
    patch_learned = patch.get("learned_routes") if isinstance(patch.get("learned_routes"), list) else []
    patch_has_plan = bool(patch_learned) or isinstance(patch.get("api_recipe"), dict)
    seed_routes = seed.get("routes") if isinstance(seed.get("routes"), list) else []
    seed_requests = seed.get("requests") if isinstance(seed.get("requests"), list) else []
    seed_request_routes = [row.get("route") for row in seed_requests if isinstance(row, dict)]
    seed_has_plan = bool(seed_routes or [route for route in seed_request_routes if route])

    routes: list[Any] = []
    if patch_has_plan:
        routes.extend(patch_learned)
        source = "provider-overrides"
    elif seed_has_plan:
        routes.extend(seed_routes)
        routes.extend(seed_request_routes)
        source = "provider-v3-recognition-seeds"
    else:
        routes.extend(embedded.get("routes") if isinstance(embedded.get("routes"), list) else [])
        source = "embedded-provider-js"

    if isinstance(recipe, dict):
        routes.extend(iter_recipe_routes(recipe))
    return unique(routes, 256), source


def _sync_effective_config(
    model: dict[str, Any],
    embedded: dict[str, Any],
    seed: dict[str, Any],
    patch: dict[str, Any],
) -> None:
    # Lowest durable config priority: the exact embedded JS model.
    for key in (
        "knownSite", "officialSite", "officialHub", "officialApi", "fixedApi",
        "identityInput", "sourceRuntimeFamily", "strategy", "supportedTypes", "origins",
    ):
        if key in embedded:
            model[key] = copy.deepcopy(embedded[key])

    # Recognition seeds intentionally correct/augment stale embedded config.
    for key in ("knownSite", "officialSite", "officialHub", "officialApi", "fixedApi", "origins"):
        if key in seed:
            model[key] = copy.deepcopy(seed[key])
    identity = seed.get("identity") if isinstance(seed.get("identity"), dict) else None
    if identity is not None:
        model["recognitionIdentity"] = copy.deepcopy(identity)
    notes = seed.get("notes") if isinstance(seed.get("notes"), list) else None
    if notes is not None:
        model["recognitionNotes"] = copy.deepcopy(notes)

    # Explicit provider overrides are authoritative over both seed and JS.
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
    if isinstance(seed.get("domainSubstitutions"), dict):
        substitutions.update(seed["domainSubstitutions"])
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
    recognition_seeds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    seed_providers = (
        recognition_seeds.get("providers")
        if isinstance(recognition_seeds, dict) and isinstance(recognition_seeds.get("providers"), dict)
        else {}
    )
    stats = {
        "providersSeen": 0,
        "providersReconciled": 0,
        "missingEmbeddedModel": 0,
        "currentConfigRoutes": 0,
        "liveValidatedRoutesPreserved": 0,
        "staleCandidatesSuppressed": 0,
        "recipesReconciled": 0,
        "recognitionSeedsUsed": 0,
        "recognitionSeedRoutes": 0,
        "recognitionSeedRequests": 0,
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
        seed = seed_providers.get(provider_id) if isinstance(seed_providers.get(provider_id), dict) else {}
        seed_requests = seed_request_map(seed)
        if seed:
            stats["recognitionSeedsUsed"] += 1
            stats["recognitionSeedRoutes"] += len(unique(seed.get("routes") or [], 256))
            stats["recognitionSeedRequests"] += len(seed_requests)

        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        _sync_effective_config(model, embedded, seed, patch)

        recipe = _effective_recipe(embedded, seed, patch)
        declared_routes, route_source = _declared_routes(embedded, seed, patch, recipe)
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
            old = by_route.get(route)
            row = copy.deepcopy(old or fresh_candidate_row(route))
            was_live = live_validated_reusable(row)
            row["route"] = route
            row["candidateCurrentConfig"] = True
            row["candidateConfigSource"] = route_source
            if route in seed_requests:
                apply_seed_request_contract(row, seed_requests[route])
            if was_live:
                # Seed contract metadata may refine method/headers, but existing live
                # proof for the exact reusable route remains valid.
                row["validationState"] = "live-validated"
                row["executedEvidence"] = bool(old.get("executedEvidence", True)) if isinstance(old, dict) else True
                row["httpUsed"] = bool(old.get("httpUsed", True)) if isinstance(old, dict) else True
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
        reconciled_set = set(reconciled_routes)
        suppressed = [route for route in old_candidate_routes if route not in reconciled_set]
        stats["staleCandidatesSuppressed"] += len(suppressed)
        stats["liveValidatedRoutesPreserved"] += len(preserved_live)

        model["candidateRouteData"] = reconciled_data
        model["candidateRoutes"] = reconciled_routes
        model["candidateReconciliation"] = {
            "version": 2,
            "source": "override>recognition-seed>provider-js>historical-candidate",
            "routePlanSource": route_source,
            "currentConfigRouteCount": len(declared_routes),
            "recognitionSeedPresent": bool(seed),
            "liveValidatedRouteCountPreserved": len(preserved_live),
            "staleCandidateCountSuppressed": len(suppressed),
            "suppressedRoutes": suppressed[:64],
            "newRoutesRequireLiveProof": True,
            "recognitionSeedIsHttpProof": False,
        }
        if isinstance(recipe, dict):
            model["candidateApiRecipe"] = copy.deepcopy(recipe)
            stats["recipesReconciled"] += 1
        else:
            model.pop("candidateApiRecipe", None)
        static_row["model"] = model

        if isinstance(patch, dict):
            patch_seed_routes = declared_routes if route_source == "provider-v3-recognition-seeds" else []
            if isinstance(patch.get("learned_routes"), list):
                patch["candidate_learned_routes"] = unique([*patch["learned_routes"], *preserved_live], 256)
            elif patch_seed_routes:
                patch["candidate_learned_routes"] = unique([*patch_seed_routes, *preserved_live], 256)
            elif "candidate_learned_routes" in patch:
                patch.pop("candidate_learned_routes", None)
            if isinstance(recipe, dict):
                patch["candidate_api_recipe"] = copy.deepcopy(recipe)
            elif "candidate_api_recipe" in patch:
                patch.pop("candidate_api_recipe", None)
            patch["candidate_config_reconciliation"] = {
                "version": 2,
                "route_plan_source": route_source,
                "current_config_route_count": len(declared_routes),
                "recognition_seed_present": bool(seed),
                "live_validated_route_count_preserved": len(preserved_live),
                "stale_candidate_count_suppressed": len(suppressed),
                "new_routes_require_live_proof": True,
                "recognition_seed_is_http_proof": False,
            }

        stats["providersReconciled"] += 1

    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--recognition-seeds", type=Path, default=RECOGNITION_SEEDS)
    args = parser.parse_args()

    root = args.root.resolve()
    manifest_path = args.manifest.resolve()
    knowledge_path = args.knowledge.resolve()
    overrides_path = args.overrides.resolve()
    recognition_path = args.recognition_seeds.resolve()
    manifest = load(manifest_path)
    knowledge = load(knowledge_path)
    overrides = load(overrides_path)
    recognition_seeds = load(recognition_path) if recognition_path.is_file() else {}
    stats = reconcile(root, manifest, knowledge, overrides, recognition_seeds)
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

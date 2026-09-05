#!/usr/bin/env python3
"""Enrich Provider v3 contracts exclusively from NiakVIO-owned durable DATA.

This is the production recognition/materialization input path. It deliberately
performs no HTTP request and reads no external provider repository. Historical
knowledge already absorbed by NiakVIO remains useful as structured DATA, while
future recognition can add routes through NiakVIO observations and reviewed
recognition seeds.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import provider_contract_recognizer as recognizer
from provider_route_normalization_guard import install as install_route_guard
from provider_route_role_classifier import install as install_route_roles
from provider_route_expression_analyzer import install as install_route_analyzer
from provider_route_reconstructor import reconstruct_provider_routes

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
DEFAULT_SEEDS = ROOT / "automation" / "provider-v3-recognition-seeds.json"
OVERRIDES = ROOT / "provider-overrides.json"
EXPECTED = 96
EXECUTABLE_ROLES = {"api", "search", "detail", "player", "source", "episode-index"}

install_route_guard(recognizer)
install_route_roles(recognizer)
install_route_analyzer(recognizer)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique(values: list[str], limit: int = 192) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if not value or value in out:
            continue
        out.append(value)
        if len(out) >= limit:
            break
    return out


def _clean_diagnostic_routes(values: list[Any]) -> list[str]:
    output: list[str] = []
    for raw in values:
        value = recognizer.normalize_dynamic(str(raw or "").strip())
        if value and not recognizer.route_is_junk(value) and value not in output:
            output.append(value)
    return output[:192]


def enrich(payload: dict[str, Any], seeds: dict[str, Any], overrides: dict[str, Any]) -> tuple[dict[str, Any], list[str], int]:
    output = copy.deepcopy(payload)
    providers = output.get("providers")
    if not isinstance(providers, dict) or len(providers) != EXPECTED:
        raise ValueError(f"durable knowledge provider count must be {EXPECTED}")
    seed_providers = seeds.get("providers") if isinstance(seeds.get("providers"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    failures: list[str] = []
    pruned = 0

    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            failures.append(f"{provider_id}: invalid knowledge row")
            continue
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        knowledge = row.get("knowledge") if isinstance(row.get("knowledge"), dict) else {}
        seed = seed_providers.get(provider_id) if isinstance(seed_providers.get(provider_id), dict) else {}
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}

        # Reviewed recognition seeds may refresh current provider-site authority
        # without claiming that any route was executed. This is intentionally
        # separate from route evidence: knownSite/officialSite/officialHub are
        # provenance facts, while seed route rows remain candidates unless their
        # own executedEvidence/httpUsed explicitly says otherwise.
        seed_known_site = str(seed.get("knownSite") or "").strip()
        seed_official_site = str(seed.get("officialSite") or "").strip()
        seed_official_hub = str(seed.get("officialHub") or "").strip()
        if seed_known_site:
            model["knownSite"] = seed_known_site
        if seed_official_site:
            model["officialSite"] = seed_official_site
        elif seed_known_site and not model.get("officialSite"):
            model["officialSite"] = seed_known_site
        if seed_official_hub:
            model["officialHub"] = seed_official_hub

        seed_origins = [str(x) for x in seed.get("origins") or []]
        for value in (seed_official_site, seed_official_hub):
            if value:
                seed_origins.append(value)
        origins = unique([str(x) for x in model.get("origins") or []] + seed_origins, 96)
        if origins:
            model["origins"] = origins
        if isinstance(seed.get("identity"), dict):
            model["identityInput"] = copy.deepcopy(seed["identity"])

        # Keep non-executable knowledge useful for diagnostics, but never retain
        # obvious filenames/assets/HTML attributes as route evidence.
        knowledge["routes"] = _clean_diagnostic_routes(list(knowledge.get("routes") or []))
        knowledge["routeFragments"] = [
            value for value in unique([str(x) for x in knowledge.get("routeFragments") or []], 192)
            if not recognizer.route_is_junk(value)
        ]
        row["model"] = model
        row["knowledge"] = knowledge

        # This is the sole route-materialization step. It updates the unique
        # Provider Object in place and does not reconstruct the provider bundle.
        reconstruct_provider_routes(provider_id, row, seed=seed, patch=patch)
        model = row["model"]
        knowledge = row["knowledge"]
        diagnostics = row.get("recognitionDiagnostics") if isinstance(row.get("recognitionDiagnostics"), dict) else {}
        route_diag = diagnostics.get("routeReconstruction") if isinstance(diagnostics.get("routeReconstruction"), dict) else {}
        pruned += int(route_diag.get("prunedCandidateCount") or 0)

        if seed.get("notes"):
            knowledge["recognitionNotes"] = list(seed.get("notes") or [])
        row["legacyProviderJsExecuted"] = False
        row["upstreamJsExecuted"] = False

        family = str(model.get("sourceRuntimeFamily") or knowledge.get("runtimeFamily") or "unknown").strip().casefold()
        strategy = str(model.get("strategy") or "unknown").strip().casefold()
        executable = bool(model.get("apiRecipe"))
        if not executable and isinstance(patch.get("api_recipe"), dict):
            executable = True
        if not executable and isinstance(patch.get("provider_lego_scripts"), list) and patch.get("provider_lego_scripts"):
            executable = True
        if strategy != "quarantined" and not executable:
            roles = {str(item.get("role") or "") for item in model.get("routeData") or [] if isinstance(item, dict)}
            has_origin = bool(
                model.get("knownSite")
                or model.get("officialSite")
                or model.get("officialHub")
                or model.get("officialApi")
                or model.get("fixedApi")
                or model.get("origins")
            )
            executable = bool(roles & EXECUTABLE_ROLES) and has_origin
        if strategy != "quarantined" and not executable:
            failures.append(
                f"{provider_id}: strategy={strategy} family={family} routes={model.get('routes')!r} has no NiakVIO-local executable plan"
            )

    output["source"] = "niakvio.provider-contract-local-enricher"
    output["role"] = "durable-structured-provider-data"
    output["legacyProviderJsExecuted"] = False
    output["upstreamJsExecuted"] = False
    output["contractRecognition"] = {
        "version": 3,
        "mode": "niakvio-local-data",
        "externalProviderRepositoriesRequired": False,
        "providerJavaScriptExecuted": False,
        "providerCount": len(providers),
        "seedCount": len(seed_providers),
        "prunedRouteCount": pruned,
        "canonicalRouteData": "providers.<id>.model.routeData",
        "routeReconstructionSeparatedFromProviderReconstruction": True,
    }
    return output, failures, pruned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", type=Path, default=DEFAULT_KNOWLEDGE)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    knowledge_path = args.knowledge.resolve()
    seeds = load(args.seeds.resolve()) if args.seeds.is_file() else {"providers": {}}
    overrides = load(OVERRIDES) if OVERRIDES.is_file() else {}
    original = load(knowledge_path)
    enriched, failures, pruned = enrich(original, seeds, overrides)
    if failures:
        for failure in failures:
            print(f"ERROR {failure}")
        return 1
    if args.check:
        print(
            f"Provider v3 local contract recognition check passed providers={EXPECTED} "
            f"pruned={pruned} externalRepositories=0 canonicalRouteData=model.routeData"
        )
        return 0
    write_json(knowledge_path, enriched)
    print(
        f"Provider v3 local contract recognition enriched providers={EXPECTED} "
        f"pruned={pruned} externalRepositories=0 canonicalRouteData=model.routeData"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

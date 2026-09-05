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


def sanitize_route(route: str, *, explicit: bool = False) -> str | None:
    value = recognizer.normalize_dynamic(str(route or "").strip())
    if not value or recognizer.route_is_junk(value):
        return None
    if not recognizer.route_is_executable_candidate(value, explicit=explicit):
        return None
    return value


def merge_requests(rows: list[dict[str, Any]], model_routes: list[str]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    allowed = set(model_routes)
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        route = sanitize_route(str(raw.get("route") or ""), explicit=True)
        if not route or route not in allowed:
            continue
        method = str(raw.get("method") or "GET").strip().upper()
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            method = "GET"
        key = (route, method)
        row = {
            "route": route,
            "role": str(raw.get("role") or recognizer.route_kind(route)).strip().casefold(),
            "method": method,
            "bodyFields": unique([str(x) for x in raw.get("bodyFields") or []], 24),
            "formEncoded": bool(raw.get("formEncoded")),
            "jsonEncoded": bool(raw.get("jsonEncoded")),
            "refererRequired": bool(raw.get("refererRequired")),
            "originRequired": bool(raw.get("originRequired")),
            "response": str(raw.get("response") or "unknown"),
            "executedEvidence": bool(raw.get("executedEvidence")),
            "evidence": str(raw.get("evidence") or "niakvio-durable-data"),
            "confidence": float(raw.get("confidence") or 0.8),
        }
        if key not in by_key:
            by_key[key] = row
            order.append(key)
            continue
        target = by_key[key]
        target["bodyFields"] = unique(target["bodyFields"] + row["bodyFields"], 24)
        for field in ("formEncoded", "jsonEncoded", "refererRequired", "originRequired", "executedEvidence"):
            target[field] = bool(target[field] or row[field])
        target["confidence"] = max(float(target["confidence"]), float(row["confidence"]))
        if target["response"] == "unknown" and row["response"] != "unknown":
            target["response"] = row["response"]
    return [by_key[key] for key in order]


def generic_request(route: str, *, explicit: bool) -> dict[str, Any]:
    return {
        "route": route,
        "role": recognizer.route_kind(route),
        "method": "GET",
        "bodyFields": [],
        "formEncoded": False,
        "jsonEncoded": False,
        "refererRequired": False,
        "originRequired": False,
        "response": "unknown",
        "executedEvidence": explicit,
        "evidence": "niakvio-owned-route-data",
        "confidence": 0.9 if explicit else 0.75,
    }


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

        existing = [str(x) for x in model.get("routes") or []]
        explicit = [str(x) for x in patch.get("learned_routes") or []]
        seeded = [str(x) for x in seed.get("routes") or []]
        explicit_set = set(explicit) | set(seeded)

        routes: list[str] = []
        for raw in explicit + seeded:
            route = sanitize_route(raw, explicit=True)
            if route and route not in routes:
                routes.append(route)
        for raw in existing:
            route = sanitize_route(raw, explicit=raw in explicit_set)
            if route and route not in routes:
                routes.append(route)
            elif not route:
                pruned += 1
        model["routes"] = routes[:192]

        if seed.get("knownSite"):
            model["knownSite"] = str(seed["knownSite"])
            if not model.get("officialSite"):
                model["officialSite"] = str(seed["knownSite"])
        origins = unique([str(x) for x in model.get("origins") or []] + [str(x) for x in seed.get("origins") or []], 96)
        if origins:
            model["origins"] = origins
        if isinstance(seed.get("identity"), dict):
            model["identityInput"] = copy.deepcopy(seed["identity"])

        previous_contract = knowledge.get("recognizedContract") if isinstance(knowledge.get("recognizedContract"), dict) else {}
        previous_requests = previous_contract.get("requests") if isinstance(previous_contract.get("requests"), list) else []
        seed_requests = seed.get("requests") if isinstance(seed.get("requests"), list) else []
        requests = merge_requests(list(previous_requests) + list(seed_requests), model["routes"])
        request_routes = {str(x.get("route") or "") for x in requests}
        for route in model["routes"]:
            if route not in request_routes:
                requests.append(generic_request(route, explicit=route in {sanitize_route(x, explicit=True) for x in explicit_set}))

        # Knowledge remains useful for diagnostics, but executable route DATA is the
        # cleaned model set. Static fragments that look like source filenames or
        # HTML attributes are pruned here as well.
        knowledge_routes: list[str] = []
        for raw in knowledge.get("routes") or []:
            value = recognizer.normalize_dynamic(str(raw or "").strip())
            if value and not recognizer.route_is_junk(value) and value not in knowledge_routes:
                knowledge_routes.append(value)
        knowledge["routes"] = knowledge_routes[:192]
        knowledge["routeFragments"] = [
            value for value in unique([str(x) for x in knowledge.get("routeFragments") or []], 192)
            if not recognizer.route_is_junk(value)
        ]

        family = str(model.get("sourceRuntimeFamily") or knowledge.get("runtimeFamily") or "unknown").strip().casefold()
        knowledge["recognizedContract"] = {
            "version": 2,
            "sourceMode": "niakvio-local-data",
            "externalRepositoryRequired": False,
            "providerJavaScriptExecuted": False,
            "runtimeFamily": family,
            "identity": copy.deepcopy(model.get("identityInput") or {}),
            "requests": requests[:128],
            "executableRouteCount": len(model["routes"]),
            "confidence": max([float(x.get("confidence") or 0) for x in requests] or [0.75]),
        }
        if seed.get("notes"):
            knowledge["recognitionNotes"] = list(seed.get("notes") or [])
        row["model"] = model
        row["knowledge"] = knowledge
        row["legacyProviderJsExecuted"] = False
        row["upstreamJsExecuted"] = False

        strategy = str(model.get("strategy") or "unknown").strip().casefold()
        executable = bool(model.get("apiRecipe"))
        if not executable and isinstance(patch.get("api_recipe"), dict):
            executable = True
        if not executable and isinstance(patch.get("provider_lego_scripts"), list) and patch.get("provider_lego_scripts"):
            executable = True
        if strategy != "quarantined" and not executable:
            roles = {recognizer.route_kind(route) for route in model["routes"]}
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
                f"{provider_id}: strategy={strategy} family={family} routes={model['routes']!r} has no NiakVIO-local executable plan"
            )

    output["source"] = "niakvio.provider-contract-local-enricher"
    output["role"] = "durable-structured-provider-data"
    output["legacyProviderJsExecuted"] = False
    output["upstreamJsExecuted"] = False
    output["contractRecognition"] = {
        "version": 2,
        "mode": "niakvio-local-data",
        "externalProviderRepositoriesRequired": False,
        "providerJavaScriptExecuted": False,
        "providerCount": len(providers),
        "seedCount": len(seed_providers),
        "prunedRouteCount": pruned,
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
            f"pruned={pruned} externalRepositories=0"
        )
        return 0
    write_json(knowledge_path, enriched)
    print(
        f"Provider v3 local contract recognition enriched providers={EXPECTED} "
        f"pruned={pruned} externalRepositories=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

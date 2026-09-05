#!/usr/bin/env python3
"""Reconstruct canonical route DATA on one NiakVIO Provider Object.

This module is deliberately independent from full provider reconstruction.  The
same per-provider function can be called while a provider is being created or by
an offline 96/96 route-only sweep.

No provider JavaScript is executed.  Optional source text is analysed only by the
bounded static expression analyser already owned by NiakVIO.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Iterable

import provider_contract_recognizer as recognizer
from provider_route_expression_analyzer import (
    expression_request_contracts,
    extract_expression_routes,
    install as install_route_analyzer,
)
from provider_route_normalization_guard import install as install_route_guard
from provider_route_role_classifier import install as install_route_roles

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
DEFAULT_SEEDS = ROOT / "automation" / "provider-v3-recognition-seeds.json"
DEFAULT_OVERRIDES = ROOT / "provider-overrides.json"
EXPECTED_PROVIDERS = 96
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

install_route_guard(recognizer)
install_route_roles(recognizer)
install_route_analyzer(recognizer)


def _load(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.is_file():
        return copy.deepcopy(default or {})
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _unique_strings(values: Iterable[Any], limit: int = 192) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if not value or value in out:
            continue
        out.append(value)
        if len(out) >= limit:
            break
    return out


def _sanitize_route(route: Any, *, explicit: bool = False) -> str | None:
    value = recognizer.normalize_dynamic(str(route or "").strip())
    if not value or recognizer.route_is_junk(value):
        return None
    if not recognizer.route_is_executable_candidate(value, explicit=explicit):
        return None
    return value


def _request_row(raw: dict[str, Any], *, explicit: bool = False, default_evidence: str) -> dict[str, Any] | None:
    route = _sanitize_route(raw.get("route"), explicit=explicit)
    if not route:
        return None
    method = str(raw.get("method") or "GET").strip().upper()
    if method not in HTTP_METHODS:
        method = "GET"
    confidence = float(raw.get("confidence") or (0.9 if explicit else 0.75))
    evidence = str(raw.get("evidence") or default_evidence).strip() or default_evidence
    evidence_sources = _unique_strings(list(raw.get("evidenceSources") or []) + [evidence], 24)
    executed = bool(raw.get("executedEvidence") or raw.get("httpUsed"))
    return {
        "route": route,
        "role": str(raw.get("role") or recognizer.route_kind(route)).strip().casefold(),
        "method": method,
        "bodyFields": _unique_strings(raw.get("bodyFields") or [], 24),
        "formEncoded": bool(raw.get("formEncoded")),
        "jsonEncoded": bool(raw.get("jsonEncoded")),
        "refererRequired": bool(raw.get("refererRequired")),
        "originRequired": bool(raw.get("originRequired")),
        "response": str(raw.get("response") or "unknown").strip() or "unknown",
        "executedEvidence": executed,
        "httpUsed": executed,
        "evidence": evidence,
        "evidenceSources": evidence_sources,
        "confidence": max(0.0, min(1.0, confidence)),
    }


def _generic_route_row(route: str, *, explicit: bool, evidence: str) -> dict[str, Any]:
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
        "executedEvidence": False,
        "httpUsed": False,
        "evidence": evidence,
        "evidenceSources": [evidence],
        "confidence": 0.9 if explicit else 0.75,
    }


def _merge_route_data(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        normalized = _request_row(raw, explicit=True, default_evidence="niakvio-route-reconstruction")
        if not normalized:
            continue
        key = (normalized["route"], normalized["method"])
        if key not in by_key:
            by_key[key] = normalized
            order.append(key)
            continue
        target = by_key[key]
        target["bodyFields"] = _unique_strings(target["bodyFields"] + normalized["bodyFields"], 24)
        target["evidenceSources"] = _unique_strings(target["evidenceSources"] + normalized["evidenceSources"], 24)
        for field in ("formEncoded", "jsonEncoded", "refererRequired", "originRequired", "executedEvidence", "httpUsed"):
            target[field] = bool(target[field] or normalized[field])
        if target["response"] == "unknown" and normalized["response"] != "unknown":
            target["response"] = normalized["response"]
        if target["role"] in {"", "other"} and normalized["role"] not in {"", "other"}:
            target["role"] = normalized["role"]
        if float(normalized["confidence"]) > float(target["confidence"]):
            target["confidence"] = normalized["confidence"]
            target["evidence"] = normalized["evidence"]
    return [by_key[key] for key in order][:192]


def _compat_requests(route_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the old recognizedContract.requests view as a derived projection."""
    fields = (
        "route", "role", "method", "bodyFields", "formEncoded", "jsonEncoded",
        "refererRequired", "originRequired", "response", "executedEvidence",
        "evidence", "confidence",
    )
    return [{field: copy.deepcopy(row.get(field)) for field in fields} for row in route_data]


def reconstruct_provider_routes(
    provider_id: str,
    provider_object: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
    patch: dict[str, Any] | None = None,
    source_text: str | None = None,
) -> dict[str, Any]:
    """Populate canonical route DATA on one Provider Object and return it.

    `provider_object` is the unique row held under static-knowledge.providers[id].
    Full provider reconstruction is intentionally out of scope.  Re-running this
    function is idempotent for identical inputs.
    """
    if not isinstance(provider_object, dict):
        raise TypeError(f"{provider_id}: provider object must be a dict")
    seed = seed if isinstance(seed, dict) else {}
    patch = patch if isinstance(patch, dict) else {}
    model = provider_object.get("model") if isinstance(provider_object.get("model"), dict) else {}
    knowledge = provider_object.get("knowledge") if isinstance(provider_object.get("knowledge"), dict) else {}

    previous_contract = knowledge.get("recognizedContract") if isinstance(knowledge.get("recognizedContract"), dict) else {}
    previous_requests = previous_contract.get("requests") if isinstance(previous_contract.get("requests"), list) else []
    previous_route_data = model.get("routeData") if isinstance(model.get("routeData"), list) else []
    seed_requests = seed.get("requests") if isinstance(seed.get("requests"), list) else []

    explicit_raw = [str(x) for x in patch.get("learned_routes") or []] + [str(x) for x in seed.get("routes") or []]
    explicit_routes = {
        value for value in (_sanitize_route(raw, explicit=True) for raw in explicit_raw) if value
    }

    candidates: list[tuple[Any, bool, str]] = []
    candidates.extend((raw, True, "niakvio-reviewed-route-data") for raw in explicit_raw)
    candidates.extend((raw, False, "niakvio-model-route-data") for raw in model.get("routes") or [])
    candidates.extend((raw, False, "niakvio-knowledge-route-data") for raw in knowledge.get("routes") or [])
    candidates.extend((raw, False, "niakvio-route-fragment-data") for raw in knowledge.get("routeFragments") or [])

    routes: list[str] = []
    route_evidence: dict[str, list[str]] = {}
    pruned = 0
    for raw, explicit, evidence in candidates:
        route = _sanitize_route(raw, explicit=explicit)
        if not route:
            if str(raw or "").strip():
                pruned += 1
            continue
        if route not in routes:
            routes.append(route)
        route_evidence.setdefault(route, [])
        if evidence not in route_evidence[route]:
            route_evidence[route].append(evidence)

    rows: list[dict[str, Any]] = []
    for raw in list(previous_route_data) + list(previous_requests):
        if isinstance(raw, dict):
            row = _request_row(raw, explicit=str(raw.get("route") or "") in explicit_routes, default_evidence="niakvio-existing-route-data")
            if row:
                rows.append(row)
    for raw in seed_requests:
        if isinstance(raw, dict):
            row = _request_row(raw, explicit=True, default_evidence="niakvio-recognition-seed")
            if row:
                rows.append(row)

    if source_text:
        expression_routes, expression_evidence, _decoded = extract_expression_routes(source_text, recognizer)
        for route in expression_routes:
            clean = _sanitize_route(route, explicit=False)
            if not clean:
                continue
            if clean not in routes:
                routes.append(clean)
            meta = expression_evidence.get(route) or {}
            evidence = str(meta.get("evidence") or "static-expression-analysis")
            route_evidence.setdefault(clean, [])
            if evidence not in route_evidence[clean]:
                route_evidence[clean].append(evidence)
        for raw in expression_request_contracts(source_text, recognizer):
            if isinstance(raw, dict):
                row = _request_row(raw, explicit=False, default_evidence="static-expression-analysis")
                if row:
                    rows.append(row)

    merged = _merge_route_data(rows)
    represented = {str(row.get("route") or "") for row in merged}
    for route in routes:
        if route in represented:
            continue
        explicit = route in explicit_routes
        evidence = (route_evidence.get(route) or ["niakvio-reviewed-route-data" if explicit else "niakvio-owned-route-data"])[0]
        merged.append(_generic_route_row(route, explicit=explicit, evidence=evidence))

    # Enrich merged rows with every independent provenance signal for the same route.
    for row in merged:
        route = str(row.get("route") or "")
        row["evidenceSources"] = _unique_strings(
            list(row.get("evidenceSources") or []) + route_evidence.get(route, []), 24
        )
        row["httpUsed"] = bool(row.get("executedEvidence"))

    # routes is deliberately derived from canonical routeData, not maintained in parallel.
    canonical_routes = _unique_strings([row.get("route") for row in merged], 192)
    model["routeData"] = merged[:192]
    model["routes"] = canonical_routes
    executed_count = sum(1 for row in model["routeData"] if row.get("httpUsed"))
    model["routeRecognition"] = {
        "version": 1,
        "status": "recognized" if model["routeData"] else "unknown",
        "routeCount": len(model["routeData"]),
        "httpProvenRouteCount": executed_count,
        "providerJavaScriptExecuted": False,
        "fullProviderReconstructionRequired": False,
    }

    # Diagnostics/legacy consumers keep a projection; routeData is the canonical owner.
    family = str(model.get("sourceRuntimeFamily") or knowledge.get("runtimeFamily") or "unknown").strip().casefold()
    knowledge["recognizedContract"] = {
        "version": 3,
        "sourceMode": "niakvio-local-data",
        "externalRepositoryRequired": False,
        "providerJavaScriptExecuted": False,
        "runtimeFamily": family,
        "identity": copy.deepcopy(model.get("identityInput") or {}),
        "requests": _compat_requests(model["routeData"]),
        "executableRouteCount": len(model["routes"]),
        "httpProvenRouteCount": executed_count,
        "confidence": max([float(row.get("confidence") or 0) for row in model["routeData"]] or [0.0]),
        "canonicalRouteData": "model.routeData",
    }
    provider_object["model"] = model
    provider_object["knowledge"] = knowledge
    provider_object["legacyProviderJsExecuted"] = False
    provider_object["upstreamJsExecuted"] = False
    provider_object.setdefault("recognitionDiagnostics", {})
    if isinstance(provider_object["recognitionDiagnostics"], dict):
        provider_object["recognitionDiagnostics"]["routeReconstruction"] = {
            "providerId": provider_id,
            "prunedCandidateCount": pruned,
            "routeCount": len(model["routeData"]),
            "status": model["routeRecognition"]["status"],
        }
    return provider_object


def reconstruct_all_routes(
    payload: dict[str, Any],
    *,
    seeds: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
    provider_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Route-only sweep.  It never invokes full provider reconstruction."""
    output = copy.deepcopy(payload)
    providers = output.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("knowledge.providers object required")
    seed_rows = (seeds or {}).get("providers") if isinstance((seeds or {}).get("providers"), dict) else {}
    patches = (overrides or {}).get("provider_patches") if isinstance((overrides or {}).get("provider_patches"), dict) else {}
    selected = [provider_id] if provider_id else list(providers)
    unknown: list[str] = []
    total_routes = 0
    http_proven = 0
    for pid in selected:
        row = providers.get(pid)
        if not isinstance(row, dict):
            raise KeyError(f"unknown provider: {pid}")
        reconstruct_provider_routes(
            pid,
            row,
            seed=seed_rows.get(pid) if isinstance(seed_rows.get(pid), dict) else {},
            patch=patches.get(pid) if isinstance(patches.get(pid), dict) else {},
        )
        route_data = row.get("model", {}).get("routeData") or []
        total_routes += len(route_data)
        http_proven += sum(1 for item in route_data if isinstance(item, dict) and item.get("httpUsed"))
        if not route_data:
            unknown.append(pid)
    report = {
        "providerCount": len(selected),
        "routeCount": total_routes,
        "httpProvenRouteCount": http_proven,
        "unknownProviders": unknown,
        "fullProviderReconstructionInvoked": False,
        "providerJavaScriptExecuted": False,
    }
    output["routeReconstruction"] = {
        "version": 1,
        "canonicalRouteData": "providers.<id>.model.routeData",
        **report,
    }
    return output, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconstruct route DATA only; do not rebuild providers")
    parser.add_argument("--knowledge", type=Path, default=DEFAULT_KNOWLEDGE)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--provider", dest="provider_id")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = _load(args.knowledge.resolve())
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("knowledge.providers object required")
    if not args.provider_id and len(providers) != EXPECTED_PROVIDERS:
        raise ValueError(f"route sweep expects {EXPECTED_PROVIDERS} providers, got {len(providers)}")
    seeds = _load(args.seeds.resolve(), {"providers": {}})
    overrides = _load(args.overrides.resolve(), {"provider_patches": {}})
    output, report = reconstruct_all_routes(
        payload,
        seeds=seeds,
        overrides=overrides,
        provider_id=args.provider_id,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if args.check:
        return 0
    target = (args.output or args.knowledge).resolve()
    _write(target, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

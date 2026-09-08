#!/usr/bin/env python3
"""V19: bridge live-positive search calls to reviewed request contracts.

A live provider trace can prove that a POST search call is causal and successful
while the route-proof dataflow sanitizer deliberately refuses to mark its exact
body reusable.  Dropping that call entirely loses real providers.  V19 keeps the
safety boundary: the live trace owns origin/route/method/semantic lane, while the
request *shape* may come only from either:

1. another successful observed call to the exact same origin+route+method whose
   sanitized requestSpec is reusable, or
2. an exact route+method contract already marked executed/reviewed in durable
   NiakVIO DATA.

No provider id, hostname, fixture title, opaque token or provider-specific route
is encoded in this algorithm.  Static DATA can never create a network authority
without a matching live-positive request in the current recovery report.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
SEEDS = ROOT / "automation" / "provider-v3-recognition-seeds.json"
PROOF_VERSION = 5
MARKER = "PROVIDER_LIVE_REQUEST_CONTRACT_BRIDGE_V19"

_QUERY_FIELDS = {
    "q", "query", "search", "search_query", "searchquery", "story", "title", "keyword", "keywords"
}
_SAFE_STATIC_HEADERS = {"accept", "content-type", "origin", "referer", "x-requested-with"}
# Only neutral pagination sentinels are generic enough to synthesize from a
# reviewed body-field contract.  Authentication/session/file ids remain forbidden.
_NEUTRAL_CONTRACT_DEFAULTS: dict[str, Any] = {"page_token": None, "page_index": 0}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _positive(row: dict[str, Any]) -> bool:
    status = int(row.get("status") or 0)
    return (
        200 <= status < 400
        and (int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0)
    )


def _searchish(row: dict[str, Any]) -> bool:
    role = str(row.get("role") or "").strip().casefold()
    route = str(row.get("route") or "").strip().casefold()
    if role == "search" or re.search(r"/(?:search|recherche)(?:[/?#.:_-]|$)", route):
        return True
    spec = row.get("requestSpec") if isinstance(row.get("requestSpec"), dict) else {}
    body = spec.get("body") if isinstance(spec.get("body"), dict) else {}
    return any(str(key).casefold() in _QUERY_FIELDS or "{query}" in str(value) for key, value in body.items())


def _same_request(a: dict[str, Any], b: dict[str, Any], *, include_origin: bool = True) -> bool:
    if str(a.get("route") or "").strip() != str(b.get("route") or "").strip():
        return False
    if str(a.get("method") or "GET").upper() != str(b.get("method") or "GET").upper():
        return False
    if include_origin and str(a.get("origin") or "").rstrip("/") != str(b.get("origin") or "").rstrip("/"):
        return False
    return True


def _observed_sibling_spec(row: dict[str, Any], route_data: list[dict[str, Any]]) -> dict[str, Any] | None:
    for other in route_data:
        if not isinstance(other, dict) or other.get("requestSpecReusable") is not True:
            continue
        if not _same_request(row, other, include_origin=True):
            continue
        status = int(other.get("status") or 0)
        spec = other.get("requestSpec") if isinstance(other.get("requestSpec"), dict) else None
        if 200 <= status < 400 and spec:
            return copy.deepcopy(spec)
    return None


def _contract_executed(contract: dict[str, Any]) -> bool:
    return bool(contract.get("executedEvidence") or contract.get("httpUsed"))


def _static_contract_spec(contract: dict[str, Any], origin: str) -> dict[str, Any] | None:
    if not _contract_executed(contract):
        return None
    method = str(contract.get("method") or "GET").upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}:
        return None

    # If durable DATA already contains a sanitized reusable requestSpec, retain
    # only the safe transport fields.  Secret/token-bearing headers are never
    # imported from static contracts by this bridge.
    raw_spec = contract.get("requestSpec") if isinstance(contract.get("requestSpec"), dict) else None
    if raw_spec:
        raw_headers = raw_spec.get("headers") if isinstance(raw_spec.get("headers"), dict) else {}
        headers = {
            str(key): copy.deepcopy(value)
            for key, value in raw_headers.items()
            if str(key).casefold() in _SAFE_STATIC_HEADERS
        }
        spec: dict[str, Any] = {"method": method, "headers": headers}
        body_kind = str(raw_spec.get("bodyKind") or "").casefold()
        body = raw_spec.get("body") if isinstance(raw_spec.get("body"), dict) else None
        if body_kind in {"json", "form"} and body is not None:
            spec["bodyKind"] = body_kind
            spec["body"] = copy.deepcopy(body)
        return spec

    fields = [str(value).strip() for value in contract.get("bodyFields") or [] if str(value).strip()]
    defaults = contract.get("bodyDefaults") if isinstance(contract.get("bodyDefaults"), dict) else {}
    body: dict[str, Any] = {}
    for field in fields:
        key = field.casefold()
        if key in _QUERY_FIELDS:
            body[field] = "{query}"
        elif field in defaults:
            body[field] = copy.deepcopy(defaults[field])
        elif key in defaults:
            body[field] = copy.deepcopy(defaults[key])
        elif key in _NEUTRAL_CONTRACT_DEFAULTS:
            body[field] = copy.deepcopy(_NEUTRAL_CONTRACT_DEFAULTS[key])
        else:
            # Unknown dynamic fields are exactly where the original sanitizer
            # refused reuse.  Do not guess them here.
            return None

    headers: dict[str, Any] = {}
    if contract.get("jsonEncoded") is True:
        body_kind = "json"
        headers["Content-Type"] = "application/json"
    elif contract.get("formEncoded") is True:
        body_kind = "form"
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    else:
        body_kind = ""
    if contract.get("refererRequired") is True and origin:
        headers["Referer"] = origin.rstrip("/") + "/"
    if contract.get("originRequired") is True and origin:
        headers["Origin"] = origin.rstrip("/")

    spec = {"method": method, "headers": headers}
    if body:
        if not body_kind:
            return None
        spec["bodyKind"] = body_kind
        spec["body"] = body
    return spec


def _durable_contracts(provider_id: str, static_row: dict[str, Any], seed_row: dict[str, Any]) -> list[dict[str, Any]]:
    model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
    knowledge = static_row.get("knowledge") if isinstance(static_row.get("knowledge"), dict) else {}
    recognized = knowledge.get("recognizedContract") if isinstance(knowledge.get("recognizedContract"), dict) else {}
    rows: list[dict[str, Any]] = []
    for source in (
        seed_row.get("requests") if isinstance(seed_row.get("requests"), list) else [],
        model.get("routeData") if isinstance(model.get("routeData"), list) else [],
        recognized.get("requests") if isinstance(recognized.get("requests"), list) else [],
    ):
        for row in source:
            if isinstance(row, dict):
                rows.append(row)
    return rows


def build_live_search_plans(
    route_data: list[dict[str, Any]],
    durable_contracts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return only live-positive plans whose missing request shape is proven."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in route_data:
        if not isinstance(row, dict) or not _positive(row) or not _searchish(row):
            continue
        if row.get("requestSpecReusable") is True and isinstance(row.get("requestSpec"), dict):
            # V14 already owns fully reusable positive requests.
            continue
        origin = str(row.get("origin") or "").strip().rstrip("/")
        route = str(row.get("route") or "").strip()
        method = str(row.get("method") or "GET").upper()
        if not origin.startswith(("http://", "https://")) or not route:
            continue

        spec = _observed_sibling_spec(row, route_data)
        authority = "observed-same-request"
        if spec is None:
            authority = "reviewed-executed-contract"
            for contract in durable_contracts:
                if not isinstance(contract, dict) or not _same_request(row, contract, include_origin=False):
                    continue
                spec = _static_contract_spec(contract, origin)
                if spec is not None:
                    break
        if spec is None or str(spec.get("method") or method).upper() != method:
            continue

        semantic = str(row.get("semanticType") or "").strip().casefold()
        plan = {
            "base": origin,
            "route": route,
            "requestSpec": spec,
            "proofModelVersion": PROOF_VERSION,
            "sourceRole": "catalog-search-live-contract-bridge",
            "semanticTypes": [semantic] if semantic in {"movie", "tv", "anime"} else [],
            "requestShapeAuthority": authority,
        }
        fp = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if fp not in seen:
            seen.add(fp)
            out.append(plan)
    return out[:12]


def apply_recovery_bridge(report: dict[str, Any]) -> dict[str, Any]:
    overrides = load(OVERRIDES)
    knowledge = load(KNOWLEDGE)
    seeds = load(SEEDS) if SEEDS.exists() else {"providers": {}}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    seed_providers = seeds.get("providers") if isinstance(seeds.get("providers"), dict) else {}

    bridged_providers = 0
    bridged_plans = 0
    sibling_plans = 0
    reviewed_plans = 0
    for recovered in report.get("providers") or []:
        if not isinstance(recovered, dict):
            continue
        provider_id = cid(recovered.get("providerId"))
        patch = patches.get(provider_id)
        static_row = providers.get(provider_id)
        if not provider_id or not isinstance(patch, dict) or not isinstance(static_row, dict):
            continue
        route_data = [row for row in recovered.get("routeData") or [] if isinstance(row, dict)]
        if not route_data:
            continue
        seed_row = seed_providers.get(provider_id) if isinstance(seed_providers.get(provider_id), dict) else {}
        contracts = _durable_contracts(provider_id, static_row, seed_row)
        plans = build_live_search_plans(route_data, contracts)
        if not plans:
            continue

        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        existing = patch.get("search_request_plan") if isinstance(patch.get("search_request_plan"), list) else []
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for plan in [*existing, *plans]:
            if not isinstance(plan, dict):
                continue
            fp = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if fp in seen:
                continue
            seen.add(fp)
            merged.append(copy.deepcopy(plan))
        patch["search_request_plan"] = merged[:12]
        model["searchRequestPlan"] = copy.deepcopy(merged[:12])
        patch["identity_input"] = {
            "mode": "catalog_search",
            "requires_tmdb_before_run": True,
            "required_fields": ["title", "mediaType"],
        }
        model["identityInput"] = {
            "mode": "catalog_search",
            "requiresTmdbBeforeRun": True,
            "requiredFields": ["title", "mediaType"],
        }
        static_row["model"] = model
        providers[provider_id] = static_row
        patches[provider_id] = patch
        bridged_providers += 1
        bridged_plans += len(plans)
        sibling_plans += sum(1 for plan in plans if plan.get("requestShapeAuthority") == "observed-same-request")
        reviewed_plans += sum(1 for plan in plans if plan.get("requestShapeAuthority") == "reviewed-executed-contract")

    overrides["provider_patches"] = patches
    knowledge["providers"] = providers
    write(OVERRIDES, overrides)
    write(KNOWLEDGE, knowledge)
    summary = {
        "marker": MARKER,
        "bridgedProviders": bridged_providers,
        "bridgedPlans": bridged_plans,
        "observedSiblingPlans": sibling_plans,
        "reviewedContractPlans": reviewed_plans,
        "staticAuthorityWithoutLivePositive": 0,
    }
    print(
        "FIELD_PROVIDER_LIVE_REQUEST_BRIDGE_V19 "
        f"providers={bridged_providers} plans={bridged_plans} sibling={sibling_plans} reviewed={reviewed_plans} "
        "static_without_live_positive=0 provider_specific_rules=0",
        flush=True,
    )
    return summary


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    path = args.report if args.report.is_absolute() else ROOT / args.report
    report = load(path)
    summary = apply_recovery_bridge(report)
    report["liveRequestContractBridgeV19"] = summary
    write(path, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

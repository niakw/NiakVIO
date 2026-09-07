#!/usr/bin/env python3
"""Wire abstracted proof-v5 request specs into recovery/bootstrap producers."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_provider_v3_routes.py"
MARKER = "ROUTE_RECOVERY_REQUEST_SPEC_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    if MARKER in text:
        return False

    old = '''    return {
        "route": route,
        "origin": derivation.get("origin"),
        "role": route_role(route),
        "method": str(fetch.get("method") or "GET").upper(),
        "semanticType": semantic_type,
        "fixture": fixture_slug,
        "requestIndex": int(derived.get("index") or 0),
        "providerValueCorrelation": bool(derivation.get("providerValueCorrelation")),
        "headers": copy.deepcopy(fetch.get("proof_headers") or {}),
        "bodyKind": fetch.get("body_kind") or "none",
        "bodyFields": list(fetch.get("body_fields") or []),
        "bodyValues": copy.deepcopy(fetch.get("body_values") or {}),
        "status": int(fetch.get("status") or 0),
        "contentType": fetch.get("content_type"),
        "proofModelVersion": PROOF_VERSION,
        "source": copy.deepcopy(source_meta),
    }
'''
    new = '''    request_spec = derivation.get("requestSpec") if isinstance(derivation.get("requestSpec"), dict) else None
    return {
        "route": route,
        "origin": derivation.get("origin"),
        "role": route_role(route),
        "method": str(fetch.get("method") or "GET").upper(),
        "semanticType": semantic_type,
        "fixture": fixture_slug,
        "requestIndex": int(derived.get("index") or 0),
        "providerValueCorrelation": bool(derivation.get("providerValueCorrelation")),
        "requestSpec": copy.deepcopy(request_spec),
        "requestSpecReusable": bool(derivation.get("requestSpecReusable")),
        "status": int(fetch.get("status") or 0),
        "contentType": fetch.get("content_type"),
        "proofModelVersion": PROOF_VERSION,
        "source": copy.deepcopy(source_meta),
    }
'''
    text = once(text, old, new, "recovery-record-request-spec")

    old_spec = '''def request_spec(record: dict[str, Any]) -> dict[str, Any] | None:
    method = str(record.get("method") or "GET").upper()
    headers = record.get("headers") if isinstance(record.get("headers"), dict) else {}
    body_kind = str(record.get("bodyKind") or "none")
    body_values = record.get("bodyValues") if isinstance(record.get("bodyValues"), dict) else {}
    if method == "GET" and not headers and body_kind in {"none", "empty"}:
        return None
    spec: dict[str, Any] = {"method": method}
    if headers:
        spec["headers"] = copy.deepcopy(headers)
    if body_values and body_kind in {"json", "form"}:
        spec["bodyKind"] = body_kind
        spec["body"] = copy.deepcopy(body_values)
    elif body_kind not in {"none", "empty"} and method != "GET":
        return None
    return spec
'''
    new_spec = '''def request_spec(record: dict[str, Any]) -> dict[str, Any] | None:
    spec = record.get("requestSpec") if isinstance(record.get("requestSpec"), dict) else None
    return copy.deepcopy(spec) if record.get("requestSpecReusable") is True and spec else None


def generic_execution_route(record: dict[str, Any]) -> bool:
    """Whether routes[] may replay this call without losing HTTP semantics."""
    spec = request_spec(record) or {"method": str(record.get("method") or "GET").upper()}
    if str(spec.get("method") or "GET").upper() != "GET":
        return False
    if spec.get("body"):
        return False
    headers = spec.get("headers") if isinstance(spec.get("headers"), dict) else {}
    nontrivial = {
        str(key).casefold() for key in headers
        if str(key).casefold() not in {"accept", "accept-language", "user-agent"}
    }
    return not nontrivial
'''
    text = once(text, old_spec, new_spec, "recovery-request-spec-reader")

    old_routes = '''    routes = unique([row.get("route") for row in deduped], 192)
    recipe = build_simple_api_recipe(deduped)
    return {
'''
    new_routes = '''    routes = unique([row.get("route") for row in deduped], 192)
    execution_routes = unique([row.get("route") for row in deduped if generic_execution_route(row)], 192)
    recipe = build_simple_api_recipe([row for row in deduped if row.get("requestSpecReusable") is True])
    return {
'''
    text = once(text, old_routes, new_routes, "recovery-execution-route-split")
    text = once(
        text,
        '''        "routeCount": len(routes),
        "routes": routes,
        "routeData": deduped,
''',
        '''        "routeCount": len(routes),
        "routes": routes,
        "executionRouteCount": len(execution_routes),
        "executionRoutes": execution_routes,
        "routeData": deduped,
''',
        "recovery-return-execution-routes",
    )

    text = once(
        text,
        '''        proven_routes = unique(recovered.get("routes") or [], 192)
        route_data = copy.deepcopy(recovered.get("routeData") or [])
        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None
        patch["learned_routes"] = proven_routes
        model["routes"] = proven_routes
''',
        '''        proven_routes = unique(recovered.get("routes") or [], 192)
        execution_routes = unique(recovered.get("executionRoutes") or [], 192)
        route_data = copy.deepcopy(recovered.get("routeData") or [])
        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None
        patch["learned_routes"] = execution_routes
        model["routes"] = execution_routes
''',
        "recovery-apply-execution-routes",
    )
    text = text.replace('"provenRouteCount": len(proven_routes),', '"provenRouteCount": len(proven_routes),\n            "genericExecutionRouteCount": len(execution_routes),', 1)
    text = text.replace('routes_total += len(proven_routes)', 'routes_total += len(proven_routes)', 1)
    text = text.replace(
        '"proofRequirements": [',
        f'"requestSpecModel": "{MARKER}",\n        "proofRequirements": [',
        1,
    )
    RECOVERY.write_text(text, encoding="utf-8")
    return True


def patch_bootstrap() -> bool:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    old = '''                route_data.append({
                    "route": route,
                    "origin": meta.get("origin"),
                    "role": route_role(route),
                    "method": str(fetch.get("method") or "GET").upper(),
                    "semanticType": semantic_type,
                    "fixture": fixture["slug"],
                    "providerValueCorrelation": bool(meta.get("providerValueCorrelation")),
                    "headers": copy.deepcopy(fetch.get("proof_headers") or {}),
                    "bodyKind": fetch.get("body_kind") or "none",
                    "bodyFields": list(fetch.get("body_fields") or []),
                    "bodyValues": copy.deepcopy(fetch.get("body_values") or {}),
                    "status": int(fetch.get("status") or 0),
                    "contentType": fetch.get("content_type"),
                    "proofModelVersion": PROOF_VERSION,
                    "validationState": "live-validated",
                    "executedEvidence": True,
                    "httpUsed": True,
                })
'''
    new = '''                request_spec = meta.get("requestSpec") if isinstance(meta.get("requestSpec"), dict) else None
                route_data.append({
                    "route": route,
                    "origin": meta.get("origin"),
                    "role": route_role(route),
                    "method": str(fetch.get("method") or "GET").upper(),
                    "semanticType": semantic_type,
                    "fixture": fixture["slug"],
                    "providerValueCorrelation": bool(meta.get("providerValueCorrelation")),
                    "requestSpec": copy.deepcopy(request_spec),
                    "requestSpecReusable": bool(meta.get("requestSpecReusable")),
                    "status": int(fetch.get("status") or 0),
                    "contentType": fetch.get("content_type"),
                    "proofModelVersion": PROOF_VERSION,
                    "validationState": "live-validated",
                    "executedEvidence": True,
                    "httpUsed": True,
                })
'''
    text = once(text, old, new, "bootstrap-request-spec")
    text = text.replace(
        '"staticCandidatesExecutable": False,',
        f'"staticCandidatesExecutable": False,\n        "requestSpecModel": "{MARKER}",',
        1,
    )
    BOOTSTRAP.write_text(text, encoding="utf-8")
    return True


def validate() -> None:
    recovery = RECOVERY.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    for needle in (
        '"executionRoutes": execution_routes',
        'generic_execution_route(row)',
        'row.get("requestSpecReusable") is True',
        'patch["learned_routes"] = execution_routes',
    ):
        if needle not in recovery:
            raise AssertionError(f"recovery request-spec wiring missing: {needle}")
    for needle in ('"requestSpec": copy.deepcopy(request_spec)', '"requestSpecReusable": bool(meta.get("requestSpecReusable"))'):
        if needle not in bootstrap:
            raise AssertionError(f"bootstrap request-spec wiring missing: {needle}")


def main() -> int:
    changed = patch_recovery() or patch_bootstrap()
    # Ensure bootstrap is still patched even when recovery already had the marker.
    patch_bootstrap()
    validate()
    print(f"ROUTE_RECOVERY_REQUEST_SPEC_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

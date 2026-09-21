#!/usr/bin/env python3
"""Build sanitized transferable repair experience from current NiakVIO evidence.

This is prior knowledge, not proof that a repair profile works. It distills the
current successful catalogue into structural hints that the Brain may use to
order experiments: capability strategy, reusable route shapes, reached stages,
Provider Lego provenance and domain-memory presence.

Provider-specific opaque tokens and fixture-specific literal routes are excluded
from peer transfer. Every transferred hint must still pass the ordinary deep
sandbox/current-byte/identity/playback/non-regression gates.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
STATUS = ROOT / "automation/provider-census-status.json"
DEFAULT_OUTPUT = ROOT / "automation/brain-repair-experience.json"
ROUTE_RECOVERY = ROOT / "automation/provider-route-recovery-v6.json"
HISTORICAL_SEED = ROOT / "automation/brain-historical-experience-seed.json"
GREEN = {"FULL OK", "PARTIAL OK"}
ROUTE_KEYS = ("candidate_learned_routes", "learned_routes", "candidate_routes", "routes")
PLACEHOLDER = re.compile(r"\{(?:query|slug|id|tmdbId|imdbId|year|season|episode|mediaType|type|binding:[A-Za-z0-9_.-]+)\}", re.I)
OPAQUE = re.compile(r"(?:[A-Za-z0-9+/]{72,}={0,2}|%[0-9A-Fa-f]{2}.{100,}|[A-Fa-f0-9]{96,})")
BODY_PLACEHOLDER = re.compile(r"\{(?:query|queryDots|slug|id|tmdbId|imdbId|year|season|episode|mediaType|type|binding:[A-Za-z0-9_.-]+)\}", re.I)
SAFE_HEADER_NAMES = {"accept", "accept-language", "content-type", "origin", "referer", "user-agent"}
IDENTITY_INFRA_HOSTS = {
    "api.themoviedb.org",
    "v3-cinemeta.strem.io",
    "arm.haglund.dev",
}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def canonical(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def classify_route(route: str) -> str:
    value = route.casefold()
    if "{query}" in value or re.search(r"(?:^|[/?&_=.-])search(?:[/?&_=.-]|$)", value) or re.search(r"[?&]s=", value):
        return "search"
    if "{episode}" in value or "{season}" in value or re.search(r"(?:episode|episodes|season|saison)", value):
        return "episode"
    if re.search(r"(?:player|embed|watch|lecteur|iframe|/e/|/v/)", value):
        return "player"
    if re.search(r"(?:^|/)(?:file|drive|source|download)(?:/|[?&]|$)", value):
        return "source"
    if re.search(r"(?:^|/)(?:api|ajax|stream|streams|sources|servers|links|load)(?:/|[?&]|$)", value):
        return "api"
    if "{slug}" in value or re.search(r"(?:^|/)(?:movie|film|films|serie|series|anime|title|download-)", value):
        return "detail"
    return "other"


def reusable_route(raw: object, *, peer: bool) -> str | None:
    route = str(raw or "").strip()
    if not route or len(route) > 360 or not route.startswith("/") or route.startswith("//"):
        return None
    lower = route.casefold()
    if OPAQUE.search(route) or any(token in lower for token in (
        "cdn-cgi/email-protection", "/gtag/", "/track", "/report", "/beacon", "logout", "login",
    )):
        return None
    if re.search(r"[?&](?:sid|token|auth|signature|hash)=", lower) and not PLACEHOLDER.search(route):
        return None
    # Literal fixture paths are valuable provider-local evidence but unsafe peer
    # priors. Peer transfer requires a template or an obviously generic endpoint.
    if peer and not PLACEHOLDER.search(route):
        if not re.search(r"^/(?:api|ajax|stream|streams|sources|servers|player|embed|search|wp-json)(?:/|\?|$)", lower):
            return None
    return route


def routes_for_patch(patch: dict, *, peer: bool) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for key in ROUTE_KEYS:
        values = patch.get(key)
        if not isinstance(values, list):
            continue
        for raw in values:
            route = reusable_route(raw, peer=peer)
            if route and route not in seen:
                seen.add(route)
                out.append(route)
    return out[:64]


def _safe_body_value(raw: object) -> str | None:
    value = str(raw or "")
    if len(value) > 160 or OPAQUE.search(value):
        return None
    if BODY_PLACEHOLDER.search(value):
        # Every placeholder must be from the allowlist above.
        leftovers = re.sub(BODY_PLACEHOLDER, "", value)
        if "{" in leftovers or "}" in leftovers:
            return None
        return value
    # Small constants such as action=search/page=1 are safe to reuse.
    if re.fullmatch(r"[A-Za-z0-9_.:+/-]{1,48}", value):
        return value
    return None


def sanitize_request_recipe(row: dict, *, peer: bool) -> dict | None:
    if row.get("requestSpecReusable") is not True:
        return None
    status = int(row.get("status") or 0)
    if status < 200 or status >= 400:
        return None
    route = reusable_route(row.get("route"), peer=peer)
    if not route:
        return None
    origin = str(row.get("origin") or "").strip()
    origin_host = host_of(origin)
    if origin_host in IDENTITY_INFRA_HOSTS:
        return None
    spec = row.get("requestSpec") if isinstance(row.get("requestSpec"), dict) else {}
    method = str(spec.get("method") or row.get("method") or "GET").upper()
    if method not in {"GET", "POST"}:
        return None
    body_kind = str(spec.get("bodyKind") or row.get("proofBodyKind") or "none").casefold()
    if body_kind not in {"none", "form", "json"}:
        return None
    body: dict[str, str] = {}
    executable = True
    raw_body = spec.get("body") if isinstance(spec.get("body"), dict) else {}
    if method == "POST":
        if body_kind == "none":
            executable = False
        for key, raw_value in raw_body.items():
            safe_key = str(key or "").strip()
            safe_value = _safe_body_value(raw_value)
            if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", safe_key) or safe_value is None:
                executable = False
                continue
            body[safe_key] = safe_value
        if not body:
            executable = False
    header_names = sorted({
        str(name).casefold()
        for name in (spec.get("headers") or {})
        if str(name).casefold() in SAFE_HEADER_NAMES
    })
    content_type = str(row.get("contentType") or "").casefold()
    response = "json" if "json" in content_type else "html-or-text"
    recipe = {
        "route": route,
        "role": str(row.get("role") or classify_route(route)).casefold(),
        "method": method,
        "bodyKind": body_kind,
        "body": body,
        "headerNames": header_names,
        "response": response,
        "semanticType": str(row.get("semanticType") or "").casefold(),
        "streamProof": int(row.get("taskStreamCount") or 0) > 0,
        "executable": executable,
    }
    if not peer:
        if origin.startswith(("http://", "https://")) and not OPAQUE.search(origin):
            recipe["origin"] = origin.rstrip("/")
    return recipe


def host_of(raw: object) -> str | None:
    value = str(raw or "").strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = "https://" + value.lstrip("/")
    try:
        return (urlsplit(value).hostname or "").casefold() or None
    except ValueError:
        return None


def _request_spec_from_plan(raw: object) -> dict:
    spec = raw if isinstance(raw, dict) else {}
    method = str(spec.get("method") or "GET").upper()
    if method not in {"GET", "POST"}:
        return {}
    body_kind = str(spec.get("bodyKind") or "none").casefold()
    if body_kind not in {"none", "form", "json"}:
        return {}
    headers = {
        str(key): str(value)
        for key, value in (spec.get("headers") or {}).items()
        if str(key).casefold() in SAFE_HEADER_NAMES and len(str(value)) <= 320
    }
    body = spec.get("body") if isinstance(spec.get("body"), dict) else {}
    clean_body: dict[str, str] = {}
    if method == "POST":
        for key, value in body.items():
            safe_key = str(key or "").strip()
            safe_value = _safe_body_value(value)
            if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", safe_key) or safe_value is None:
                return {}
            clean_body[safe_key] = safe_value
        if body_kind == "none" or not clean_body:
            return {}
    return {
        "method": method,
        "bodyKind": body_kind,
        "body": clean_body,
        "headers": headers,
    }


def _split_recipe_route(base: object, route: object) -> tuple[str, str]:
    base_text = str(base or "").strip().rstrip("/")
    route_text = str(route or "").strip()
    if route_text.startswith(("http://", "https://")):
        parsed = urlsplit(route_text)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        return origin, path
    return base_text, route_text


def _recipe_from_plan(
    *,
    base: object,
    route: object,
    request_spec: object,
    role: str,
    semantic_type: str,
    response: str = "html-or-text",
    stream_proof: bool = False,
) -> dict | None:
    origin, route_value = _split_recipe_route(base, route)
    route_value = reusable_route(route_value, peer=False)
    if not route_value:
        return None
    origin_host = host_of(origin)
    if not origin_host or origin_host in IDENTITY_INFRA_HOSTS:
        return None
    spec = _request_spec_from_plan(request_spec)
    if not spec:
        return None
    recipe = {
        "route": route_value,
        "origin": origin,
        "role": str(role or classify_route(route_value)).casefold(),
        "method": spec["method"],
        "bodyKind": spec["bodyKind"],
        "body": spec["body"],
        "headerNames": sorted(str(key).casefold() for key in spec["headers"]),
        "response": response if response in {"json", "html-or-text"} else "html-or-text",
        "semanticType": str(semantic_type or "").casefold(),
        "streamProof": bool(stream_proof),
        "executable": True,
    }
    return recipe


def proof_owned_patch_recipes(patch: dict) -> list[dict]:
    """Harvest already-proven Provider DATA as reusable Brain examples.

    This is deliberately stricter than provider execution: only proof-model >=5
    request plans/recipes are imported, and every recipe still goes through the
    ordinary sanitizer before peer transfer.
    """
    out: list[dict] = []
    seen: set[str] = set()

    def add(recipe: dict | None) -> None:
        if not recipe:
            return
        clean = sanitize_request_recipe({
            **recipe,
            "requestSpecReusable": True,
            "status": 200,
            "requestSpec": {
                "method": recipe.get("method"),
                "bodyKind": recipe.get("bodyKind"),
                "body": recipe.get("body"),
                "headers": {name: "x" for name in recipe.get("headerNames") or []},
            },
            "contentType": "application/json" if recipe.get("response") == "json" else "text/html",
            "taskStreamCount": 1 if recipe.get("streamProof") is True else 0,
        }, peer=False)
        if not clean:
            return
        if recipe.get("origin"):
            clean["origin"] = str(recipe["origin"]).rstrip("/")
        key = json.dumps(clean, sort_keys=True, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            out.append(clean)

    for row in patch.get("search_request_plan") or []:
        if not isinstance(row, dict) or int(row.get("proofModelVersion") or 0) < 5:
            continue
        types = [str(value).casefold() for value in row.get("semanticTypes") or []] or [""]
        for semantic_type in types:
            add(_recipe_from_plan(
                base=row.get("base"),
                route=row.get("route"),
                request_spec=row.get("requestSpec"),
                role="search",
                semantic_type=semantic_type,
                response=str(row.get("responseKind") or "html-or-text").casefold(),
                stream_proof=row.get("streamProof") is True,
            ))

    for plan in patch.get("provider_value_plan") or []:
        if not isinstance(plan, dict) or int(plan.get("proofModelVersion") or 0) < 5:
            continue
        types = [str(value).casefold() for value in plan.get("semanticTypes") or []] or [""]
        for step in plan.get("steps") or []:
            if not isinstance(step, dict):
                continue
            for semantic_type in types:
                add(_recipe_from_plan(
                    base=step.get("base"),
                    route=step.get("route"),
                    request_spec=step.get("requestSpec"),
                    role=str(step.get("role") or "detail"),
                    semantic_type=semantic_type,
                    response=str(step.get("responseKind") or "html-or-text").casefold(),
                    stream_proof=step.get("streamProof") is True,
                ))

    api = patch.get("api_recipe")
    if isinstance(api, dict) and int(api.get("proofModelVersion") or 0) >= 5:
        base = api.get("base") or api.get("api")
        definitions = (
            ("searchRoute", "searchRequest", "search", ""),
            ("movieRoute", "movieRequest", "api", "movie"),
            ("episodeRoute", "episodeRequest", "api", "tv"),
            ("directRoute", "directRequest", "api", ""),
        )
        for route_key, request_key, role, semantic_type in definitions:
            route = api.get(route_key)
            if not route:
                continue
            spec = api.get(request_key) if isinstance(api.get(request_key), dict) else {
                "method": "GET",
                "headers": api.get("requestHeaders") if isinstance(api.get("requestHeaders"), dict) else {},
            }
            add(_recipe_from_plan(
                base=base,
                route=route,
                request_spec=spec,
                role=role,
                semantic_type=semantic_type,
                response="json",
                stream_proof=False,
            ))
    return out[:64]


def load_historical_cases(path: Path = HISTORICAL_SEED) -> list[dict]:
    """Load only the explicitly-scoped NiakVIO technical history seed.

    No account memory, personal profile or other GPT project is accepted here.
    The seed is schema-whitelisted and prior-only; it cannot publish/mutate code.
    """
    if not path.is_file():
        return []
    payload = load(path)
    if payload.get("role") != "historical-repair-prior-only":
        raise ValueError("historical Brain seed role is not prior-only")
    scope = str(payload.get("sourceScope") or "")
    if not scope.startswith("NiakVIO project chats + repository history"):
        raise ValueError("historical Brain seed source scope is not NiakVIO-only")
    safety = payload.get("safety") if isinstance(payload.get("safety"), dict) else {}
    if safety.get("directMutationAuthority") is not False or safety.get("publicationAuthority") is not False:
        raise ValueError("historical Brain seed unexpectedly grants mutation/publication authority")
    allowed_evidence = {
        "project-chat", "repo-history", "user-tv-tests", "native-labs",
        "tailscale-residential-runs", "user-manual-tests", "provider-overrides",
    }
    allowed_keys = {
        "id", "firstObserved", "providers", "symptomFamilies", "failureClass",
        "solutionClass", "transferableSignals", "avoid", "evidence", "lesson",
    }
    output: list[dict] = []
    for raw in payload.get("cases") or []:
        if not isinstance(raw, dict) or set(raw) - allowed_keys:
            raise ValueError("historical Brain case contains non-whitelisted fields")
        evidence = [str(value) for value in raw.get("evidence") or []]
        if not evidence or any(value not in allowed_evidence for value in evidence):
            raise ValueError("historical Brain case has non-NiakVIO evidence source")
        row = {
            "id": str(raw.get("id") or "")[:160],
            "firstObserved": str(raw.get("firstObserved") or "")[:32],
            "providers": [canonical(value) for value in raw.get("providers") or [] if canonical(value)][:64],
            "symptomFamilies": [str(value)[:96] for value in raw.get("symptomFamilies") or []][:32],
            "failureClass": str(raw.get("failureClass") or "")[:96],
            "solutionClass": str(raw.get("solutionClass") or "")[:128],
            "transferableSignals": [str(value)[:240] for value in raw.get("transferableSignals") or []][:32],
            "avoid": [str(value)[:240] for value in raw.get("avoid") or []][:32],
            "evidence": evidence[:16],
            "lesson": str(raw.get("lesson") or "")[:800],
        }
        if row["id"] and row["failureClass"] and row["solutionClass"]:
            output.append(row)
    return output[:512]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--status", type=Path, default=STATUS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--route-recovery", type=Path, default=ROUTE_RECOVERY)
    args = parser.parse_args()

    overrides = load(args.overrides)
    status = load(args.status)
    route_recovery = load(args.route_recovery) if args.route_recovery.exists() else {"providers": []}
    recovery_by_provider = {
        canonical(row.get("providerId")): row
        for row in route_recovery.get("providers") or []
        if isinstance(row, dict) and canonical(row.get("providerId"))
    }
    status_rows = {
        canonical(row.get("provider")): row
        for row in status.get("providers") or []
        if isinstance(row, dict) and canonical(row.get("provider"))
    }
    patches = overrides.get("provider_patches") or {}
    capabilities = overrides.get("provider_capabilities") or {}

    providers: dict[str, dict] = {}
    route_support: dict[str, Counter[str]] = defaultdict(Counter)
    family_support: dict[str, Counter[str]] = defaultdict(Counter)
    request_support: dict[str, Counter[str]] = defaultdict(Counter)
    request_examples: dict[str, dict[str, dict]] = defaultdict(dict)
    green_by_strategy: dict[str, set[str]] = defaultdict(set)

    for raw_id, raw_patch in patches.items():
        provider_id = canonical(raw_id)
        if not provider_id or not isinstance(raw_patch, dict):
            continue
        capability = capabilities.get(raw_id)
        if not isinstance(capability, dict):
            capability = capabilities.get(provider_id) if isinstance(capabilities.get(provider_id), dict) else {}
        strategy = str(capability.get("strategy") or raw_patch.get("capability") or "unknown").strip().casefold()
        row = status_rows.get(provider_id) or {}
        state = str(row.get("status") or "UNKNOWN")
        operational = state in GREEN
        local_routes = routes_for_patch(raw_patch, peer=False)
        peer_routes = routes_for_patch(raw_patch, peer=True)
        route_families = sorted({classify_route(route) for route in local_routes})
        recovery_row = recovery_by_provider.get(provider_id) or {}
        local_request_recipes: list[dict] = []
        peer_request_recipes: list[dict] = []
        seen_local_requests: set[str] = set()
        seen_peer_requests: set[str] = set()

        for recipe in proof_owned_patch_recipes(raw_patch):
            key = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
            if key not in seen_local_requests:
                seen_local_requests.add(key)
                local_request_recipes.append(recipe)
            peer_recipe = sanitize_request_recipe({
                **recipe,
                "requestSpecReusable": True,
                "status": 200,
                "requestSpec": {
                    "method": recipe.get("method"),
                    "bodyKind": recipe.get("bodyKind"),
                    "body": recipe.get("body"),
                    "headers": {name: "x" for name in recipe.get("headerNames") or []},
                },
                "contentType": "application/json" if recipe.get("response") == "json" else "text/html",
                "taskStreamCount": 1 if recipe.get("streamProof") is True else 0,
            }, peer=True)
            if peer_recipe and peer_recipe.get("executable") is True:
                peer_key = json.dumps(peer_recipe, sort_keys=True, separators=(",", ":"))
                if peer_key not in seen_peer_requests:
                    seen_peer_requests.add(peer_key)
                    peer_request_recipes.append(peer_recipe)

        for request_row in recovery_row.get("routeData") or []:
            if not isinstance(request_row, dict):
                continue
            local_recipe = sanitize_request_recipe(request_row, peer=False)
            if local_recipe:
                key = json.dumps(local_recipe, sort_keys=True, separators=(",", ":"))
                if key not in seen_local_requests:
                    seen_local_requests.add(key)
                    local_request_recipes.append(local_recipe)
            peer_recipe = sanitize_request_recipe(request_row, peer=True)
            if peer_recipe and peer_recipe.get("executable") is True:
                peer_key = json.dumps(peer_recipe, sort_keys=True, separators=(",", ":"))
                if peer_key not in seen_peer_requests:
                    seen_peer_requests.add(peer_key)
                    peer_request_recipes.append(peer_recipe)
        lego = [
            Path(str(value)).name
            for value in raw_patch.get("provider_lego_scripts") or []
            if str(value).strip()
        ]
        official_host = host_of(raw_patch.get("official_site"))
        domain_memory = bool(
            official_host
            or raw_patch.get("domain_substitutions")
            or raw_patch.get("runtime_domain_replacements")
            or raw_patch.get("replacements")
        )
        providers[provider_id] = {
            "status": state,
            "operational": operational,
            "strategy": strategy,
            "routeTemplates": local_routes,
            "routeFamilies": route_families,
            "requestRecipes": local_request_recipes[:32],
            "providerLegoScripts": lego,
            "domainMemory": domain_memory,
            "officialHost": official_host,
            "evidenceDepth": [
                str(value) for value in row.get("evidenceDepth") or [] if str(value)
            ],
        }
        if operational:
            green_by_strategy[strategy].add(provider_id)
            for route in peer_routes:
                route_support[strategy][route] += 1
            for family in set(route_families):
                family_support[strategy][family] += 1
            for recipe in peer_request_recipes:
                recipe_key = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
                request_support[strategy][recipe_key] += 1
                request_examples[strategy][recipe_key] = recipe

    patterns: dict[str, dict] = {}
    for strategy in sorted(set(green_by_strategy) | set(route_support) | set(family_support)):
        green = sorted(green_by_strategy.get(strategy) or set())
        common_routes = [
            {
                "route": route,
                "role": classify_route(route),
                "providerSupport": count,
                "supportRatio": round(count / max(1, len(green)), 4),
            }
            for route, count in route_support[strategy].most_common()
            if count >= 2
        ][:48]
        families = [
            {
                "role": role,
                "providerSupport": count,
                "supportRatio": round(count / max(1, len(green)), 4),
            }
            for role, count in family_support[strategy].most_common()
        ]
        common_requests = [
            {
                **request_examples[strategy][recipe_key],
                "providerSupport": count,
                "supportRatio": round(count / max(1, len(green)), 4),
            }
            for recipe_key, count in request_support[strategy].most_common()
            if count >= 2
        ][:32]
        patterns[strategy] = {
            "greenProviders": green,
            "greenProviderCount": len(green),
            "routeFamilies": families,
            "commonRouteTemplates": common_routes,
            "commonRequestRecipes": common_requests,
        }

    payload = {
        "schemaVersion": 2,
        "role": "repair-prior-only",
        "sourceRunId": status.get("runId"),
        "sourceSha": status.get("triggerSha"),
        "providerCount": len(providers),
        "operationalProviderCount": sum(1 for row in providers.values() if row["operational"]),
        "providers": providers,
        "strategyPatterns": patterns,
        "historicalCases": load_historical_cases(),
        "safety": {
            "peerRouteMinimumProviders": 2,
            "peerRequestMinimumProviders": 2,
            "opaqueRouteTransfer": False,
            "opaqueBodyTransfer": False,
            "nonReconstructiblePostExecution": False,
            "fixtureLiteralPeerTransfer": False,
            "directMutationAuthority": False,
            "historicalCasesArePriorOnly": True,
            "historicalSourceScope": "NiakVIO-only",
            "personalDataAllowed": False,
            "crossProjectDataAllowed": False,
            "requiresDeepValidation": True,
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_REPAIR_EXPERIENCE "
        f"providers={payload['providerCount']} operational={payload['operationalProviderCount']} "
        f"strategies={len(patterns)} historical_cases={len(payload['historicalCases'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

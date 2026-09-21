#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Provider-agnostic adaptive layer for the strict runtime repair engine."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from brain_positive_program_memory import (
    provider_request_recipes as positive_program_request_recipes,
    provider_routes as positive_program_routes,
    provider_user_agent as positive_program_user_agent,
)
BASE_PATH = ROOT / "scripts" / "runtime_repair.py"
_spec = importlib.util.spec_from_file_location("_nuvio_runtime_repair_base", BASE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load base runtime repair engine: {BASE_PATH}")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
for _name in dir(_base):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_base, _name)

INFRASTRUCTURE_HOSTS = {
    "api.themoviedb.org", "graphql.anilist.co", "kitsu.io",
    "arm.haglund.dev", "v3-cinemeta.strem.io", "raw.githubusercontent.com",
    "github.com", "npms.io", "lodash.com", "openjsf.org", "underscorejs.org",
    "google.com", "google.co.in", "support.google.com", "www.google.com", "www.google.co.in",
    "bing.com", "www.bing.com", "duckduckgo.com", "html.duckduckgo.com",
    "yandex.com", "www.yandex.com", "googletagmanager.com", "google-analytics.com",
    "static.cloudflareinsights.com", "cloudflareinsights.com", "connect.facebook.net",
    "doubleclick.net", "googlesyndication.com",
}
ADAPTIVE_MARKERS = (
    "/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
    "/* NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5",
)
ADAPTIVE_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
SAFE_STRUCTURED_PARSE_PROFILE = "safe_structured_parse"
# `excluded` is not an availability/runtime failure. It represents a deliberate
# policy/safety exclusion and therefore must not be turned into an unattended
# network-repair attempt. Every other non-healthy/non-playable observation is a
# repair input; the repair loop remains bounded and still requires strict
# before/after playable evidence before accepting a generated candidate.
NON_REPAIRABLE_POLICY_STATUSES = {"excluded"}
EXPERIENCE_PATH = ROOT / "automation" / "brain-repair-experience.json"
CENSUS_STATUS_PATH = ROOT / "automation" / "provider-census-status.json"
ROUTE_KEYS = ("candidate_learned_routes", "learned_routes", "candidate_routes", "routes")
_ROUTE_PLACEHOLDER = re.compile(r"\{(?:query|slug|id|tmdbId|imdbId|year|season|episode|mediaType|type|binding:[A-Za-z0-9_.-]+)\}", re.I)
_REQUEST_PLACEHOLDER = re.compile(r"\{(?:query|queryDots|slug|id|tmdbId|imdbId|year|season|episode|mediaType|type|binding:[A-Za-z0-9_.-]+)\}", re.I)
_ROUTE_OPAQUE = re.compile(r"(?:[A-Za-z0-9+/]{72,}={0,2}|[A-Fa-f0-9]{96,})")
_SAFE_REQUEST_HEADERS = {"accept", "accept-language", "content-type", "origin", "referer", "user-agent"}


def _census_runtime_focus(provider_id: str) -> dict[str, Any]:
    try:
        status = json.loads(CENSUS_STATUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    wanted = str(provider_id or "").strip().casefold()
    for row in status.get("providers") or []:
        if not isinstance(row, dict) or str(row.get("provider") or "").strip().casefold() != wanted:
            continue
        state = str(row.get("status") or "")
        profiles = {
            "CHAIN REACHED": {
                "focus": "terminal-chain",
                "direct_role_order": ["player", "api", "episode", "detail", "other"],
                "max_pages": 16, "max_embeds": 20, "max_depth": 4,
            },
            "ROUTE PROVEN": {
                "focus": "proven-route-chain",
                "direct_role_order": ["detail", "episode", "player", "api", "other"],
                "max_pages": 16, "max_embeds": 16, "max_depth": 4,
            },
            "CANDIDATE OK": {
                "focus": "candidate-replay",
                "direct_role_order": ["player", "api", "detail", "episode", "other"],
                "max_pages": 18, "max_embeds": 20, "max_depth": 4,
            },
            "PROVIDER NETWORK BLOCKED": {
                "focus": "transport-first",
                "direct_role_order": ["api", "detail", "player", "episode", "other"],
                "max_pages": 8, "max_embeds": 8, "max_depth": 2,
            },
        }
        result = dict(profiles.get(state) or {})
        result["status"] = state
        result["dominant_issue"] = str(row.get("dominantIssue") or "")[:240]
        return result
    return {}


def _load_experience() -> dict[str, Any]:
    try:
        value = json.loads(EXPERIENCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


TERMINAL_MEDIA_ROLES = {"player", "source", "api"}


def _route_role(route: str) -> str:
    value = route.casefold()
    if "{query}" in value or re.search(r"(?:^|[/?&_=.-])search(?:[/?&_=.-]|$)", value) or re.search(r"[?&]s=", value):
        return "search"
    if "{episode}" in value or "{season}" in value or re.search(r"(?:episode|episodes|season|saison)", value):
        return "episode"
    if re.search(r"(?:player|embed|watch|lecteur|iframe|/e/|/v/)", value):
        return "player"
    # Terminal download hosts commonly expose a provider-owned intermediate
    # source page (for example /file/<id> or /drive/<token>) before the actual
    # media URL. Keep this distinct from catalogue/detail pages such as
    # /download-<title>-..., which remain detail routes.
    if re.search(r"(?:^|/)(?:file|drive|source|download)(?:/|[?&]|$)", value):
        return "source"
    if re.search(r"(?:^|/)(?:api|ajax|stream|streams|sources|servers|links|load)(?:/|[?&]|$)", value):
        return "api"
    if "{slug}" in value or re.search(r"(?:^|/)(?:movie|film|films|serie|series|anime|title|download-)", value):
        return "detail"
    return "other"


def _safe_route(raw: Any) -> str | None:
    route = str(raw or "").strip()
    if not route or len(route) > 360 or not route.startswith("/") or route.startswith("//"):
        return None
    lower = route.casefold()
    if _ROUTE_OPAQUE.search(route):
        return None
    if any(token in lower for token in ("cdn-cgi/email-protection", "/gtag/", "/track", "/report", "/beacon")):
        return None
    if lower in {"/favicon.ico", "/robots.txt", "/sitemap.xml"}:
        return None
    if re.search(r"[?&](?:sid|token|auth|signature|hash)=", lower) and not _ROUTE_PLACEHOLDER.search(route):
        return None
    return route


def _patch_routes(patch: dict[str, Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for key in ROUTE_KEYS:
        values = patch.get(key)
        if not isinstance(values, list):
            continue
        for raw in values:
            route = _safe_route(raw)
            if route and route not in seen:
                seen.add(route)
                output.append(route)
    # Templates are more reusable than fixture literals. Generic API/player
    # endpoints come next; exact historical fixture routes remain last and are
    # still useful for the same provider when the catalogue is stable.
    return sorted(
        output,
        key=lambda route: (
            0 if _ROUTE_PLACEHOLDER.search(route) else 1,
            0 if _route_role(route) in {"search", "api", "player", "source", "episode", "detail"} else 1,
            len(route),
            route,
        ),
    )[:64]


def _peer_routes(strategy: str) -> list[str]:
    experience = _load_experience()
    patterns = experience.get("strategyPatterns")
    if not isinstance(patterns, dict):
        return []
    row = patterns.get(strategy)
    if not isinstance(row, dict):
        return []
    output: list[str] = []
    for item in row.get("commonRouteTemplates") or []:
        if not isinstance(item, dict) or int(item.get("providerSupport") or 0) < 2:
            continue
        route = _safe_route(item.get("route"))
        if route and route not in output:
            output.append(route)
    return output[:48]


def _safe_request_recipe(raw: Any, *, peer: bool = False) -> dict[str, Any] | None:
    if not isinstance(raw, dict) or raw.get("executable") is not True:
        return None
    route = _safe_route(raw.get("route"))
    if not route:
        return None
    method = str(raw.get("method") or "GET").upper()
    if method not in {"GET", "POST"}:
        return None
    body_kind = str(raw.get("bodyKind") or "none").casefold()
    if body_kind not in {"none", "form", "json"}:
        return None
    body: dict[str, str] = {}
    for key, value in (raw.get("body") or {}).items():
        safe_key = str(key or "").strip()
        safe_value = str(value or "")
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", safe_key):
            return None
        if len(safe_value) > 160 or _ROUTE_OPAQUE.search(safe_value):
            return None
        if "{" in safe_value or "}" in safe_value:
            leftovers = re.sub(_REQUEST_PLACEHOLDER, "", safe_value)
            if "{" in leftovers or "}" in leftovers:
                return None
        elif not re.fullmatch(r"[A-Za-z0-9_.:+/-]{1,48}", safe_value):
            return None
        body[safe_key] = safe_value
    if method == "POST" and (body_kind == "none" or not body):
        return None
    header_names = sorted({
        str(name).casefold()
        for name in raw.get("headerNames") or []
        if str(name).casefold() in _SAFE_REQUEST_HEADERS
    })
    template_values = [route, *body.values()]
    referenced_bindings = sorted({
        match.group(1).casefold()
        for value in template_values
        for match in _BINDING_PLACEHOLDER.finditer(str(value))
    })
    declared_bindings = sorted({
        str(value).strip().casefold()
        for value in raw.get("requiredBindings") or []
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", str(value).strip())
    })
    if referenced_bindings != declared_bindings and (referenced_bindings or declared_bindings):
        return None
    recipe = {
        "route": route,
        "role": str(raw.get("role") or _route_role(route)).casefold(),
        "method": method,
        "bodyKind": body_kind,
        "body": body,
        "headerNames": header_names,
        "response": str(raw.get("response") or "html-or-text").casefold(),
        "semanticType": str(raw.get("semanticType") or "").casefold(),
        "streamProof": raw.get("streamProof") is True,
        "requiredBindings": referenced_bindings,
        "executable": True,
        "source": "peer-experience" if peer else "provider-experience",
    }
    if not peer:
        origin = str(raw.get("origin") or "").strip().rstrip("/")
        if origin.startswith(("http://", "https://")):
            normalized = _origin(origin)
            if not normalized:
                return None
            host = (urlparse(normalized).hostname or "").casefold()
            if host in INFRASTRUCTURE_HOSTS or any(host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):
                return None
            recipe["origin"] = normalized
    return recipe



_SENSITIVE_REQUEST_KEY = re.compile(r"(?:api[_-]?key|token|auth|authorization|signature|sig|secret|password|cookie|session|nonce|hash)", re.I)
_QUERY_KEYS = {"q", "query", "search", "keyword", "term", "story", "title", "name"}
_SAFE_CONSTANT_KEYS = {"page", "limit", "offset", "action", "do", "subaction", "sort", "order", "lang", "language", "locale", "quality"}
_BINDABLE_RESPONSE_KEYS = {
    "id", "_id", "media_id", "mediaid", "post_id", "postid", "content_id", "contentid",
    "movie_id", "movieid", "series_id", "seriesid", "show_id", "showid", "slug",
}
_BINDING_PLACEHOLDER = re.compile(r"\{binding:([A-Za-z0-9_.-]+)\}", re.I)


def _fixture_context(raw_test: dict[str, Any]) -> dict[str, str]:
    fixture = raw_test.get("fixture") if isinstance(raw_test.get("fixture"), dict) else {}
    title = str(fixture.get("title") or fixture.get("label") or "").strip()
    media_type = str(fixture.get("mediaType") or fixture.get("type") or "").strip().casefold()
    category = str(fixture.get("category") or "").strip().casefold()
    if category == "anime":
        media_type = "anime"
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    return {
        "title": title,
        "title_cf": title.casefold(),
        "slug": slug,
        "tmdbId": str(fixture.get("tmdbId") or fixture.get("id") or "").strip(),
        "imdbId": str(fixture.get("imdbId") or fixture.get("imdb_id") or "").strip(),
        "year": str(fixture.get("year") or "").strip(),
        "season": str(fixture.get("season") or "").strip(),
        "episode": str(fixture.get("episode") or "").strip(),
        "mediaType": media_type,
    }


def _binding_name(raw: Any) -> str | None:
    key = str(raw or "").strip().casefold().replace("-", "_")
    if key not in _BINDABLE_RESPONSE_KEYS:
        return None
    key = re.sub(r"[^a-z0-9_.-]+", "_", key).strip("_")
    return key or None


def _response_binding_candidates(raw: dict[str, Any]) -> dict[str, str]:
    """Return every safe response value that has an unambiguous binding key.

    A multi-result search may expose many different id values. We do not choose
    one here. A later observed request may prove that one exact value was
    consumed; runtime replay must then independently recover the correct value
    from the new fixture by identity correlation before the dependent request
    can execute.
    """
    by_value: dict[str, set[str]] = {}
    for hint in raw.get("response_value_hints") or []:
        if not isinstance(hint, dict):
            continue
        name = _binding_name(hint.get("key"))
        value = str(hint.get("value") or "").strip()
        if not name or not value or len(value) > 160 or value == "<redacted>":
            continue
        if _ROUTE_OPAQUE.search(value) or _SENSITIVE_REQUEST_KEY.search(name):
            continue
        by_value.setdefault(value, set()).add(name)
    output: dict[str, str] = {}
    for value, names in by_value.items():
        if len(names) == 1:
            output[value] = next(iter(names))
    return output


def _unique_response_bindings(raw: dict[str, Any]) -> dict[str, str]:
    """Backward-compatible conservative subset used by older contracts."""
    candidates = _response_binding_candidates(raw)
    grouped: dict[str, set[str]] = {}
    for value, name in candidates.items():
        grouped.setdefault(name, set()).add(value)
    return {
        value: name
        for value, name in candidates.items()
        if len(grouped.get(name) or ()) == 1
    }


def _abstract_observed_value(
    key: str,
    raw: Any,
    fixture: dict[str, str],
    *,
    allow_constant: bool,
    bindings: dict[str, str] | None = None,
) -> str | None:
    name = str(key or "").strip()
    value = str(raw if raw is not None else "").strip()
    if not name or not value or value == "<redacted>" or _SENSITIVE_REQUEST_KEY.search(name):
        return None
    if len(value) > 160 or _ROUTE_OPAQUE.search(value):
        return None
    folded = value.casefold()
    if fixture.get("title_cf") and folded == fixture["title_cf"]:
        return "{query}"
    if fixture.get("slug") and folded.strip("/") == fixture["slug"]:
        return "{slug}"
    for field, placeholder in (
        ("tmdbId", "{tmdbId}"),
        ("imdbId", "{imdbId}"),
        ("year", "{year}"),
        ("season", "{season}"),
        ("episode", "{episode}"),
        ("mediaType", "{mediaType}"),
    ):
        known = fixture.get(field) or ""
        if known and folded == known.casefold():
            return placeholder

    if bindings and value in bindings:
        bind_name = _binding_name(bindings[value])
        if bind_name:
            return "{binding:" + bind_name + "}"

    lowered = name.casefold()
    if lowered in _QUERY_KEYS:
        return "{query}"
    if lowered in {"tmdb", "tmdbid", "tmdb_id"}:
        return "{tmdbId}" if fixture.get("tmdbId") else None
    if lowered in {"imdb", "imdbid", "imdb_id"}:
        return "{imdbId}" if fixture.get("imdbId") else None
    if lowered in {"season", "saison"}:
        return "{season}" if fixture.get("season") else None
    if lowered in {"episode", "ep"}:
        return "{episode}" if fixture.get("episode") else None
    if lowered == "year":
        return "{year}" if fixture.get("year") else None
    if lowered in {"mediatype", "media_type", "type"} and fixture.get("mediaType") and folded == fixture["mediaType"]:
        return "{mediaType}"
    # Generic provider IDs are NEVER mapped to TMDB. They become executable only
    # after an earlier response exposed the exact same unique value.
    if lowered in {"id", "_id", "media_id", "post_id", "content_id", "movie_id", "series_id", "show_id"}:
        return None
    if allow_constant and lowered in _SAFE_CONSTANT_KEYS and re.fullmatch(r"[A-Za-z0-9_.:+/-]{1,48}", value):
        return value
    return None


def _observed_route(
    raw: dict[str, Any],
    fixture: dict[str, str],
    bindings: dict[str, str] | None = None,
) -> tuple[str | None, str | None]:
    proof_url = str(raw.get("proof_url") or "").strip()
    if proof_url:
        try:
            parsed = urlparse(proof_url)
        except ValueError:
            return None, None
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None, None
        observed_host = str(raw.get("host") or "").strip().casefold()
        if observed_host and parsed.hostname.casefold() != observed_host:
            return None, None
        segments: list[str] = []
        for segment_raw in parsed.path.split("/"):
            if not segment_raw:
                continue
            segment = unquote(segment_raw)
            abstracted = _abstract_observed_value(
                "path", segment, fixture, allow_constant=False, bindings=bindings
            )
            if abstracted:
                segments.append(abstracted)
                continue
            if re.fullmatch(r"\d+", segment) or _ROUTE_OPAQUE.search(segment) or len(segment) > 64:
                return None, None
            if not re.fullmatch(r"[A-Za-z0-9._~+%-]{1,64}", segment):
                return None, None
            segments.append(segment)
        route = "/" + "/".join(segments)
        if parsed.path.endswith("/") and route != "/":
            route += "/"
        query_parts: list[str] = []
        try:
            pairs = list(parse_qsl(parsed.query, keep_blank_values=True))
        except Exception:
            pairs = []
        for key, value in pairs[:20]:
            if _SENSITIVE_REQUEST_KEY.search(str(key)):
                return None, None
            abstracted = _abstract_observed_value(
                key, value, fixture, allow_constant=True, bindings=bindings
            )
            if abstracted is None:
                return None, None
            if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", str(key)):
                return None, None
            query_parts.append(f"{key}={abstracted}")
        if query_parts:
            route += "?" + "&".join(query_parts)
        return _safe_route(route), f"{parsed.scheme}://{parsed.netloc}"

    # Without the raw safe URL, only already-reusable normalized patterns are
    # executable. Ambiguous worker placeholders remain evidence-only.
    pattern = str(raw.get("path_pattern") or "").strip()
    if not pattern or "{token}" in pattern or re.search(r"/\{(?:id|value)\}(?:/|$)", pattern):
        return None, None
    if "?" in pattern:
        path, query = pattern.split("?", 1)
        converted: list[str] = []
        for part in query.split("&"):
            if "=" not in part:
                return None, None
            key, value = part.split("=", 1)
            if _SENSITIVE_REQUEST_KEY.search(key):
                return None, None
            if value == "{value}":
                placeholder = _abstract_observed_value(
                    key, "observed", fixture, allow_constant=False, bindings=bindings
                )
                if not placeholder:
                    return None, None
                value = placeholder
            converted.append(f"{key}={value}")
        pattern = path + "?" + "&".join(converted)
    return _safe_route(pattern), None


def observed_request_recipes(candidate: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    """Synthesize current provider request programs from current-run evidence.

    Provider-local response values may flow into a later request only when the
    preceding response exposed one unique safe value for that key and the later
    request consumed that exact value. This is causal binding, not ID guessing.
    """
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_test in result.get("tests") or []:
        if not isinstance(raw_test, dict):
            continue
        fixture = _fixture_context(raw_test)
        semantic_type = fixture.get("mediaType") or ""
        available_bindings: dict[str, str] = {}
        for raw in raw_test.get("network_observations") or []:
            if not isinstance(raw, dict) or raw.get("infrastructure") is True:
                continue
            status = raw.get("status")
            if not isinstance(status, int) or not (200 <= status < 400):
                continue
            if raw.get("synthetic_fixture_fallback") is True:
                continue
            method = str(raw.get("method") or "GET").upper()
            if method not in {"GET", "POST"}:
                continue
            route, origin = _observed_route(raw, fixture, available_bindings)
            recipe: dict[str, Any] | None = None
            if route:
                stage = str(raw.get("stage") or "").strip().casefold()
                role = {
                    "search": "search",
                    "player": "player",
                    "episode": "episode",
                    "content_lookup": "detail",
                    "origin_probe": "other",
                }.get(stage, _route_role(route))
                body_kind = str(raw.get("proof_body_kind") or "none").casefold()
                body: dict[str, str] = {}
                if method == "POST":
                    if body_kind not in {"form", "json"}:
                        route = None
                    else:
                        values = raw.get("proof_body_values") if isinstance(raw.get("proof_body_values"), dict) else {}
                        fields = [str(value) for value in raw.get("proof_body_fields") or []][:40]
                        if not fields:
                            fields = list(values)[:40]
                        valid = True
                        for key in fields:
                            if key == "$text":
                                valid = False
                                break
                            abstracted = _abstract_observed_value(
                                key,
                                values.get(key),
                                fixture,
                                allow_constant=True,
                                bindings=available_bindings,
                            )
                            if abstracted is None:
                                valid = False
                                break
                            body[key] = abstracted
                        if not valid or not body:
                            route = None
                else:
                    body_kind = "none"

                if route:
                    header_names = sorted({
                        str(name).casefold()
                        for name in (raw.get("proof_headers") or {}).keys()
                        if str(name).casefold() in _SAFE_REQUEST_HEADERS
                    })
                    content_type = str(raw.get("content_type") or "").casefold()
                    template_values = [route, *body.values()]
                    required_bindings = sorted({
                        match.group(1).casefold()
                        for value in template_values
                        for match in _BINDING_PLACEHOLDER.finditer(str(value))
                    })
                    recipe_raw = {
                        "route": route,
                        "origin": origin or "",
                        "role": role,
                        "method": method,
                        "bodyKind": body_kind,
                        "body": body,
                        "headerNames": header_names,
                        "response": "json" if "json" in content_type else "html-or-text",
                        "semanticType": semantic_type,
                        "streamProof": bool(stage == "player" and any(token in content_type for token in ("mpegurl", "dash", "video/"))),
                        "requiredBindings": required_bindings,
                        "executable": True,
                    }
                    recipe = _safe_request_recipe(recipe_raw, peer=False)

            # Bindings are learned only from a response we can replay. This
            # prevents a dependent player recipe from relying on an unreachable
            # native-only search/detail request.
            if recipe:
                recipe["source"] = "current-observation"
                fingerprint = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    output.append(recipe)
                    if len(output) >= 32:
                        return output
                for value, name in _response_binding_candidates(raw).items():
                    available_bindings.setdefault(value, name)
    return output


def _provider_request_recipes(provider_id: str) -> list[dict[str, Any]]:
    experience = _load_experience()
    providers = experience.get("providers")
    if not isinstance(providers, dict):
        return []
    row = providers.get(provider_id)
    if not isinstance(row, dict):
        return []
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in row.get("requestRecipes") or []:
        recipe = _safe_request_recipe(raw, peer=False)
        if not recipe:
            continue
        key = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        output.append(recipe)
    return output[:32]


def _peer_request_recipes(strategy: str) -> list[dict[str, Any]]:
    experience = _load_experience()
    patterns = experience.get("strategyPatterns")
    if not isinstance(patterns, dict):
        return []
    row = patterns.get(strategy)
    if not isinstance(row, dict):
        return []
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in row.get("commonRequestRecipes") or []:
        if not isinstance(raw, dict) or int(raw.get("providerSupport") or 0) < 2:
            continue
        recipe = _safe_request_recipe(raw, peer=True)
        if not recipe:
            continue
        key = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        output.append(recipe)
    return output[:24]


def _unique_request_recipes(*groups: list[dict[str, Any]], limit: int = 32) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in groups:
        for recipe in group:
            key = json.dumps(recipe, sort_keys=True, separators=(",", ":"))
            if key in seen:
                continue
            seen.add(key)
            output.append(recipe)
            if len(output) >= limit:
                return output
    return output


def _unique_routes(*groups: list[str], limit: int = 32) -> list[str]:
    output: list[str] = []
    for group in groups:
        for raw in group:
            route = _safe_route(raw)
            if route and route not in output:
                output.append(route)
                if len(output) >= limit:
                    return output
    return output


def _runtime_network_hints(patch: dict[str, Any]) -> dict[str, Any]:
    bases: list[str] = []
    user_agent = ""
    blocked_hosts: list[str] = []
    blocked_paths: list[str] = []
    for options in (patch.get("provider_lego_options") or {}).values():
        if not isinstance(options, dict):
            continue
        for key in ("base", "base_url", "origin", "site_ref", "api", "api_base"):
            value = options.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")) and value not in bases:
                bases.append(value)
        for value in options.get("fallbackBases") or []:
            if isinstance(value, str) and value.startswith(("http://", "https://")) and value not in bases:
                bases.append(value)
        if not user_agent:
            value = options.get("user_agent") or options.get("userAgent")
            if isinstance(value, str) and value.strip():
                user_agent = value.strip()[:320]
    core_options = patch.get("core_options") if isinstance(patch.get("core_options"), dict) else {}
    sanitizer = core_options.get("stream_sanitizer") if isinstance(core_options.get("stream_sanitizer"), dict) else {}
    blocked_hosts.extend(str(value).casefold().lstrip(".") for value in sanitizer.get("blocked_hosts") or [] if str(value).strip())
    blocked_paths.extend(str(value).casefold() for value in sanitizer.get("blocked_path_patterns") or [] if str(value).strip())
    return {
        "bases": bases[:16],
        "user_agent": user_agent,
        "blocked_hosts": blocked_hosts,
        "blocked_paths": blocked_paths,
    }


def _mapping_entry(mapping: Any, provider_id: str) -> dict[str, Any]:
    if not isinstance(mapping, dict):
        return {}
    direct = mapping.get(provider_id)
    if isinstance(direct, dict):
        return direct
    wanted = provider_id.casefold()
    for key, value in mapping.items():
        if str(key).casefold() == wanted and isinstance(value, dict):
            return value
    return {}


def _origin(raw: Any) -> str | None:
    value = str(raw or "").strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = "https://" + value.lstrip("/")
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _provider_metadata(candidate: dict[str, Any]) -> dict[str, Any]:
    for key in ("manifest_provider", "metadata", "canonical_metadata", "manifest"):
        value = candidate.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _experiment_role_preferences(
    census_focus: dict[str, Any],
    failure_class: str,
    variant: int,
) -> list[str]:
    """Choose a materially different exploration order for each failure family."""
    failure = str(failure_class or "").strip().casefold()
    variant = max(0, min(int(variant), 4))
    by_failure = {
        "provider_transport_gap": [
            ["api", "detail", "search", "player", "episode", "other"],
            ["api", "search", "detail", "player", "episode", "other"],
            ["detail", "api", "player", "search", "episode", "other"],
            ["search", "detail", "api", "player", "episode", "other"],
            ["search", "api", "detail", "player", "episode", "other"],
        ],
        "route_proven_gap": [
            ["detail", "episode", "player", "source", "api", "other"],
            ["player", "source", "detail", "episode", "api", "other"],
            ["api", "source", "player", "detail", "episode", "other"],
            ["episode", "detail", "player", "source", "api", "other"],
            ["player", "source", "api", "episode", "detail", "other"],
        ],
        "chain_terminal_gap": [
            ["player", "source", "api", "episode", "detail", "other"],
            ["api", "source", "player", "episode", "detail", "other"],
            ["player", "source", "episode", "api", "detail", "other"],
            ["detail", "player", "source", "api", "episode", "other"],
            ["player", "source", "api", "other", "episode", "detail"],
        ],
        "candidate_replay_gap": [
            ["player", "source", "api", "detail", "episode", "other"],
            ["api", "source", "player", "detail", "episode", "other"],
            ["detail", "player", "source", "api", "episode", "other"],
            ["episode", "detail", "player", "source", "api", "other"],
            ["player", "source", "api", "detail", "episode", "search", "other"],
        ],
        "media_extraction_gap": [
            ["player", "source", "api", "other", "episode", "detail", "search"],
            ["source", "api", "player", "other", "episode", "detail", "search"],
            ["player", "source", "api", "episode", "other", "detail", "search"],
            ["api", "source", "player", "episode", "other", "detail", "search"],
            ["player", "source", "api", "other", "episode", "detail", "search"],
        ],
    }
    if failure in by_failure:
        return list(by_failure[failure][variant])
    default = list(census_focus.get("direct_role_order") or [])
    fallbacks = [
        default,
        ["player", "source", "api", "episode", "detail", "other"],
        ["api", "source", "player", "detail", "episode", "other"],
        ["detail", "episode", "player", "source", "api", "other"],
        ["player", "source", "api", "detail", "episode", "search", "other"],
    ]
    return list(fallbacks[variant] or fallbacks[1])


def _historical_failure_priors(provider_id: str, failure_class: str) -> list[dict[str, Any]]:
    experience = _load_experience()
    wanted_provider = str(provider_id or "").strip().casefold()
    wanted_failure = str(failure_class or "").strip().casefold()
    if not wanted_failure:
        return []
    output: list[dict[str, Any]] = []
    for row in experience.get("historicalCases") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("failureClass") or "").strip().casefold() != wanted_failure:
            continue
        providers = {
            str(value or "").strip().casefold()
            for value in row.get("providers") or []
            if str(value or "").strip()
        }
        if providers and "global" not in providers and wanted_provider not in providers:
            continue
        case_id = str(row.get("id") or "").strip()
        solution = str(row.get("solutionClass") or "").strip()
        if case_id and solution:
            output.append({
                "id": case_id,
                "solutionClass": solution,
                "providers": sorted(providers),
                "priorOnly": True,
            })
    return output[:16]


def _peer_route_min_variant(failure_class: str) -> int:
    failure = str(failure_class or "").strip().casefold()
    if failure in {"candidate_replay_gap", "media_extraction_gap"}:
        return 3
    if failure == "provider_transport_gap":
        return 2
    return 1


def _peer_recipe_min_variant(failure_class: str) -> int:
    failure = str(failure_class or "").strip().casefold()
    if failure in {"candidate_replay_gap", "media_extraction_gap"}:
        return 3
    return 2


def _new_strategy_id(failure_class: str, variant: int, generation: int = 1) -> str:
    if int(variant) != 4:
        return ""
    base = {
        "provider_transport_gap": "provider_origin_failover_v1",
        "route_proven_gap": "proven_route_terminal_traversal_v1",
        "chain_terminal_gap": "chain_terminal_extractor_v1",
        "candidate_replay_gap": "retained_candidate_replay_v1",
        "media_extraction_gap": "player_media_extractor_v1",
    }.get(str(failure_class or "").strip().casefold(), "expanded_family_strategy_v1")
    generation = max(1, int(generation or 1))
    # Generation 2 is the current production-safe final strategy. Higher
    # generations are Learning-only planner outputs and must correspond to
    # materially different sandbox exploration, never a relabelled retry.
    return base if generation <= 2 else f"{base}_g{generation}"


def _adaptive_runtime_options(candidate: dict[str, Any], config: dict[str, Any]) -> dict[str, Any] | None:
    provider_id = str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold()
    if not provider_id:
        return None
    patch = _mapping_entry(config.get("provider_patches"), provider_id)
    capability = _mapping_entry(config.get("provider_capabilities"), provider_id)
    metadata = _provider_metadata(candidate)
    canonical = candidate.get("canonical") if isinstance(candidate.get("canonical"), dict) else {}
    if str(capability.get("strategy") or patch.get("capability") or "") == "official_domain_hub" and not patch.get("official_site"):
        return None

    recovery_options: dict[str, Any] = {}
    core_options = patch.get("core_options") if isinstance(patch.get("core_options"), dict) else {}
    catalogue_core = core_options.get("catalogue_alias_recovery")
    if isinstance(catalogue_core, dict):
        recovery_options.update(catalogue_core)
    script_options = patch.get("patch_script_options")
    if isinstance(script_options, dict):
        for key, value in script_options.items():
            if str(key).endswith("vf_catalogue_recovery.py") and isinstance(value, dict):
                recovery_options.update(value)
                break

    network_hints = _runtime_network_hints(patch)
    validated_positive_user_agent = positive_program_user_agent(provider_id)
    current_request_recipes = [
        recipe for recipe in candidate.get("brain_observed_request_recipes") or []
        if isinstance(recipe, dict) and recipe.get("source") == "current-observation"
    ]
    positive_request_recipes = positive_program_request_recipes(provider_id)
    historical_provider_request_recipes = _provider_request_recipes(provider_id)
    provider_recipe_origins = [
        str(recipe.get("origin") or "").strip()
        for recipe in [
            *current_request_recipes,
            *positive_request_recipes,
            *historical_provider_request_recipes,
        ]
        if str(recipe.get("origin") or "").strip()
    ]
    explicit = [
        recovery_options.get("base_url"), patch.get("official_site"),
        *network_hints["bases"],
        metadata.get("baseUrl"), metadata.get("base_url"), metadata.get("url"),
        canonical.get("baseUrl"), canonical.get("base_url"), canonical.get("url"),
    ]
    explicit.extend((metadata.get("logo"), canonical.get("logo")))
    observed = capability.get("observed_origins") if isinstance(capability.get("observed_origins"), list) else []

    provider_token = re.sub(r"[^a-z0-9]+", "", provider_id)
    base_url = None
    trusted_recipe_origins = {
        _origin(raw)
        for raw in provider_recipe_origins
        if _origin(raw)
    }
    for raw in [*explicit, *list(observed), *provider_recipe_origins]:
        peer = _origin(raw)
        if not peer:
            continue
        host = (urlparse(peer).hostname or "").casefold()
        if host in INFRASTRUCTURE_HOSTS or any(host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):
            continue
        compact_host = re.sub(r"[^a-z0-9]+", "", host)
        if (
            raw in {patch.get("official_site"), recovery_options.get("base_url")}
            or peer in trusted_recipe_origins
            or (provider_token and provider_token in compact_host)
        ):
            base_url = peer
            break
    if not base_url:
        return None

    types: list[str] = []
    for source in (
        recovery_options.get("types"), patch.get("published_types"),
        metadata.get("supportedTypes"), canonical.get("supportedTypes"),
        capability.get("catalogue_types"),
    ):
        if isinstance(source, list):
            for value in source:
                item = str(value).casefold()
                if item in {"movie", "tv", "anime"} and item not in types:
                    types.append(item)
    if not types:
        types = ["movie", "tv", "anime"]

    learned_routes = _unique_routes(
        positive_program_routes(provider_id),
        _patch_routes(patch),
        limit=64,
    )
    learned_search = [route for route in learned_routes if _route_role(route) == "search"]
    learned_direct = [route for route in learned_routes if _route_role(route) != "search"]
    strategy = str(capability.get("strategy") or patch.get("capability") or "unknown").strip().casefold()
    census_focus = _census_runtime_focus(provider_id)
    brain_plan = candidate.get("brain_repair_plan") if isinstance(candidate.get("brain_repair_plan"), dict) else {}
    experiment_variant = max(0, min(int(brain_plan.get("experimentVariant") or 0), 4))
    experiment_generation = max(1, int(brain_plan.get("experimentGeneration") or 1))
    experiment_failure = str(brain_plan.get("failureClass") or "").strip()
    historical_priors = _historical_failure_priors(provider_id, experiment_failure)
    peer_route_min_variant = _peer_route_min_variant(experiment_failure)
    peer_recipe_min_variant = _peer_recipe_min_variant(experiment_failure)
    if historical_priors:
        # Historical NiakVIO evidence is a prior only: it may reach compatible
        # peer DATA one failed variant earlier, never skip deep validation.
        peer_route_min_variant = max(1, peer_route_min_variant - 1)
        peer_recipe_min_variant = max(1, peer_recipe_min_variant - 1)
    peer_routes = _peer_routes(strategy) if experiment_variant >= peer_route_min_variant else []
    provider_request_recipes = _unique_request_recipes(
        positive_request_recipes,
        historical_provider_request_recipes,
        limit=32,
    )
    peer_request_recipes = _peer_request_recipes(strategy)
    request_recipes = _unique_request_recipes(
        current_request_recipes,
        provider_request_recipes,
        peer_request_recipes if experiment_variant >= peer_recipe_min_variant else [],
        limit=32,
    )
    new_strategy_id = _new_strategy_id(experiment_failure, experiment_variant, experiment_generation)
    if experiment_variant == 4 and experiment_failure in {"candidate_replay_gap", "media_extraction_gap"}:
        # Production g2 stays conservative and prioritizes current/provider-owned
        # terminal evidence. Learning g3+ deliberately fuses peer recipes again:
        # that is a new causal strategy, still bounded by identity/media gates.
        if experiment_generation <= 2:
            request_recipes = _unique_request_recipes(current_request_recipes, provider_request_recipes, limit=32)
        else:
            request_recipes = _unique_request_recipes(
                current_request_recipes,
                provider_request_recipes,
                peer_request_recipes,
                limit=32,
            )
    peer_search = [route for route in peer_routes if _route_role(route) == "search"]
    peer_direct = [route for route in peer_routes if _route_role(route) != "search"]
    configured_search = [str(v) for v in recovery_options.get("search_paths") or [] if str(v).strip()]
    configured_direct = [str(v) for v in recovery_options.get("direct_paths") or [] if str(v).strip()]
    generic_search = [
        "/?s={query}", "/search?q={query}",
        "/index.php?do=search&subaction=search&story={query}",
    ]
    generic_direct = [
        "/{slug}", "/film/{slug}", "/films/{slug}",
        "/anime/{slug}", "/serie/{slug}", "/series/{slug}",
    ]
    if experiment_variant >= 3:
        generic_search.extend([
            "/search/{query}", "/search/{slug}",
            "/recherche?q={query}", "/recherche/{slug}",
            "/api/search?q={query}", "/api/search/{query}",
            "/ajax/search?query={query}",
        ])
        generic_direct.extend([
            "/watch/{slug}", "/movie/{id}", "/film/{id}", "/title/{id}",
            "/player/{id}", "/embed/{id}", "/api/sources/{id}",
            "/api/stream/{id}", "/api/servers/{id}",
            "/episode/{id}/{season}/{episode}",
        ])
    search_paths = _unique_routes(configured_search, learned_search, peer_search, generic_search, limit=24)
    direct_paths = _unique_routes(configured_direct, learned_direct, peer_direct, generic_direct, limit=32)
    if experiment_failure == "media_extraction_gap":
        # Current bytes have already reached a player. From variant 0 onward,
        # keep exploration at/after that causal frontier: owned search recipes
        # may still be needed to reacquire a fresh player, but generic catalogue
        # guesses and TMDB-as-provider-id terminal routes are no longer useful.
        terminal_owned = [
            route for route in learned_direct
            if _route_role(route) in TERMINAL_MEDIA_ROLES
        ]
        terminal_configured = [
            route for route in configured_direct
            if _route_role(route) in TERMINAL_MEDIA_ROLES
        ]
        terminal_peer = [
            route for route in peer_direct
            if experiment_variant >= peer_route_min_variant
            and _route_role(route) in TERMINAL_MEDIA_ROLES
        ]
        search_paths = _unique_routes(configured_search, learned_search, limit=12)
        direct_paths = _unique_routes(
            terminal_owned,
            terminal_configured,
            terminal_peer,
            limit=24,
        )
    if experiment_variant == 4:
        terminal_generic = [
            "/player/{id}", "/embed/{id}", "/watch/{slug}",
            "/api/sources/{id}", "/api/stream/{id}", "/api/servers/{id}",
            "/episode/{id}/{season}/{episode}",
        ]
        terminal_peer = [
            route for route in peer_direct
            if _route_role(route) in {"player", "source", "api", "episode"}
        ]
        if experiment_failure == "route_proven_gap":
            search_paths = _unique_routes(configured_search, learned_search, limit=16)
            direct_paths = _unique_routes(
                learned_direct, configured_direct, terminal_peer, terminal_generic, limit=32
            )
        elif experiment_failure == "chain_terminal_gap":
            search_paths = _unique_routes(configured_search, learned_search, limit=12)
            direct_paths = _unique_routes(
                [
                    route for route in learned_direct
                    if _route_role(route) in {"player", "source", "api", "episode"}
                ],
                configured_direct, terminal_peer, terminal_generic, learned_direct,
                limit=32,
            )
        elif experiment_failure == "candidate_replay_gap":
            exact_search = [route for route in learned_search if not _ROUTE_PLACEHOLDER.search(route)]
            templated_search = [route for route in learned_search if _ROUTE_PLACEHOLDER.search(route)]
            exact_direct = [route for route in learned_direct if not _ROUTE_PLACEHOLDER.search(route)]
            templated_direct = [route for route in learned_direct if _ROUTE_PLACEHOLDER.search(route)]
            search_paths = _unique_routes(exact_search, templated_search, configured_search, limit=20)
            direct_paths = _unique_routes(exact_direct, templated_direct, configured_direct, limit=32)
        elif experiment_failure == "media_extraction_gap":
            # The current run already proved the player. Do not regress into
            # catalogue discovery and do not synthesize provider-local IDs from
            # TMDB placeholders. Replay owned recipes and only proven terminal
            # route shapes.
            search_paths = _unique_routes(configured_search, learned_search, limit=12)
            direct_paths = _unique_routes(
                [
                    route for route in learned_direct
                    if _route_role(route) in TERMINAL_MEDIA_ROLES
                ],
                [
                    route for route in configured_direct
                    if _route_role(route) in TERMINAL_MEDIA_ROLES
                ],
                limit=24,
            )
        elif experiment_failure == "provider_transport_gap":
            search_paths = _unique_routes(
                learned_search, configured_search, peer_search, generic_search, limit=24
            )
            direct_paths = _unique_routes(
                learned_direct, configured_direct, peer_direct, generic_direct, limit=32
            )
    # Final-strategy Learning generations are deliberately different programs:
    # g3 = evidence fusion, g4 = broader terminal traversal, g5 = bounded broad
    # fallback. Production never emits >g2.
    if experiment_variant == 4 and experiment_generation >= 3:
        search_paths = _unique_routes(search_paths, peer_search, limit=28)
        direct_paths = _unique_routes(direct_paths, peer_direct, limit=36)
    if experiment_variant == 4 and experiment_generation >= 4:
        direct_paths = _unique_routes(
            direct_paths,
            [
                "/player/{id}", "/embed/{id}", "/watch/{slug}",
                "/api/sources/{id}", "/api/stream/{id}", "/api/servers/{id}",
                "/episode/{id}/{season}/{episode}",
            ],
            limit=40,
        )
    if experiment_variant == 4 and experiment_generation >= 5:
        search_paths = _unique_routes(
            search_paths,
            generic_search,
            [
                "/api/search?q={query}",
                "/ajax/search?query={query}",
                "/index.php?do=search&subaction=search&story={query}",
            ],
            limit=32,
        )
        direct_paths = _unique_routes(direct_paths, generic_direct, limit=40)

    role_preferences = _experiment_role_preferences(
        census_focus,
        experiment_failure,
        experiment_variant,
    )
    role_order = {role: index for index, role in enumerate(role_preferences)}
    # Binding placeholders are causal request-program inputs, not standalone
    # direct paths. They become executable only after an earlier response has
    # produced the binding value.
    direct_paths = [
        route for route in direct_paths
        if not _BINDING_PLACEHOLDER.search(route)
    ]
    if role_order:
        direct_paths = sorted(
            direct_paths,
            key=lambda route: (
                role_order.get(_route_role(route), len(role_order)),
                0 if _ROUTE_PLACEHOLDER.search(route) else 1,
                len(route),
                route,
            ),
        )
    blocked_hosts = {
        "googletagmanager.com", "google-analytics.com", "static.cloudflareinsights.com",
        "cloudflareinsights.com", "connect.facebook.net", "doubleclick.net",
        "googlesyndication.com", "fstream.top",
    }
    blocked_hosts.update(str(v).casefold().lstrip(".") for v in recovery_options.get("blocked_hosts") or [] if str(v).strip())
    blocked_hosts.update(network_hints["blocked_hosts"])
    blocked_paths = {"/gtag/js", "/cdn-cgi/rum", "/beacon.min.js", "/troll/"}
    blocked_paths.update(str(v).casefold() for v in recovery_options.get("blocked_path_patterns") or [] if str(v).strip())
    blocked_paths.update(network_hints["blocked_paths"])

    endpoint_origins: list[str] = []
    recipe_origins = [
        str(recipe.get("origin") or "")
        for recipe in request_recipes
        if str(recipe.get("origin") or "").startswith(("http://", "https://"))
    ]
    fixed_endpoint = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
    origin_inputs = [
        base_url,
        patch.get("official_site"),
        patch.get("official_api"),
        fixed_endpoint.get("api"),
        *observed,
        *network_hints["bases"],
        *recipe_origins,
    ]
    for raw in origin_inputs:
        peer = _origin(raw)
        if not peer:
            continue
        host = (urlparse(peer).hostname or "").casefold()
        if host in INFRASTRUCTURE_HOSTS or any(host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):
            continue
        if peer not in endpoint_origins:
            endpoint_origins.append(peer)

    if experiment_variant == 4 and experiment_failure == "provider_transport_gap":
        alternates = [origin for origin in endpoint_origins if origin != base_url]
        if alternates:
            # g2 keeps the established first failover. Learning g3+ rotates the
            # provider-owned origin deterministically so repeated generations do
            # not probe the same transport topology under a different label.
            alternate_index = 0 if experiment_generation <= 2 else (experiment_generation - 2) % len(alternates)
            base_url = alternates[alternate_index]

    return {
        "provider_name": str(metadata.get("name") or provider_id or "Provider"),
        "base_url": base_url,
        "endpoint_origins": endpoint_origins[:32],
        "types": types,
        "search_paths": search_paths,
        "direct_paths": direct_paths,
        "request_recipes": request_recipes,
        "historical_prior_ids": [row["id"] for row in historical_priors],
        "historical_solution_classes": [row["solutionClass"] for row in historical_priors],
        "route_prior_counts": {
            "historicalCases": len(historical_priors),
            "provider": len(learned_routes),
            "peer": len(peer_routes),
            "search": len(search_paths),
            "direct": len(direct_paths),
            "requestRecipes": len(request_recipes),
            "currentObservationRequestRecipes": len(current_request_recipes),
            "providerRequestRecipes": len(provider_request_recipes),
            "positiveProgramRequestRecipes": len(positive_program_request_recipes(provider_id)),
            "positiveProgramRoutes": len(positive_program_routes(provider_id)),
            "positiveProgramUserAgent": bool(validated_positive_user_agent),
            "peerRequestRecipes": len(peer_request_recipes),
        },
        "repair_focus": (
            "media-extraction"
            if experiment_failure == "media_extraction_gap"
            else census_focus.get("focus") or "generic"
        ),
        "census_status": census_focus.get("status") or "",
        "experiment_variant": experiment_variant,
        "experiment_generation": experiment_generation,
        "experiment_failure_class": experiment_failure,
        "experiment_strategy": (
            "owned-evidence"
            if experiment_variant == 0
            else "route-shape-transfer"
            if experiment_variant == 1
            else "request-recipe-transfer"
            if experiment_variant == 2
            else "expanded-discovery"
            if experiment_variant == 3
            else "learned-family-new-strategy"
        ),
        "new_strategy_id": new_strategy_id,
        "peer_route_min_variant": peer_route_min_variant,
        "peer_recipe_min_variant": peer_recipe_min_variant,
        "negative_memory_matches": max(0, int(brain_plan.get("negativeMemoryMatches") or 0)),
        "max_recipe_passes": (
            3 if experiment_generation <= 2
            else 4 if experiment_generation == 3
            else 5 if experiment_generation == 4
            else 6
        ),
        "max_pages": max(
            int(census_focus.get("max_pages") or 10),
            14 if experiment_variant == 1
            else 12 if experiment_variant == 2
            else 20 if experiment_variant == 3
            else (
                24 if experiment_generation <= 2
                else 28 if experiment_generation == 3
                else 32 if experiment_generation == 4
                else 36
            ) if experiment_variant == 4
            else 10,
        ),
        "max_embeds": max(
            int(census_focus.get("max_embeds") or 10),
            (
                24 if experiment_generation <= 2
                else 28 if experiment_generation == 3
                else 32 if experiment_generation == 4
                else 36
            ) if experiment_variant == 4
            else 24 if experiment_variant in {1, 2, 3}
            else 10,
        ),
        "max_depth": max(
            int(census_focus.get("max_depth") or 3),
            (
                4 if experiment_generation <= 2
                else 5 if experiment_generation in {3, 4}
                else 6
            ) if experiment_variant == 4
            else 4 if experiment_variant in {1, 2, 3}
            else 3,
        ),
        "timeout_ms": max(2000, min(int(recovery_options.get("timeout_ms") or 9000), 20000)),
        "user_agent": validated_positive_user_agent or network_hints["user_agent"],
        "blocked_hosts": sorted(blocked_hosts),
        "blocked_path_patterns": sorted(blocked_paths),
    }


def _adaptive_failure(result: dict[str, Any]) -> bool:
    """Return whether a runtime observation must enter bounded repair.

    Availability labels are observations, not terminal decisions. Anything that
    is not both healthy and backed by at least one playable stream is repairable
    unless it was deliberately excluded by a separate safety/policy decision.
    This covers legacy labels such as no_streams, blocked, unavailable and
    provider_unreachable as well as runtime_error and future diagnostic labels.
    """
    status = str(result.get("status") or "runtime_error")
    if status in NON_REPAIRABLE_POLICY_STATUSES:
        return False
    playable = _base.playable_stream_count(result)
    return not (status == "healthy" and playable > 0)


def _load_safe_structured_parse_module():
    script = ROOT / "scripts" / "adaptive_runtime" / "safe_structured_parse_v1.py"
    spec = importlib.util.spec_from_file_location("nuvio_safe_structured_parse", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _safe_structured_parse_applicable(source_text: str) -> bool:
    try:
        patched = _load_safe_structured_parse_module().apply(source_text)
    except Exception:
        return False
    return isinstance(patched, str) and patched != source_text


def matching_profiles(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
    config = config or load_overrides()
    matches = list(_base.matching_profiles(candidate, result, source_text, config))
    if (
        str(result.get("status") or "") == "runtime_error"
        and _safe_structured_parse_applicable(source_text)
        and SAFE_STRUCTURED_PARSE_PROFILE not in matches
    ):
        matches.append(SAFE_STRUCTURED_PARSE_PROFILE)
    name = "adaptive_runtime_recovery"
    if _adaptive_failure(result) and _adaptive_runtime_options(candidate, config) is not None and name not in matches:
        matches.append(name)
    return matches


def _strip_generated_adaptive_wrapper(source_text: str) -> str:
    """Remove repository-generated V1-V5 adaptive wrappers before peer inference."""
    cursor = 0
    parts: list[str] = []
    while True:
        starts = [source_text.find(marker, cursor) for marker in ADAPTIVE_MARKERS]
        starts = [value for value in starts if value >= 0]
        if not starts:
            parts.append(source_text[cursor:])
            break
        start = min(starts)
        parts.append(source_text[cursor:start])
        call = source_text.find(ADAPTIVE_CALL, start)
        end = source_text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated adaptive runtime recovery wrapper")
        cursor = end + 2
    return "".join(parts)


def _source_endpoint_origins(source_text: str) -> list[str]:
    output: list[str] = []
    for raw in re.findall(r"https?://[A-Za-z0-9.-]+(?::\d+)?", source_text):
        peer = _origin(raw)
        if not peer:
            continue
        host = (urlparse(peer).hostname or "").casefold()
        if host in INFRASTRUCTURE_HOSTS or any(host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):
            continue
        if peer not in output:
            output.append(peer)
        if len(output) >= 32:
            break
    return output


def _apply_adaptive(parent_data: bytes, candidate: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]]]:
    options = _adaptive_runtime_options(candidate, load_overrides())
    if options is None:
        return parent_data, []
    source_text = parent_data.decode("utf-8", errors="strict")
    native_source = _strip_generated_adaptive_wrapper(source_text)
    options = dict(options)
    peers = list(options.get("endpoint_origins") or [])
    for peer in _source_endpoint_origins(native_source):
        if peer not in peers:
            peers.append(peer)
    options["endpoint_origins"] = peers[:32]
    script = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v5.py"
    spec = importlib.util.spec_from_file_location("nuvio_adaptive_runtime_recovery", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    patched = module.apply(source_text, options=options).encode("utf-8")
    if patched == parent_data:
        return parent_data, []
    return patched, [{"type": "patch_profile", "profile": "adaptive_runtime_recovery", "phase": "runtime", "revision": 5, "options": options}]


def _apply_safe_structured_parse(parent_data: bytes) -> tuple[bytes, list[dict[str, Any]]]:
    source_text = parent_data.decode("utf-8", errors="strict")
    patched_text = _load_safe_structured_parse_module().apply(source_text)
    if not isinstance(patched_text, str):
        raise TypeError("safe_structured_parse_v1.apply() must return str")
    patched = patched_text.encode("utf-8")
    if patched == parent_data:
        return parent_data, []
    return patched, [{
        "type": "patch_profile",
        "profile": SAFE_STRUCTURED_PARSE_PROFILE,
        "phase": "runtime",
        "revision": 1,
        "scope": "global_structured_parse",
    }]


def _materialize_repair(
    stage: Path,
    candidate: dict[str, Any],
    profile_name: str,
    round_number: int,
    parent_data: bytes,
    patched: bytes,
    records: list[dict[str, Any]],
    revision: int,
) -> tuple[dict[str, Any] | None, str | None]:
    if patched == parent_data or not records:
        return None, "structural_profile_made_no_change"

    digest = hashlib.sha256(patched).hexdigest()
    parent_digest = hashlib.sha256(parent_data).hexdigest()
    repair_dir = stage / "providers" / "runtime-repairs" / _base._safe_fragment(str(candidate.get("source") or "source"))
    repair_dir.mkdir(parents=True, exist_ok=True)
    target = repair_dir / (
        f"{_base._safe_fragment(str(candidate.get('canonical_id') or 'provider'))}--"
        f"r{round_number}--{_base._safe_fragment(profile_name)}--{digest[:16]}.js"
    )
    target.write_bytes(patched)
    try:
        _base._validate_artifact(target)
    except Exception as exc:
        target.unlink(missing_ok=True)
        return None, f"artifact_validation_failed:{type(exc).__name__}:{exc}"

    repaired = copy.deepcopy(candidate)
    parent_key = str(candidate.get("key"))
    repaired["key"] = f"{parent_key}::repair:r{round_number}:{profile_name}:{digest[:8]}"
    repaired["local_path"] = target.relative_to(stage).as_posix()
    repaired["sha256"] = digest
    repaired["bytes"] = len(patched)
    repaired["local_patches"] = list(candidate.get("local_patches") or []) + records
    runtime_profile = "" if profile_name == "adaptive_runtime_recovery" else profile_name
    repaired["runtime_repair"] = {
        "parent_key": parent_key,
        "parent_sha256": parent_digest,
        "round": round_number,
        "profile": runtime_profile,
        "strategy": profile_name,
        "revision": revision,
    }
    return repaired, None


def create_repair_candidate(stage: Path, candidate: dict[str, Any], profile_name: str, round_number: int) -> tuple[dict[str, Any] | None, str | None]:
    if profile_name not in {"adaptive_runtime_recovery", SAFE_STRUCTURED_PARSE_PROFILE}:
        return _base.create_repair_candidate(stage, candidate, profile_name, round_number)
    source_path = (stage / str(candidate.get("local_path") or "")).resolve()
    providers_root = (stage / "providers").resolve()
    try:
        source_path.relative_to(providers_root)
    except ValueError:
        return None, "unsafe_parent_path"
    if not source_path.is_file():
        return None, "missing_parent_artifact"
    parent_data = source_path.read_bytes()
    try:
        if profile_name == SAFE_STRUCTURED_PARSE_PROFILE:
            patched, records = _apply_safe_structured_parse(parent_data)
            revision = 1
        else:
            patched, records = _apply_adaptive(parent_data, candidate)
            revision = 5
    except Exception as exc:
        return None, f"patch_exception:{type(exc).__name__}:{exc}"
    return _materialize_repair(
        stage,
        candidate,
        profile_name,
        round_number,
        parent_data,
        patched,
        records,
        revision,
    )

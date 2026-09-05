#!/usr/bin/env python3
"""Strict sequential live gate for Provider v3 reconstruction.

Contract:
- provider N is reconstructed/probed/finalized before provider N+1 starts;
- static routes are only candidates;
- every observed provider HTTP request may be retained as diagnostic/runtime evidence;
- advancement is gated by the provider's declared semantic media types, not by
  arbitrary internal HTTP request-shape coverage;
- every declared type must have one successful live type route (or a verified
  direct output for that type) before the provider advances;
- search/status/player/source traffic can prove the chain but never creates an
  extra required route or denominator by itself;
- relative recipe routes are matched against their declared API base, never
  promoted as literal dynamic IDs by accident;
- only a proven unavailable/blocked provider may advance without normal type-route proof.

There is deliberately no inter-provider concurrency.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from validate_provider_v3_routes_live import (
    CORPUS,
    EXPECTED,
    KNOWLEDGE,
    MANIFEST,
    OUTPUT,
    OVERRIDES,
    REPRESENTATIVE,
    live_evidence,
    load,
    provider_fetch,
    recipe_is_live,
    route_matches_url,
    run_task,
    semantic_types,
    success,
    unique,
    write,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIN_COVERAGE = 0.75  # diagnostic compatibility only; type gate is always 100%.
# PROVIDER_V3_HTTP_BLOCK_CLASSIFICATION_V1
# 451 is an explicit policy/jurisdiction block. It is never positive route
# proof, but a 451-only traversal is terminal-blocked rather than broken.
BLOCKED_STATUSES = {401, 403, 407, 429, 451}


def canonical(value: object) -> str:
    return str(value or "").strip().casefold()


def route_role(route: str) -> str:
    value = str(route or "").strip().casefold()
    # PROVIDER_V3_SEASON_QUERY_ROLE_V1
    # `s=` is ambiguous: WordPress-style search uses it as a query, while many
    # provider resolver APIs use `s` + `e` as season/episode coordinates. Treat
    # it as search only when it is not paired with episode semantics.
    try:
        parsed_role = urllib.parse.urlsplit(value)
        role_query = urllib.parse.parse_qs(parsed_role.query, keep_blank_values=True)
    except ValueError:
        role_query = {}
    has_episode_coordinate = any(key in role_query for key in ("e", "ep", "episode", "episode_number"))
    has_season_coordinate = any(key in role_query for key in ("season", "season_number")) or (
        "s" in role_query and has_episode_coordinate
    )
    explicit_search_query = any(key in role_query for key in ("q", "query", "keyword", "search", "story"))
    ambiguous_s_search = "s" in role_query and not has_season_coordinate
    if (
        re.search(r"/(?:search|recherche)(?:[/?#]|$)", value)
        or explicit_search_query
        or ambiguous_s_search
    ):
        return "search"
    if re.search(r"/(?:video[-_]?player|watchplayer|iframeplayer|player|embed|play)(?:[/?#.-]|$)", value):
        return "player"
    if re.search(r"/(?:download|file|mediafile|source|sources)(?:[/?#.-]|$)", value):
        return "source"
    if re.search(r"/(?:episodes?(?:\.js|\.json|\.txt)?|season-list|episode-list)(?:[/?#.-]|$)", value):
        return "episode-index"
    if re.search(r"/api(?:[./?#]|$)", value):
        return "api"
    return "detail"


def fixture_rows() -> list[dict[str, Any]]:
    corpus = load(CORPUS)
    rows: list[dict[str, Any]] = []
    for row in corpus.get("fixtures") or []:
        if not isinstance(row, dict) or not isinstance(row.get("fixture"), dict):
            continue
        fixture = copy.deepcopy(row["fixture"])
        media_type = canonical(fixture.get("mediaType") or fixture.get("category"))
        if media_type not in REPRESENTATIVE:
            continue
        rows.append({
            "slug": str(row.get("slug") or "").strip(),
            "providers": {canonical(v) for v in row.get("providers") or [] if canonical(v)},
            "fixture": fixture,
            "semantic_type": media_type,
        })
    return rows


def build_provider_queue() -> tuple[list[dict[str, Any]], int]:
    manifest = load(MANIFEST)
    fixtures = fixture_rows()
    by_slug = {row["slug"]: row for row in fixtures}
    queue: list[dict[str, Any]] = []
    provider_count = 0
    for manifest_row in manifest.get("scrapers") or []:
        if not isinstance(manifest_row, dict):
            continue
        provider_id = canonical(manifest_row.get("id"))
        filename = str(manifest_row.get("filename") or "").strip()
        if not provider_id or not filename or not (ROOT / filename).is_file():
            continue
        provider_count += 1
        supported = semantic_types(manifest_row)
        selected: list[dict[str, Any]] = []

        for row in fixtures:
            if provider_id in row["providers"] and row["semantic_type"] in supported:
                selected.append(row)

        for media_type in supported:
            # A provider-targeted fixture is stronger than the generic fallback.
            # In particular, anime-specialized providers use an anime feature film
            # for canonical movie proof instead of being forced through Interstellar.
            if any(existing["semantic_type"] == media_type for existing in selected):
                continue
            slug = REPRESENTATIVE[media_type]
            row = by_slug.get(slug)
            if row is not None and all(existing["slug"] != slug for existing in selected):
                selected.append(row)

        for row in fixtures:
            if not row["providers"] and row["semantic_type"] in supported:
                if all(existing["slug"] != row["slug"] for existing in selected):
                    selected.append(row)

        tasks = [{
            "provider_id": provider_id,
            "provider_name": str(manifest_row.get("name") or manifest_row.get("id") or provider_id),
            "filename": filename,
            "semantic_type": row["semantic_type"],
            "fixture": copy.deepcopy(row["fixture"]),
            "fixture_slug": row["slug"],
        } for row in selected]
        queue.append({
            "provider_id": provider_id,
            "provider_name": str(manifest_row.get("name") or manifest_row.get("id") or provider_id),
            "filename": filename,
            "supported_types": supported,
            "tasks": tasks,
        })
    return queue, provider_count


def request_shape(fetch: dict[str, Any]) -> str:
    raw = str(fetch.get("final_url") or fetch.get("url") or "")
    try:
        parsed = urllib.parse.urlsplit(raw)
        query_keys = sorted(urllib.parse.parse_qs(parsed.query, keep_blank_values=True))
        host = (parsed.hostname or "").casefold()
        path = parsed.path or "/"
    except ValueError:
        host, path, query_keys = "", raw, []
    return "|".join([
        str(fetch.get("method") or "GET").upper(),
        host,
        path,
        ",".join(query_keys),
        str(fetch.get("body_kind") or "none"),
        ",".join(sorted(str(v) for v in fetch.get("body_fields") or [])),
    ])


def _slug_candidates(fixture: dict[str, Any]) -> list[str]:
    values = [fixture.get("title"), *(fixture.get("aliases") or [])]
    out: list[str] = []
    for raw in values:
        text = str(raw or "").strip().casefold()
        if not text:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
        compact = re.sub(r"[^a-z0-9]+", "", text)
        for value in (slug, compact):
            if value and len(value) >= 4 and value not in out:
                out.append(value)
    return out


def derive_observed_route(fetch: dict[str, Any], task: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    """Derive a reusable route only from values observed in this exact live call."""
    raw = str(fetch.get("final_url") or fetch.get("url") or "")
    fixture = task.get("fixture") if isinstance(task.get("fixture"), dict) else {}
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError:
        return None, {"reason": "invalid-url", "observedUrl": raw}
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None, {"reason": "invalid-origin", "observedUrl": raw}

    path = parsed.path or "/"
    substitutions: list[dict[str, str]] = []
    reusable = True

    tmdb = str(fixture.get("tmdbId") or "").strip()
    if tmdb:
        parts = path.split("/")
        for index, part in enumerate(parts):
            if part == tmdb:
                parts[index] = "{tmdbId}"
                substitutions.append({"value": tmdb, "placeholder": "{tmdbId}", "location": "path"})
        path = "/".join(parts)

    for slug in _slug_candidates(fixture):
        pattern = re.compile(r"(?<![a-z0-9])" + re.escape(slug) + r"(?![a-z0-9])", re.I)
        if pattern.search(path):
            path = pattern.sub("{slug}", path)
            substitutions.append({"value": slug, "placeholder": "{slug}", "location": "path"})

    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    rendered_query: list[tuple[str, str]] = []
    season = str(fixture.get("season") or "").strip()
    episode = str(fixture.get("episode") or "").strip()
    title_values = {str(fixture.get("title") or "").strip().casefold()}
    title_values.update(str(v or "").strip().casefold() for v in fixture.get("aliases") or [])
    for key, value in query:
        key_l = key.casefold()
        replacement = value
        placeholder = None
        if tmdb and value == tmdb and key_l in {"id", "tmdb", "tmdbid", "tmdb_id", "movie", "tv"}:
            placeholder = "{tmdbId}"
        elif season and value == season and key_l in {"s", "season", "season_number", "seasonid", "season_id"}:
            placeholder = "{season}"
        elif episode and value == episode and key_l in {"e", "ep", "episode", "episode_number", "episodeid", "episode_id"}:
            placeholder = "{episode}"
        elif value.strip().casefold() in title_values and key_l in {"q", "query", "search", "title", "keyword", "story", "s"}:
            placeholder = "{query}"
        if placeholder:
            replacement = placeholder
            substitutions.append({"value": value, "placeholder": placeholder, "location": f"query:{key}"})
        rendered_query.append((key, replacement))

    route = path
    if rendered_query:
        route += "?" + urllib.parse.urlencode(rendered_query, doseq=True, safe="{}:/")

    # PROVIDER_V3_DYNAMIC_QUERY_RESIDUE_V1
    # A request observed live is not reusable Provider DATA while it still
    # contains literal content identity or request/session state. Season/episode
    # aliases above are abstracted first; remaining values under these keys must
    # stay diagnostic evidence only until Learning can derive a stable recipe.
    volatile_query_keys = {
        "seed", "token", "access_token", "auth", "signature", "sig", "hash",
        "nonce", "timestamp", "ts", "expires", "expiry", "expire", "key",
    }
    content_identity_query_keys = {
        "imdb", "imdbid", "imdb_id", "year", "releaseyear", "release_year",
        "seasonid", "season_id", "episodeid", "episode_id",
    }
    dynamic_query_residue = []
    for residue_key, residue_value in rendered_query:
        key_l = str(residue_key or "").strip().casefold()
        value_s = str(residue_value or "").strip()
        if not value_s or ("{" in value_s and "}" in value_s):
            continue
        if key_l in volatile_query_keys or key_l in content_identity_query_keys:
            dynamic_query_residue.append({"key": residue_key, "value": value_s})
    if dynamic_query_residue:
        reusable = False

    fixture_specific = []
    if tmdb and tmdb in route:
        fixture_specific.append(tmdb)

    # PROVIDER_V3_SEMANTIC_QUERY_RESIDUE_V1
    # Detect leaked fixture titles only in path/query values that can actually
    # carry content identity. Canonical semantic constants (type=movie|tv|anime)
    # are stable Provider contract DATA, not fixture-specific residue.
    try:
        residue_parts = urllib.parse.urlsplit(route)
        residue_haystacks = [urllib.parse.unquote(residue_parts.path or "/").casefold()]
        semantic_query_keys = {
            "type", "mediatype", "media_type", "media", "category", "kind"
        }
        for residue_key, residue_value in urllib.parse.parse_qsl(
            residue_parts.query, keep_blank_values=True
        ):
            if (
                residue_key.casefold() in semantic_query_keys
                and canonical(residue_value) in REPRESENTATIVE
            ):
                continue
            residue_haystacks.append(urllib.parse.unquote(residue_value).casefold())
    except ValueError:
        residue_haystacks = [urllib.parse.unquote(route).casefold()]

    for raw_title in title_values:
        if (
            raw_title
            and len(raw_title) >= 4
            and any(raw_title in haystack for haystack in residue_haystacks)
        ):
            fixture_specific.append(raw_title)
    if fixture_specific:
        reusable = False

    meta = {
        "origin": f"{parsed.scheme}://{parsed.netloc}",
        "observedUrl": raw,
        "substitutions": substitutions,
        "reusable": reusable,
        "fixtureSpecificValues": unique(fixture_specific, 12),
        "dynamicQueryResidue": dynamic_query_residue[:12],
    }
    return (route if reusable else None), meta


def _semantic_values(value: Any) -> set[str]:
    if isinstance(value, str):
        raw_values = re.split(r"[,|\s]+", value)
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = []
    return {canonical(v) for v in raw_values if canonical(v) in REPRESENTATIVE}


def _candidate_type_hints(row: dict[str, Any], required_types: set[str]) -> set[str]:
    hints: set[str] = set()
    for key in (
        "type", "types", "mediaType", "mediaTypes", "semanticType", "semanticTypes",
        "supportedType", "supportedTypes", "canonicalType", "canonicalTypes",
    ):
        hints.update(_semantic_values(row.get(key)))

    route = canonical(row.get("route"))
    if re.search(r"/(?:movie|movies|film|films)(?:[/?.#_-]|$)", route):
        hints.add("movie")
    if re.search(r"/(?:tv|series|serie|shows?|television)(?:[/?.#_-]|$)", route):
        hints.add("tv")
    if re.search(r"/(?:anime|animes)(?:[/?.#_-]|$)", route):
        hints.add("anime")
    if any(token in route for token in ("{season}", "{episode}", "season=", "episode=")):
        if "tv" in required_types:
            hints.add("tv")
        if "anime" in required_types:
            hints.add("anime")
    return hints & required_types


def _declared_type_templates(model: dict[str, Any], required_types: set[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {media_type: [] for media_type in required_types}

    recipes: list[dict[str, Any]] = []
    for key in ("candidateApiRecipe", "apiRecipe"):
        recipe = model.get(key)
        if isinstance(recipe, dict) and recipe not in recipes:
            recipes.append(recipe)

    recipe_keys = {
        "movie": ("movieRoute", "filmRoute"),
        "tv": ("tvRoute", "seriesRoute", "showRoute", "episodeRoute"),
        "anime": ("animeRoute", "episodeRoute"),
    }
    for recipe in recipes:
        for media_type in required_types:
            for key in recipe_keys.get(media_type, ()):
                route = str(recipe.get(key) or "").strip()
                if route and route not in out[media_type]:
                    out[media_type].append(route)

    current_route_data = model.get("candidateRouteData") if isinstance(model.get("candidateRouteData"), list) else None
    if current_route_data is None:
        current_route_data = model.get("routeData") if isinstance(model.get("routeData"), list) else []
    for row in current_route_data:
        if not isinstance(row, dict):
            continue
        route = str(row.get("route") or "").strip()
        if not route:
            continue
        for media_type in _candidate_type_hints(row, required_types):
            if route not in out[media_type]:
                out[media_type].append(route)
    return out


def _recipe_bases(model: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("officialApi", "fixedApi"):
        raw = str(model.get(key) or "").strip()
        if raw and raw not in values:
            values.append(raw)
    for recipe_key in ("candidateApiRecipe", "apiRecipe"):
        recipe = model.get(recipe_key)
        if not isinstance(recipe, dict):
            continue
        for key in ("base", "api", "baseUrl", "endpoint"):
            raw = str(recipe.get(key) or "").strip()
            if raw and raw not in values:
                values.append(raw)
    return values


def _route_matches_model_url(route: str, actual_url: str, model: dict[str, Any]) -> bool:
    if route_matches_url(route, actual_url):
        return True
    try:
        actual = urllib.parse.urlsplit(str(actual_url or ""))
    except ValueError:
        return False
    actual_host = (actual.hostname or "").casefold()
    for base in _recipe_bases(model):
        try:
            base_parts = urllib.parse.urlsplit(base)
            route_parts = urllib.parse.urlsplit(route)
        except ValueError:
            continue
        if base_parts.hostname and (base_parts.hostname or "").casefold() != actual_host:
            continue
        if route_parts.scheme or route_parts.netloc:
            continue
        base_path = (base_parts.path or "").rstrip("/")
        route_path = (route_parts.path or "/").lstrip("/")
        combined_path = (base_path + "/" + route_path) if route_path else (base_path or "/")
        combined = combined_path
        if route_parts.query:
            combined += "?" + route_parts.query
        if route_matches_url(combined, actual_url):
            return True
    return False


# PROVIDER_V3_REDIRECT_ROUTE_MATCH_V1
def _fetch_route_urls(fetch: dict[str, Any]) -> list[str]:
    """Request URL first; redirect target second. Both are evidence, not authority."""
    values: list[str] = []
    for key in ("url", "final_url"):
        raw = str(fetch.get(key) or "").strip()
        if raw and raw not in values:
            values.append(raw)
    return values


def _fetch_matches_model_route(route: str, fetch: dict[str, Any], model: dict[str, Any]) -> bool:
    return any(_route_matches_model_url(route, raw, model) for raw in _fetch_route_urls(fetch))


def _provider_contract_hosts(model: dict[str, Any]) -> set[str]:
    values: list[str] = []
    for key in ("knownSite", "officialSite", "officialHub", "officialApi", "fixedApi"):
        if model.get(key):
            values.append(str(model[key]))
    values.extend(_recipe_bases(model))
    hosts: set[str] = set()
    for value in values:
        try:
            host = (urllib.parse.urlsplit(value).hostname or "").casefold()
        except ValueError:
            host = ""
        if host:
            hosts.add(host)
    if hosts:
        return hosts
    for value in model.get("origins") or []:
        try:
            host = (urllib.parse.urlsplit(str(value)).hostname or "").casefold()
        except ValueError:
            host = ""
        if host:
            hosts.add(host)
    return hosts


def _fetch_on_contract_host(fetch: dict[str, Any], hosts: set[str]) -> bool:
    if not hosts:
        return True
    for raw in _fetch_route_urls(fetch):
        try:
            host = (urllib.parse.urlsplit(raw).hostname or "").casefold()
        except ValueError:
            continue
        if host in hosts:
            return True
    return False


def _generic_control_route(route: str) -> bool:
    value = str(route or "").strip().casefold()
    if not value:
        return True
    try:
        parsed = urllib.parse.urlsplit(value)
        path = parsed.path or "/"
    except ValueError:
        path = value.split("?", 1)[0] or "/"
    # PROVIDER_V3_QUERY_IDENTITY_ROUTE_V1
    # A root URL is normally a generic homepage, but some providers expose a
    # real typed API entirely through query parameters. Accept only a stable
    # reusable identity template plus an explicit canonical media type.
    try:
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    except (ValueError, AttributeError):
        query_pairs = []
    identity_keys = {"id", "tmdb", "tmdbid", "tmdb_id"}
    semantic_keys = {"type", "mediatype", "media_type", "media", "category", "kind"}
    has_reusable_identity = any(
        str(key).casefold() in identity_keys
        and "{" in str(raw_value)
        and "}" in str(raw_value)
        for key, raw_value in query_pairs
    )
    has_semantic_type = any(
        str(key).casefold() in semantic_keys
        and canonical(raw_value) in REPRESENTATIVE
        for key, raw_value in query_pairs
    )
    if path in {"", "/"} and not (has_reusable_identity and has_semantic_type):
        return True
    if route_role(value) == "search":
        return True
    if re.search(r"/(?:status|health|healthz|ping)(?:[/?#]|$)", value):
        return True
    segments = [segment for segment in path.split("/") if segment]
    if route_role(value) == "api" and len(segments) <= 2 and "{" not in value:
        return True
    return False


def _safe_observed_type_route(route: str, derivation: dict[str, Any], media_type: str) -> bool:
    # A literal provider-internal id (e.g. /stream/525) is not a reusable route
    # unless we can prove how it varies. Only fixture-derived placeholders or an
    # explicit semantic path can be promoted by the generic fallback.
    if derivation.get("substitutions"):
        return True
    value = canonical(route)
    if media_type == "movie" and re.search(r"/(?:movie|movies|film|films)(?:[/?.#_-]|$)", value):
        return True
    if media_type == "tv" and (
        re.search(r"/(?:tv|series|serie|shows?|television)(?:[/?.#_-]|$)", value)
        or any(token in value for token in ("{season}", "{episode}", "season=", "episode="))
    ):
        return True
    if media_type == "anime" and (
        re.search(r"/(?:anime|animes)(?:[/?.#_-]|$)", value)
        or any(token in value for token in ("{season}", "{episode}", "season=", "episode="))
    ):
        return True
    return False


def _observed_type_entry(
    media_type: str,
    task_rows: list[dict[str, Any]],
    model: dict[str, Any],
) -> dict[str, Any] | None:
    hosts = _provider_contract_hosts(model)
    for task in task_rows:
        if canonical(task.get("semantic_type")) != media_type:
            continue
        for fetch in task.get("fetches") or []:
            if not isinstance(fetch, dict) or not provider_fetch(fetch) or not success(fetch):
                continue
            if not _fetch_on_contract_host(fetch, hosts):
                continue
            route, derivation = derive_observed_route(fetch, task)
            if not route or _generic_control_route(route):
                continue
            if not _safe_observed_type_route(route, derivation, media_type):
                continue
            return {
                "route": route,
                "source": "live-observed-type-entry",
                "fixture": task.get("fixture_slug"),
                "evidence": live_evidence(fetch, task),
                "derivation": derivation,
            }
    return None


def _validate_declared_type_routes(
    model: dict[str, Any],
    task_rows: list[dict[str, Any]],
    required_types: set[str],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[str]], set[str]]:
    templates = _declared_type_templates(model, required_types)
    hosts = _provider_contract_hosts(model)
    evidence_by_type: dict[str, list[dict[str, Any]]] = {media_type: [] for media_type in required_types}

    for media_type in sorted(required_types):
        for template in templates.get(media_type) or []:
            for task in task_rows:
                if canonical(task.get("semantic_type")) != media_type:
                    continue
                for fetch in task.get("fetches") or []:
                    if not isinstance(fetch, dict) or not provider_fetch(fetch) or not success(fetch):
                        continue
                    if not _fetch_on_contract_host(fetch, hosts):
                        continue
                    if _fetch_matches_model_route(template, fetch, model):
                        evidence_by_type[media_type].append({
                            "route": template,
                            "source": "declared-type-template-live-match",
                            "fixture": task.get("fixture_slug"),
                            "evidence": live_evidence(fetch, task),
                        })
                        break
                if evidence_by_type[media_type]:
                    break
            if evidence_by_type[media_type]:
                break

        # Discovery fallback is deliberately conservative: it may only promote a
        # route whose dynamic part came from this fixture, or whose path itself
        # explicitly identifies the declared semantic type. Unknown literal IDs
        # remain evidence, never templates.
        if not evidence_by_type[media_type]:
            observed = _observed_type_entry(media_type, task_rows, model)
            if observed:
                evidence_by_type[media_type].append(observed)

        if not evidence_by_type[media_type]:
            for task in task_rows:
                if canonical(task.get("semantic_type")) != media_type or task.get("status") != "playable_verified":
                    continue
                provider_fetches = [
                    fetch for fetch in task.get("fetches") or []
                    if isinstance(fetch, dict) and provider_fetch(fetch)
                ]
                if not provider_fetches:
                    evidence_by_type[media_type].append({
                        "route": "direct-output",
                        "source": "verified-direct-output",
                        "fixture": task.get("fixture_slug"),
                    })
                    break

    validated = {media_type for media_type, rows in evidence_by_type.items() if rows}
    return evidence_by_type, templates, validated


def provider_origins(model: dict[str, Any], patch: dict[str, Any]) -> list[str]:
    fixed = patch.get("fixed_endpoint") if isinstance(patch.get("fixed_endpoint"), dict) else {}
    values = [
        patch.get("official_site"), patch.get("official_hub"), patch.get("official_api"), fixed.get("api"),
        model.get("knownSite"), model.get("officialSite"), model.get("officialHub"), model.get("officialApi"), model.get("fixedApi"),
        *(model.get("origins") or []),
    ]
    origins: list[str] = []
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        try:
            parsed = urllib.parse.urlsplit(text)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                continue
            origin = f"{parsed.scheme}://{parsed.netloc}"
        except ValueError:
            continue
        if origin not in origins:
            origins.append(origin)
    return origins[:24]


def probe_origin(url: str, timeout: int = 8) -> dict[str, Any]:
    headers = {"User-Agent": "NiakVIO-ProviderRouteGate/1.0", "Accept": "text/html,application/json;q=0.9,*/*;q=0.5"}
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return {"url": url, "reachable": True, "status": int(response.status or 0), "method": method, "error": None}
        except urllib.error.HTTPError as exc:
            return {"url": url, "reachable": True, "status": int(exc.code or 0), "method": method, "error": type(exc).__name__}
        except Exception as exc:
            last = {"url": url, "reachable": False, "status": 0, "method": method, "error": type(exc).__name__}
    return last


def coverage_target(candidate_count: int, minimum: float) -> float:
    """Legacy diagnostic only. Advancement uses 100% declared-type coverage."""
    if candidate_count <= 2:
        return 1.0
    return minimum


def evaluate_provider(
    provider_id: str,
    model: dict[str, Any],
    task_rows: list[dict[str, Any]],
    minimum: float,
) -> dict[str, Any]:
    current_route_data = model.get("candidateRouteData") if isinstance(model.get("candidateRouteData"), list) else None
    if current_route_data is None:
        current_route_data = model.get("routeData") if isinstance(model.get("routeData"), list) else []
    candidates = copy.deepcopy(current_route_data)
    original_routes = unique([row.get("route") for row in candidates if isinstance(row, dict)], 256)

    fetch_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for task in task_rows:
        for fetch in task.get("fetches") or []:
            if isinstance(fetch, dict) and provider_fetch(fetch):
                fetch_rows.append((fetch, task))

    matched_indexes: set[int] = set()
    enriched: list[dict[str, Any]] = []
    live_rows: list[dict[str, Any]] = []
    attempted = live = blocked = failed = 0

    for raw in candidates:
        if not isinstance(raw, dict):
            continue
        row = copy.deepcopy(raw)
        route = str(row.get("route") or "").strip()
        matches = []
        for index, (fetch, task) in enumerate(fetch_rows):
            if route and _fetch_matches_model_route(route, fetch, model):
                matches.append((fetch, task, index))
                matched_indexes.add(index)
        row["staticCallEvidence"] = bool(row.get("executedEvidence") or row.get("staticCallEvidence"))
        row["executedEvidence"] = False
        row["httpUsed"] = False
        row.pop("liveEvidence", None)
        row.pop("attemptEvidence", None)
        if matches:
            attempted += 1
            row["attemptEvidence"] = [live_evidence(fetch, task) for fetch, task, _ in matches[:16]]
        successful = [(fetch, task, index) for fetch, task, index in matches if success(fetch)]
        if successful:
            live += 1
            row["validationState"] = "live-validated"
            row["executedEvidence"] = True
            row["httpUsed"] = True
            row["liveEvidence"] = [live_evidence(fetch, task) for fetch, task, _ in successful[:16]]
            strongest, _task, _index = successful[0]
            row["method"] = str(strongest.get("method") or row.get("method") or "GET").upper()
            row["observedHeaderNames"] = list(strongest.get("header_names") or [])
            row["observedBodyKind"] = strongest.get("body_kind")
            row["observedBodyFields"] = list(strongest.get("body_fields") or [])
            row["observedContentType"] = strongest.get("content_type")
            live_rows.append(copy.deepcopy(row))
        elif matches:
            statuses = {int(fetch.get("status") or 0) for fetch, _task, _ in matches}
            if statuses and statuses <= BLOCKED_STATUSES:
                blocked += 1
                row["validationState"] = "blocked-live"
            else:
                failed += 1
                row["validationState"] = "failed-live"
        else:
            row["validationState"] = "candidate-not-executed"
        enriched.append(row)

    derived_by_route: dict[str, dict[str, Any]] = {}
    unresolved_observed: list[dict[str, Any]] = []
    for index, (fetch, task) in enumerate(fetch_rows):
        if index in matched_indexes:
            continue
        route, derivation = derive_observed_route(fetch, task)
        evidence = live_evidence(fetch, task)
        if not route:
            unresolved_observed.append({**evidence, "derivation": derivation, "shape": request_shape(fetch)})
            continue
        existing = derived_by_route.get(route)
        if existing is None:
            state = "live-validated" if success(fetch) else ("blocked-live" if int(fetch.get("status") or 0) in BLOCKED_STATUSES else "failed-live")
            existing = {
                "route": route,
                "role": route_role(route),
                "method": str(fetch.get("method") or "GET").upper(),
                "bodyFields": list(fetch.get("body_fields") or []),
                "formEncoded": str(fetch.get("body_kind") or "") == "form",
                "jsonEncoded": str(fetch.get("body_kind") or "") == "json",
                "refererRequired": "referer" in [str(v).casefold() for v in fetch.get("header_names") or []],
                "originRequired": "origin" in [str(v).casefold() for v in fetch.get("header_names") or []],
                "response": str(fetch.get("content_type") or "unknown"),
                "executedEvidence": success(fetch),
                "httpUsed": success(fetch),
                "evidence": "live-observed-runtime-request",
                "evidenceSources": ["live-observed-runtime-request"],
                "confidence": 1.0,
                "validationState": state,
                "liveDerived": True,
                "derivation": derivation,
                "attemptEvidence": [],
                "liveEvidence": [],
            }
            derived_by_route[route] = existing
        existing["attemptEvidence"].append(evidence)
        if success(fetch):
            existing["executedEvidence"] = True
            existing["httpUsed"] = True
            existing["validationState"] = "live-validated"
            existing["liveEvidence"].append(evidence)

    for row in derived_by_route.values():
        row["attemptEvidence"] = row["attemptEvidence"][:16]
        row["liveEvidence"] = row["liveEvidence"][:16]
        enriched.append(copy.deepcopy(row))
        if row["validationState"] == "live-validated":
            live_rows.append(copy.deepcopy(row))

    observed_shapes = {request_shape(fetch) for fetch, _task in fetch_rows}
    reusable_observed_shapes: set[str] = set()
    for fetch, task in fetch_rows:
        route, _meta = derive_observed_route(fetch, task)
        if route:
            reusable_observed_shapes.add(request_shape(fetch))

    candidate_count = len(original_routes)
    candidate_ratio = attempted / candidate_count if candidate_count else 0.0
    observed_ratio = len(reusable_observed_shapes) / len(observed_shapes) if observed_shapes else 0.0

    attempted_types = {canonical(task.get("semantic_type")) for task in task_rows}
    required_types = set(model.get("canonicalSupportedTypes") or [])
    required_types = {canonical(v) for v in required_types if canonical(v) in REPRESENTATIVE}
    if not required_types:
        required_types = attempted_types

    type_route_evidence, type_route_templates, validated_types = _validate_declared_type_routes(
        model, task_rows, required_types
    )
    declared_type_ratio = len(validated_types) / len(required_types) if required_types else 1.0
    type_complete = required_types <= validated_types
    playable_verified = any(task.get("status") == "playable_verified" for task in task_rows)
    provider_success_http = any(success(fetch) for fetch, _task in fetch_rows)
    provider_blocked_only = bool(fetch_rows) and all(int(fetch.get("status") or 0) in BLOCKED_STATUSES for fetch, _task in fetch_rows)
    direct_output_only = bool(required_types) and type_complete and not fetch_rows and all(
        any(
            canonical(task.get("semantic_type")) == media_type and task.get("status") == "playable_verified"
            for task in task_rows
        )
        for media_type in required_types
    )

    return {
        "providerId": provider_id,
        "candidateRouteData": enriched,
        "liveRouteData": live_rows,
        "liveRoutes": unique([row.get("route") for row in live_rows], 256),
        "candidateRouteCount": candidate_count,
        "attemptedRouteCount": attempted,
        "liveValidatedRouteCount": sum(1 for row in live_rows if row.get("validationState") == "live-validated"),
        "blockedRouteCount": blocked + sum(1 for row in derived_by_route.values() if row.get("validationState") == "blocked-live"),
        "failedRouteCount": failed + sum(1 for row in derived_by_route.values() if row.get("validationState") == "failed-live"),
        "unexecutedCandidateRouteCount": max(0, candidate_count - attempted),
        "providerRequestCount": len(fetch_rows),
        "observedRequestShapeCount": len(observed_shapes),
        "reusableObservedShapeCount": len(reusable_observed_shapes),
        "unresolvedObservedRequestCount": len(unresolved_observed),
        "candidateCoverageRatio": round(candidate_ratio, 4),
        "observedRouteCaptureRatio": round(observed_ratio, 4),
        "effectiveCoverageRatio": round(declared_type_ratio, 4),
        "requiredCoverageRatio": 1.0,
        "declaredTypeCoverageRatio": round(declared_type_ratio, 4),
        "requiredTypes": sorted(required_types),
        "attemptedTypes": sorted(attempted_types),
        "validatedTypes": sorted(validated_types),
        "missingTypes": sorted(required_types - validated_types),
        "declaredTypeRouteTemplates": type_route_templates,
        "declaredTypeRouteEvidence": type_route_evidence,
        "typeComplete": type_complete,
        "playableVerified": playable_verified,
        "directOutputOnly": direct_output_only,
        "providerSuccessHttp": provider_success_http,
        "providerBlockedOnly": provider_blocked_only,
        "unresolvedObservedRequests": unresolved_observed[:40],
        "tasks": [{k: v for k, v in task.items() if k not in {"fetches", "fixture"}} for task in task_rows],
    }


def should_pass(evaluation: dict[str, Any]) -> bool:
    return bool(
        evaluation.get("typeComplete")
        and float(evaluation.get("declaredTypeCoverageRatio") or 0.0) >= 1.0
    )


def finalize_provider(
    provider_id: str,
    provider_row: dict[str, Any],
    knowledge: dict[str, Any],
    overrides: dict[str, Any],
    evaluation: dict[str, Any],
    completion_state: str,
    origin_evidence: list[dict[str, Any]],
) -> None:
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    static_row = providers.get(provider_id)
    if not isinstance(static_row, dict):
        raise ValueError(f"{provider_id}: missing static knowledge row")
    model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
    knowledge_row = static_row.get("knowledge") if isinstance(static_row.get("knowledge"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}

    if not isinstance(model.get("candidateApiRecipe"), dict) and isinstance(model.get("apiRecipe"), dict):
        model["candidateApiRecipe"] = copy.deepcopy(model["apiRecipe"])
    if not isinstance(model.get("candidateRoutes"), list):
        model["candidateRoutes"] = unique(model.get("routes") or [], 256)
    model["candidateRouteData"] = copy.deepcopy(evaluation["candidateRouteData"])

    # PROVIDER_V3_EXECUTION_PLAN_FINALIZATION_V1
    # Coverage proof, runtime traversal evidence and persistent Provider DATA are
    # distinct layers. Dynamic landing/gateway URLs may prove a type without
    # becoming fixed routes in the next bundle.
    stable_candidate_rows = [
        copy.deepcopy(row)
        for row in evaluation["candidateRouteData"]
        if isinstance(row, dict)
        and str(row.get("route") or "").strip()
        and not row.get("liveDerived")
    ]
    runtime_derived_rows = [
        copy.deepcopy(row)
        for row in evaluation["candidateRouteData"]
        if isinstance(row, dict)
        and str(row.get("route") or "").strip()
        and row.get("liveDerived")
    ]
    # PROVIDER_V3_SAFE_RUNTIME_ROUTE_PROMOTION_V2
    # Runtime-derived does not automatically mean volatile. A route template may
    # be discovered from live execution and still be safe Provider DATA when its
    # derivation proves that all fixture-specific values were abstracted away.
    safe_runtime_derived_rows = [
        copy.deepcopy(row)
        for row in runtime_derived_rows
        if row.get("validationState") == "live-validated"
        and isinstance(row.get("derivation"), dict)
        and row["derivation"].get("reusable") is True
        and not (row["derivation"].get("fixtureSpecificValues") or [])
        and "{" in str(row.get("route") or "")
        and "}" in str(row.get("route") or "")
    ]
    if completion_state in {"terminal-blocked", "terminal-unreachable"}:
        execution_plan_rows = stable_candidate_rows
    elif completion_state == "declared-types-qualified":
        # PROVIDER_V3_FAILED_LIVE_NOT_EXECUTION_DATA_V2
        # A route that was actually traversed and failed is useful negative
        # evidence, but it is not executable Provider source DATA. Keep blocked
        # routes (auth/rate/policy can be environmental), keep live-validated
        # routes, and keep failed-live rows only in candidate/diagnostic evidence.
        execution_plan_rows = [
            row for row in stable_candidate_rows
            if row.get("validationState") != "failed-live"
            and (
                row.get("attemptEvidence")
                or row.get("validationState") == "live-validated"
            )
        ]
        execution_plan_routes = {
            str(row.get("route") or "") for row in execution_plan_rows if isinstance(row, dict)
        }
        for row in safe_runtime_derived_rows:
            route = str(row.get("route") or "")
            if route and route not in execution_plan_routes:
                execution_plan_rows.append(row)
                execution_plan_routes.add(route)
    else:
        execution_plan_rows = stable_candidate_rows

    model["routeData"] = execution_plan_rows
    model["routes"] = unique(
        [row.get("route") for row in execution_plan_rows if isinstance(row, dict)],
        256,
    )

    # Runtime observations are diagnostics, not Provider DATA authority. Preserve
    # the stable candidate origins/URLs exactly; collect traversal observations
    # separately for the report so signed/session URLs cannot alter the final build.
    stable_origins = list(model.get("origins") or [])
    stable_observed_urls = list(model.get("observedUrls") or [])
    runtime_observed_urls = []
    runtime_observed_origins = []
    for row in evaluation["candidateRouteData"]:
        for item in row.get("attemptEvidence") or []:
            raw = str(item.get("finalUrl") or item.get("url") or "")
            if raw and raw not in runtime_observed_urls:
                runtime_observed_urls.append(raw)
            try:
                parsed = urllib.parse.urlsplit(raw)
                if parsed.scheme in {"http", "https"} and parsed.hostname:
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    if origin not in runtime_observed_origins:
                        runtime_observed_origins.append(origin)
            except ValueError:
                pass
    model["origins"] = stable_origins[:64]
    model["observedUrls"] = stable_observed_urls[:128]

    live_set = set(evaluation["liveRoutes"])
    execution_plan_set = set(model.get("routes") or [])
    candidate_model_recipe = model.get("candidateApiRecipe")
    if isinstance(candidate_model_recipe, dict):
        model["apiRecipe"] = copy.deepcopy(candidate_model_recipe)

    model["routeRecognition"] = {
        "version": 4,
        "status": completion_state,
        "completionState": completion_state,
        "candidateRouteCount": evaluation["candidateRouteCount"],
        "attemptedRouteCount": evaluation["attemptedRouteCount"],
        "liveValidatedRouteCount": evaluation["liveValidatedRouteCount"],
        "blockedRouteCount": evaluation["blockedRouteCount"],
        "failedRouteCount": evaluation["failedRouteCount"],
        "unexecutedCandidateRouteCount": evaluation["unexecutedCandidateRouteCount"],
        "providerRequestCount": evaluation["providerRequestCount"],
        "observedRequestShapeCount": evaluation["observedRequestShapeCount"],
        "reusableObservedShapeCount": evaluation["reusableObservedShapeCount"],
        "unresolvedObservedRequestCount": evaluation["unresolvedObservedRequestCount"],
        "candidateCoverageRatio": evaluation["candidateCoverageRatio"],
        "observedRouteCaptureRatio": evaluation["observedRouteCaptureRatio"],
        "effectiveCoverageRatio": evaluation["effectiveCoverageRatio"],
        "requiredCoverageRatio": evaluation["requiredCoverageRatio"],
        "declaredTypeCoverageRatio": evaluation["declaredTypeCoverageRatio"],
        "requiredTypes": evaluation["requiredTypes"],
        "attemptedTypes": evaluation["attemptedTypes"],
        "validatedTypes": evaluation["validatedTypes"],
        "missingTypes": evaluation["missingTypes"],
        "declaredTypeRouteTemplates": evaluation["declaredTypeRouteTemplates"],
        "declaredTypeRouteEvidence": evaluation["declaredTypeRouteEvidence"],
        "typeComplete": evaluation["typeComplete"],
        "providerJavaScriptExecuted": True,
        "liveTraversalRequiredForPromotion": True,
        "staticEvidenceIsNotHttpProof": True,
        "declaredTypesAreGateDenominator": True,
        "internalRequestsAreNotGateDenominator": True,
        "executionPlanRouteCount": len(model.get("routes") or []),
        "executionPlanRetainsAttemptedNon2xx": completion_state in {"terminal-blocked", "terminal-unreachable"},
        "executionPlanRetainsFailedLive": False,
        "blockedNon2xxPlanPreserved": completion_state in {"terminal-blocked", "terminal-unreachable"},
        "runtimeDerivedRouteCount": len(runtime_derived_rows),
        "runtimeDerivedRoutesPersisted": False,
        "safeRuntimeDerivedRouteCount": len(safe_runtime_derived_rows),
        "safeRuntimeDerivedRoutesPromoted": (
            len(safe_runtime_derived_rows) if completion_state == "declared-types-qualified" else 0
        ),
        "runtimeObservedUrlCount": len(runtime_observed_urls),
        "runtimeObservedOriginCount": len(runtime_observed_origins),
        "runtimeObservationsPersistedAsProviderData": False,
        "blockedPlanPreserved": completion_state in {"terminal-blocked", "terminal-unreachable"},
        "sequentialProviderGate": True,
        "advancedToNextProvider": True,
        "originEvidence": origin_evidence,
    }

    recognized = knowledge_row.get("recognizedContract") if isinstance(knowledge_row.get("recognizedContract"), dict) else {}
    recognized["requests"] = copy.deepcopy(evaluation["liveRouteData"])
    recognized["candidateRequests"] = copy.deepcopy(evaluation["candidateRouteData"])
    recognized["candidateRouteCount"] = evaluation["candidateRouteCount"]
    recognized["attemptedRouteCount"] = evaluation["attemptedRouteCount"]
    recognized["liveValidatedRouteCount"] = evaluation["liveValidatedRouteCount"]
    recognized["httpProvenRouteCount"] = evaluation["liveValidatedRouteCount"]
    recognized["effectiveCoverageRatio"] = evaluation["effectiveCoverageRatio"]
    recognized["requiredCoverageRatio"] = evaluation["requiredCoverageRatio"]
    recognized["declaredTypeCoverageRatio"] = evaluation["declaredTypeCoverageRatio"]
    recognized["validatedTypes"] = evaluation["validatedTypes"]
    recognized["missingTypes"] = evaluation["missingTypes"]
    recognized["declaredTypeRouteEvidence"] = copy.deepcopy(evaluation["declaredTypeRouteEvidence"])
    recognized["completionState"] = completion_state
    recognized["providerJavaScriptExecuted"] = True
    recognized["liveTraversalRequiredForPromotion"] = True
    recognized["staticEvidenceIsNotHttpProof"] = True
    recognized["declaredTypesAreGateDenominator"] = True
    recognized["executionPlanRequests"] = copy.deepcopy(model.get("routeData") or [])
    recognized["executionPlanRouteCount"] = len(model.get("routes") or [])
    recognized["runtimeDerivedRequests"] = copy.deepcopy(runtime_derived_rows[:80])
    recognized["runtimeDerivedRoutesPersisted"] = False
    recognized["safeRuntimeDerivedRequests"] = copy.deepcopy(safe_runtime_derived_rows[:80])
    recognized["safeRuntimeDerivedRoutesPromoted"] = (
        len(safe_runtime_derived_rows) if completion_state == "declared-types-qualified" else 0
    )
    recognized["runtimeObservedUrls"] = runtime_observed_urls[:80]
    recognized["runtimeObservedOrigins"] = runtime_observed_origins[:40]
    recognized["runtimeObservationsPersistedAsProviderData"] = False
    recognized["sequentialProviderGate"] = True
    knowledge_row["recognizedContract"] = recognized
    static_row["model"] = model
    static_row["knowledge"] = knowledge_row

    if isinstance(patch, dict):
        if isinstance(patch.get("learned_routes"), list) and not isinstance(patch.get("candidate_learned_routes"), list):
            patch["candidate_learned_routes"] = list(patch.get("learned_routes") or [])
        candidate_learned = patch.get("candidate_learned_routes") if isinstance(patch.get("candidate_learned_routes"), list) else patch.get("learned_routes") or []
        patch["learned_routes"] = [
            str(route) for route in candidate_learned
            if str(route) in execution_plan_set
        ]
        for route in model.get("routes") or []:
            if route not in patch["learned_routes"]:
                patch["learned_routes"].append(route)
        if isinstance(patch.get("api_recipe"), dict) and not isinstance(patch.get("candidate_api_recipe"), dict):
            patch["candidate_api_recipe"] = copy.deepcopy(patch["api_recipe"])
        candidate_recipe = patch.get("candidate_api_recipe") if isinstance(patch.get("candidate_api_recipe"), dict) else patch.get("api_recipe")
        if isinstance(candidate_recipe, dict):
            patch["api_recipe"] = copy.deepcopy(candidate_recipe)
        patch["live_route_gate"] = {
            "completion_state": completion_state,
            "effective_coverage_ratio": evaluation["effectiveCoverageRatio"],
            "required_coverage_ratio": evaluation["requiredCoverageRatio"],
            "declared_type_coverage_ratio": evaluation["declaredTypeCoverageRatio"],
            "required_types": evaluation["requiredTypes"],
            "validated_types": evaluation["validatedTypes"],
            "missing_types": evaluation["missingTypes"],
            "provider_request_count": evaluation["providerRequestCount"],
            "live_validated_route_count": evaluation["liveValidatedRouteCount"],
            "execution_plan_route_count": len(model.get("routes") or []),
            "runtime_derived_route_count": len(runtime_derived_rows),
            "runtime_derived_routes_persisted": False,
            "safe_runtime_derived_route_count": len(safe_runtime_derived_rows),
            "safe_runtime_derived_routes_promoted": (
                len(safe_runtime_derived_rows) if completion_state == "declared-types-qualified" else 0
            ),
            "runtime_observed_url_count": len(runtime_observed_urls),
            "runtime_observed_origin_count": len(runtime_observed_origins),
            "runtime_observations_persisted_as_provider_data": False,
            "blocked_plan_preserved": completion_state in {"terminal-blocked", "terminal-unreachable"},
            "declared_types_are_gate_denominator": True,
            "sequential": True,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sequential Provider v3 declared-type live route/DATA gate")
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--minimum-coverage", type=float, default=DEFAULT_MIN_COVERAGE)
    parser.add_argument("--timeout", type=int, default=50)
    parser.add_argument("--origin-timeout", type=int, default=8)
    args = parser.parse_args()

    minimum = float(args.minimum_coverage)
    if not 0.5 <= minimum <= 1.0:
        raise SystemExit("--minimum-coverage must be between 0.5 and 1.0")
    if not (str(__import__("os").environ.get("TMDB_API_KEY") or "").strip() or str(__import__("os").environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        raise SystemExit("TMDB_API_KEY or TMDB_ACCESS_TOKEN is required")

    queue, provider_count = build_provider_queue()
    if provider_count != EXPECTED or len(queue) != EXPECTED:
        raise SystemExit(f"sequential gate provider count={provider_count}/{len(queue)}, expected={EXPECTED}")

    knowledge_path = args.knowledge.resolve()
    overrides_path = args.overrides.resolve()
    output_path = args.output.resolve()
    knowledge = load(knowledge_path)
    overrides = load(overrides_path)
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    report_rows: list[dict[str, Any]] = []
    totals = Counter()

    for index, provider in enumerate(queue, start=1):
        provider_id = provider["provider_id"]
        static_row = providers.get(provider_id)
        if not isinstance(static_row, dict):
            raise SystemExit(f"{provider_id}: missing static knowledge")
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        model["canonicalSupportedTypes"] = list(provider.get("supported_types") or [])

        print(
            "FIELD_PROVIDER_SEQUENTIAL_BEGIN "
            f"index={index} total={EXPECTED} provider={provider_id} "
            f"types={','.join(provider['supported_types'])} fixtures={len(provider['tasks'])}",
            flush=True,
        )

        rows: list[dict[str, Any]] = []
        evaluation = evaluate_provider(provider_id, model, rows, minimum)
        passed = False
        for task_index, task in enumerate(provider["tasks"], start=1):
            result = run_task(task, max(20, min(int(args.timeout), 120)))
            result["fixture_slug"] = task.get("fixture_slug")
            result["fixture"] = copy.deepcopy(task.get("fixture") or {})
            rows.append(result)
            evaluation = evaluate_provider(provider_id, model, rows, minimum)
            print(
                "FIELD_PROVIDER_SEQUENTIAL_PROBE "
                f"provider={provider_id} fixture={task.get('fixture_slug')} step={task_index}/{len(provider['tasks'])} "
                f"declared_types={','.join(evaluation['requiredTypes']) or 'none'} "
                f"validated_types={','.join(evaluation['validatedTypes']) or 'none'} "
                f"missing_types={','.join(evaluation['missingTypes']) or 'none'} "
                f"type_coverage={evaluation['declaredTypeCoverageRatio']:.3f} target=1.000 "
                f"requests={evaluation['providerRequestCount']} live={evaluation['liveValidatedRouteCount']}",
                flush=True,
            )
            if should_pass(evaluation):
                passed = True
                break

        origin_evidence: list[dict[str, Any]] = []
        completion_state = "declared-types-qualified"
        if not passed:
            origins = provider_origins(model, patch)
            if evaluation.get("providerRequestCount", 0) == 0 or not evaluation.get("providerSuccessHttp"):
                origin_evidence = [probe_origin(url, max(3, min(int(args.origin_timeout), 15))) for url in origins]

            if evaluation.get("directOutputOnly") and evaluation.get("typeComplete"):
                completion_state = "direct-output-verified"
                passed = True
            elif evaluation.get("providerBlockedOnly") and evaluation.get("providerRequestCount", 0) > 0:
                completion_state = "terminal-blocked"
                passed = True
            elif origins and origin_evidence and not any(row.get("reachable") for row in origin_evidence):
                completion_state = "terminal-unreachable"
                passed = True
            else:
                failure = {
                    **evaluation,
                    "completionState": "missing-declared-type-route-proof",
                    "originEvidence": origin_evidence,
                    "advancedToNextProvider": False,
                }
                report_rows.append(failure)
                partial = {
                    "schemaVersion": 3,
                    "method": "strict-sequential-provider-declared-type-live-route-gate",
                    "providerCount": EXPECTED,
                    "completedProviderCount": index - 1,
                    "failedProvider": provider_id,
                    "providers": report_rows,
                }
                write(output_path, partial)
                write(knowledge_path, knowledge)
                write(overrides_path, overrides)
                raise SystemExit(
                    f"{provider_id}: missing live route proof for declared types "
                    f"{','.join(evaluation['missingTypes']) or 'unknown'}; refusing to advance to provider {index + 1}"
                )

        finalize_provider(provider_id, provider, knowledge, overrides, evaluation, completion_state, origin_evidence)
        row = {
            **evaluation,
            "completionState": completion_state,
            "originEvidence": origin_evidence,
            "advancedToNextProvider": True,
        }
        report_rows.append(row)
        totals["candidates"] += int(evaluation["candidateRouteCount"])
        totals["attempted"] += int(evaluation["attemptedRouteCount"])
        totals["live"] += int(evaluation["liveValidatedRouteCount"])
        totals["blocked"] += int(evaluation["blockedRouteCount"])
        totals["failed"] += int(evaluation["failedRouteCount"])
        totals["requests"] += int(evaluation["providerRequestCount"])
        totals[completion_state] += 1

        write(knowledge_path, knowledge)
        write(overrides_path, overrides)
        write(output_path, {
            "schemaVersion": 3,
            "method": "strict-sequential-provider-declared-type-live-route-gate",
            "providerCount": EXPECTED,
            "completedProviderCount": index,
            "candidateRouteCount": totals["candidates"],
            "attemptedRouteCount": totals["attempted"],
            "liveValidatedRouteCount": totals["live"],
            "blockedRouteCount": totals["blocked"],
            "failedRouteCount": totals["failed"],
            "providerRequestCount": totals["requests"],
            "completionStates": {k: v for k, v in totals.items() if k not in {"candidates", "attempted", "live", "blocked", "failed", "requests"}},
            "providers": report_rows,
        })
        print(
            "FIELD_PROVIDER_SEQUENTIAL_PASS "
            f"index={index} provider={provider_id} state={completion_state} "
            f"validated_types={','.join(evaluation['validatedTypes']) or 'none'} "
            f"type_coverage={evaluation['declaredTypeCoverageRatio']:.3f} "
            f"live={evaluation['liveValidatedRouteCount']} requests={evaluation['providerRequestCount']}",
            flush=True,
        )

    final_report = load(output_path)
    final_report["allProvidersAdvancedSequentially"] = True
    final_report["sequentialNoInterProviderConcurrency"] = True
    final_report["declaredTypesAreGateDenominator"] = True
    write(output_path, final_report)
    knowledge["liveRouteValidation"] = {
        "schemaVersion": 3,
        "method": "strict-sequential-provider-declared-type-live-route-gate",
        "providerCount": EXPECTED,
        "completedProviderCount": EXPECTED,
        "allProvidersAdvancedSequentially": True,
        "declaredTypesAreGateDenominator": True,
        "requiredDeclaredTypeCoverageRatio": 1.0,
        "internalRequestsAreGateDenominator": False,
        "staticEvidenceIsHttpProof": False,
        "candidateRoutesAreExecutableAuthority": False,
    }
    write(knowledge_path, knowledge)
    print(
        "FIELD_PROVIDER_ROUTE_SEQUENTIAL_COMPLETE "
        f"providers={EXPECTED} declared_type_coverage=1.00 "
        f"live={final_report.get('liveValidatedRouteCount', 0)} requests={final_report.get('providerRequestCount', 0)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

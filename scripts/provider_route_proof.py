#!/usr/bin/env python3
"""Shared proof-first Provider v3 route derivation.

Static/upstream route strings are candidates only. Executable Provider DATA may only
be derived from HTTP requests observed while executing that provider. Dynamic values
are abstracted only when the trace proves where they came from (fixture identity or a
prior provider response value). Anything with unresolved fixture/session residue stays
diagnostic evidence and is never promoted to runtime authority.
"""
from __future__ import annotations

import copy
import re
import urllib.parse
from typing import Any, Iterable

SEMANTIC_TYPES = {"movie", "tv", "anime"}
ROUTE_FIELD_SUFFIXES = ("route", "routes", "path", "paths", "endpoint", "endpoints", "url", "urls")
ROUTE_FIELD_EXCLUDED = {
    "base", "baseurl", "referer", "referrer", "origin", "host", "domain",
    "officialsite", "officialhub", "officialapi", "fixedapi",
}
PROVIDER_VALUE_KEYS = {
    "id", "_id", "media_id", "mediaid", "post_id", "postid", "content_id", "contentid",
    "movie_id", "movieid", "series_id", "seriesid", "show_id", "showid", "slug",
}
VOLATILE_QUERY_KEYS = {
    "seed", "token", "access_token", "auth", "signature", "sig", "hash", "nonce",
    "timestamp", "ts", "expires", "expiry", "expire", "key", "session", "session_id",
}
CONTENT_IDENTITY_QUERY_KEYS = {
    "imdb", "imdbid", "imdb_id", "year", "releaseyear", "release_year",
    "seasonid", "season_id", "episodeid", "episode_id",
}


def canonical(value: object) -> str:
    return str(value or "").strip().casefold()


def unique(values: Iterable[Any], limit: int = 256) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def routeish_key(key: object) -> bool:
    compact = str(key or "").strip().replace("-", "").replace("_", "").casefold()
    return bool(compact and compact not in ROUTE_FIELD_EXCLUDED and compact.endswith(ROUTE_FIELD_SUFFIXES))


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


def filter_recipe_by_live_routes(recipe: dict[str, Any], live_routes: set[str]) -> dict[str, Any] | None:
    """Keep recipe metadata but only route fields proven live in this provider trace."""
    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, child in value.items():
                if routeish_key(key):
                    if isinstance(child, str):
                        text = child.strip()
                        if text and text in live_routes:
                            out[key] = child
                    elif isinstance(child, list):
                        kept = [item for item in child if isinstance(item, str) and item.strip() in live_routes]
                        if kept:
                            out[key] = kept
                    continue
                if isinstance(child, (dict, list)):
                    nested = walk(child)
                    if nested not in ({}, [], None):
                        out[key] = nested
                else:
                    out[key] = copy.deepcopy(child)
            return out
        if isinstance(value, list):
            out = []
            for child in value:
                if isinstance(child, (dict, list)):
                    nested = walk(child)
                    if nested not in ({}, [], None):
                        out.append(nested)
                else:
                    out.append(copy.deepcopy(child))
            return out
        return copy.deepcopy(value)

    filtered = walk(recipe)
    if not isinstance(filtered, dict):
        return None
    if not list(iter_recipe_routes(filtered)):
        return None
    return filtered


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


def route_role(route: str) -> str:
    value = canonical(route)
    try:
        parsed = urllib.parse.urlsplit(value)
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    except ValueError:
        query = {}
    has_episode = any(key in query for key in ("e", "ep", "episode", "episode_number"))
    has_season = any(key in query for key in ("season", "season_number")) or ("s" in query and has_episode)
    if (
        re.search(r"/(?:search|recherche)(?:[/?#]|$)", value)
        or any(key in query for key in ("q", "query", "keyword", "search", "story"))
        or ("s" in query and not has_season)
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


def _slug_candidates(fixture: dict[str, Any]) -> list[str]:
    values = [fixture.get("title"), *(fixture.get("aliases") or [])]
    out: list[str] = []
    for raw in values:
        text = canonical(raw)
        if not text:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
        compact = re.sub(r"[^a-z0-9]+", "", text)
        for value in (slug, compact):
            if value and len(value) >= 4 and value not in out:
                out.append(value)
    return out


def _provider_hint_values(prior_value_hints: Iterable[dict[str, Any]] | None) -> set[str]:
    out: set[str] = set()
    for row in prior_value_hints or []:
        if not isinstance(row, dict):
            continue
        key = canonical(row.get("key"))
        value = str(row.get("value") or "").strip()
        if key not in PROVIDER_VALUE_KEYS or not value or len(value) < 2 or len(value) > 160:
            continue
        if re.fullmatch(r"[A-Za-z0-9._~-]+", value):
            out.add(value)
    return out


def response_value_hints(fetch: dict[str, Any]) -> list[dict[str, str]]:
    rows = fetch.get("response_value_hints")
    if not isinstance(rows, list):
        return []
    out: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = canonical(row.get("key"))
        value = str(row.get("value") or "").strip()
        if key in PROVIDER_VALUE_KEYS and value and len(value) <= 160:
            out.append({"key": key, "value": value})
    return out[:80]


def derive_observed_route(
    fetch: dict[str, Any],
    task: dict[str, Any],
    prior_value_hints: Iterable[dict[str, Any]] | None = None,
) -> tuple[str | None, dict[str, Any]]:
    """Derive one reusable route only from this observed provider HTTP call."""
    raw = str(fetch.get("final_url") or fetch.get("url") or "")
    fixture = task.get("fixture") if isinstance(task.get("fixture"), dict) else {}
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError:
        return None, {"reason": "invalid-url", "observedUrl": raw, "reusable": False}
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None, {"reason": "invalid-origin", "observedUrl": raw, "reusable": False}

    path = parsed.path or "/"
    substitutions: list[dict[str, str]] = []
    reusable = True
    provider_values = _provider_hint_values(prior_value_hints)

    tmdb = str(fixture.get("tmdbId") or "").strip()
    season = str(fixture.get("season") or "").strip()
    episode = str(fixture.get("episode") or "").strip()
    title_values = {canonical(fixture.get("title"))}
    title_values.update(canonical(v) for v in fixture.get("aliases") or [])
    title_values.discard("")

    parts = path.split("/")
    for index, part in enumerate(parts):
        decoded = urllib.parse.unquote(part)
        placeholder = None
        if tmdb and decoded == tmdb:
            placeholder = "{tmdbId}"
        elif decoded in provider_values:
            placeholder = "{id}"
        else:
            for slug in _slug_candidates(fixture):
                if canonical(decoded) == canonical(slug):
                    placeholder = "{slug}"
                    break
        if placeholder:
            substitutions.append({"value": decoded, "placeholder": placeholder, "location": "path"})
            parts[index] = placeholder
    path = "/".join(parts)

    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    rendered_query: list[tuple[str, str]] = []
    dynamic_query_residue: list[dict[str, str]] = []
    for key, value in query:
        key_l = canonical(key)
        replacement = value
        placeholder = None
        if tmdb and value == tmdb and key_l in {"id", "tmdb", "tmdbid", "tmdb_id", "movie", "tv"}:
            placeholder = "{tmdbId}"
        elif season and value == season and key_l in {"s", "season", "season_number", "seasonid", "season_id"}:
            placeholder = "{season}"
        elif episode and value == episode and key_l in {"e", "ep", "episode", "episode_number", "episodeid", "episode_id"}:
            placeholder = "{episode}"
        elif canonical(value) in title_values and key_l in {"q", "query", "search", "title", "keyword", "story", "s"}:
            placeholder = "{query}"
        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:
            placeholder = "{id}"
        if placeholder:
            replacement = placeholder
            substitutions.append({"value": value, "placeholder": placeholder, "location": f"query:{key}"})
        elif value and key_l in VOLATILE_QUERY_KEYS | CONTENT_IDENTITY_QUERY_KEYS:
            dynamic_query_residue.append({"key": key, "value": value})
        rendered_query.append((key, replacement))
    if dynamic_query_residue:
        reusable = False

    route = path
    if rendered_query:
        route += "?" + urllib.parse.urlencode(rendered_query, doseq=True, safe="{}:/")

    fixture_specific: list[str] = []
    if tmdb and tmdb in route:
        fixture_specific.append(tmdb)
    try:
        residue_parts = urllib.parse.urlsplit(route)
        haystacks = [urllib.parse.unquote(residue_parts.path or "/").casefold()]
        semantic_keys = {"type", "mediatype", "media_type", "media", "category", "kind"}
        for residue_key, residue_value in urllib.parse.parse_qsl(residue_parts.query, keep_blank_values=True):
            if canonical(residue_key) in semantic_keys and canonical(residue_value) in SEMANTIC_TYPES:
                continue
            haystacks.append(urllib.parse.unquote(residue_value).casefold())
    except ValueError:
        haystacks = [urllib.parse.unquote(route).casefold()]
    for raw_title in title_values:
        if raw_title and len(raw_title) >= 4 and any(raw_title in haystack for haystack in haystacks):
            fixture_specific.append(raw_title)
    if fixture_specific:
        reusable = False

    # Literal provider-internal numeric/opaque path values are not generalized
    # unless the prior response trace proved their origin.
    unresolved_segments = [
        segment for segment in urllib.parse.urlsplit(route).path.split("/")
        if segment and "{" not in segment and re.fullmatch(r"[A-Za-z0-9._~-]{2,}", segment)
    ]
    # Fixed route words are fine; only values that look like opaque IDs need proof.
    opaque = [segment for segment in unresolved_segments if re.fullmatch(r"\d{2,}|[A-Fa-f0-9]{12,}|[A-Za-z0-9_-]{18,}", segment)]
    if opaque:
        reusable = False

    meta = {
        "origin": f"{parsed.scheme}://{parsed.netloc}",
        "observedUrl": raw,
        "substitutions": substitutions,
        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),
        "reusable": reusable,
        "fixtureSpecificValues": unique(fixture_specific, 12),
        "dynamicQueryResidue": dynamic_query_residue[:12],
        "unresolvedOpaqueSegments": opaque[:12],
    }
    return (route if reusable else None), meta


def derive_task_routes(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive routes in request order so response values can feed later requests."""
    hints: list[dict[str, str]] = []
    out: list[dict[str, Any]] = []
    for index, fetch in enumerate(task.get("fetches") or []):
        if not isinstance(fetch, dict):
            continue
        route, derivation = derive_observed_route(fetch, task, hints)
        out.append({"index": index, "fetch": fetch, "route": route, "derivation": derivation})
        hints.extend(response_value_hints(fetch))
        if len(hints) > 240:
            hints = hints[-240:]
    return out

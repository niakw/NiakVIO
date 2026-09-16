#!/usr/bin/env python3
"""Fail-closed semantic authority guard for parity-only upstream evidence.

A terminal URL proves that bytes are playable; it does not prove that an upstream
provider selected the requested work. This module is intentionally parity-only.
For Coflix it replays the public search/player contract and correlates the
upstream worker's observed player route to the concrete search candidate that
produced it. A mismatch can downgrade regression evidence only when that
correlation is conclusive. Any network/parser ambiguity returns trusted=None and
leaves the regression fail-closed.
"""
from __future__ import annotations

import json
import re
import unicodedata
import urllib.parse
import urllib.request
from typing import Any, Callable

COFLIX_BASE = "https://coflix.wiki"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36"


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _coflix_title_from_slug(slug: str) -> str:
    value = re.sub(r"-(?:vf|vostfr|truefrench|french)$", "", str(slug or ""), flags=re.I)
    return _norm(value.replace("-", " "))


def coflix_candidate_matches_fixture(slug: str, fixture: dict[str, Any]) -> bool:
    expected = _norm(fixture.get("title") or fixture.get("name"))
    actual = _coflix_title_from_slug(slug)
    if not expected or not actual:
        return False
    if actual == expected:
        return True
    year = str(fixture.get("year") or "").strip()
    return bool(year and actual in {f"{expected} {year}", f"{year} {expected}"})


def _route_key(host: object, path: object) -> str:
    h = str(host or "").strip().casefold()
    if h.startswith("www."):
        h = h[4:]
    p = str(path or "").strip()
    if not h or not p:
        return ""
    return h + p


def _url_route_key(raw: object) -> str:
    try:
        parsed = urllib.parse.urlsplit(str(raw or ""))
        return _route_key(parsed.hostname, parsed.path)
    except Exception:
        return ""


def _request(url: str, *, method: str = "GET", body: bytes | None = None, referer: str | None = None, timeout: int = 12) -> str:
    headers = {
        "User-Agent": UA,
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
    }
    if referer:
        headers["Referer"] = referer
    if method == "POST":
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["X-Requested-With"] = "XMLHttpRequest"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=max(3, min(15, timeout))) as response:
        return response.read(1_500_000).decode("utf-8", errors="replace")


def _coflix_candidates(fixture: dict[str, Any], timeout: int) -> list[dict[str, Any]]:
    title = str(fixture.get("title") or fixture.get("name") or "").strip()
    if not title:
        return []
    raw = _request(
        COFLIX_BASE + "/ajax/search/suggest?keyword=" + urllib.parse.quote(title),
        timeout=timeout,
        referer=COFLIX_BASE + "/",
    )
    doc = json.loads(raw)
    html = str(doc.get("html") or "") if isinstance(doc, dict) else ""
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    pattern = re.compile(r'''href=["'](?:https?://coflix\.wiki)?/film/([^"'/]+)/ep-(\d+)["']''', re.I)
    for match in pattern.finditer(html):
        slug, episode_id = match.group(1), match.group(2)
        key = (slug, episode_id)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "slug": slug,
            "episodeId": episode_id,
            "semanticMatch": coflix_candidate_matches_fixture(slug, fixture),
        })
    return rows


def _coflix_candidate_routes(candidate: dict[str, Any], timeout: int) -> set[str]:
    episode_id = str(candidate.get("episodeId") or "")
    slug = str(candidate.get("slug") or "")
    if not episode_id or not slug:
        return set()
    body = ("episode_id=" + urllib.parse.quote(episode_id)).encode()
    raw = _request(
        COFLIX_BASE + "/ajax/episode/player?episode_id=" + urllib.parse.quote(episode_id),
        method="POST",
        body=body,
        referer=COFLIX_BASE + "/film/" + slug + "/",
        timeout=timeout,
    )
    doc = json.loads(raw)
    message = doc.get("message") if isinstance(doc, dict) else None
    routes: set[str] = set()
    for server in message if isinstance(message, list) else []:
        if not isinstance(server, dict):
            continue
        link = server.get("server_link")
        if isinstance(link, dict):
            link = link.get("url")
        route = _url_route_key(link)
        if route:
            routes.add(route)
    return routes


def assess_coflix_upstream(
    upstream_path: Any,
    fixture: dict[str, Any],
    timeout: int,
    worker_raw: Callable[[Any, dict[str, Any], int], dict[str, Any]],
) -> dict[str, Any]:
    if str(fixture.get("mediaType") or fixture.get("type") or "").casefold() not in {"movie", "film"}:
        return {"trusted": None, "reason": "unsupported_lane"}
    try:
        raw = worker_raw(upstream_path, fixture, timeout)
        observed = {
            _route_key(row.get("host"), row.get("path_pattern"))
            for row in raw.get("network_observations") or []
            if isinstance(row, dict) and not row.get("infrastructure")
        }
        observed.discard("")
        if not observed:
            return {"trusted": None, "reason": "no_upstream_routes"}
        candidates = _coflix_candidates(fixture, timeout)
        if not candidates:
            return {"trusted": None, "reason": "no_search_candidates"}
        matched: list[dict[str, Any]] = []
        for candidate in candidates:
            routes = _coflix_candidate_routes(candidate, timeout)
            overlap = sorted(observed & routes)
            if overlap:
                matched.append({
                    "slug": candidate["slug"],
                    "semanticMatch": bool(candidate["semanticMatch"]),
                    "routeCount": len(overlap),
                })
        if not matched:
            return {"trusted": None, "reason": "player_route_not_correlated", "candidateCount": len(candidates)}
        states = {bool(row["semanticMatch"]) for row in matched}
        if states == {True}:
            trusted: bool | None = True
            reason = "correlated_requested_work"
        elif states == {False}:
            trusted = False
            reason = "correlated_different_work"
        else:
            trusted = None
            reason = "ambiguous_mixed_correlation"
        return {
            "trusted": trusted,
            "reason": reason,
            "matchedCandidates": matched[:6],
            "candidateCount": len(candidates),
        }
    except Exception as exc:
        return {"trusted": None, "reason": "guard_error", "error": type(exc).__name__[:80]}


def assess_upstream(
    provider_id: str,
    upstream_path: Any,
    fixture: dict[str, Any],
    timeout: int,
    worker_raw: Callable[[Any, dict[str, Any], int], dict[str, Any]],
) -> dict[str, Any]:
    if str(provider_id or "").strip().casefold().replace("_", "-") != "coflix":
        return {"trusted": None, "reason": "unsupported_provider"}
    return assess_coflix_upstream(upstream_path, fixture, timeout, worker_raw)


if __name__ == "__main__":
    raise SystemExit("parity helper; import assess_upstream()")

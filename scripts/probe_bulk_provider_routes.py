#!/usr/bin/env python3
"""Probe bulk-onboarding candidates for sanitized executable route DATA.

The probe is read-only. It never promotes a provider and never treats GitHub
network failure as provider failure. A caller may route traffic through the
repository's authorized residential exit; the report records that transport.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / ".github/provider-onboarding/batch.json"
DEFAULT_OUTPUT = ROOT / "automation/provider-bulk-route-discovery-shard.json"
PROBE = ROOT / "scripts/probe_provider_site_structure.py"

sys.path.insert(0, str((ROOT / "scripts").resolve()))
from provider_base_store import provider_model_route_kind, provider_route_is_identity_aware
from provider_patch_blocks import decode_managed_data

SENSITIVE_KEYS = {"k","key","token","sig","signature","auth","authorization","expires","expiry","exp"}
SEARCH_KEYS = {"s","q","query","keyword","search","story"}
TMDB_KEYS = {"tmdb","tmdbid","tmdb_id","tmdb-id"}
IMDB_KEYS = {"imdb","imdbid","imdb_id","imdb-id"}
MEDIA_KEYS = {"media","media_type","mediatype","type"}
SEASON_KEYS = {"season"}
EPISODE_KEYS = {"episode","ep"}

FIXTURES = {
    "movie": {"title": "Interstellar", "tmdbId": "157336", "mediaType": "movie"},
    "tv": {"title": "Breaking Bad", "tmdbId": "1396", "mediaType": "tv", "season": 1, "episode": 1},
    "anime": {"title": "Jujutsu Kaisen", "tmdbId": "95479", "mediaType": "anime", "season": 1, "episode": 1},
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().casefold()).strip("-")


def fixtures_for(row: dict[str, Any]) -> list[dict[str, Any]]:
    types = [str(x).strip().casefold() for x in row.get("types") or row.get("supportedTypes") or []]
    fixtures = [dict(FIXTURES[lane]) for lane in ("movie", "tv", "anime") if lane in types]
    return fixtures or [dict(FIXTURES["movie"])]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").casefold()).strip("-")


def _template_query(query: str, fixture: dict[str, Any]) -> str | None:
    if not query:
        return ""
    pairs = parse_qsl(query, keep_blank_values=True)
    lowered_keys = {str(key or "").strip().casefold() for key, _ in pairs}
    episode_context = bool(lowered_keys & {"e", "ep", "episode"})
    out: list[tuple[str, str]] = []
    for key, value in pairs:
        k = key.strip()
        lk = k.casefold()
        if lk in SENSITIVE_KEYS:
            return None
        raw = str(value or "")
        # A common player pattern is ?s=1&e=1 where s means season, not search.
        if lk == "s" and episode_context and raw.strip().isdigit():
            value = "{season}"
        elif lk in SEARCH_KEYS:
            value = "{query}"
        elif lk in TMDB_KEYS:
            value = "{tmdbId}"
        elif lk in IMDB_KEYS:
            value = "{imdbId}"
        elif lk in MEDIA_KEYS and raw.casefold() not in {"search","find","lookup","play","stream"}:
            value = "{media}"
        elif lk in SEASON_KEYS:
            value = "{season}"
        elif lk in EPISODE_KEYS or lk in {"e", "ep"}:
            value = "{episode}"
        elif raw == str(fixture.get("tmdbId") or ""):
            value = "{tmdbId}"
        elif raw and len(raw) > 80:
            return None
        out.append((k, value))
    # urlencode would escape our placeholders; build a conservative query by hand.
    return "&".join(
        quote(k, safe="._-") + "=" + quote(v, safe="{}._-")
        for k, v in out
    )


def route_pattern(raw: Any, fixture: dict[str, Any]) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    absolute = bool(parsed.scheme and parsed.netloc)
    path = parsed.path or ("/" if absolute else "")
    query = parsed.query
    tmdb_id = str(fixture.get("tmdbId") or "")
    title_slug = slug(str(fixture.get("title") or ""))
    if tmdb_id:
        path = re.sub(rf"(?<!\d){re.escape(tmdb_id)}(?!\d)", "{tmdbId}", path)
    if title_slug and title_slug in path.casefold():
        path = re.sub(re.escape(title_slug), "{slug}", path, flags=re.I)
    templated_query = _template_query(query, fixture)
    if templated_query is None:
        return ""
    if absolute:
        value = urlunsplit((parsed.scheme, parsed.netloc, path, templated_query, ""))
    else:
        value = path + (("?" + templated_query) if templated_query else "")
    # Empty search query literals are common in site JS. Turn them into Core title input.
    value = re.sub(r"([?&](?:s|q|query|keyword|search|story)=)(?=&|$)", r"\1{query}", value, flags=re.I)
    return value[:420] if provider_model_route_kind(value) != "ignore" else ""


def identity_route_candidate(value: Any) -> bool:
    """Discovery uses the same identity-aware publication contract."""
    return provider_route_is_identity_aware(value)


def _host_key(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        host = str(urlsplit(raw).hostname or "").strip().casefold()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def retained_v3_routes(row: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Reuse only exact managed Provider-v3 route DATA on the same current host.

    Historical JS is never executed. Relative routes are accepted only when the
    old managed CONFIG binds the same canonical host as today's intake origin.
    """
    pid = norm(row.get("id") or row.get("provider"))
    current_host = _host_key(row.get("direct") or row.get("direct_url"))
    if not pid or not current_host:
        return [], []
    routes: list[str] = []
    sources: list[str] = []
    config_id = f"PROVIDER.{pid.upper()}.CONFIG.V1"
    archive = ROOT / "provider-old" / "providers"
    for path in sorted(archive.glob(f"{pid}--nuvio--*.js")):
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
            model = decode_managed_data(text, config_id)
        except (OSError, UnicodeError, ValueError):
            continue
        if not isinstance(model, dict):
            continue
        model_hosts = {
            _host_key(value)
            for value in [
                model.get("knownSite"),
                model.get("officialSite"),
                model.get("officialApi"),
                model.get("fixedApi"),
                *(model.get("origins") or []),
            ]
            if _host_key(value)
        }
        if current_host not in model_hosts:
            continue
        accepted = [
            str(route).strip()
            for route in model.get("routes") or []
            if str(route).strip() and identity_route_candidate(route)
        ]
        if not accepted:
            continue
        for route in accepted:
            if route not in routes:
                routes.append(route)
        sources.append(path.relative_to(ROOT).as_posix())
    return routes[:24], sources[:24]


def _norm_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _render_route(route: str, fixture: dict[str, Any]) -> str:
    values = {
        "query": urllib.parse.quote_plus(str(fixture.get("title") or "")),
        "title": urllib.parse.quote_plus(str(fixture.get("title") or "")),
        "slug": slug(str(fixture.get("title") or "")),
        "tmdbId": str(fixture.get("tmdbId") or ""),
        "media": str(fixture.get("mediaType") or "movie"),
        "season": str(fixture.get("season") or 1),
        "episode": str(fixture.get("episode") or 1),
    }
    out = route
    for key, value in values.items():
        out = out.replace("{" + key + "}", value)
    return out


def _identity_response(body: bytes, fixture: dict[str, Any], *, direct_media_route: bool) -> bool:
    if not body:
        return False
    text = body[:1_500_000].decode("utf-8", errors="ignore")
    norm = _norm_text(text)
    title = _norm_text(fixture.get("title"))
    if title and title in norm:
        return True
    if direct_media_route:
        lowered = text.casefold()
        tmdb = str(fixture.get("tmdbId") or "")
        media_markers = (".m3u8", ".mp4", '"stream"', '"streams"', '"url"', "playlist")
        if tmdb and tmdb in text and any(marker in lowered for marker in media_markers):
            return True
    return False


def probe_common_identity_routes(
    direct: str,
    fixture: dict[str, Any],
    *,
    timeout: int,
) -> list[str]:
    """Validate a tiny generic route vocabulary against a real content fixture.

    This is ordinary HTTP observation, not a WAF bypass. Challenges/timeouts
    simply yield no route and remain transport-inconclusive.
    """
    lane = str(fixture.get("mediaType") or "movie").casefold()
    search_routes = [
        "/?s={query}",
        "/search?q={query}",
        "/search?query={query}",
        "/search?keyword={query}",
        "/recherche?q={query}",
        "/recherche?query={query}",
        "/index.php?do=search&subaction=search&story={query}",
    ]
    direct_routes = [
        f"/{lane}/{{tmdbId}}",
        f"/embed/{lane}/{{tmdbId}}",
        f"/api/{lane}/{{tmdbId}}",
        f"/api/sources/{lane}/{{tmdbId}}",
    ]
    if lane in {"tv", "anime"}:
        direct_routes.extend([
            f"/{lane}/{{tmdbId}}/{{season}}/{{episode}}",
            f"/embed/{lane}/{{tmdbId}}/{{season}}/{{episode}}",
            f"/api/sources/{lane}/{{tmdbId}}/{{season}}/{{episode}}",
        ])
    headers = {
        "User-Agent": "NiakVIO/5 provider-route-discovery",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.7",
    }
    accepted: list[str] = []
    for route, direct_media in [
        *((value, False) for value in search_routes),
        *((value, True) for value in direct_routes),
    ]:
        rendered = _render_route(route, fixture)
        url = urllib.parse.urljoin(direct.rstrip("/") + "/", rendered.lstrip("/"))
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=max(2, min(timeout, 10))) as response:
                status = int(getattr(response, "status", 200) or 200)
                if status >= 400:
                    continue
                body = response.read(1_500_000)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            continue
        if _identity_response(body, fixture, direct_media_route=direct_media):
            accepted.append(route)
            # One real search and one direct-media contract are enough for this
            # bounded discovery pass.
            if len(accepted) >= 2:
                break
    return accepted


def observed_candidates(report: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    for row in report.get("route_hints") or []:
        if isinstance(row, dict):
            values.append(row.get("value"))
    for row in report.get("next_chunks") or []:
        if isinstance(row, dict):
            values.extend(row.get("route_hints") or [])
    for row in report.get("runtime_routes") or []:
        if not isinstance(row, dict):
            continue
        values.extend(row.get("route_hints") or [])
        values.extend(row.get("runtime_chunk_route_hints") or [])
        values.extend(row.get("runtime_api_patterns") or [])
        for chunk in row.get("runtime_chunks") or []:
            if isinstance(chunk, dict):
                values.extend(chunk.get("route_hints") or [])
                values.extend(chunk.get("runtime_api_patterns") or [])
    return values


def active_provider_ids() -> set[str]:
    ids: set[str] = set()
    for relative in ("manifest.json", "vf/manifest.json"):
        path = ROOT / relative
        if not path.is_file():
            continue
        payload = load(path)
        for row in payload.get("scrapers") or []:
            if isinstance(row, dict) and row.get("enabled") is not False:
                pid = norm(row.get("id"))
                if pid:
                    ids.add(pid)
    return ids


def provider_rows(request: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in ("providers", "deferredProviders"):
        for row in request.get(section) or []:
            if not isinstance(row, dict):
                continue
            pid = norm(row.get("id") or row.get("provider"))
            if not pid or pid in seen:
                continue
            seen.add(pid)
            rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--shard-count", type=int, default=1)
    ap.add_argument("--shard-index", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=8)
    ap.add_argument("--max-chunks", type=int, default=10)
    ap.add_argument("--max-runtime-chunks", type=int, default=10)
    ap.add_argument("--provider-timeout", type=int, default=150)
    args = ap.parse_args()

    request = load(args.request)
    if not isinstance(request, dict):
        raise SystemExit("bulk route discovery request must be an object")
    active = active_provider_ids()
    rows = [
        row for row in provider_rows(request)
        if norm(row.get("id") or row.get("provider")) not in active
    ]
    selected = [row for index, row in enumerate(rows) if index % args.shard_count == args.shard_index]
    transport = "residential-exit" if os.environ.get("NIAKVIO_BULK_ROUTE_DISCOVERY_RESIDENTIAL") == "1" else "github-hosted"
    results: list[dict[str, Any]] = []

    for row in selected:
        pid = norm(row.get("id") or row.get("provider"))
        direct = str(row.get("direct") or row.get("direct_url") or "").strip()
        fixtures = fixtures_for(row)
        retained_routes, retained_sources = retained_v3_routes(row)
        existing: list[str] = []
        for fixture in fixtures:
            for raw_route in [*(row.get("routes") or []), *retained_routes]:
                pattern = route_pattern(raw_route, fixture)
                if pattern and identity_route_candidate(pattern) and pattern not in existing:
                    existing.append(pattern)
        if existing:
            results.append({
                "provider": pid,
                "scope": str(row.get("scope") or "global"),
                "transport": "retained-v3-rag" if retained_sources else "request-existing",
                "probeAttempted": False,
                "probeReachedSite": False if retained_sources else True,
                "routePatterns": existing,
                "routeCount": len(existing),
                "qualified": True,
                "reason": "retained_identity_route_plan_host_matched" if retained_sources else "existing_identity_executable_route_plan",
                "retainedRouteSources": retained_sources,
                "liveProof": False if retained_sources else None,
            })
            continue
        if not re.match(r"^https?://[^/\s]+", direct):
            results.append({
                "provider": pid, "scope": str(row.get("scope") or "global"),
                "transport": transport, "probeAttempted": False, "probeReachedSite": False,
                "routePatterns": [], "routeCount": 0, "qualified": False,
                "reason": "direct_origin_missing",
            })
            continue

        reached = False
        patterns: list[str] = []
        return_codes: list[int] = []
        with tempfile.TemporaryDirectory(prefix=f"niakvio-route-{pid}-") as td:
            td_path = Path(td)
            for fixture_index, fixture in enumerate(fixtures):
                current = td_path / f"current-{fixture_index}.json"
                report_path = td_path / f"site-structure-{fixture_index}.json"
                current.write_text(json.dumps({
                    "id": pid,
                    "direct": direct,
                    "site": direct,
                    "fixture": fixture,
                }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                cmd = [
                    sys.executable, str(PROBE),
                    "--current", str(current),
                    "--output", str(report_path),
                    "--timeout", str(args.timeout),
                    "--max-chunks", str(args.max_chunks),
                    "--max-runtime-chunks", str(args.max_runtime_chunks),
                ]
                try:
                    proc = subprocess.run(
                        cmd, cwd=ROOT, text=True, capture_output=True,
                        timeout=max(30, args.provider_timeout), check=False,
                    )
                    return_codes.append(proc.returncode)
                    report = load(report_path) if report_path.is_file() else {}
                except subprocess.TimeoutExpired:
                    report = {}
                pages = [x for x in report.get("pages") or [] if isinstance(x, dict)]
                reached = reached or any(x.get("ok") is True and int(x.get("status") or 0) < 500 for x in pages)
                for raw in observed_candidates(report):
                    pattern = route_pattern(raw, fixture)
                    if pattern and identity_route_candidate(pattern) and pattern not in patterns:
                        patterns.append(pattern)
                    if len(patterns) >= 24:
                        break
                if len(patterns) >= 24:
                    break

        if not patterns:
            for fixture in fixtures:
                for route in probe_common_identity_routes(direct, fixture, timeout=args.timeout):
                    if route not in patterns and identity_route_candidate(route):
                        patterns.append(route)
                if len(patterns) >= 2:
                    break
        reason = (
            "observed_identity_executable_routes"
            if patterns
            else ("reachable_no_identity_route_observed" if reached else "network_or_site_unreached")
        )
        results.append({
            "provider": pid,
            "scope": str(row.get("scope") or "global"),
            "direct": direct,
            "transport": transport,
            "probeAttempted": True,
            "probeReachedSite": reached,
            "probeReturnCode": max(return_codes) if return_codes else None,
            "routePatterns": patterns,
            "routeCount": len(patterns),
            "qualified": bool(patterns),
            "reason": reason,
        })

    payload = {
        "schemaVersion": 1,
        "requestVersion": request.get("requestVersion"),
        "source": request.get("source"),
        "shardIndex": args.shard_index,
        "shardCount": args.shard_count,
        "transport": transport,
        "providerCount": len(selected),
        "qualifiedCount": sum(1 for row in results if row.get("qualified") is True),
        "providers": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"PROVIDER_BULK_ROUTE_DISCOVERY shard={args.shard_index}/{args.shard_count} "
        f"providers={len(selected)} qualified={payload['qualifiedCount']} transport={transport}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

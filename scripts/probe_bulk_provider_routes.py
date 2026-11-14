#!/usr/bin/env python3
"""Probe bulk-onboarding candidates for sanitized executable route DATA.

The probe is read-only. It never promotes a provider and never treats GitHub
network failure as provider failure. A caller may route traffic through the
repository's authorized residential exit; the report records that transport.
"""
from __future__ import annotations

import argparse
import html
import http.client
import json
import os
import re
import subprocess
import sys
import tempfile
import time
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
RESERVE_GLOB = "provider-intake-reserve-*.json"

sys.path.insert(0, str((ROOT / "scripts").resolve()))
from provider_base_store import provider_model_route_kind, provider_route_is_identity_aware
from provider_patch_blocks import decode_managed_data

SENSITIVE_KEYS = {"k","key","token","sig","signature","auth","authorization","expires","expiry","exp"}
SEARCH_KEYS = {"s","q","query","keyword","search","story","term","search_query","search_term","text","title"}
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


def _hardcoded_content_id_mismatch(path: str, fixture: dict[str, Any]) -> bool:
    """Reject detail/player paths pinned to another content identity.

    A query placeholder elsewhere in the URL must never make a fixed movie/TV
    identity reusable. This is the exact failure shape observed on Chillflix:
    /tv/291507?...s={query} was accepted while the requested TMDB id differed.
    """
    requested = str(fixture.get("tmdbId") or "").strip()
    if not requested:
        return False
    matches = re.findall(
        r"/(?:movie|movies|film|films|tv|series|show|watch|play|player|embed|title)/([0-9]{3,})(?:[/?#.-]|$)",
        str(path or ""),
        flags=re.I,
    )
    return any(value != requested for value in matches)


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
    if _hardcoded_content_id_mismatch(path, fixture):
        return ""
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


def _decode_owned_provider_model(text: str, config_id: str) -> dict[str, Any] | None:
    """Statically decode NiakVIO-owned Provider DATA without executing archived JS."""
    try:
        managed = decode_managed_data(text, config_id)
    except ValueError:
        managed = None
    if isinstance(managed, dict):
        return managed
    marker = "const NIAKVIO_PROVIDER_MODEL = Object.freeze("
    pos = text.find(marker)
    if pos < 0:
        return None
    raw = text[pos + len(marker):].lstrip()
    try:
        value, _end = json.JSONDecoder().raw_decode(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def retained_v3_routes(row: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Reuse statically decoded NiakVIO-owned route DATA on the same current host.

    Historical JS is never executed. Both managed Provider-v3 archives and older
    NiakVIO-owned ProviderBase DATA are read as JSON only. Relative routes are
    accepted only when the archived DATA binds the same canonical host as today's
    intake origin and the current identity-aware publication contract accepts them.
    """
    pid = norm(row.get("id") or row.get("provider"))
    current_host = _host_key(row.get("direct") or row.get("direct_url"))
    if not pid or not current_host:
        return [], []
    routes: list[str] = []
    sources: list[str] = []
    config_id = f"PROVIDER.{pid.upper()}.CONFIG.V1"
    archives = [
        *(ROOT / "provider-old" / "providers").glob(f"{pid}--nuvio--*.js"),
        *(ROOT / "provider-old").glob(f"{pid}--base--*.js"),
    ]
    for path in sorted(set(archives)):
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
            model = _decode_owned_provider_model(text, config_id)
        except (OSError, UnicodeError):
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
    title = _norm_text(fixture.get("title"))
    tmdb = str(fixture.get("tmdbId") or "").strip()
    lowered = text.casefold()

    if direct_media_route:
        media_markers = (".m3u8", ".mp4", '"stream"', '"streams"', '"url"', "playlist")
        if tmdb and tmdb in text and any(marker in lowered for marker in media_markers):
            return True
        return False

    # Search-route qualification must prove a catalogue/result identity, not merely
    # reflect the query in <title>, canonical URL, meta description, form value or
    # a generic "Search: <query>" heading.
    if tmdb:
        tmdb_patterns = (
            rf'data-(?:id|tmdb|tmdb-id)\s*=\s*["\']{re.escape(tmdb)}["\']',
            rf'href\s*=\s*["\'][^"\']*{re.escape(tmdb)}[^"\']*["\']',
        )
        if any(re.search(pattern, text, flags=re.I) for pattern in tmdb_patterns):
            return True

    if not title:
        return False

    anchor_re = re.compile(r"<a\b([^>]*)>([\s\S]{0,5000}?)</a\s*>", re.I)
    title_attr_re = re.compile(r"""\btitle\s*=\s*["']([^"']+)["']""", re.I)
    tag_re = re.compile(r"<[^>]+>")
    for match in anchor_re.finditer(text):
        attrs = match.group(1) or ""
        body_text = html.unescape(tag_re.sub(" ", match.group(2) or ""))
        labels = [body_text]
        title_attr = title_attr_re.search(attrs)
        if title_attr:
            labels.append(html.unescape(title_attr.group(1)))
        for label in labels:
            normalized = _norm_text(
                re.sub(r"\b(?:online\s+free|watch\s+online|stream\s+online)\b.*$", "", label, flags=re.I)
            )
            if normalized == title:
                return True
    return False


def probe_common_identity_routes(
    direct: str,
    fixture: dict[str, Any],
    *,
    timeout: int,
    deadline: float | None = None,
) -> list[str]:
    """Validate a tiny generic route vocabulary against a real content fixture.

    This is ordinary HTTP observation, not a WAF bypass. Challenges/timeouts
    simply yield no route and remain transport-inconclusive.
    """
    lane = str(fixture.get("mediaType") or "movie").casefold()
    search_routes = [
        "/?s={query}",
        "/?q={query}",
        "/?query={query}",
        "/?keyword={query}",
        "/search?q={query}",
        "/search?query={query}",
        "/search?keyword={query}",
        "/search/{slug}",
        "/find?q={query}",
        "/find?query={query}",
        "/browse?search={query}",
        "/recherche?q={query}",
        "/recherche?query={query}",
        "/recherche/{slug}",
        "/api/search?q={query}",
        "/api/search?query={query}",
        "/api/search?keyword={query}",
        "/api/v1/search?q={query}",
        "/api/v1/search?query={query}",
        "/index.php?do=search&subaction=search&story={query}",
    ]
    direct_routes = [
        f"/{lane}/{{tmdbId}}",
        f"/watch/{{tmdbId}}",
        f"/play/{{tmdbId}}",
        f"/embed/{{tmdbId}}",
        f"/embed/{lane}/{{tmdbId}}",
        f"/api/{lane}/{{tmdbId}}",
        f"/api/stream/{{tmdbId}}",
        f"/api/streams/{{tmdbId}}",
        f"/api/source/{{tmdbId}}",
        f"/api/sources/{{tmdbId}}",
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
        remaining = (deadline - time.monotonic()) if deadline is not None else None
        if remaining is not None and remaining <= 0.5:
            break
        rendered = _render_route(route, fixture)
        url = urllib.parse.urljoin(direct.rstrip("/") + "/", rendered.lstrip("/"))
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            request_timeout = max(0.5, min(float(timeout), 10.0))
            if remaining is not None:
                request_timeout = max(0.5, min(request_timeout, remaining))
            with urllib.request.urlopen(req, timeout=request_timeout) as response:
                status = int(getattr(response, "status", 200) or 200)
                if status >= 400:
                    continue
                body = response.read(1_500_000)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, http.client.InvalidURL):
            continue
        if _identity_response(body, fixture, direct_media_route=direct_media):
            accepted.append(route)
            # One real search and one direct-media contract are enough for this
            # bounded discovery pass.
            if len(accepted) >= 2:
                break
    return accepted



def _bounded_get(url: str, *, timeout: float, max_bytes: int = 2_500_000) -> tuple[int, bytes, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151 Safari/537.36",
        "Accept": "text/html,application/javascript,application/json;q=0.9,*/*;q=0.7",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=max(0.5, min(float(timeout), 10.0))) as response:
            status = int(getattr(response, "status", 200) or 200)
            final_url = str(getattr(response, "geturl", lambda: url)() or url)
            return status, response.read(max(1, int(max_bytes))), final_url
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(min(max(1, int(max_bytes)), 262_144))
        except Exception:
            body = b""
        return int(exc.code or 0), body, url
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return 0, b"", url


def _template_js_route(raw: Any, fixture: dict[str, Any]) -> str:
    """Convert a bounded first-party JS route literal into Provider-v3 DATA."""
    value = html.unescape(str(raw or "").strip()).replace("\\/", "/")
    if not value or len(value) > 700:
        return ""

    replacements = (
        (r"(?i)((?:tmdb(?:_?id)?|tmdb-id)=)\$\{[^}]+\}", r"\1{tmdbId}"),
        (r"(?i)((?:season)=)\$\{[^}]+\}", r"\1{season}"),
        (r"(?i)((?:episode|ep)=)\$\{[^}]+\}", r"\1{episode}"),
        (r"(?i)((?:media|media_type|mediatype|type)=)\$\{[^}]+\}", r"\1{media}"),
        (r"(?i)((?:q|query|keyword|search|story|term|title)=)\$\{[^}]+\}", r"\1{query}"),
    )
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value)

    value = re.sub(r"\$\{[^}]*tmdb[^}]*\}", "{tmdbId}", value, flags=re.I)
    value = re.sub(r"\$\{[^}]*season[^}]*\}", "{season}", value, flags=re.I)
    value = re.sub(r"\$\{[^}]*(?:episode|\bep\b)[^}]*\}", "{episode}", value, flags=re.I)
    value = re.sub(r"\$\{[^}]*(?:query|search|title)[^}]*\}", "{query}", value, flags=re.I)
    value = re.sub(r"\$\{[^}]*(?:media|type)[^}]*\}", "{media}", value, flags=re.I)

    value = re.sub(
        r"(?i)(/(?:movie|movies|film|films|tv|series|show|anime|embed)/(?:movie/|tv/|anime/)?)\$\{[^}]+\}",
        r"\1{tmdbId}",
        value,
    )
    value = re.sub(
        r"(?i)(/(?:tv|series|show|anime)/\{tmdbId\}/)\$\{[^}]+\}/\$\{[^}]+\}",
        r"\1{season}/{episode}",
        value,
    )
    value = re.sub(
        r"(?i)(/embed/(?:tv|anime)/\{tmdbId\}/)\$\{[^}]+\}/\$\{[^}]+\}",
        r"\1{season}/{episode}",
        value,
    )
    if "$" + "{" in value:
        return ""
    return route_pattern(value, fixture)


def _js_route_templates(text: str, fixture: dict[str, Any], *, origin_host: str) -> list[str]:
    """Extract identity-aware first-party routes from static SPA JS."""
    if not text:
        return []
    values: list[str] = []
    literal_re = re.compile(
        r'''(?:"([^"\r\n]{3,700})"|'([^'\r\n]{3,700})'|\x60([^\x60]{3,900})\x60)'''
    )
    interesting = re.compile(
        r"(?i)(?:/api/|/embed/|/source|/stream|/player|tmdb|imdb|season|episode|/movie/|/tv/|/anime/)"
    )
    for match in literal_re.finditer(text[:3_000_000]):
        raw = next((part for part in match.groups() if part is not None), "")
        if not interesting.search(raw):
            continue
        candidate = raw.replace("\\/", "/")
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            continue
        if parsed.scheme and parsed.netloc:
            host = _host_key(candidate)
            if not host or host != origin_host:
                continue
        pattern = _template_js_route(candidate, fixture)
        if not pattern or not _safe_spa_route_candidate(pattern) or not identity_route_candidate(pattern):
            continue
        if pattern not in values:
            values.append(pattern)
        if len(values) >= 32:
            break
    return values



def _safe_spa_route_candidate(value: Any) -> bool:
    raw = str(value or "").strip()
    if not raw or len(raw) > 420:
        return False
    if any(ord(ch) < 32 or ch.isspace() for ch in raw):
        return False
    if any(token in raw for token in ("<", ">", '"', "'", "\x60", "\\n", "\\r", "\\t")):
        return False
    if not (raw.startswith("/") or re.match(r"^https?://", raw, flags=re.I)):
        return False
    placeholders = set(re.findall(r"\{[^{}]+\}", raw))
    allowed = {"{tmdbId}", "{imdbId}", "{season}", "{episode}", "{media}", "{query}", "{slug}", "{title}"}
    if not placeholders.issubset(allowed):
        return False
    stripped = re.sub(r"\{[^{}]+\}", "X", raw)
    if not re.fullmatch(r"[A-Za-z0-9:/?&=._%+\-~,\[\]@!$()*;X]+", stripped):
        return False
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return False
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return False
    return True


def _identity_bound_api_response(body: bytes, route: str, fixture: dict[str, Any]) -> bool:
    if _identity_response(body, fixture, direct_media_route=True):
        return True
    if not body or "{tmdbId}" not in route:
        return False
    lane = str(fixture.get("mediaType") or "movie").casefold()
    if lane in {"tv", "anime"} and ("{season}" not in route or "{episode}" not in route):
        return False
    lowered = body[:1_500_000].decode("utf-8", errors="ignore").casefold()
    media_markers = (
        '"url"', '"src"', '"source"', '"sources"', '"stream"', '"streams"',
        ".m3u8", ".mp4", "/embed/", "playlist",
    )
    return any(marker in lowered for marker in media_markers)


def probe_spa_bundle_identity_routes(
    direct: str,
    fixture: dict[str, Any],
    *,
    timeout: int,
    deadline: float | None = None,
) -> list[str]:
    """Inspect static first-party SPA bundles, then verify discovered routes live."""
    remaining = (deadline - time.monotonic()) if deadline is not None else float(timeout)
    if remaining <= 0.5:
        return []
    status, body, final_url = _bounded_get(
        direct,
        timeout=min(float(timeout), remaining),
        max_bytes=700_000,
    )
    if status <= 0 or status >= 500 or not body:
        return []
    html_text = body.decode("utf-8", errors="ignore")
    origin_host = _host_key(final_url or direct)
    if not origin_host:
        return []

    srcs: list[str] = []
    for match in re.finditer(
        r'''<script\b[^>]*\bsrc\s*=\s*["']([^"']+)["'][^>]*>''',
        html_text,
        flags=re.I,
    ):
        src = html.unescape(match.group(1).strip())
        absolute = urllib.parse.urljoin(final_url or direct, src)
        if _host_key(absolute) != origin_host:
            continue
        if not re.search(r"\.m?js(?:[?#]|$)", absolute, flags=re.I):
            continue
        if absolute not in srcs:
            srcs.append(absolute)
        if len(srcs) >= 6:
            break

    candidates = _js_route_templates(html_text, fixture, origin_host=origin_host)
    for src in srcs:
        remaining = (deadline - time.monotonic()) if deadline is not None else float(timeout)
        if remaining <= 0.5:
            break
        js_status, js_body, _ = _bounded_get(
            src,
            timeout=min(float(timeout), remaining),
            max_bytes=3_000_000,
        )
        if js_status <= 0 or js_status >= 500 or not js_body:
            continue
        for pattern in _js_route_templates(
            js_body.decode("utf-8", errors="ignore"),
            fixture,
            origin_host=origin_host,
        ):
            if pattern not in candidates:
                candidates.append(pattern)
            if len(candidates) >= 48:
                break
        if len(candidates) >= 48:
            break

    accepted: list[str] = []
    headers = {
        "User-Agent": "NiakVIO/5 provider-route-discovery-spa",
        "Accept": "application/json,text/html;q=0.9,*/*;q=0.7",
        "Referer": final_url or direct,
    }
    for route in candidates:
        remaining = (deadline - time.monotonic()) if deadline is not None else float(timeout)
        if remaining <= 0.5:
            break
        rendered = _render_route(route, fixture)
        if not _safe_spa_route_candidate(rendered):
            continue
        url = rendered if re.match(r"^https?://", rendered) else urllib.parse.urljoin(
            (final_url or direct).rstrip("/") + "/", rendered.lstrip("/")
        )
        if _host_key(url) != origin_host:
            continue
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            request_timeout = max(0.5, min(float(timeout), 8.0, remaining))
            with urllib.request.urlopen(req, timeout=request_timeout) as response:
                response_status = int(getattr(response, "status", 200) or 200)
                if response_status >= 400:
                    continue
                response_body = response.read(1_500_000)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            continue
        if _identity_bound_api_response(response_body, route, fixture):
            if route not in accepted:
                accepted.append(route)
        if len(accepted) >= 4:
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

    def add(values: Any) -> None:
        for row in values or []:
            if not isinstance(row, dict):
                continue
            pid = norm(row.get("id") or row.get("provider"))
            if not pid or pid in seen:
                continue
            seen.add(pid)
            rows.append(dict(row))

    for section in ("providers", "deferredProviders"):
        add(request.get(section))
    for path in sorted((ROOT / "automation").glob(RESERVE_GLOB)):
        try:
            reserve = load(path)
        except Exception:
            continue
        if isinstance(reserve, dict):
            add(reserve.get("providers"))
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
        provider_deadline = time.monotonic() + max(10.0, float(args.provider_timeout))
        with tempfile.TemporaryDirectory(prefix=f"niakvio-route-{pid}-") as td:
            td_path = Path(td)
            for fixture_index, fixture in enumerate(fixtures):
                remaining = provider_deadline - time.monotonic()
                if remaining <= 0.5:
                    break
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
                        timeout=max(0.5, remaining), check=False,
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
                if provider_deadline - time.monotonic() <= 0.5:
                    break
                for route in probe_spa_bundle_identity_routes(
                    direct,
                    fixture,
                    timeout=args.timeout,
                    deadline=provider_deadline,
                ):
                    if route not in patterns and identity_route_candidate(route):
                        patterns.append(route)
                if len(patterns) >= 4:
                    break
        if not patterns:
            for fixture in fixtures:
                if provider_deadline - time.monotonic() <= 0.5:
                    break
                for route in probe_common_identity_routes(
                    direct,
                    fixture,
                    timeout=args.timeout,
                    deadline=provider_deadline,
                ):
                    if route not in patterns and identity_route_candidate(route):
                        patterns.append(route)
                if len(patterns) >= 2:
                    break
        budget_exhausted = provider_deadline - time.monotonic() <= 0.5
        reason = (
            "observed_identity_executable_routes"
            if patterns
            else (
                "provider_probe_budget_exhausted"
                if budget_exhausted
                else ("reachable_no_identity_route_observed" if reached else "network_or_site_unreached")
            )
        )
        results.append({
            "provider": pid,
            "scope": str(row.get("scope") or "global"),
            "direct": direct,
            "transport": transport,
            "probeAttempted": True,
            "probeReachedSite": reached,
            "probeReturnCode": max(return_codes) if return_codes else None,
            "probeBudgetExhausted": budget_exhausted,
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

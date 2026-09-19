#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRENT = ROOT / ".provider-onboarding" / "current.json"
DEFAULT_OUTPUT = ROOT / ".provider-onboarding" / "routes" / "provider-site-structure.json"

UA = "Mozilla/5.0 NiakVIO/2"
ROUTE_HINT = re.compile(
    r"""(?P<q>["'])(?P<route>/(?:api|search|watch|movie|movies|film|films|series|tv|show|title|media|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|manifest|action)[^"'\\\s<>]{0,220})(?P=q)""",
    re.I,
)
ATTR_URL = re.compile(r"""(?:href|src)\s*=\s*["']([^"'<>\s]+)["']""", re.I)
ABS_URL = re.compile(r"""https?://[^"'<>\s\\]+""", re.I)
PLAYER_PATH = re.compile(r"/(?:watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy)(?:/|$)", re.I)
DIRECT_MEDIA = re.compile(r"\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|/(?:hls|dash|stream)(?:/|[?#]|$)", re.I)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_text(url: str, timeout: int = 10, referer: str = "") -> tuple[int, str, str, str]:
    headers = {"User-Agent": UA, "Accept": "text/html,application/javascript,text/plain,*/*"}
    if referer:
        headers["Referer"] = referer
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as response:
        status = int(getattr(response, "status", 200))
        final = str(response.geturl())
        ctype = str(response.headers.get("content-type") or "")
        raw = response.read(2_000_000)
    return status, final, ctype, raw.decode("utf-8", errors="replace")


def same_origin(url: str, origin: str) -> bool:
    try:
        return f"{urlsplit(url).scheme}://{urlsplit(url).netloc}".rstrip("/") == origin.rstrip("/")
    except ValueError:
        return False


def clean_route(value: str) -> str:
    value = html.unescape(value).replace("\\/", "/").replace("\\u002f", "/").replace("\\u003a", ":")
    return value[:260]


def slugify(value: str) -> str:
    value = html.unescape(str(value or "")).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def sanitized_url_pattern(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    keys = sorted({part.split("=", 1)[0] for part in parsed.query.split("&") if part})
    return (parsed.path or "/") + (("?" + "&".join(keys)) if keys else "")


def direct_media_hosts(text: str) -> list[str]:
    normalized = html.unescape(text).replace("\\/", "/").replace("\\u002f", "/").replace("\\u003a", ":")
    out: list[str] = []
    seen: set[str] = set()
    for raw in ABS_URL.findall(normalized):
        value = clean_route(raw)
        if not DIRECT_MEDIA.search(value):
            continue
        try:
            host = (urlsplit(value).hostname or "").casefold()
        except ValueError:
            continue
        if host and host not in seen:
            seen.add(host)
            out.append(host)
        if len(out) >= 12:
            break
    return out


def useful_absolute_urls(text: str) -> list[str]:
    normalized = html.unescape(text).replace("\\/", "/").replace("\\u002f", "/").replace("\\u003a", ":")
    out: list[str] = []
    seen: set[str] = set()
    for raw in ABS_URL.findall(normalized):
        value = clean_route(raw)
        try:
            parsed = urlsplit(value)
        except ValueError:
            continue
        host = (parsed.hostname or "").casefold()
        path_query = (parsed.path + "?" + parsed.query).casefold()
        if not host or host in {"image.tmdb.org", "nextjs.org", "www.nextjs.org"}:
            continue
        if "/_next/static/" in parsed.path:
            continue
        if not any(token in path_query for token in (
            "api", "search", "stream", "source", "server", "embed", "player",
            "watch", "video", "resolve", "proxy", "manifest", "action",
        )):
            continue
        if value not in seen:
            seen.add(value)
            out.append(value)
        if len(out) >= 40:
            break
    return out


def discover_routes(text: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    normalized = html.unescape(text).replace("\\/", "/").replace("\\u002f", "/").replace("\\u003a", ":")
    for match in ROUTE_HINT.finditer(normalized):
        value = clean_route(match.group("route") or "")
        if value and value not in seen:
            seen.add(value)
            out.append(value)
            if len(out) >= 120:
                return out
    return out


def sanitized_route_contexts(text: str, routes: list[str]) -> list[dict[str, str]]:
    normalized = html.unescape(text).replace("\\/", "/").replace("\\u002f", "/").replace("\\u003a", ":")
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_route in routes:
        route = clean_route(raw_route)
        if not route or route in seen:
            continue
        if not re.search(r"^/(?:api|player|stream|source|resolve|proxy)", route, re.I):
            continue
        pos = normalized.find(route)
        if pos < 0:
            continue
        seen.add(route)
        snippet = normalized[max(0, pos - 700): pos + len(route) + 1200]
        snippet = re.sub(
            r"(?i)([?&](?:k|key|token|sig|signature|auth|expires|expiry|exp)=)[^&\"'\\s]+",
            r"\\1<redacted>",
            snippet,
        )
        snippet = re.sub(
            r"(?i)(?:bearer\\s+)?[A-Za-z0-9_-]{48,}(?:\\.[A-Za-z0-9_-]{16,}){0,2}",
            "<redacted>",
            snippet,
        )
        snippet = re.sub(r"\\s+", " ", snippet).strip()
        out.append({
            "route": sanitized_url_pattern(route),
            "context": snippet[:1900],
        })
        if len(out) >= 12:
            break
    return out


RUNTIME_API_LITERAL = re.compile(
    r"""(?P<q>["'`])(?P<route>/api/(?:streams?|source|sources|resolve|proxy)[^"'\\`\\s<>]{0,300})(?P=q)""",
    re.I,
)


def runtime_api_patterns(text: str, media_type: str) -> list[str]:
    normalized = html.unescape(text).replace("\\/", "/").replace("\\u002f", "/").replace("\\u003a", ":")
    out: list[str] = []
    seen: set[str] = set()
    for match in RUNTIME_API_LITERAL.finditer(normalized):
        raw = clean_route(match.group("route") or "")
        try:
            parsed = urlsplit(raw)
        except ValueError:
            continue
        path = parsed.path
        if re.search(r"/(?:working|dead|warm)$", path, re.I):
            continue
        media = (media_type or "").casefold()
        if media and re.search(rf"/{re.escape(media)}$", path, re.I):
            path = path[: -(len(media))] + "{media}"
        keys = sorted({
            part.split("=", 1)[0]
            for part in parsed.query.split("&")
            if part and part.split("=", 1)[0]
        })
        pattern = path + (("?" + "&".join(keys)) if keys else "")
        if pattern not in seen:
            seen.add(pattern)
            out.append(pattern)
        if len(out) >= 20:
            break
    return out


def instantiate_runtime_api(pattern: str, runtime_url: str, media_type: str, season: Any, episode: Any) -> str:
    try:
        parsed = urlsplit(pattern)
        runtime = urlsplit(runtime_url)
    except ValueError:
        return ""
    path = parsed.path.replace("{media}", media_type or "movie")
    runtime_params = parse_qs(runtime.query, keep_blank_values=True)
    values: dict[str, str] = {}
    for part in parsed.query.split("&"):
        key = part.split("=", 1)[0].strip()
        if not key:
            continue
        if key in runtime_params and runtime_params[key]:
            values[key] = runtime_params[key][0]
        elif key.casefold() in {"media", "m", "type"}:
            values[key] = media_type or "movie"
        elif key.casefold() in {"season", "s"} and season is not None:
            values[key] = str(season)
        elif key.casefold() in {"episode", "e"} and episode is not None:
            values[key] = str(episode)
        else:
            return ""
    return urljoin(runtime_url, path + (("?" + urlencode(values)) if values else ""))


def json_source_patterns(text: str, base: str) -> tuple[int, list[str], list[str]]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return 0, [], []
    urls: list[str] = []
    types: list[str] = []

    def walk(node: Any, key: str = "") -> None:
        if isinstance(node, dict):
            for child_key, child in node.items():
                if child_key.casefold() in {"type", "format"} and isinstance(child, str):
                    token = child.strip().casefold()
                    if token and token not in types:
                        types.append(token[:40])
                walk(child, child_key)
        elif isinstance(node, list):
            for child in node:
                walk(child, key)
        elif isinstance(node, str) and key.casefold() in {"src", "url", "file", "stream", "source"}:
            absolute = urljoin(base, node)
            pattern = sanitized_url_pattern(absolute)
            host = urlsplit(absolute).hostname or ""
            label = pattern + ("@" + host if host else "")
            if label not in urls:
                urls.append(label)

    walk(value)
    return len(urls), urls[:20], types[:12]



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--max-chunks", type=int, default=12)
    ap.add_argument("--max-runtime-chunks", type=int, default=18)
    args = ap.parse_args()

    current = load_json(args.current)
    site = str(current.get("direct") or current.get("site") or "").strip()
    fixture = current.get("fixture") if isinstance(current.get("fixture"), dict) else {}
    title = str(fixture.get("title") or "").strip()
    tmdb_id = str(fixture.get("tmdbId") or fixture.get("tmdb_id") or "").strip()
    media_type = str(fixture.get("mediaType") or fixture.get("media_type") or "movie").strip().lower()
    if not site:
        raise SystemExit("provider site probe: no direct/site URL")

    parsed = urlsplit(site)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    pages = [site]
    if title:
        pages.extend([
            urljoin(site, "/?s=" + quote(title)),
            urljoin(site, "/search?q=" + quote(title)),
        ])
    if tmdb_id:
        kind = "movie" if media_type == "movie" else "tv"
        slug = slugify(title)
        if slug:
            pages.append(urljoin(site, f"/title/{kind}/{quote(tmdb_id)}-{quote(slug)}"))
        pages.append(urljoin(site, f"/title/{kind}/{quote(tmdb_id)}"))
    pages = list(dict.fromkeys(pages))

    report: dict[str, Any] = {
        "schema_version": 2,
        "provider_id": current.get("id"),
        "site": site,
        "origin": origin,
        "pages": [],
        "next_chunks": [],
        "route_hints": [],
        "runtime_routes": [],
    }
    route_seen: set[str] = set()
    chunk_priority: dict[str, int] = {}
    runtime_candidates: dict[str, str] = {}

    for page in pages:
        try:
            status, final, ctype, text = fetch_text(page, args.timeout)
        except Exception as exc:
            report["pages"].append({"url": page, "ok": False, "error": type(exc).__name__})
            continue
        attrs = [urljoin(final, clean_route(v)) for v in ATTR_URL.findall(text)]
        same = [u for u in attrs if same_origin(u, origin)]
        page_is_detail = "/title/" in urlsplit(final).path
        if page_is_detail:
            for candidate in same:
                try:
                    candidate_path = urlsplit(candidate).path
                except ValueError:
                    continue
                if PLAYER_PATH.search(candidate_path):
                    runtime_candidates.setdefault(candidate, final)
        for u in same:
            if "/_next/static/" in u:
                priority = (100 if page_is_detail else 10) + (20 if u.lower().endswith(".js") else 0)
                chunk_priority[u] = max(priority, chunk_priority.get(u, 0))
        hints = discover_routes(text)
        useful_abs = useful_absolute_urls(text)
        for value in hints:
            if value not in route_seen:
                route_seen.add(value)
                report["route_hints"].append({"source": "html", "value": value})
        report["pages"].append({
            "url": page,
            "ok": True,
            "status": status,
            "final_url": final,
            "content_type": ctype,
            "bytes_scanned": min(len(text.encode("utf-8", errors="ignore")), 2_000_000),
            "same_origin_links": sorted(set(same))[:80],
            "useful_absolute_urls": useful_abs,
            "next_chunk_count": len([u for u in same if "/_next/static/" in u]),
        })

    for runtime_url, referer in list(runtime_candidates.items())[:4]:
        pattern = sanitized_url_pattern(runtime_url)
        try:
            status, final, ctype, text = fetch_text(runtime_url, args.timeout, referer=referer)
            runtime_same = [
                urljoin(final, clean_route(value))
                for value in ATTR_URL.findall(text)
            ]
            runtime_chunks = [
                value for value in runtime_same
                if same_origin(value, origin)
                and "/_next/static/" in urlsplit(value).path
                and value.lower().split("?", 1)[0].endswith(".js")
            ]
            runtime_chunk_rows: list[dict[str, Any]] = []
            runtime_route_hints: list[str] = []
            runtime_api_routes: list[str] = []
            runtime_direct_hosts: list[str] = direct_media_hosts(text)
            for chunk in list(dict.fromkeys(runtime_chunks))[: min(max(0, args.max_runtime_chunks), 24)]:
                chunk_pattern = sanitized_url_pattern(chunk)
                try:
                    chunk_status, chunk_final, chunk_ctype, chunk_text = fetch_text(
                        chunk,
                        args.timeout,
                        referer=final,
                    )
                    chunk_hints = discover_routes(chunk_text)[:80]
                    chunk_api_routes = runtime_api_patterns(chunk_text, media_type)
                    chunk_direct_hosts = direct_media_hosts(chunk_text)
                    for value in chunk_api_routes:
                        if value not in runtime_api_routes:
                            runtime_api_routes.append(value)
                    for value in chunk_hints:
                        if value not in runtime_route_hints:
                            runtime_route_hints.append(value)
                    for value in chunk_direct_hosts:
                        if value not in runtime_direct_hosts:
                            runtime_direct_hosts.append(value)
                    runtime_chunk_rows.append({
                        "url_pattern": chunk_pattern,
                        "ok": True,
                        "status": chunk_status,
                        "final_path": urlsplit(chunk_final).path or "/",
                        "content_type": chunk_ctype,
                        "bytes_scanned": min(len(chunk_text.encode("utf-8", errors="ignore")), 2_000_000),
                        "route_hints": chunk_hints,
                        "runtime_api_patterns": chunk_api_routes,
                        "route_contexts": sanitized_route_contexts(chunk_text, chunk_hints),
                        "useful_absolute_urls": [
                            sanitized_url_pattern(value) + "@" + (urlsplit(value).hostname or "")
                            for value in useful_absolute_urls(chunk_text)[:40]
                        ],
                        "direct_media_hosts": chunk_direct_hosts,
                    })
                except Exception as exc:
                    runtime_chunk_rows.append({
                        "url_pattern": chunk_pattern,
                        "ok": False,
                        "error": type(exc).__name__,
                    })
            runtime_api_probes: list[dict[str, Any]] = []
            for api_pattern in runtime_api_routes[:6]:
                api_url = instantiate_runtime_api(
                    api_pattern,
                    runtime_url,
                    media_type,
                    fixture.get("season"),
                    fixture.get("episode"),
                )
                if not api_url:
                    continue
                try:
                    api_status, api_final, api_ctype, api_text = fetch_text(
                        api_url,
                        args.timeout,
                        referer=final,
                    )
                    source_count, source_patterns, source_types = json_source_patterns(
                        api_text,
                        api_final or api_url,
                    )
                    runtime_api_probes.append({
                        "pattern": api_pattern,
                        "ok": True,
                        "status": api_status,
                        "content_type": api_ctype,
                        "source_count": source_count,
                        "source_patterns": source_patterns,
                        "source_types": source_types,
                    })
                except Exception as exc:
                    runtime_api_probes.append({
                        "pattern": api_pattern,
                        "ok": False,
                        "error": type(exc).__name__,
                    })

            report["runtime_routes"].append({
                "url_pattern": pattern,
                "referer_path": urlsplit(referer).path or "/",
                "ok": True,
                "status": status,
                "final_path": urlsplit(final).path or "/",
                "content_type": ctype,
                "bytes_scanned": min(len(text.encode("utf-8", errors="ignore")), 2_000_000),
                "route_hints": discover_routes(text)[:80],
                "useful_absolute_urls": [
                    sanitized_url_pattern(value) + "@" + (urlsplit(value).hostname or "")
                    for value in useful_absolute_urls(text)[:40]
                ],
                "direct_media_hosts": direct_media_hosts(text),
                "next_chunk_count": len(runtime_chunks),
                "runtime_chunk_route_hints": runtime_route_hints[:120],
                "runtime_api_patterns": runtime_api_routes[:20],
                "runtime_api_probes": runtime_api_probes,
                "runtime_direct_media_hosts": runtime_direct_hosts[:24],
                "runtime_chunks": runtime_chunk_rows,
            })
        except Exception as exc:
            report["runtime_routes"].append({
                "url_pattern": pattern,
                "referer_path": urlsplit(referer).path or "/",
                "ok": False,
                "error": type(exc).__name__,
            })

    ordered_chunks = sorted(
        chunk_priority,
        key=lambda value: (chunk_priority[value], value.lower().endswith(".js")),
        reverse=True,
    )
    for chunk in ordered_chunks[: max(0, args.max_chunks)]:
        try:
            status, final, ctype, text = fetch_text(chunk, args.timeout)
        except Exception as exc:
            report["next_chunks"].append({"url": chunk, "ok": False, "error": type(exc).__name__})
            continue
        hints = discover_routes(text)
        useful_abs = useful_absolute_urls(text)
        for value in hints:
            if value not in route_seen:
                route_seen.add(value)
                report["route_hints"].append({"source": "next_chunk", "value": value})
        report["next_chunks"].append({
            "url": chunk,
            "ok": True,
            "status": status,
            "final_url": final,
            "content_type": ctype,
            "bytes_scanned": min(len(text.encode("utf-8", errors="ignore")), 2_000_000),
            "route_hints": hints[:80],
            "useful_absolute_urls": useful_abs,
            "priority": chunk_priority.get(chunk, 0),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_SITE_STRUCTURE "
        f"id={current.get('id')} pages={len(report['pages'])} "
        f"chunks={len(report['next_chunks'])} hints={len(report['route_hints'])} runtime_routes={len(report['runtime_routes'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

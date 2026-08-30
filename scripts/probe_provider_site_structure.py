#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRENT = ROOT / ".provider-onboarding" / "current.json"
DEFAULT_OUTPUT = ROOT / ".provider-onboarding" / "routes" / "provider-site-structure.json"

UA = "Mozilla/5.0 NiakVIO/2"
ROUTE_HINT = re.compile(
    r"""(?P<q>["'])(?P<route>/(?:api|search|watch|movie|movies|film|films|series|tv|show|title|media|embed|player)[^"'\\\s<>]{0,220})(?P=q)""",
    re.I,
)
TMDB_HINT = re.compile(r"""(?P<q>["'])(?P<value>[^"'\\\s<>]{0,100}tmdb[^"'\\\s<>]{0,140})(?P=q)""", re.I)
ATTR_URL = re.compile(r"""(?:href|src)\s*=\s*["']([^"'<>\s]+)["']""", re.I)
ABS_URL = re.compile(r"""https?://[^"'<>\s\\]+""", re.I)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_text(url: str, timeout: int = 10) -> tuple[int, str, str, str]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/javascript,text/plain,*/*"})
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


def discover_routes(text: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    normalized = html.unescape(text).replace("\\/", "/").replace("\\u002f", "/").replace("\\u003a", ":")
    for pattern in (ROUTE_HINT, TMDB_HINT):
        for match in pattern.finditer(normalized):
            value = clean_route(match.groupdict().get("route") or match.groupdict().get("value") or "")
            if value and value not in seen:
                seen.add(value)
                out.append(value)
                if len(out) >= 120:
                    return out
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--max-chunks", type=int, default=12)
    args = ap.parse_args()

    current = load_json(args.current)
    site = str(current.get("direct") or current.get("site") or "").strip()
    title = str((current.get("fixture") or {}).get("title") or "").strip()
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

    report: dict[str, Any] = {
        "schema_version": 1,
        "provider_id": current.get("id"),
        "site": site,
        "origin": origin,
        "pages": [],
        "next_chunks": [],
        "route_hints": [],
    }
    route_seen: set[str] = set()
    chunk_urls: list[str] = []
    chunk_seen: set[str] = set()

    for page in pages:
        try:
            status, final, ctype, text = fetch_text(page, args.timeout)
        except Exception as exc:
            report["pages"].append({"url": page, "ok": False, "error": type(exc).__name__})
            continue
        attrs = [urljoin(final, clean_route(v)) for v in ATTR_URL.findall(text)]
        same = [u for u in attrs if same_origin(u, origin)]
        for u in same:
            if "/_next/static/" in u and u not in chunk_seen:
                chunk_seen.add(u)
                chunk_urls.append(u)
        hints = discover_routes(text)
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
            "next_chunk_count": len([u for u in same if "/_next/static/" in u]),
        })

    for chunk in chunk_urls[: max(0, args.max_chunks)]:
        try:
            status, final, ctype, text = fetch_text(chunk, args.timeout)
        except Exception as exc:
            report["next_chunks"].append({"url": chunk, "ok": False, "error": type(exc).__name__})
            continue
        hints = discover_routes(text)
        absolute = [clean_route(v) for v in ABS_URL.findall(text)]
        useful_abs = sorted({
            u for u in absolute
            if any(token in u.lower() for token in ("api", "search", "stream", "embed", "player", "tmdb"))
        })[:40]
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
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_SITE_STRUCTURE "
        f"id={current.get('id')} pages={len(report['pages'])} "
        f"chunks={len(report['next_chunks'])} hints={len(report['route_hints'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

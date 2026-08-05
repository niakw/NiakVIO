#!/usr/bin/env python3
from __future__ import annotations

import http.cookiejar
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "automation" / "targeted-provider-routes.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/148 Safari/537.36"
MEDIA_HINT = re.compile(r"https?://[^\s\"'<>]+(?:m3u8|mp4|mpd|embed|player|stream|watch)[^\s\"'<>]*", re.I)
URL_ATTR = re.compile(r"(?:href|src|data-src|data-url|data-embed|data-player)=[\"']([^\"']+)[\"']", re.I)
SCRIPT_ATTR = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.I)
API_HINT = re.compile(r"(?:https?://[^\s\"'<>]+|/[A-Za-z0-9_?&=./{}:$-]+)", re.I)

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def fetch(url: str, *, referer: str | None = None, timeout: int = 15) -> dict[str, Any]:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
        "Cache-Control": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(2_000_000)
            content_type = response.headers.get("content-type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            text = raw.decode(charset, errors="replace")
            final_url = response.geturl()
            return {
                "requested_url": url,
                "final_url": final_url,
                "status": response.status,
                "content_type": content_type,
                "length": len(raw),
                "text": text,
                "set_cookie": bool(response.headers.get("set-cookie")),
            }
    except Exception as error:
        return {
            "requested_url": url,
            "final_url": None,
            "status": None,
            "content_type": None,
            "length": 0,
            "text": "",
            "error": f"{type(error).__name__}: {error}",
        }


def absolute_links(text: str, base: str, pattern: re.Pattern[str] = URL_ATTR) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        value = urllib.parse.urljoin(base, match.group(1).replace("&amp;", "&"))
        if value.startswith(("http://", "https://")) and value not in seen:
            seen.add(value)
            values.append(value)
    return values


def summary(response: dict[str, Any]) -> dict[str, Any]:
    text = response.get("text") or ""
    final_url = response.get("final_url") or response.get("requested_url") or ""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    links = absolute_links(text, final_url)
    scripts = absolute_links(text, final_url, SCRIPT_ATTR)
    return {
        key: response.get(key)
        for key in ("requested_url", "final_url", "status", "content_type", "length", "set_cookie", "error")
        if response.get(key) is not None
    } | {
        "title": re.sub(r"\s+", " ", title_match.group(1)).strip()[:200] if title_match else None,
        "interstellar_links": [url for url in links if "interstellar" in url.casefold()][:20],
        "player_links": [url for url in links if re.search(r"(?:embed|player|watch|stream|video|/e/|/v/)", url, re.I)][:30],
        "media_hints": list(dict.fromkeys(MEDIA_HINT.findall(text)))[:30],
        "scripts": scripts[:30],
        "markers": {
            "contains_interstellar": "interstellar" in text.casefold(),
            "contains_iframe": "<iframe" in text.casefold(),
            "contains_m3u8": ".m3u8" in text.casefold(),
            "contains_cloudflare": any(token in text.casefold() for token in ("cf-chl", "cloudflare", "challenge-platform")),
            "contains_next_data": "__next_data__" in text.casefold(),
        },
    }


def probe_many(urls: list[str], *, referer: str | None = None) -> list[dict[str, Any]]:
    return [summary(fetch(url, referer=referer)) for url in urls]


def inspect_scripts(script_urls: list[str], *, referer: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for url in script_urls[:10]:
        response = fetch(url, referer=referer)
        text = response.get("text") or ""
        hints: list[str] = []
        for value in API_HINT.findall(text):
            low = value.casefold()
            if any(token in low for token in ("api", "search", "movie", "series", "stream", "player", "embed", "tmdb", "graphql")):
                hints.append(value[:500])
        reports.append(summary(response) | {"route_hints": list(dict.fromkeys(hints))[:80]})
    return reports


def worker_probe(provider_id: str) -> dict[str, Any]:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    row = next(item for item in manifest.get("scrapers", []) if str(item.get("id") or "").casefold() == provider_id)
    provider_path = ROOT / str(row["filename"])
    media = {
        "tmdbId": "157336",
        "mediaType": "movie",
        "title": "Interstellar",
        "year": 2014,
        "label": "Interstellar (2014)",
        "category": "movie",
    }
    context = {
        "locale": "fr-FR",
        "language": "fr",
        "languages": ["fr-FR", "fr"],
        "platform": "android",
        "settings": {},
        "storage": {},
    }
    try:
        process = subprocess.run(
            ["node", "scripts/provider_worker.cjs", str(provider_path), json.dumps(media), json.dumps(context), "2"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=90,
            env={"NUVIO_NETWORK_MAX_REQUESTS": "100"},
        )
        stdout = process.stdout[-200_000:]
        stderr = process.stderr[-50_000:]
        parsed: Any = None
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
                break
            except json.JSONDecodeError:
                pass
        return {
            "returncode": process.returncode,
            "parsed_type": type(parsed).__name__ if parsed is not None else None,
            "stream_count": len(parsed) if isinstance(parsed, list) else None,
            "stdout_tail": stdout[-4000:],
            "stderr_tail": stderr[-4000:],
        }
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"}


def main() -> int:
    streamzo_root = fetch("https://streamzo.fr/")
    streamzo_summary = summary(streamzo_root)
    streamzo_urls = [
        "https://streamzo.fr/interstellar",
        "https://streamzo.fr/interstellar-2014",
        "https://streamzo.fr/?s=Interstellar",
        "https://streamzo.fr/search?q=Interstellar",
    ]

    hub = fetch("https://www.fstream.org/")
    hub_summary = summary(hub)
    outbound = [
        url for url in absolute_links(hub.get("text") or "", hub.get("final_url") or "https://www.fstream.org/")
        if urllib.parse.urlsplit(url).hostname not in {"fstream.org", "www.fstream.org"}
        and re.search(r"(?:^|\.)fs\d+\.", urllib.parse.urlsplit(url).hostname or "", re.I)
    ]
    french_base = (outbound[0].rstrip("/") if outbound else "https://fs13.lol")
    french_urls = [
        french_base + "/",
        french_base + "/index.php?do=search&subaction=search&story=Interstellar",
        french_base + "/?do=search&subaction=search&story=Interstellar",
        french_base + "/?s=Interstellar",
    ]

    movix_root = fetch("https://movix.fun/")
    movix_summary = summary(movix_root)
    movix_scripts = absolute_links(
        movix_root.get("text") or "",
        movix_root.get("final_url") or "https://movix.fun/",
        SCRIPT_ATTR,
    )

    report = {
        "fixture": "Interstellar (2014) / TMDB 157336",
        "streamzo": {
            "root": streamzo_summary,
            "routes": probe_many(streamzo_urls, referer="https://streamzo.fr/"),
            "scripts": inspect_scripts(streamzo_summary.get("scripts") or [], referer="https://streamzo.fr/"),
            "worker": worker_probe("streamzo"),
        },
        "frenchstream": {
            "hub": hub_summary,
            "resolved_base": french_base,
            "routes": probe_many(french_urls, referer="https://www.fstream.org/"),
            "worker": worker_probe("frenchstream"),
        },
        "movix": {
            "root": movix_summary,
            "scripts": inspect_scripts(movix_scripts, referer="https://movix.fun/"),
            "api_roots": probe_many(
                [
                    "https://api.movix.fun/",
                    "https://api.movix.fun/api",
                    "https://api.movix.fun/openapi.json",
                    "https://api.movix.fun/graphql",
                ],
                referer="https://movix.fun/",
            ),
            "worker": worker_probe("movix"),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "streamzo_base": streamzo_summary.get("final_url"),
        "frenchstream_base": french_base,
        "movix_base": movix_summary.get("final_url"),
        "output": str(OUTPUT),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

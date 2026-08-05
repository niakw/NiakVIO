#!/usr/bin/env python3
from __future__ import annotations

import html
import http.cookiejar
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "automation" / "nuvio-tv-target-diagnostics-v2.json"
UA = "Mozilla/5.0 (Linux; Android 14; Android TV) AppleWebKit/537.36 Chrome/131 Safari/537.36 NuvioTV"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def fetch(url: str, *, referer: str | None = None, method: str = "GET", data: bytes | None = None) -> dict[str, Any]:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/json,text/plain,video/*,*/*",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
        "Cache-Control": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
        try:
            headers["Origin"] = urllib.parse.urlsplit(referer)._replace(path="", query="", fragment="").geturl().rstrip("/")
        except Exception:
            pass
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    request = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        with opener.open(request, timeout=22) as response:
            raw = response.read(2_500_000)
            charset = response.headers.get_content_charset() or "utf-8"
            return {
                "requested_url": url,
                "final_url": response.geturl(),
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "length": len(raw),
                "text": raw.decode(charset, errors="replace"),
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


def absolute(value: str, base: str) -> str:
    try:
        return urllib.parse.urljoin(base, html.unescape(value).replace("\\/", "/"))
    except Exception:
        return ""


def candidates(text: str, base: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        url = absolute(value, base)
        if not url.startswith(("http://", "https://")) or url in seen:
            return
        low = url.casefold()
        if re.search(r"\.(?:css|js|mjs|map|woff2?|ttf|png|jpe?g|gif|svg|ico)(?:[?#]|$)", low):
            return
        if not re.search(r"(?:m3u8|mp4|mpd|embed|player|watch|stream|video|/e/|/v/)", low):
            return
        seen.add(url)
        out.append(url)

    patterns = [
        r"(?:src|href|data-src|data-url|data-embed|data-player|data-link|data-file)=[\"']([^\"']+)[\"']",
        r"(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*[\"']([^\"']+)[\"']",
        r"(https?://[^\"'<>\s\\]+(?:m3u8|mp4|mpd|embed|player|watch|stream|/e/|/v/)[^\"'<>\s\\]*)",
    ]
    normalized = html.unescape(text).replace("\\/", "/")
    for pattern in patterns:
        for match in re.finditer(pattern, normalized, re.I):
            add(match.group(1))
    return out[:40]


def title(text: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()[:240] if match else None


def compact(response: dict[str, Any]) -> dict[str, Any]:
    text = response.get("text") or ""
    base = response.get("final_url") or response.get("requested_url") or ""
    return {
        key: response.get(key)
        for key in ("requested_url", "final_url", "status", "content_type", "length", "error")
        if response.get(key) not in (None, "")
    } | {
        "title": title(text),
        "starts_extm3u": text.lstrip("\ufeff \r\n\t").startswith("#EXTM3U"),
        "candidates": candidates(text, base),
        "markers": {
            "packed": "eval(function(p,a,c,k,e" in text,
            "iframe": "<iframe" in text.casefold(),
            "m3u8": ".m3u8" in text.casefold(),
            "cloudflare": any(token in text.casefold() for token in ("cf-chl", "challenge-platform", "just a moment")),
        },
        "preview": re.sub(r"\s+", " ", text[:1500]).strip(),
    }


def follow_candidates(response: dict[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    base = response.get("final_url") or response.get("requested_url") or ""
    return [compact(fetch(url, referer=base)) for url in candidates(response.get("text") or "", base)[:limit]]


def streamzo() -> dict[str, Any]:
    page = fetch("https://streamzo.fr/interstellar", referer="https://streamzo.fr/")
    text = page.get("text") or ""
    match = re.search(r"data-film-id=[\"'](\d+)[\"']", text, re.I)
    film_id = match.group(1) if match else None
    mirror = fetch(f"https://streamzo.fr/api/mirrors/film/{film_id}", referer=page.get("final_url") or "https://streamzo.fr/interstellar") if film_id else {"error": "film id missing", "text": ""}
    mirror_urls: list[str] = []
    if mirror.get("text"):
        try:
            payload = json.loads(mirror["text"])
        except Exception:
            payload = None

        def walk(value: Any) -> None:
            if isinstance(value, str) and value.startswith(("http://", "https://", "/")):
                url = absolute(value, "https://streamzo.fr/")
                if url not in mirror_urls:
                    mirror_urls.append(url)
            elif isinstance(value, list):
                for item in value:
                    walk(item)
            elif isinstance(value, dict):
                for item in value.values():
                    walk(item)

        walk(payload)
    return {
        "page": compact(page),
        "film_id": film_id,
        "mirror_api": compact(mirror),
        "mirror_urls": mirror_urls,
        "mirror_pages": [compact(fetch(url, referer=page.get("final_url") or "https://streamzo.fr/interstellar")) for url in mirror_urls[:12]],
    }


def wookafr() -> dict[str, Any]:
    search = fetch("https://wookafr.center/?s=Interstellar", referer="https://wookafr.center/")
    detail_url = "https://wookafr.center/streaming/aventure/interstellar/"
    detail = fetch(detail_url, referer="https://wookafr.center/")
    embed = "https://lecteurvideo.com/embed.php?id=18230&tp=3&url=wookafr.tel"
    player = fetch(embed, referer=detail_url)
    nested = follow_candidates(player, limit=12)
    return {
        "search": compact(search),
        "detail": compact(detail),
        "known_embed": compact(player),
        "nested": nested,
    }


def frenchstream() -> dict[str, Any]:
    hub = fetch("https://www.fstream.org/")
    match = re.search(r"https://fs\d+\.[a-z0-9.-]+", hub.get("text") or "", re.I)
    base = match.group(0).rstrip("/") if match else "https://fs16.lol"
    post = fetch(
        base + "/engine/ajax/search.php",
        referer=base + "/",
        method="POST",
        data=urllib.parse.urlencode({"query": "Interstellar", "page": "1"}).encode(),
    )
    get = fetch(base + "/?do=search&subaction=search&story=Interstellar", referer=base + "/")
    search_candidates = candidates(post.get("text") or "", post.get("final_url") or base + "/") + candidates(get.get("text") or "", get.get("final_url") or base + "/")
    detail_links: list[str] = []
    for body, source in ((post.get("text") or "", post.get("final_url") or base + "/"), (get.get("text") or "", get.get("final_url") or base + "/")):
        for found in re.findall(r"href=[\"']([^\"']*(?:newsid=\d+|interstellar)[^\"']*)[\"']", body, re.I):
            url = absolute(found, source)
            if url not in detail_links:
                detail_links.append(url)
    details = [fetch(url, referer=base + "/") for url in detail_links[:6]]
    player_urls: list[str] = []
    for response in details:
        for url in candidates(response.get("text") or "", response.get("final_url") or base + "/"):
            host = urllib.parse.urlsplit(url).hostname or ""
            if host in {"french-stream.one", "french-stream.club"}:
                continue
            if url not in player_urls:
                player_urls.append(url)
    return {
        "hub": compact(hub),
        "base": base,
        "post_search": compact(post),
        "get_search": compact(get),
        "search_candidates": search_candidates[:30],
        "detail_links": detail_links,
        "details": [compact(item) for item in details],
        "player_urls": player_urls,
        "player_pages": [compact(fetch(url, referer=detail_links[0] if detail_links else base + "/")) for url in player_urls[:15]],
    }


def coflix() -> dict[str, Any]:
    bases = ["https://coflix.esq", "https://coflix.wiki", "https://coflix.life"]
    reports: list[dict[str, Any]] = []
    for base in bases:
        root = fetch(base + "/")
        searches = [
            fetch(base + "/?s=Interstellar", referer=base + "/"),
            fetch(base + "/search?q=Interstellar", referer=base + "/"),
            fetch(base + "/film/interstellar", referer=base + "/"),
            fetch(base + "/interstellar", referer=base + "/"),
        ]
        detail_urls: list[str] = []
        for response in searches:
            body = response.get("text") or ""
            source = response.get("final_url") or response.get("requested_url") or base + "/"
            for found in re.findall(r"href=[\"']([^\"']*interstellar[^\"']*)[\"']", body, re.I):
                url = absolute(found, source)
                if url not in detail_urls:
                    detail_urls.append(url)
        details = [fetch(url, referer=base + "/") for url in detail_urls[:6]]
        players: list[str] = []
        for response in searches + details:
            for url in candidates(response.get("text") or "", response.get("final_url") or base + "/"):
                if url not in players:
                    players.append(url)
        reports.append(
            {
                "base": base,
                "root": compact(root),
                "searches": [compact(item) for item in searches],
                "detail_urls": detail_urls,
                "details": [compact(item) for item in details],
                "player_urls": players,
                "player_pages": [compact(fetch(url, referer=detail_urls[0] if detail_urls else base + "/")) for url in players[:12]],
            }
        )
    return {"bases": reports}


def main() -> int:
    report = {
        "fixture": "Interstellar (2014) / TMDB 157336",
        "streamzo": streamzo(),
        "wookafr": wookafr(),
        "frenchstream": frenchstream(),
        "coflix": coflix(),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "streamzo_film_id": report["streamzo"].get("film_id"),
        "wookafr_nested": len(report["wookafr"].get("nested") or []),
        "frenchstream_players": len(report["frenchstream"].get("player_urls") or []),
        "coflix_bases": len(report["coflix"].get("bases") or []),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

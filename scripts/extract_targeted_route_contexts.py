#!/usr/bin/env python3
from __future__ import annotations

import html
import http.cookiejar
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from evidence_sanitization import sanitize_evidence

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "automation" / "targeted-provider-contexts.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/148 Safari/537.36"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def fetch(url: str, *, referer: str | None = None, method: str = "GET", data: bytes | None = None) -> dict[str, Any]:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*",
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
        with opener.open(request, timeout=20) as response:
            raw = response.read(3_000_000)
            charset = response.headers.get_content_charset() or "utf-8"
            return {
                "requested_url": url,
                "final_url": response.geturl(),
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "headers": {key.lower(): value for key, value in response.headers.items() if key.lower() in {"set-cookie", "location", "content-type"}},
                "text": raw.decode(charset, errors="replace"),
                "length": len(raw),
            }
    except Exception as error:
        return {"requested_url": url, "status": None, "text": "", "length": 0, "error": f"{type(error).__name__}: {error}"}


def contexts(text: str, needles: list[str], *, radius: int = 900, limit: int = 8) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    lower = text.casefold()
    for needle in needles:
        cursor = 0
        rows: list[str] = []
        target = needle.casefold()
        while len(rows) < limit:
            index = lower.find(target, cursor)
            if index < 0:
                break
            start = max(0, index - radius)
            end = min(len(text), index + len(needle) + radius)
            excerpt = html.unescape(text[start:end]).replace("\\/", "/")
            excerpt = re.sub(r"[\r\n\t]+", " ", excerpt)
            excerpt = re.sub(r"\s{2,}", " ", excerpt)
            rows.append(excerpt)
            cursor = index + len(needle)
        output[needle] = rows
    return output


def script_urls(page: dict[str, Any]) -> list[str]:
    base = page.get("final_url") or page.get("requested_url") or ""
    values: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"<script[^>]+src=[\"']([^\"']+)[\"']", page.get("text") or "", re.I):
        url = urllib.parse.urljoin(base, html.unescape(match.group(1)))
        if url not in seen:
            seen.add(url)
            values.append(url)
    return values


def compact(response: dict[str, Any]) -> dict[str, Any]:
    text = response.get("text") or ""
    return {
        key: response.get(key)
        for key in ("requested_url", "final_url", "status", "content_type", "length", "headers", "error")
        if response.get(key) not in (None, "", {})
    } | {
        "json_preview": text[:4000] if "json" in str(response.get("content_type") or "").casefold() else None,
    }


def worker(provider_id: str) -> dict[str, Any]:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    row = next(item for item in manifest.get("scrapers", []) if str(item.get("id") or "").casefold() == provider_id)
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
    env = dict(os.environ)
    env.update({"NUVIO_NETWORK_MAX_REQUESTS": "120", "NUVIO_WORKER_MEMORY_MB": "1024"})
    try:
        process = subprocess.run(
            ["node", "scripts/provider_worker.cjs", str(ROOT / str(row["filename"])), json.dumps(media), json.dumps(context), "2"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        parsed: Any = None
        for line in reversed(process.stdout.splitlines()):
            try:
                parsed = json.loads(line.strip())
                break
            except Exception:
                continue
        return {
            "returncode": process.returncode,
            "stream_count": len(parsed) if isinstance(parsed, list) else None,
            "streams": parsed[:5] if isinstance(parsed, list) else None,
            "stdout_tail": process.stdout[-7000:],
            "stderr_tail": process.stderr[-5000:],
        }
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"}


def main() -> int:
    stream_page = fetch("https://streamzo.fr/interstellar", referer="https://streamzo.fr/")
    stream_app_url = next((url for url in script_urls(stream_page) if "/static/js/app.js" in url), "https://streamzo.fr/static/js/app.js")
    stream_app = fetch(stream_app_url, referer="https://streamzo.fr/interstellar")

    french_hub = fetch("https://www.fstream.org/")
    fs_match = re.search(r"https://fs\d+\.[a-z0-9.-]+", french_hub.get("text") or "", re.I)
    french_base = (fs_match.group(0).rstrip("/") if fs_match else "https://fs16.lol")
    french_search = fetch(french_base + "/?do=search&subaction=search&story=Interstellar", referer=french_base + "/")
    french_scripts: dict[str, Any] = {}
    for url in script_urls(french_search):
        if any(token in url for token in ("search01.js", "auto-repair", "dle_js.js", "vidzy")):
            response = fetch(url, referer=french_search.get("final_url") or french_base + "/")
            french_scripts[url] = {
                "meta": compact(response),
                "contexts": contexts(response.get("text") or "", ["search", "subaction", "story", "dle_search", "film_api", "vidzy", "ajax"], radius=700, limit=6),
            }

    movix_page = fetch("https://movix.fun/")
    movix_bundle_url = next((url for url in script_urls(movix_page) if "/assets/index-" in url), "")
    movix_bundle = fetch(movix_bundle_url, referer="https://movix.fun/") if movix_bundle_url else {"text": ""}

    # Safe, unauthenticated route-shape probes inferred from the public bundles.
    stream_probes = []
    for url in (
        "https://streamzo.fr/api/v1/web-identity",
        "https://streamzo.fr/api/v1/films/interstellar",
        "https://streamzo.fr/api/v1/films/157336",
        "https://streamzo.fr/api/films?ids=157336",
        "https://streamzo.fr/api/mirrors/interstellar",
        "https://streamzo.fr/api/mirrors/157336",
    ):
        stream_probes.append(compact(fetch(url, referer="https://streamzo.fr/interstellar")))

    movix_probes = []
    for url in (
        "https://api.movix.fun/api/content?type=movie&id=157336",
        "https://api.movix.fun/api/content?media_type=movie&tmdb_id=157336",
        "https://api.movix.fun/api/content/movie/157336",
        "https://api.movix.fun/api/content/157336",
        "https://proxy.movix.fun/api/content?type=movie&id=157336",
        "https://proxiesembed.movix.fun/api/content?type=movie&id=157336",
    ):
        movix_probes.append(compact(fetch(url, referer="https://movix.fun/movie/157336")))

    report = {
        "fixture": "Interstellar (2014) / TMDB 157336",
        "streamzo": {
            "page": compact(stream_page),
            "page_contexts": contexts(stream_page.get("text") or "", ["Interstellar", "data-film", "film-id", "tmdb", "mirror", "web-identity", "/api/"], radius=900, limit=10),
            "app_url": stream_app_url,
            "app_contexts": contexts(stream_app.get("text") or "", ["/api/v1/web-identity", "/api/films?ids=", "/api/mirrors/", "/api/v1/films/", "/api/v1/episodes/"], radius=1400, limit=8),
            "probes": stream_probes,
            "worker": worker("streamzo"),
        },
        "frenchstream": {
            "base": french_base,
            "search": compact(french_search),
            "search_contexts": contexts(french_search.get("text") or "", ["Interstellar", "news-id", "data-id", "shortstory", "film_api", "search_result", "result"], radius=1200, limit=15),
            "scripts": french_scripts,
            "worker": worker("frenchstream"),
        },
        "movix": {
            "page": compact(movix_page),
            "bundle_url": movix_bundle_url,
            "bundle_contexts": contexts(movix_bundle.get("text") or "", ["/api/content", "api.movix.fun", "proxiesembed.movix.fun", "verify-access-code", "turnstile", "accessCode", "tmdbId", "media_type"], radius=1700, limit=12),
            "probes": movix_probes,
            "worker": worker("movix"),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    persisted_report = sanitize_evidence(report)
    OUTPUT.write_text(json.dumps(persisted_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "streamzo_worker": report["streamzo"]["worker"].get("stream_count"),
        "frenchstream_worker": report["frenchstream"]["worker"].get("stream_count"),
        "movix_worker": report["movix"]["worker"].get("stream_count"),
        "output": str(OUTPUT),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

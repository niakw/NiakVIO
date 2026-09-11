#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import ssl
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
CTX = ssl.create_default_context()


def get(url: str, referer: str | None = None) -> tuple[int, str, str]:
    headers = {"User-Agent": UA, "Accept": "text/html,application/json,*/*"}
    if referer:
        headers["Referer"] = referer
    try:
        with urlopen(Request(url, headers=headers), timeout=12, context=CTX) as response:
            return int(response.status), response.geturl(), response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        code = int(getattr(exc, "code", 0) or 0)
        try:
            body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
        except Exception:
            body = ""
        print(f"ANIDB_LIVE_HTTP_ERROR url={url} status={code} error={type(exc).__name__}")
        return code, url, body


def collect_episodes(node: object, out: list[tuple[int, int]]) -> None:
    if isinstance(node, list):
        for item in node:
            collect_episodes(item, out)
    elif isinstance(node, dict):
        try:
            if "id" in node and "number" in node:
                eid, num = int(node["id"]), int(node["number"])
                if eid > 0 and num > 0:
                    out.append((eid, num))
        except Exception:
            pass
        for item in node.values():
            collect_episodes(item, out)


def collect_embeds(node: object, out: list[str]) -> None:
    if isinstance(node, list):
        for item in node:
            collect_embeds(item, out)
    elif isinstance(node, dict):
        value = node.get("embed_url") or node.get("embedUrl")
        if isinstance(value, str) and value.strip() and value not in out:
            out.append(value.strip())
        for key, item in node.items():
            if key not in {"embed_url", "embedUrl"}:
                collect_embeds(item, out)


def main() -> int:
    base = "https://anidb.app"
    search_url = f"{base}/browse?q={quote('Jujutsu Kaisen')}"
    status, final, html = get(search_url, base + "/")
    print(f"ANIDB_LIVE_SEARCH status={status} final={final} bytes={len(html)}")
    if not 200 <= status < 300:
        print("ANIDB_LIVE_STATUS unavailable_stage=search")
        return 0

    matches = re.findall(r'href=["\'](?:https?://[^"\']+)?/anime/([a-z0-9-]+-([0-9]+))["\']', html, re.I)
    chosen: tuple[str, str] | None = None
    for slug, aid in matches:
        if re.sub(r"-[0-9]+$", "", slug.lower()) == "jujutsu-kaisen":
            chosen = (slug, aid)
            break
    if chosen is None and matches:
        chosen = matches[0]
    if chosen is None:
        print("ANIDB_LIVE_STATUS unresolved_stage=search_parse")
        return 0
    slug, aid = chosen
    print(f"ANIDB_LIVE_ANIME id={aid} slug={slug}")

    ep_url = f"{base}/api/frontend/anime/{aid}/episodes"
    status, _, raw = get(ep_url, search_url)
    print(f"ANIDB_LIVE_EPISODES status={status} bytes={len(raw)}")
    if not 200 <= status < 300:
        print("ANIDB_LIVE_STATUS unavailable_stage=episodes")
        return 0
    try:
        ep_json = json.loads(raw)
    except Exception:
        print("ANIDB_LIVE_STATUS unresolved_stage=episodes_json")
        return 0
    episodes: list[tuple[int, int]] = []
    collect_episodes(ep_json, episodes)
    selected = next((row for row in episodes if row[1] == 1), episodes[0] if episodes else None)
    if selected is None:
        print("ANIDB_LIVE_STATUS unresolved_stage=episode_select")
        return 0
    eid, enum = selected
    print(f"ANIDB_LIVE_EPISODE id={eid} number={enum} count={len(episodes)}")

    lang_url = f"{base}/api/frontend/episode/{eid}/languages"
    status, _, raw = get(lang_url, search_url)
    print(f"ANIDB_LIVE_LANGUAGES status={status} bytes={len(raw)}")
    if not 200 <= status < 300:
        print("ANIDB_LIVE_STATUS unavailable_stage=languages")
        return 0
    try:
        lang_json = json.loads(raw)
    except Exception:
        print("ANIDB_LIVE_STATUS unresolved_stage=languages_json")
        return 0
    embeds: list[str] = []
    collect_embeds(lang_json, embeds)
    print(f"ANIDB_LIVE_EMBEDS count={len(embeds)}")
    if not embeds:
        print("ANIDB_LIVE_STATUS unresolved_stage=embed_list")
        return 0

    hls = 0
    for raw_embed in embeds[:4]:
        embed = urljoin(base + "/", raw_embed)
        estatus, _, page = get(embed, search_url)
        if not 200 <= estatus < 300:
            continue
        match = re.search(r"file\s*:\s*[\"']([^\"']+)[\"']", page, re.I)
        if not match:
            match = re.search(r"[\"'](https?://[^\"']+\.m3u8[^\"']*)[\"']", page, re.I)
        if not match:
            continue
        master = urljoin(embed, match.group(1).replace("\\/", "/"))
        mstatus, _, playlist = get(master, embed)
        valid = 200 <= mstatus < 300 and bool(re.search(r"^#EXTM3U", playlist, re.M))
        print(
            f"ANIDB_LIVE_MEDIA embed_host={urlparse(embed).hostname or ''} "
            f"status={mstatus} hls={1 if valid else 0} media_host={urlparse(master).hostname or ''}"
        )
        if valid:
            hls += 1
    print(f"ANIDB_LIVE_STATUS search=1 episodes=1 languages=1 embeds={len(embeds)} hls={hls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

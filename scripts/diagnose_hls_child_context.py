#!/usr/bin/env python3
"""Compare HLS child playback context without persisting signed media URLs.

This diagnostic executes current provider bytes, keeps returned stream URLs only
in memory, then tests whether a master/variant/segment requires a player referer
or a same-origin browser-style cookie warm-up. Output is deliberately limited to
statuses, media classification and cookie counts.
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import run_provider_upstream_parity_v3 as parity3
from parity_hls_terminal_probe import parse_hls

ROOT = Path(__file__).resolve().parents[1]
READ_LIMIT = 196_608
SEGMENT_LIMIT = 4096


def cid(value: object) -> str:
    return str(value or "").strip().casefold()


def provider_path(provider_id: str) -> Path:
    wanted = cid(provider_id)
    for manifest_path in (ROOT / "manifest.json", ROOT / "vf" / "manifest.json"):
        if not manifest_path.is_file():
            continue
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for row in data.get("scrapers") or []:
            if not isinstance(row, dict) or cid(row.get("id")) != wanted or row.get("enabled") is False:
                continue
            filename = str(row.get("filename") or "").strip()
            path = (manifest_path.parent / filename).resolve()
            if ROOT in path.parents and path.is_file():
                return path
    raise SystemExit(f"active provider not found: {provider_id}")


def player_referer(fixture: dict[str, Any], base: str) -> str:
    media_type = str(fixture.get("mediaType") or "").strip().casefold()
    tmdb_id = str(fixture.get("tmdbId") or "").strip()
    if media_type == "movie":
        return f"{base.rstrip('/')}/embed/movie/{tmdb_id}"
    season = int(fixture.get("season") or 0)
    episode = int(fixture.get("episode") or 0)
    return f"{base.rstrip('/')}/embed/tv/{tmdb_id}/{season}/{episode}"


def request_headers(base: dict[str, str], *, referer: str | None = None, origin: str | None = None, segment: bool = False) -> dict[str, str]:
    out = {
        str(key): str(value)
        for key, value in (base or {}).items()
        if value is not None and str(key).casefold() not in {"host", "content-length", "connection", "transfer-encoding", "cookie", "range"}
    }
    if referer:
        out["Referer"] = referer
    if origin:
        out["Origin"] = origin
    out.setdefault("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")
    out.setdefault("Accept-Language", "en-US,en;q=0.8")
    out["Accept"] = "video/*,audio/*,application/octet-stream,*/*;q=0.5" if segment else "application/vnd.apple.mpegurl,application/x-mpegURL,*/*;q=0.8"
    if segment:
        out["Range"] = f"bytes=0-{SEGMENT_LIMIT - 1}"
    return out


def fetch(opener: urllib.request.OpenerDirector, url: str, headers: dict[str, str], *, segment: bool, timeout: int) -> tuple[int, str, str, bytes]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        response = opener.open(req, timeout=max(3, min(timeout, 20)))
    except urllib.error.HTTPError as exc:
        response = exc
    with response as resp:
        status = int(getattr(resp, "status", None) or getattr(resp, "code", None) or 0)
        final = str(resp.geturl() or url)
        ctype = str(resp.headers.get("content-type") or "")
        body = resp.read(SEGMENT_LIMIT if segment else READ_LIMIT)
    return status, final, ctype, body


def looks_media(content_type: str, body: bytes) -> bool:
    ctype = str(content_type or "").split(";", 1)[0].strip().casefold()
    sample = body[:SEGMENT_LIMIT]
    if ctype.startswith(("video/", "audio/")):
        return True
    if b"ftyp" in sample[:128] or any(atom in sample[:256] for atom in (b"styp", b"moof", b"mdat")):
        return True
    return len(sample) >= 189 and sample[0] == 0x47 and sample[188] == 0x47


def profile(stream_url: str, stream_headers: dict[str, str], *, referer: str | None, origin: str | None, warmup: str | None, timeout: int) -> dict[str, Any]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    warmup_status = None
    if warmup:
        try:
            warmup_status, _, _, _ = fetch(
                opener,
                warmup,
                request_headers(stream_headers, referer=referer, origin=origin),
                segment=False,
                timeout=timeout,
            )
        except Exception:
            warmup_status = 0

    current_headers = request_headers(stream_headers, referer=referer, origin=origin)
    master_status, master_url, master_type, master_body = fetch(
        opener, stream_url, current_headers, segment=False, timeout=timeout
    )
    parsed = parse_hls(master_body, master_url)
    result: dict[str, Any] = {
        "warmup_status": warmup_status,
        "cookie_count": len(jar),
        "master_status": master_status,
        "master_hls": bool(parsed.get("valid")),
        "master_is_master": bool(parsed.get("master")),
        "variant_status": None,
        "segment_status": None,
        "segment_media": False,
    }
    if master_status not in {200, 206} or not parsed.get("valid"):
        return result

    body = master_body
    current_url = master_url
    for _depth in range(3):
        parsed = parse_hls(body, current_url)
        if parsed.get("master"):
            variants = list(parsed.get("variants") or [])
            if not variants:
                return result
            status, current_url, _ctype, body = fetch(
                opener, variants[0], current_headers, segment=False, timeout=timeout
            )
            result["variant_status"] = status
            if status not in {200, 206}:
                return result
            continue
        segments = list(parsed.get("segments") or [])
        if not segments:
            return result
        status, _final, ctype, segment_body = fetch(
            opener,
            segments[0],
            request_headers(stream_headers, referer=referer, origin=origin, segment=True),
            segment=True,
            timeout=timeout,
        )
        result["segment_status"] = status
        result["segment_media"] = status in {200, 206} and looks_media(ctype, segment_body)
        return result
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True)
    ap.add_argument("--fixture-json", required=True)
    ap.add_argument("--embed-base", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--timeout", type=int, default=20)
    args = ap.parse_args()

    fixture = json.loads(args.fixture_json)
    path = provider_path(args.provider)
    raw = parity3._worker_raw(path, fixture, max(15, min(args.timeout * 2, 60)))
    streams = [row for row in raw.get("streams") or [] if isinstance(row, dict)]
    if not streams:
        payload = {"provider": cid(args.provider), "candidate_count": 0, "profiles": {}}
    else:
        stream = streams[0]
        url = str(stream.get("url") or "")
        headers = parity3._safe_headers(stream.get("headers"))
        embed = player_referer(fixture, args.embed_base)
        origin = urllib.parse.urlsplit(args.embed_base).scheme + "://" + str(urllib.parse.urlsplit(args.embed_base).netloc)
        payload = {
            "provider": cid(args.provider),
            "candidate_count": len(streams),
            "profiles": {
                "current": profile(url, headers, referer=None, origin=None, warmup=None, timeout=args.timeout),
                "embed_referer": profile(url, headers, referer=embed, origin=origin, warmup=None, timeout=args.timeout),
                "embed_session": profile(url, headers, referer=embed, origin=origin, warmup=embed, timeout=args.timeout),
            },
        }

    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("HLS_CHILD_CONTEXT " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

PLAYLIST_BYTES = 196_608
SEGMENT_BYTES = 4096


def _headers(base: dict[str, str], *, playlist: bool) -> dict[str, str]:
    out = {str(k): str(v) for k, v in (base or {}).items() if v is not None}
    for key in list(out):
        if key.casefold() == "range":
            out.pop(key, None)
    out.setdefault(
        "User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    )
    out.setdefault("Accept-Language", "en-US,en;q=0.8")
    if playlist:
        out.setdefault("Accept", "application/vnd.apple.mpegurl,application/x-mpegURL,*/*;q=0.8")
    else:
        out.setdefault("Accept", "video/*,audio/*,application/octet-stream,*/*;q=0.5")
        out["Range"] = f"bytes=0-{SEGMENT_BYTES - 1}"
    return out


def _fetch(url: str, headers: dict[str, str], timeout: int, *, playlist: bool) -> tuple[int, str, str, bytes]:
    request = urllib.request.Request(url, headers=_headers(headers, playlist=playlist), method="GET")
    with urllib.request.urlopen(request, timeout=max(3, min(18, int(timeout or 12)))) as response:
        status = int(response.getcode() or 0)
        final_url = str(response.geturl() or url)
        content_type = str(response.headers.get("content-type") or "")
        body = response.read(PLAYLIST_BYTES if playlist else SEGMENT_BYTES)
    return status, final_url, content_type, body


def _decode(body: bytes) -> str:
    return body.decode("utf-8", errors="replace").lstrip("\ufeffï»¿")


def parse_hls(body: bytes, base_url: str) -> dict[str, Any]:
    text = _decode(body)
    lines = [line.strip() for line in text.splitlines()]
    if not lines or lines[0].upper() != "#EXTM3U":
        return {"valid": False, "master": False, "variants": [], "segments": [], "duration": None, "complete": False}

    variants: list[str] = []
    segments: list[str] = []
    durations: list[float] = []
    master = False
    for index, line in enumerate(lines):
        upper = line.upper()
        if upper.startswith("#EXT-X-STREAM-INF:"):
            master = True
            for candidate in lines[index + 1:]:
                if not candidate or candidate.startswith("#"):
                    continue
                variants.append(urllib.parse.urljoin(base_url, candidate))
                break
        if upper.startswith("#EXTINF:"):
            try:
                duration = float(line.split(":", 1)[1].split(",", 1)[0].strip())
                if duration >= 0:
                    durations.append(duration)
            except (TypeError, ValueError):
                pass
            for candidate in lines[index + 1:]:
                if not candidate or candidate.startswith("#"):
                    continue
                segments.append(urllib.parse.urljoin(base_url, candidate))
                break

    return {
        "valid": True,
        "master": master,
        "variants": variants,
        "segments": segments,
        "duration": float(sum(durations)) if durations else None,
        "complete": any(line.upper() == "#EXT-X-ENDLIST" for line in lines),
    }


def _segment_media(content_type: str, body: bytes) -> bool:
    ctype = str(content_type or "").split(";", 1)[0].strip().casefold()
    sample = body[:SEGMENT_BYTES]
    head = sample.lstrip()[:128].lower()
    if not sample:
        return False
    if ctype.startswith("text/") or ctype in {"application/json", "application/xhtml+xml", "text/html"}:
        return False
    if head.startswith(b"<!doctype") or head.startswith(b"<html") or head.startswith(b"{") or head.startswith(b"["):
        return False
    if ctype.startswith("video/") or ctype.startswith("audio/"):
        return True
    if b"ftyp" in sample[:128]:
        return True
    if len(sample) >= 189 and sample[0] == 0x47 and sample[188] == 0x47:
        return True
    # fMP4 media segments may begin with styp/moof rather than ftyp.
    if any(atom in sample[:256] for atom in (b"styp", b"moof", b"mdat")):
        return True
    return False


def verify_hls_terminal(
    body: bytes,
    final_url: str,
    stream_headers: dict[str, str],
    timeout: int,
    *,
    min_vod_seconds: float = 60.0,
    max_depth: int = 2,
) -> dict[str, Any]:
    """Verify HLS by reaching a real media segment, not merely an HLS-looking master."""
    current_body = body
    current_url = final_url
    for depth in range(max_depth + 1):
        parsed = parse_hls(current_body, current_url)
        if not parsed["valid"]:
            return {"verified": False, "kind": "hls", "reason": "hls_invalid_structure"}

        duration = parsed.get("duration")
        if parsed.get("complete") and isinstance(duration, (int, float)) and 0 < float(duration) < float(min_vod_seconds):
            return {
                "verified": False,
                "kind": "hls",
                "reason": "short_finite_vod",
                "short_vod_seconds": round(float(duration), 3),
            }

        if parsed.get("master"):
            variants = list(parsed.get("variants") or [])
            if not variants:
                return {"verified": False, "kind": "hls", "reason": "hls_master_no_variant"}
            if depth >= max_depth:
                return {"verified": False, "kind": "hls", "reason": "hls_variant_depth"}
            try:
                status, current_url, _ctype, current_body = _fetch(
                    variants[0], stream_headers, timeout, playlist=True
                )
            except urllib.error.HTTPError as exc:
                return {"verified": False, "kind": "hls", "status": int(exc.code), "reason": f"hls_variant_http_{int(exc.code)}"}
            except Exception as exc:
                return {"verified": False, "kind": "hls", "reason": type(exc).__name__[:80]}
            if status not in {200, 206}:
                return {"verified": False, "kind": "hls", "status": status, "reason": f"hls_variant_http_{status}"}
            continue

        segments = list(parsed.get("segments") or [])
        if not segments:
            return {"verified": False, "kind": "hls", "reason": "hls_no_media_segment"}
        try:
            status, _segment_url, content_type, segment_body = _fetch(
                segments[0], stream_headers, timeout, playlist=False
            )
        except urllib.error.HTTPError as exc:
            return {"verified": False, "kind": "hls", "status": int(exc.code), "reason": f"hls_segment_http_{int(exc.code)}"}
        except Exception as exc:
            return {"verified": False, "kind": "hls", "reason": type(exc).__name__[:80]}
        if status not in {200, 206}:
            return {"verified": False, "kind": "hls", "status": status, "reason": f"hls_segment_http_{status}"}
        if not _segment_media(content_type, segment_body):
            return {"verified": False, "kind": "hls", "status": status, "reason": "hls_segment_non_media"}
        return {
            "verified": True,
            "kind": "hls",
            "status": status,
            "reason": "hls_segment_media",
            "media_duration_seconds": round(float(duration), 3) if isinstance(duration, (int, float)) and parsed.get("complete") else None,
        }

    return {"verified": False, "kind": "hls", "reason": "hls_unresolved"}

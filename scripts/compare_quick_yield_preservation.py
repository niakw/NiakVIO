#!/usr/bin/env python3
"""Portfolio preservation gate with stream-level wrong-content classification.

The gate also rejects known generic application-shell media as preservation proof.
A browser/app fallback asset can be technically playable while being unrelated to
the requested work; preserving that historical false positive would be a content
identity regression, not a non-regression guarantee.
"""
from __future__ import annotations

from urllib.parse import urlsplit

import compare_quick_yield_preservation_impl as impl

_original_load = impl.load


def accepted_verified_stream(row: dict) -> bool:
    return int(row.get("playable") or 0) > 0 and int(row.get("verified") or 0) > 0


def generic_app_shell_media(url: object) -> bool:
    """Recognize deterministic app-shell media, never provider/content media."""
    try:
        parsed = urlsplit(str(url or ""))
    except ValueError:
        return False
    host = str(parsed.hostname or "").casefold()
    path = str(parsed.path or "").casefold().rstrip("/")
    # Telegram serves this fixed MP4 when its web application cannot run JS. It
    # is independent of the requested title and therefore cannot prove content.
    return host == "web.telegram.org" and path in {"/a/nojs.mp4", "/k/nojs.mp4"}


def generic_shell_only_positive(row: dict) -> bool:
    if not accepted_verified_stream(row):
        return False
    media_fetches: list[str] = []
    for fetch in row.get("debug_fetches") or []:
        if not isinstance(fetch, dict):
            continue
        status = int(fetch.get("status") or 0)
        content_type = str(fetch.get("content_type") or "").casefold()
        url = str(fetch.get("response_url") or fetch.get("url") or "")
        try:
            path = str(urlsplit(url).path or "").casefold()
        except ValueError:
            path = ""
        is_media = content_type.startswith(("video/", "audio/")) or path.endswith(
            (".m3u8", ".mpd", ".mp4", ".mkv", ".webm", ".m4v", ".ts")
        )
        if 200 <= status < 400 and is_media:
            media_fetches.append(url)
    return bool(media_fetches) and all(generic_app_shell_media(url) for url in media_fetches)


def normalize_report(report: dict) -> dict:
    value = dict(report)
    terminal_wrong: set[str] = set()
    false_positive: set[str] = set()
    for row in report.get("rows") or []:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider_id") or row.get("provider") or "").strip().casefold()
        contradictions = int(row.get("contradictions") or 0)
        if provider and contradictions > 0 and not accepted_verified_stream(row):
            terminal_wrong.add(provider)
        if provider and generic_shell_only_positive(row):
            false_positive.add(provider)
    # Old reports without rows retain their declared summary for compatibility.
    if isinstance(report.get("rows"), list):
        value["wrong_content_providers"] = sorted(terminal_wrong)
        value["audit_false_positive_providers"] = sorted(false_positive)
        for key in (
            "raw_providers",
            "playable_providers",
            "accepted_playable_providers",
            "verified_providers",
        ):
            if isinstance(report.get(key), list):
                value[key] = sorted(
                    str(provider)
                    for provider in report.get(key) or []
                    if str(provider).strip().casefold() not in false_positive
                )
    return value


def load(path: str) -> dict:
    return normalize_report(_original_load(path))


impl.load = load


def main() -> int:
    return impl.main()


if __name__ == "__main__":
    raise SystemExit(main())

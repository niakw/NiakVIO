#!/usr/bin/env python3
"""Preserve HLS master playlists when they carry external audio renditions.

Several upstream bundles expand a master playlist into one child URL per video
quality. That is safe for muxed A/V variants, but it drops EXT-X-MEDIA audio
renditions when audio is carried separately. In that case the Nuvio player sees
video-only child playlists and cannot select/hear the audio track.

This patch is intentionally structural and conservative: it only changes the
common master-expansion guard already present in provider bundles. When an HLS
master advertises TYPE=AUDIO, the original master URL is returned unchanged so
the player receives the complete audio-group graph.
"""
from __future__ import annotations

import re
from typing import Any

MARKER = "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1"

# Matches the compact helper used by multiple published provider bundles:
#   if(!/#EXT-X-STREAM-INF/i.test(x))return ...
# We extend only the condition; the provider's original return expression stays
# byte-for-byte intact.
GUARD = re.compile(
    r"if\s*\(\s*!\s*/#EXT-X-STREAM-INF/i\.test\((?P<var>[A-Za-z_$][A-Za-z0-9_$]*)\)\s*\)\s*return"
)


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    if MARKER in text:
        return text

    changed = 0

    def replacement(match: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        variable = match.group("var")
        return (
            f"if(!/#EXT-X-STREAM-INF/i.test({variable})||"
            f"/#EXT-X-MEDIA:[^\\r\\n]*TYPE=AUDIO/i.test({variable}))return"
        )

    output = GUARD.sub(replacement, text)
    if not changed:
        return text
    return output.rstrip() + f"\n/* {MARKER} */\n"

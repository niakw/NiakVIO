#!/usr/bin/env python3
"""Movy clean-v3 WeCollege/Wings runtime Lego.

Physical Mac browser proof (2026-11-15) observed:
- seed API: https://api.wecollege.net/seed?mediaId={tmdbId}
- VisionQuest S01E01: miami/sources -> encrypted Wings payload -> 1080p HLS
- Fahrenheit 451 (2018): miami/boise fail, nashville/sources -> media HLS

The runtime keeps only the reusable API contract. Seed values and media URLs are
ephemeral and are never persisted in Provider DATA.
"""
from __future__ import annotations
from typing import Any

from provider_patch_blocks import replace_managed_fix
from provider_wings_runtime_common import render_wings_runtime

MANAGED_FIX_ID = "PROVIDER.MOVY.WECOLLEGE.WINGS.V1"
MARKER = "NIAKVIO_MOVY_WECOLLEGE_WINGS_V1"

DEFAULT_ENDPOINTS = [
    {"label": "Miami", "path": "miami/sources"},
    {"label": "Boise", "path": "boise/sources"},
    {"label": "Nashville", "path": "nashville/sources"},
]


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    runtime = {
        "apiBase": str(cfg.get("api_base") or "https://api.wecollege.net"),
        "origin": str(cfg.get("origin") or "https://www.movy.sx"),
        "referer": str(cfg.get("referer") or "https://www.movy.sx/"),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        ),
        "providerId": "movy",
        "providerName": "Movy",
        "installMarker": "__niakvioMovyWeCollegeWingsV1",
        "endpoints": list(cfg.get("endpoints") or DEFAULT_ENDPOINTS),
    }
    body = render_wings_runtime(marker=MARKER, config=runtime)
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        body,
        data={
            "runtime": runtime,
            "family": "wings-v1",
            "identity": "core-tmdb-title-year-imdb",
            "movieProof": "physical-mac-fahrenheit-451-2018",
            "tvProof": "physical-mac-visionquest-s01e01-1080p",
            "ephemeralSeedPersisted": False,
            "terminalMediaPersisted": False,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")

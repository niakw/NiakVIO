#!/usr/bin/env python3
"""Static Provider-Lego entrypoint for the shared non-display recovery runtime."""
from __future__ import annotations
from typing import Any

from provider_patch_blocks import replace_managed_fix
import non_display_recovery_runtime_v1 as common

MANAGED_FIX_ID = "PROVIDER.NONDISPLAY.RECOVERY.V1"
MARKER = common.MARKER


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    provider = str(cfg.get("provider") or "").strip().casefold().replace("_", "-")
    if provider not in common.SUPPORTED:
        raise ValueError(f"unsupported non-display recovery provider: {provider!r}")
    default_bases = {
        "animesama-co": "https://animesama.co",
        "animevostfr": "https://v2.animevostfr.org",
        "coflix": "https://coflix.wiki",
        "neko-sama": "https://animes-sama.su",
        "sekai": "https://sekai.one",
        "voiranime-rip": "https://voiranime.rip",
    }
    payload = {
        "provider": provider,
        "base": str(cfg.get("base") or default_bases[provider]).rstrip("/"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
        "maxStreams": max(1, min(int(cfg.get("max_streams") or 4), 8)),
    }
    if not payload["base"].startswith("https://"):
        raise ValueError("non-display recovery runtime requires https base")
    wrapper = common.WRAPPER.replace("CONFIG_PLACEHOLDER", common.json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "scope": "fresh-live-parity-regression-recovery",
            "upstreamJsExecuted": False,
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "terminalResolution": "existing-bounded-direct-media-crawler",
            "evidenceRun": 35112301175,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")

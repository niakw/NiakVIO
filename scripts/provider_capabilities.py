#!/usr/bin/env python3
"""Provider capability classification and policy helpers.

The capability layer is intentionally descriptive: it does not rewrite every
provider into one playback model. It records how a provider is expected to
behave so discovery, migration and runtime validation can choose an adapted
strategy (iframe player, direct media, API resolver, HTML scraper, or official
address hub).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"


def load_config() -> dict[str, Any]:
    data = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    return data if isinstance(data, dict) else {}


def configured_capability(provider_id: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    values = config.get("provider_capabilities") or {}
    capability = values.get(provider_id.casefold()) or {}
    return dict(capability) if isinstance(capability, dict) else {}


def infer_capability(provider_id: str, source: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    configured = configured_capability(provider_id, config)
    if configured:
        configured.setdefault("source", "configured")
        return configured

    text = source.lower()
    result: dict[str, Any] = {"source": "inferred", "strategy": "unknown"}
    if "postmessage" in text or "player_event" in text or re.search(r"/movie/[^\s]+.*?/tv/", text):
        result.update(strategy="iframe_player", validation="embed_page", allow_html_url=True)
    elif ".m3u8" in text or "master.m3u8" in text:
        result.update(strategy="direct_media", validation="media_probe", allow_html_url=False)
    elif re.search(r"/api/|api\.", text) and ("getstreams" in text or "fetch(" in text):
        result.update(strategy="api_stream_resolver", validation="api_then_output")
    elif "cheerio" in text or ".load(" in text:
        result.update(strategy="html_scraper", validation="search_then_detail")
    return result

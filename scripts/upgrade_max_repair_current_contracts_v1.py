#!/usr/bin/env python3
"""Persist current live contracts proven by the 2026-09-16 max-repair campaign."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
WOOKA_DECODER = "scripts/provider_patches/wookafr_showvideo_base64_v1.py"
VIDLOVE_SELECTOR = "scripts/provider_patches/vidlove_current_api_v1.py"
VIDFAST_EMBED = "scripts/provider_patches/vidfast_current_embed_v1.py"


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = value.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider_patches missing")
    for pid in ("wookafr", "vidlove", "vidfast"):
        if not isinstance(patches.get(pid), dict):
            raise AssertionError(f"provider patch missing: {pid}")
    capabilities = value.get("provider_capabilities")
    if not isinstance(capabilities, dict):
        raise AssertionError("provider_capabilities missing")
    return value


def add_script(row: dict[str, Any], script: str) -> None:
    scripts = [str(v) for v in row.get("provider_lego_scripts") or [] if str(v).strip()]
    if script not in scripts:
        scripts.append(script)
    row["provider_lego_scripts"] = scripts


def add_note(row: dict[str, Any], note: str) -> None:
    notes = [str(v) for v in row.get("notes") or []]
    if note not in notes:
        notes.append(note)
    row["notes"] = notes


def patch() -> bool:
    value = load()
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)
    patches = value["provider_patches"]
    capabilities = value["provider_capabilities"]

    wooka = patches["wookafr"]
    add_script(wooka, WOOKA_DECODER)
    wooka["capability"] = "mixed_embed_resolver"
    wooka["preserve_embed_urls"] = True
    add_note(wooka, "Current lecteurvideo embeds encode player URLs in showVideo(base64,...); Wooka decodes those provider-local seeds before the existing bounded shared crawler and terminal guards.")
    add_note(wooka, "When the identity-qualified Wooka path reaches lecteurvideo but no direct media is extractable, the provider preserves the freshly decoded player embeds as a fallback instead of returning a false zero; the cache is reset per getStreams call to prevent cross-title leakage.")

    vidlove = patches["vidlove"]
    add_script(vidlove, VIDLOVE_SELECTOR)
    # ProviderBase has a real bounded JSON API recipe and its executable reader
    # understands api_stream_resolver/direct_media. `direct_api_hls` was a local
    # label invented by this one-shot and is not a runtime strategy; persisting it
    # makes the strategy-plan gate fail and can make a later reapply inconsistent.
    vidlove["capability"] = "api_stream_resolver"
    vidlove_capability = capabilities.setdefault("vidlove", {})
    if not isinstance(vidlove_capability, dict):
        raise AssertionError("VidLove provider capability must be an object")
    vidlove_capability["strategy"] = "api_stream_resolver"
    vidlove_capability["validation"] = "provider_native"
    vidlove_capability["requires_direct_media"] = True
    vidlove["official_site"] = "https://player.vidlove.cc"
    vidlove["official_api"] = "https://api.vidlove.cc"
    vidlove["published_types"] = ["movie", "tv"]
    vidlove.setdefault("domain_substitutions", {})
    for old in (
        "ballerinacappuccinalovestungtungtungsahur.com",
        "api.ballerinacappuccinalovestungtungtungsahur.com",
    ):
        vidlove["domain_substitutions"][old] = "api.vidlove.cc"
    recipe = {
        "proofModelVersion": 5,
        "allowGenericFallback": False,
        "base": "https://api.vidlove.cc",
        "referer": "https://player.vidlove.cc/",
        "origin": "https://player.vidlove.cc",
        "directRoute": "/{media}?id={tmdbId}&mode=json&season={season}&episode={episode}",
        "directRequest": {
            "method": "GET",
            "headers": {
                "Accept": "application/json,text/plain,*/*",
                "Origin": "https://player.vidlove.cc",
                "Referer": "https://player.vidlove.cc/",
            },
        },
        "requestHeaders": {
            "Accept": "application/json,text/plain,*/*",
            "Origin": "https://player.vidlove.cc",
            "Referer": "https://player.vidlove.cc/",
        },
        "playbackHeaders": {
            "Origin": "https://player.vidlove.cc",
        },
        "sources": [],
        "requestTimeoutMs": 8000,
        "minStreamsBeforeStop": 1,
    }
    vidlove["candidate_api_recipe"] = copy.deepcopy(recipe)
    vidlove["api_recipe"] = copy.deepcopy(recipe)
    add_note(vidlove, "2026-09-16 live contract: api.vidlove.cc movie/tv JSON returns source.url; with player.vidlove.cc Referer that URL responds 200 application/vnd.apple.mpegurl. Subtitle URLs are excluded by a provider-local source selector.")

    vidfast = patches["vidfast"]
    add_script(vidfast, VIDFAST_EMBED)
    vidfast["capability"] = "iframe_player"
    vidfast["official_site"] = "https://vidfast.vc"
    vidfast["published_types"] = ["movie", "tv"]
    vidfast["preserve_embed_urls"] = True
    routes = [str(v) for v in vidfast.get("learned_routes") or []]
    for route in ("/movie/{tmdbId}", "/tv/{tmdbId}/{season}/{episode}"):
        if route not in routes:
            routes.append(route)
    vidfast["learned_routes"] = routes
    add_note(vidfast, "Current documented VidFast routes are /movie/{tmdbId} and /tv/{tmdbId}/{season}/{episode}; provider-local fallback verifies the HTML player before returning the embed URL and does not invent a direct-media URL.")

    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    changed = before != after
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    value = load()
    patches = value["provider_patches"]
    capabilities = value["provider_capabilities"]
    wooka = patches["wookafr"]
    if WOOKA_DECODER not in (wooka.get("provider_lego_scripts") or []):
        raise AssertionError("Wooka showVideo decoder missing")
    if wooka.get("capability") != "mixed_embed_resolver" or wooka.get("preserve_embed_urls") is not True:
        raise AssertionError("Wooka mixed embed contract missing")

    vidlove = patches["vidlove"]
    if VIDLOVE_SELECTOR not in (vidlove.get("provider_lego_scripts") or []):
        raise AssertionError("VidLove source selector missing")
    if vidlove.get("capability") != "api_stream_resolver":
        raise AssertionError("VidLove runtime strategy mismatch")
    if (capabilities.get("vidlove") or {}).get("strategy") != "api_stream_resolver":
        raise AssertionError("VidLove capability strategy mismatch")
    recipe = vidlove.get("api_recipe") or {}
    if recipe.get("base") != "https://api.vidlove.cc":
        raise AssertionError("VidLove API base mismatch")
    if recipe.get("directRoute") != "/{media}?id={tmdbId}&mode=json&season={season}&episode={episode}":
        raise AssertionError("VidLove direct route mismatch")
    if set(str(v) for v in vidlove.get("published_types") or []) != {"movie", "tv"}:
        raise AssertionError("VidLove capability mismatch")

    vidfast = patches["vidfast"]
    if VIDFAST_EMBED not in (vidfast.get("provider_lego_scripts") or []):
        raise AssertionError("VidFast current embed Lego missing")
    routes = set(str(v) for v in vidfast.get("learned_routes") or [])
    if not {"/movie/{tmdbId}", "/tv/{tmdbId}/{season}/{episode}"}.issubset(routes):
        raise AssertionError("VidFast current routes missing")


def main() -> int:
    changed = patch()
    validate()
    print(f"MAX_REPAIR_CURRENT_CONTRACTS_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

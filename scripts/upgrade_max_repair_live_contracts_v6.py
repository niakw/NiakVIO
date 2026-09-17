#!/usr/bin/env python3
"""Bind V41 residual runtimes with strict ProviderBase v3 ownership.

This supersedes the failed V40 AniKoto overlay approach: AniKoto V3 is a
standalone owned fix and replaces the V2 runtime instead of mutating its bytes.
Sekai and YFlix bindings are re-asserted idempotently because V40 persisted their
override metadata before materialization failed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVR = ROOT / "provider-overrides.json"

ANIKOTO_V3 = "scripts/provider_patches/anikototv_runtime_v3.py"
SEKAI = "scripts/provider_patches/sekai_inline_media_runtime_v1.py"
YFLIX = "scripts/provider_patches/yflix_current_runtime_v2.py"

OLD_ANIKOTO = {
    "scripts/provider_patches/anikototv_runtime_v1.py",
    "scripts/provider_patches/anikototv_runtime_v2.py",
    "scripts/provider_patches/anikototv_megaplay_embed_fallback_v3.py",
}

DEFAULT_MIRRORS = [
    "https://anikototv.to",
    "https://anikoto.cz",
    "https://anikoto.me",
    "https://anikoto.net",
    "https://anikototv.se",
]


def note(row: dict, value: str) -> None:
    notes = [str(x) for x in row.get("notes") or [] if str(x)]
    if value not in notes:
        notes.append(value)
    row["notes"] = notes


def append_once(row: dict, path: str) -> None:
    seq = [str(x) for x in row.get("provider_lego_scripts") or [] if str(x)]
    if path not in seq:
        seq.append(path)
    row["provider_lego_scripts"] = seq


def main() -> int:
    data = json.loads(OVR.read_text(encoding="utf-8"))
    rows = data.get("provider_patches") or {}
    for pid in ("anikototv", "sekai", "yflix", "streamzo"):
        if not isinstance(rows.get(pid), dict):
            raise SystemExit(f"missing provider override: {pid}")

    # AniKoto: replace old/overlay scripts with one standalone V3 owned block.
    anikoto = rows["anikototv"]
    seq = [str(x) for x in anikoto.get("provider_lego_scripts") or [] if str(x)]
    seq = [x for x in seq if x not in OLD_ANIKOTO]
    if ANIKOTO_V3 not in seq:
        seq.append(ANIKOTO_V3)
    anikoto["provider_lego_scripts"] = seq

    opts = anikoto.setdefault("provider_lego_options", {})
    mirrors = None
    for old in OLD_ANIKOTO:
        old_opts = opts.get(old)
        if isinstance(old_opts, dict) and isinstance(old_opts.get("mirrors"), list):
            mirrors = old_opts.get("mirrors")
            break
    for old in OLD_ANIKOTO:
        opts.pop(old, None)
    current = opts.get(ANIKOTO_V3) if isinstance(opts.get(ANIKOTO_V3), dict) else {}
    current = dict(current)
    current["mirrors"] = [str(x).rstrip("/") for x in (mirrors or DEFAULT_MIRRORS) if str(x).startswith(("http://", "https://"))][:5]
    opts[ANIKOTO_V3] = current
    anikoto["preserve_embed_urls"] = True
    anikoto["published_types"] = ["anime"]
    anikoto["route_data_state"] = "repair"
    note(anikoto, "V41 AniKoto uses one standalone V3 owned runtime. MegaPlay plaintext sources remain direct media; encrypted enc responses preserve only the already identity-correlated, HTTP-verified player embed for Core/player handling.")

    # Re-assert V40 Sekai/YFlix bindings idempotently.
    sekai = rows["sekai"]
    append_once(sekai, SEKAI)
    sekai.setdefault("provider_lego_options", {}).setdefault(SEKAI, {"base": "https://sekai.one"})
    sekai["published_types"] = ["anime"]
    sekai["route_data_state"] = "repair"

    yflix = rows["yflix"]
    append_once(yflix, YFLIX)
    yflix.setdefault("provider_lego_options", {}).setdefault(YFLIX, {})
    for key in ("candidate_api_recipe", "api_recipe"):
        recipe = yflix.get(key)
        if isinstance(recipe, dict):
            direct = str(recipe.get("directRoute") or "")
            if "db/flix/find" in direct and "type=movie" in direct:
                recipe.pop("directRoute", None)
            recipe["movieRoute"] = "/db/flix/find?tmdb_id={tmdbId}&type=movie"
            recipe["tvRoute"] = "/db/flix/find?tmdb_id={tmdbId}&type=tv"
            recipe["allowGenericFallback"] = False
    yflix["published_types"] = ["movie", "tv"]
    yflix["route_data_state"] = "repair"

    streamzo = rows["streamzo"]
    note(streamzo, "V41 live requalification uses Jujutsu Kaisen S1E3 because the current upstream page exposes S1E3/S1E6 but not S1E1; catalog absence is not a parser failure.")

    OVR.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("V6_BOUND", {
        "anikototv": anikoto["provider_lego_scripts"],
        "sekai": SEKAI,
        "yflix": YFLIX,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bind the V40 residual current-site contracts without overstating live proof."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVR = ROOT / "provider-overrides.json"

SEKAI = "scripts/provider_patches/sekai_inline_media_runtime_v1.py"
YFLIX = "scripts/provider_patches/yflix_current_runtime_v2.py"
ANIKOTO_V2 = "scripts/provider_patches/anikototv_runtime_v2.py"
ANIKOTO_V3 = "scripts/provider_patches/anikototv_megaplay_embed_fallback_v3.py"


def note(row: dict, value: str) -> None:
    notes = [str(x) for x in row.get("notes") or [] if str(x)]
    if value not in notes:
        notes.append(value)
    row["notes"] = notes


def scripts(row: dict) -> list[str]:
    return [str(x) for x in row.get("provider_lego_scripts") or [] if str(x)]


def append_once(row: dict, path: str) -> None:
    seq = scripts(row)
    if path not in seq:
        seq.append(path)
    row["provider_lego_scripts"] = seq


def main() -> int:
    data = json.loads(OVR.read_text(encoding="utf-8"))
    rows = data.get("provider_patches") or {}
    for pid in ("sekai", "yflix", "anikototv", "streamzo"):
        if not isinstance(rows.get(pid), dict):
            raise SystemExit(f"missing provider override: {pid}")

    sekai = rows["sekai"]
    append_once(sekai, SEKAI)
    opts = sekai.setdefault("provider_lego_options", {})
    opts.setdefault(SEKAI, {"base": "https://sekai.one"})
    sekai["route_data_state"] = "repair"
    note(sekai, "V40 current Sekai authority: locate the title-matched sekai.one catalogue page, parse inline atob host + episode MP4 template without executing upstream JavaScript, and range-verify media before output.")

    yflix = rows["yflix"]
    append_once(yflix, YFLIX)
    opts = yflix.setdefault("provider_lego_options", {})
    opts.setdefault(YFLIX, {})
    # The historical directRoute hard-coded type=movie and can map a TV TMDB id
    # to an unrelated film. Preserve the evidence as candidates, but remove that
    # route from executable recipe authority now that the namespace-aware runtime
    # owns execution.
    for key in ("candidate_api_recipe", "api_recipe"):
        recipe = yflix.get(key)
        if isinstance(recipe, dict):
            direct = str(recipe.get("directRoute") or "")
            if "db/flix/find" in direct and "type=movie" in direct:
                recipe.pop("directRoute", None)
            recipe["movieRoute"] = "/db/flix/find?tmdb_id={tmdbId}&type=movie"
            recipe["tvRoute"] = "/db/flix/find?tmdb_id={tmdbId}&type=tv"
            recipe["allowGenericFallback"] = False
    yflix["route_data_state"] = "repair"
    note(yflix, "V40 namespace correction: movie requests use type=movie and TV requests use type=tv. A TV request must never reuse the numeric TMDB id on the movie namespace (TMDB 1396 otherwise resolves to the unrelated film Mirror).")
    note(yflix, "Current downstream YFlix/1Movies/SolarMovie AJAX frontends are unavailable from the GitHub runner; execution therefore fails closed after the identity-correct enc-dec.app DB stage instead of manufacturing playback proof.")

    anikoto = rows["anikototv"]
    seq = scripts(anikoto)
    seq = [x for x in seq if not x.endswith("anikototv_runtime_v1.py")]
    if ANIKOTO_V2 not in seq:
        seq.append(ANIKOTO_V2)
    if ANIKOTO_V3 not in seq:
        seq.append(ANIKOTO_V3)
    anikoto["provider_lego_scripts"] = seq
    anikoto.setdefault("provider_lego_options", {}).setdefault(ANIKOTO_V3, {})
    anikoto["preserve_embed_urls"] = True
    anikoto["route_data_state"] = "repair"
    note(anikoto, "V40 MegaPlay contract: plaintext sources are used when present; current encrypted enc payloads preserve only the already identity-correlated, HTTP-verified MegaPlay embed for Core player handling. No fake direct HLS is emitted.")

    streamzo = rows["streamzo"]
    note(streamzo, "V40 requalification must use a currently present catalogue episode (Jujutsu Kaisen S1E3 or S2E1); current S1E1 is absent upstream and must not be scored as a parser regression.")

    OVR.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("V5_BOUND", {"sekai": SEKAI, "yflix": YFLIX, "anikototv": [ANIKOTO_V2, ANIKOTO_V3]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

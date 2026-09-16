#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
WOOKA = "scripts/provider_patches/wookafr_current_runtime_v2.py"
ALLANIME = "scripts/provider_patches/allanime_current_runtime_v1.py"


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = value.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider_patches missing")
    for pid in ("wookafr", "allanime"):
        if not isinstance(patches.get(pid), dict):
            raise AssertionError(f"provider patch missing: {pid}")
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


def main() -> int:
    value = load()
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)
    p = value["provider_patches"]

    w = p["wookafr"]
    add_script(w, WOOKA)
    w["official_site"] = "https://wookafr.boston"
    w["capability"] = "mixed_embed_resolver"
    w["preserve_embed_urls"] = True
    routes = [str(v) for v in w.get("learned_routes") or []]
    for route in ("/?s={title}", "/streaming/{category}/{slug}/", "https://lecteurvideo.com/embed.php?id={id}&tp={type}&url={source}"):
        if route not in routes:
            routes.append(route)
    w["learned_routes"] = routes
    add_note(w, "2026-09-16 V26/V27: live Wooka contract is WP search /?s={title} -> /streaming/... detail -> lecteurvideo.com/embed.php -> showVideo(base64). V2 runtime is explicitly wired because the generic ProviderBase route planner did not consume the current search route before fallback.")

    aa = p["allanime"]
    add_script(aa, ALLANIME)
    aa["official_site"] = "https://ww2.aniwatch.fit"
    aa["capability"] = "mixed_embed_resolver"
    aa["preserve_embed_urls"] = True
    aa["published_types"] = ["anime"]
    add_note(aa, "2026-09-16 V26/V27: One Piece search/detail/episode/MegaPlay chain is live. Current runtime now reads Core media context/cache before falling back to _tmdb so title search is not skipped when ProviderBase TMDB projection is unavailable.")

    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    changed = before != after
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    value = load(); p = value["provider_patches"]
    if WOOKA not in [str(v) for v in p["wookafr"].get("provider_lego_scripts") or []]:
        raise AssertionError("Wooka V2 runtime not wired")
    if ALLANIME not in [str(v) for v in p["allanime"].get("provider_lego_scripts") or []]:
        raise AssertionError("AllAnime current runtime missing")
    if set(p["allanime"].get("published_types") or []) != {"anime"}:
        raise AssertionError("AllAnime semantic drift")
    print("MAX_REPAIR_RESIDUAL_RUNTIMES_V5_OK changed=" + str(changed).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

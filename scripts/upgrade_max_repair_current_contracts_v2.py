#!/usr/bin/env python3
"""Wire current AllWish/Flemmix clean-room runtimes without widening semantic lanes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
ALLWISH = "scripts/provider_patches/allwish_current_runtime_v1.py"
FLEMMIX = "scripts/provider_patches/flemmix_current_runtime_v1.py"


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = value.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider_patches missing")
    for pid in ("allwish", "flemmix"):
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


def patch() -> bool:
    value = load()
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)
    patches = value["provider_patches"]

    allwish = patches["allwish"]
    allwish_types_before = list(allwish.get("published_types") or [])
    add_script(allwish, ALLWISH)
    allwish["capability"] = "mixed_embed_resolver"
    allwish["official_site"] = "https://all-wish.me"
    allwish["preserve_embed_urls"] = True
    routes = [str(v) for v in allwish.get("learned_routes") or []]
    for route in (
        "/filter?keyword={title}",
        "/ajax/episode/list/{id}",
        "/ajax/server/list?servers={serverKey}",
        "/ajax/server?get={serverId}",
    ):
        if route not in routes:
            routes.append(route)
    allwish["learned_routes"] = routes
    if list(allwish.get("published_types") or []) != allwish_types_before:
        raise AssertionError("AllWish semantic lanes changed unexpectedly")
    add_note(allwish, "2026-09-16 current contract: title search returns /watch cards with a provider series id; the watch page confirms that id, episode/list yields the requested episode data-ids token, server/list yields per-language server link ids, and ajax/server yields current Mega player embeds. The runtime does not widen published semantic lanes.")

    flemmix = patches["flemmix"]
    flemmix_types_before = list(flemmix.get("published_types") or [])
    add_script(flemmix, FLEMMIX)
    flemmix["capability"] = "mixed_embed_resolver"
    flemmix["official_site"] = "https://flemmix.me"
    flemmix["preserve_embed_urls"] = True
    routes = [str(v) for v in flemmix.get("learned_routes") or []]
    for route in ("/search?q={title}", "/embed/video/{id}?expires={expires}&signature={signature}"):
        if route not in routes:
            routes.append(route)
    flemmix["learned_routes"] = routes
    if list(flemmix.get("published_types") or []) != flemmix_types_before:
        raise AssertionError("Flemmix semantic lanes changed unexpectedly")
    add_note(flemmix, "2026-09-16 current contract: /search?q= returns typed JSON rows with title/year/url; identity-gated details expose short-lived signed /embed/video/... URLs which are preserved dynamically rather than hardcoded. TV traversal remains season/episode scoped and must be proven independently by Labs.")

    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    changed = before != after
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    patches = load()["provider_patches"]
    aw = patches["allwish"]
    fx = patches["flemmix"]
    if ALLWISH not in [str(v) for v in aw.get("provider_lego_scripts") or []]:
        raise AssertionError("AllWish current runtime missing")
    if FLEMMIX not in [str(v) for v in fx.get("provider_lego_scripts") or []]:
        raise AssertionError("Flemmix current runtime missing")
    if aw.get("official_site") != "https://all-wish.me" or aw.get("preserve_embed_urls") is not True:
        raise AssertionError("AllWish current embed contract missing")
    if fx.get("official_site") != "https://flemmix.me" or fx.get("preserve_embed_urls") is not True:
        raise AssertionError("Flemmix current embed contract missing")


def main() -> int:
    before = load()["provider_patches"]
    types_before = {pid: list(before[pid].get("published_types") or []) for pid in ("allwish", "flemmix")}
    changed = patch()
    validate()
    after = load()["provider_patches"]
    for pid in ("allwish", "flemmix"):
        if list(after[pid].get("published_types") or []) != types_before[pid]:
            raise AssertionError(f"{pid} published_types widened")
    print("MAX_REPAIR_CURRENT_CONTRACTS_V2_OK changed=" + str(changed).lower() + " types=" + json.dumps(types_before, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Wire residual live provider runtimes proven during the max-repair campaign."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
ALLANIME = "scripts/provider_patches/allanime_current_runtime_v1.py"
MOVIEBOX = "scripts/provider_patches/moviebox_current_embed_v2.py"


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = value.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider_patches missing")
    for pid in ("allanime", "moviebox"):
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


def set_repair_active(row: dict[str, Any], required: list[str], reason: str) -> None:
    row["route_data_state"] = "on"
    disp = row.get("repair_disposition")
    if not isinstance(disp, dict):
        disp = {"schemaVersion": 1, "authority": "provider-repair-disposition-v1"}
    disp["activationState"] = "enabled"
    disp["activationAuthority"] = "provider-folder-lifecycle"
    disp["quarantined"] = False
    disp["terminalState"] = None
    disp["requiredLanes"] = list(required)
    # Do not invent proof: activation is restored so the real provider probe can run,
    # but completeCapabilityProof remains false until the proof workflow succeeds.
    proven = [str(v) for v in disp.get("provenLanes") or [] if str(v) in required]
    disp["provenLanes"] = proven
    disp["currentVerifiedLanes"] = [str(v) for v in disp.get("currentVerifiedLanes") or [] if str(v) in required]
    disp["missingLanes"] = [v for v in required if v not in set(proven)]
    disp["completeCapabilityProof"] = False
    disp["recoveryStatus"] = "repair"
    codes = [str(v) for v in disp.get("reasonCodes") or [] if str(v)]
    if reason not in codes:
        codes.append(reason)
    disp["reasonCodes"] = codes
    row["repair_disposition"] = disp


def patch() -> bool:
    value = load()
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)
    p = value["provider_patches"]

    aa = p["allanime"]
    add_script(aa, ALLANIME)
    aa["capability"] = "mixed_embed_resolver"
    aa["official_site"] = "https://ww2.aniwatch.fit"
    aa["preserve_embed_urls"] = True
    aa["published_types"] = ["anime"]
    routes = [str(v) for v in aa.get("learned_routes") or []]
    for route in ("/?s={title}", "/{slug}/", "/{slug}-episode-{episode}/"):
        if route not in routes:
            routes.append(route)
    aa["learned_routes"] = routes
    set_repair_active(aa, ["anime"], "current_wordpress_episode_embed_contract_live_pending_real_probe")
    add_note(aa, "2026-09-16 current contract: WordPress search /?s= resolves anime detail pages; episode anchors carry epl-num identity, and current episode pages expose playable MegaPlay/Vidmoly iframes. Jujutsu Kaisen currently misses the catalogue, while One Piece proves the provider transport is alive.")

    mb = p["moviebox"]
    add_script(mb, MOVIEBOX)
    mb["capability"] = "mixed_embed_resolver"
    mb["official_site"] = "https://moviebox.yachts"
    mb["official_api"] = "https://vidsrcme.ru/vs_src.php"
    mb["preserve_embed_urls"] = True
    mb["published_types"] = ["movie", "tv"]
    routes = [str(v) for v in mb.get("learned_routes") or []]
    for route in ("https://vidsrcme.ru/vs_src.php?type=movie&id={tmdbId}", "https://vidsrcme.ru/vs_src.php?type=tv&id={tmdbId}&season={season}&episode={episode}"):
        if route not in routes:
            routes.append(route)
    mb["learned_routes"] = routes
    set_repair_active(mb, ["movie", "tv"], "current_vidsrcme_embed_contract_live_pending_real_probe")
    add_note(mb, "2026-09-16 current contract: vidsrcme vs_src.php returns a current cloudorchestranova embed for both movie and TV. data.vidsrcme.ru stream_urls is encrypted/WASM, so NiakVIO preserves the verified embed instead of implementing brittle decryption or claiming direct media.")

    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    changed = before != after
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    p = load()["provider_patches"]
    aa, mb = p["allanime"], p["moviebox"]
    if ALLANIME not in [str(v) for v in aa.get("provider_lego_scripts") or []]:
        raise AssertionError("AllAnime runtime not wired")
    if set(aa.get("published_types") or []) != {"anime"}:
        raise AssertionError("AllAnime semantic lane drift")
    if aa.get("capability") != "mixed_embed_resolver" or aa.get("preserve_embed_urls") is not True:
        raise AssertionError("AllAnime embed contract missing")
    if MOVIEBOX not in [str(v) for v in mb.get("provider_lego_scripts") or []]:
        raise AssertionError("MovieBox current embed runtime not wired")
    if set(mb.get("published_types") or []) != {"movie", "tv"}:
        raise AssertionError("MovieBox lane drift")
    if (mb.get("repair_disposition") or {}).get("quarantined") is not False:
        raise AssertionError("MovieBox remains quarantined")


def main() -> int:
    changed = patch()
    validate()
    print("MAX_REPAIR_RESIDUAL_RUNTIMES_V4_OK changed=" + str(changed).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
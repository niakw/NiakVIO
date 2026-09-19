#!/usr/bin/env python3
"""Stage current, independently observed contracts for MovieBox + AnikotoTV.

This migration is intentionally provider-DATA/Lego only. Core runtime compatibility,
timeouts, cancellation, HTTP/media fail-closed and final output validation remain
owned globally by Core.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
ANIKOTO = ROOT / "scripts" / "provider_patches" / "anikototv_runtime_v1.py"
MOVIEBOX_LEGO = "scripts/provider_patches/moviebox_vidsrcme_runtime_v1.py"


def patch_anikoto_runtime(text: str) -> str:
    old = 'var search=base+"/search?keyword="+encodeURIComponent(meta.title),page=await get(search,base+"/",false,""),cands=results(page.body,meta);'
    new = 'var search=base+"/ajax/anime/search?keyword="+encodeURIComponent(meta.title),page=await get(search,base+"/",true,""),sd=parsed(page.body),sr=sd&&sd.result,sh=sr&&typeof sr==="object"?s(sr.html):typeof sr==="string"?sr:page.body,cands=results(sh,meta);'
    if new in text:
        return text
    if old not in text:
        raise SystemExit("Anikoto search contract anchor not found")
    return text.replace(old, new, 1)


def main() -> int:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = data.get("provider_patches")
    if not isinstance(patches, dict):
        raise SystemExit("provider_patches missing")

    moviebox = patches.get("moviebox")
    anikoto = patches.get("anikototv")
    if not isinstance(moviebox, dict) or not isinstance(anikoto, dict):
        raise SystemExit("MovieBox/Anikoto patches missing")

    moviebox.update({
        "capability": "api_stream_resolver",
        "official_hub": "https://moviiebox.lol/",
        "official_site": "https://moviebox.yachts",
        "route_data_state": "repair",
        "route_proof_version": 5,
        "learned_routes": [
            "/vs_src.php?type={mediaType}&id={tmdbId}",
            "/vs_src.php?type=tv&id={tmdbId}&season={season}&episode={episode}",
        ],
        "identity_input": {
            "mode": "tmdb_direct",
            "requires_tmdb_before_run": False,
            "required_fields": ["tmdbId", "mediaType"],
        },
        "provider_lego_scripts": [MOVIEBOX_LEGO],
        "provider_lego_options": {
            MOVIEBOX_LEGO: {
                "base": "https://vidsrcme.ru",
                "referer": "https://vidsrcme.ru/",
            }
        },
        "notes": [
            "Current MovieBox browser contract resolves TMDB directly through vidsrcme /vs_src.php and returns JSON src.",
            "The historical non-playable HTML quarantine is superseded only after strict stream-positive proof of this current resolver.",
            "Core owns terminal media probing, identity guard, timeout/cancellation and fail-closed HTTP handling.",
        ],
    })
    moviebox.pop("quarantine_reason", None)
    disp = moviebox.get("repair_disposition")
    if isinstance(disp, dict):
        disp["routeDataState"] = "repair"
        disp["terminalState"] = None
        disp["quarantined"] = False
        disp["recoveryStatus"] = "current-contract-staged"
        disp["reasonCodes"] = ["declared_lane_unproven", "current_contract_staged"]
        disp["currentVerifiedLanes"] = []
        disp["provenLanes"] = []
        disp["missingLanes"] = ["movie", "tv"]
        disp["completeCapabilityProof"] = False

    routes = [
        "/ajax/anime/search?keyword={query}",
        "/watch/{slug}",
        "/ajax/episode/list/{id}",
        "/ajax/server/list?servers={id}",
        "/ajax/server?get={id}",
    ]
    anikoto["learned_routes"] = routes
    candidates = [str(v) for v in (anikoto.get("candidate_learned_routes") or []) if str(v)]
    candidates = [v for v in candidates if v != "/search?keyword={query}"]
    for v in routes:
        if v not in candidates:
            candidates.insert(0 if v.startswith("/ajax/anime/search") else len(candidates), v)
    anikoto["candidate_learned_routes"] = candidates
    notes = anikoto.get("notes") if isinstance(anikoto.get("notes"), list) else []
    note = "Current Anikoto search authority is /ajax/anime/search?keyword={query}; response JSON carries result.html and must be parsed before candidate extraction."
    if note not in notes:
        notes.append(note)
    anikoto["notes"] = notes

    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    before = ANIKOTO.read_text(encoding="utf-8")
    after = patch_anikoto_runtime(before)
    ANIKOTO.write_text(after, encoding="utf-8")
    print(
        "MOVIEBOX_ANIKOTO_CURRENT_CONTRACT_V1_OK "
        f"moviebox_lego=1 anikoto_runtime_changed={after != before}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/webflix_fastflux_runtime_v1.py"
MARKER = "NIAKVIO_WEBFLIX_FASTFLUX_ORACLE_V1"

def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("webflix"), dict):
        raise AssertionError("webflix provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["webflix"]

    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts

    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    options[LEGO] = {"base": "https://webflix.art", "name": "Webflix"}
    row["provider_lego_options"] = options
    row["capability"] = "direct_media"
    row["learned_routes"] = [
        "/api/fastflux?type=movie&tmdb_id={tmdbId}",
        "/api/fastflux?type=episode&tmdb_id={tmdbId}&season={season}&episode={episode}",
        "/api/series-season-discovery?tmdb_id={tmdbId}",
    ]
    row["identity_input"] = {
        "mode": "tmdb_direct",
        "requires_tmdb_before_run": True,
        "required_fields": ["tmdbId", "mediaType"],
    }

    notes = row.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    note = (
        f"{MARKER}: Mac residential oracle proved FastFlux movie and episode APIs return "
        "structured exact identity plus direct MP4 media for Interstellar and Breaking Bad S1E1."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes

    capabilities = data.get("provider_capabilities")
    if not isinstance(capabilities, dict):
        capabilities = {}
        data["provider_capabilities"] = capabilities
    cap = capabilities.get("webflix")
    if not isinstance(cap, dict):
        cap = {}
    cap.update({
        "strategy": "direct_media",
        "validation": "residential_runtime_oracle",
        "allow_html_url": False,
        "requires_direct_media": True,
        "observed_origins": ["https://webflix.art", "https://cdn80.zen-blk.store"],
        "catalogue_types": ["movie", "tv"],
    })
    capabilities["webflix"] = cap

    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)

def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("webflix") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("Webflix runtime Lego missing")
    if row.get("capability") != "direct_media":
        raise AssertionError(f"unexpected Webflix capability: {row.get('capability')!r}")
    routes = row.get("learned_routes") or []
    if not any("fastflux?type=movie" in str(v) for v in routes):
        raise AssertionError("Webflix movie FastFlux route missing")
    if not any("fastflux?type=episode" in str(v) for v in routes):
        raise AssertionError("Webflix episode FastFlux route missing")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("Webflix oracle marker missing")

def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WEBFLIX_FASTFLUX_REGISTRATION_OK changed={str(changed).lower()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

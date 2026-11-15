#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/movy_wecollege_runtime_v1.py"
MARKER = "NIAKVIO_MOVY_WECOLLEGE_ORACLE_V1"

ROUTES = [
    "/seed?mediaId={tmdbId}",
    "/miami/sources",
    "/boise/sources",
    "/nashville/sources",
]


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("movy"), dict):
        raise AssertionError("movy provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["movy"]

    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts

    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    options[LEGO] = {
        "api_base": "https://api.wecollege.net",
        "origin": "https://www.movy.sx",
        "referer": "https://www.movy.sx/",
        "double_encode_title": True,
        "endpoints": [
            {"label": "Miami", "path": "miami/sources"},
            {"label": "Boise", "path": "boise/sources"},
            {"label": "Nashville", "path": "nashville/sources"},
        ],
    }
    row["provider_lego_options"] = options
    row["capability"] = "api_stream_resolver"
    row["official_site"] = "https://www.movy.sx"
    row["official_api"] = "https://api.wecollege.net"
    row["learned_routes"] = list(ROUTES)
    row["identity_input"] = {
        "mode": "external_id",
        "requires_tmdb_before_run": True,
        "required_fields": ["tmdbId", "mediaType", "title", "year", "imdbId"],
    }

    notes = row.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    note = (
        f"{MARKER}: physical Mac/Brave proved Movy uses the reusable Wings family: "
        "seed?mediaId=<tmdb> followed by Miami/Boise/Nashville sources. "
        "VisionQuest S01E01 reached 1080p HLS and Fahrenheit 451 (2018) reached "
        "terminal HLS through Nashville. Seed and terminal URLs remain ephemeral."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes

    caps = data.get("provider_capabilities")
    if not isinstance(caps, dict):
        caps = {}
        data["provider_capabilities"] = caps
    cap = caps.get("movy")
    if not isinstance(cap, dict):
        cap = {}
    cap.update({
        "strategy": "api_stream_resolver",
        "validation": "physical_mac_terminal_oracle_2026_11_15",
        "allow_html_url": False,
        "requires_direct_media": True,
        "observed_origins": [
            "https://www.movy.sx",
            "https://api.wecollege.net",
        ],
        "catalogue_types": ["movie", "tv", "anime"],
    })
    caps["movy"] = cap
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("movy") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("Movy WeCollege runtime Lego missing")
    options = (row.get("provider_lego_options") or {}).get(LEGO) or {}
    if options.get("api_base") != "https://api.wecollege.net":
        raise AssertionError("Movy API base drift")
    if options.get("double_encode_title") is not True:
        raise AssertionError("Movy double title encoding drift")
    paths = [str(x.get("path") or "") for x in options.get("endpoints") or [] if isinstance(x, dict)]
    if paths != ["miami/sources", "boise/sources", "nashville/sources"]:
        raise AssertionError(f"Movy endpoint order drift: {paths!r}")
    identity = row.get("identity_input") or {}
    if identity.get("mode") != "external_id" or identity.get("requires_tmdb_before_run") is not True:
        raise AssertionError(f"Movy identity preflight drift: {identity!r}")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("Movy physical Mac oracle marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MOVY_WECOLLEGE_REGISTRATION_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

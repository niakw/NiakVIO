#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/chillflix_tmdb_direct_embed_runtime_v1.py"
MARKER = "NIAKVIO_CHILLFLIX_TMDB_DIRECT_EMBED_ORACLE_V1"


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("chillflix"), dict):
        raise AssertionError("chillflix provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["chillflix"]

    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts

    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    options[LEGO] = {
        "provider": "chillflix",
        "name": "Chillflix",
        "siteBase": "https://www.chillflix.lol",
        "searchTemplate": "/search?q={query}",
        "embedBase": "https://www.chillflix.pw",
        "movieEmbedTemplate": "/embed/movie/{tmdbId}",
        "tvEmbedTemplate": "/embed/tv/{tmdbId}/{season}/{episode}",
        "parentOriginParam": "parent_origin",
        "maxDepth": 2,
        "maxStreams": 8,
    }
    row["provider_lego_options"] = options

    # The old rows were fixed TV identities, not reusable request plans.
    row["learned_routes"] = ["/search?q={query}"]
    row["identity_input"] = {
        "mode": "catalog_search",
        "requires_tmdb_before_run": True,
        "required_fields": ["tmdbId", "mediaType", "title"],
    }

    notes = row.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    note = (
        f"{MARKER}: residential oracle proved /search?q={{query}} exposes exact "
        "data-id/data-type TMDB cards and site JS maps movie/tv TMDB ids to "
        "chillflix.pw /embed/movie/{tmdbId} and /embed/tv/{tmdbId}/{season}/{episode}. "
        "Hard-coded /tv/291507 and /tv/303044 routes are forbidden because they "
        "returned unrelated identity (The Body for an Interstellar request)."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("chillflix") or {}
    if row.get("learned_routes") != ["/search?q={query}"]:
        raise AssertionError(f"unexpected Chillflix routes: {row.get('learned_routes')}")
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("generic TMDB direct-embed Lego missing")
    options = (row.get("provider_lego_options") or {}).get(LEGO) or {}
    expected = {
        "siteBase": "https://www.chillflix.lol",
        "embedBase": "https://www.chillflix.pw",
        "movieEmbedTemplate": "/embed/movie/{tmdbId}",
        "tvEmbedTemplate": "/embed/tv/{tmdbId}/{season}/{episode}",
    }
    for key, value in expected.items():
        if options.get(key) != value:
            raise AssertionError(f"{key} drift: {options.get(key)!r}")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("Chillflix oracle marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CHILLFLIX_TMDB_DIRECT_EMBED_REGISTRATION_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

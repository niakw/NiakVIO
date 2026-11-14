#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/watchott_tmdb_iframe_runtime_v1.py"
MARKER = "NIAKVIO_WATCHOTT_TMDB_IFRAME_ORACLE_V1"

def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("watchott"), dict):
        raise AssertionError("watchott provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["watchott"]

    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts

    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    options[LEGO] = {
        "base": "https://watchott.org",
        "name": "WatchOTT",
        "maxDepth": 2,
        "maxStreams": 6,
    }
    row["provider_lego_options"] = options
    row["capability"] = "iframe_player"
    row["learned_routes"] = [
        "/play?id={tmdbId}&type=movie",
        "/play?id={tmdbId}&type=tv&season={season}&episode={episode}",
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
        f"{MARKER}: residential Mac proved server-rendered movie/TV identity on /play "
        "and an exact cinesrc.st iframe for Interstellar TMDB 157336; runtime validates "
        "rendered title and season/episode before bounded iframe-to-terminal traversal."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes

    capabilities = data.get("provider_capabilities")
    if not isinstance(capabilities, dict):
        capabilities = {}
        data["provider_capabilities"] = capabilities
    cap = capabilities.get("watchott")
    if not isinstance(cap, dict):
        cap = {}
    cap.update({
        "strategy": "iframe_player",
        "validation": "residential_runtime_oracle_pending_terminal",
        "allow_html_url": True,
        "requires_direct_media": False,
        "observed_origins": ["https://watchott.org", "https://cinesrc.st"],
    })
    capabilities["watchott"] = cap

    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)

def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("watchott") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("WatchOTT runtime Lego missing")
    if row.get("capability") != "iframe_player":
        raise AssertionError(f"unexpected WatchOTT capability: {row.get('capability')!r}")
    expected = [
        "/play?id={tmdbId}&type=movie",
        "/play?id={tmdbId}&type=tv&season={season}&episode={episode}",
    ]
    if row.get("learned_routes") != expected:
        raise AssertionError(f"unexpected WatchOTT routes: {row.get('learned_routes')!r}")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("WatchOTT oracle marker missing")

def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WATCHOTT_TMDB_IFRAME_REGISTRATION_OK changed={str(changed).lower()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

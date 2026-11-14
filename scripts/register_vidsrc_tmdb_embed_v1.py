#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/vidsrc_tmdb_embed_runtime_v1.py"
MARKER = "NIAKVIO_VIDSRC_TMDB_EMBED_ORACLE_V1"

ROUTES = [
    "/vs_src.php?type=movie&id={tmdbId}",
    "/vs_src.php?type=tv&id={tmdbId}&season={season}&episode={episode}",
]

def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("vidsrc"), dict):
        raise AssertionError("vidsrc provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["vidsrc"]

    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts

    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    options[LEGO] = {
        "base": "https://vidsrc.sh",
        "name": "VidSrc",
        "maxDepth": 3,
        "maxStreams": 8,
    }
    row["provider_lego_options"] = options
    row["capability"] = "api_stream_resolver"
    row["official_site"] = "https://vidsrc.sh/"
    row["official_api"] = "https://vidsrc.sh/vs_src.php"
    row["learned_routes"] = list(ROUTES)
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
        f"{MARKER}: residential Mac proved JSON /vs_src.php movie and TV endpoints "
        "bind exact TMDB and S/E identity to an ephemeral signed player; runtime "
        "validates that signed player path before bounded terminal traversal."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes

    capabilities = data.get("provider_capabilities")
    if not isinstance(capabilities, dict):
        capabilities = {}
        data["provider_capabilities"] = capabilities
    cap = capabilities.get("vidsrc")
    if not isinstance(cap, dict):
        cap = {}
    cap.update({
        "strategy": "api_stream_resolver",
        "validation": "residential_runtime_oracle_pending_terminal",
        "allow_html_url": False,
        "requires_direct_media": True,
        "observed_origins": ["https://vidsrc.sh", "https://stellarconductornexus.com"],
        "catalogue_types": ["movie", "tv"],
    })
    capabilities["vidsrc"] = cap
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)

def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("vidsrc") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("VidSrc runtime Lego missing")
    if row.get("capability") != "api_stream_resolver":
        raise AssertionError(f"unexpected VidSrc capability: {row.get('capability')!r}")
    if row.get("learned_routes") != ROUTES:
        raise AssertionError(f"unexpected VidSrc routes: {row.get('learned_routes')!r}")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("VidSrc oracle marker missing")

def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"VIDSRC_TMDB_EMBED_REGISTRATION_OK changed={str(changed).lower()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

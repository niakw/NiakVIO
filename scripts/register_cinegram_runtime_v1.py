#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/cinegram_runtime_v1.py"
MARKER = "NIAKVIO_CINEGRAM_RUNTIME_ORACLE_V1"


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("cinegram"), dict):
        raise AssertionError("cinegram provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["cinegram"]

    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts

    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    current = options.get(LEGO)
    if not isinstance(current, dict):
        current = {}
    current.setdefault("base", "https://cinegram.tv")
    current.setdefault("provider", "cinegram")
    current.setdefault("name", "Cinegram")
    current.setdefault("maxStreams", 8)
    options[LEGO] = current
    row["provider_lego_options"] = options

    routes = [
        value
        for value in (row.get("learned_routes") or [])
        if isinstance(value, dict)
        and str(value.get("url") or "")
        not in {
            "https://cinegram.tv/?s={query}",
            "https://cinegram.tv/index.php?do=search&subaction=search&story={query}",
        }
    ]
    route = {
        "method": "GET",
        "url": "https://cinegram.tv/index.php?menu=search&query={query}",
        "role": "search",
        "source": "manual_residential_oracle",
        "identityAware": True,
    }
    if not any(str(value.get("url") or "") == route["url"] for value in routes):
        routes.append(route)
    row["learned_routes"] = routes

    notes = row.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    note = (
        f"{MARKER}: residential oracle observed current GET search form "
        "index.php?menu=search&query={query}, exact title/year detail selection, "
        "and inline /ajax/cinemov.php?t=<token> movie player request."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("cinegram") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("cinegram runtime Lego missing")
    options = (row.get("provider_lego_options") or {}).get(LEGO) or {}
    if options.get("base") != "https://cinegram.tv":
        raise AssertionError("cinegram base drift")
    urls = {
        str(value.get("url") or "")
        for value in (row.get("learned_routes") or [])
        if isinstance(value, dict)
    }
    if "https://cinegram.tv/index.php?menu=search&query={query}" not in urls:
        raise AssertionError("current Cinegram search route missing")
    if "https://cinegram.tv/?s={query}" in urls:
        raise AssertionError("stale Cinegram wordpress route retained")
    if "https://cinegram.tv/index.php?do=search&subaction=search&story={query}" in urls:
        raise AssertionError("stale Cinegram DLE route retained")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("Cinegram oracle marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CINEGRAM_RUNTIME_V1_REGISTRATION_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

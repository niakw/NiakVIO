#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/french_manga_dle_runtime_v1.py"
MARKER = "NIAKVIO_FRENCH_MANGA_DLE_REGISTRATION_V1"
CONFIG = {
    "base": "https://w16.french-manga.net",
    "provider": "french-manga",
    "name": "French-Manga",
    "max_streams": 6,
}


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("french-manga"), dict):
        raise AssertionError("french-manga provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["french-manga"]
    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts
    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    options[LEGO] = dict(CONFIG)
    row["provider_lego_options"] = options
    row["proof_search_bases"] = [CONFIG["base"]]
    notes = row.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    note = (
        f"{MARKER}: live reverse-order parity must prove French-Manga's DLE search-item "
        "transport before this registration is retained."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("french-manga") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("french-manga DLE Lego missing")
    actual = (row.get("provider_lego_options") or {}).get(LEGO) or {}
    for key, value in CONFIG.items():
        if actual.get(key) != value:
            raise AssertionError(f"french-manga DLE option drift {key}: {actual.get(key)!r} != {value!r}")
    if row.get("proof_search_bases") != [CONFIG["base"]]:
        raise AssertionError("french-manga proof_search_bases drift")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("french-manga registration marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"FRENCH_MANGA_DLE_REGISTRATION_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

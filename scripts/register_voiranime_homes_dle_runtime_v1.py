#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/voiranime_homes_dle_runtime_v1.py"
MARKER = "NIAKVIO_VOIRANIME_HOMES_DLE_REGISTRATION_V1"
CONFIG = {
    "base": "https://voiranime.homes",
    "provider": "voiranime-homes",
    "name": "VoirAnime Homes",
    "max_streams": 6,
}


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("voiranime-homes"), dict):
        raise AssertionError("voiranime-homes provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["voiranime-homes"]
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
    note = f"{MARKER}: reverse-order terminal parity on Dan Da Dan S01E01 is required before retaining this runtime."
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("voiranime-homes") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("voiranime-homes DLE Lego missing")
    actual = (row.get("provider_lego_options") or {}).get(LEGO) or {}
    for key, value in CONFIG.items():
        if actual.get(key) != value:
            raise AssertionError(f"voiranime-homes DLE option drift {key}: {actual.get(key)!r} != {value!r}")
    if row.get("proof_search_bases") != [CONFIG["base"]]:
        raise AssertionError("voiranime-homes proof_search_bases drift")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("voiranime-homes registration marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"VOIRANIME_HOMES_DLE_REGISTRATION_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

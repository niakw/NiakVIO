#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/neko_sama_runtime_v1.py"
MARKER = "NIAKVIO_NEKO_SAMA_SEARCH_SEASON_EPLISTER_REGISTRATION_V2"


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("neko-sama"), dict):
        raise AssertionError("neko-sama provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["neko-sama"]
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
    current.setdefault("base", "https://animes-sama.su")
    current.setdefault("provider", "neko-sama")
    current.setdefault("name", "Neko-Sama")
    options[LEGO] = current
    row["provider_lego_options"] = options
    notes = row.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    note = (
        f"{MARKER}: reverse-order terminal parity on Jujutsu Kaisen S01E01 is required; "
        "runtime follows search -> franchise season/saga -> eplister -> server-group/loadMi."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("neko-sama") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("neko-sama runtime Lego missing")
    options = (row.get("provider_lego_options") or {}).get(LEGO) or {}
    if options.get("base") != "https://animes-sama.su":
        raise AssertionError("neko-sama base drift")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("neko-sama v2 registration marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NEKO_SAMA_RUNTIME_V2_REGISTRATION_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

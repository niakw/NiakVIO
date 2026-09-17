#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
LEGO = "scripts/provider_patches/kehflix_anime_runtime_v1.py"
MARKER = "NIAKVIO_KEHFLIX_ANIME_RUNTIME_REGISTRATION_V1"


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("kehflix"), dict):
        raise AssertionError("kehflix provider patch missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    row = patches["kehflix"]
    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts
    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    cfg = options.get(LEGO)
    if not isinstance(cfg, dict):
        cfg = {}
    cfg.setdefault("base", "")
    cfg.setdefault("targetStreams", 4)
    options[LEGO] = cfg
    row["provider_lego_options"] = options
    notes = row.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    note = (
        f"{MARKER}: semantic anime uses the current signed title/episode API; "
        "same-origin gateway rows and exact episode-correlated players are prioritized, "
        "while movie/tv delegate to the existing native ProviderBase route."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get("kehflix") or {}
    if LEGO not in (row.get("provider_lego_scripts") or []):
        raise AssertionError("kehflix anime runtime Lego missing")
    cfg = ((row.get("provider_lego_options") or {}).get(LEGO) or {})
    if int(cfg.get("targetStreams") or 0) != 4:
        raise AssertionError("kehflix anime targetStreams drift")
    if MARKER not in json.dumps(row, ensure_ascii=False):
        raise AssertionError("kehflix anime registration marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"KEHFLIX_ANIME_RUNTIME_V1_REGISTRATION_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

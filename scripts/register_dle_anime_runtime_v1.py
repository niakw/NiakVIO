#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
MARKER = "NIAKVIO_DLE_ANIME_RUNTIME_REGISTRATION_V1"
TARGETS = {
    "french-manga": {
        "lego": "scripts/provider_patches/french_manga_dle_runtime_v1.py",
        "base": "https://w16.french-manga.net",
        "provider": "french-manga",
        "name": "French-Manga",
        "max_streams": 6,
    },
    "voiranime-homes": {
        "lego": "scripts/provider_patches/voiranime_homes_dle_runtime_v1.py",
        "base": "https://voiranime.homes",
        "provider": "voiranime-homes",
        "name": "VoirAnime Homes",
        "max_streams": 6,
    },
}
GENERIC_LEGO = "scripts/provider_patches/dle_anime_runtime_v1.py"


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider_patches missing")
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    for pid, target in TARGETS.items():
        row = patches.get(pid)
        if not isinstance(row, dict):
            raise AssertionError(f"provider patch missing: {pid}")
        lego = target["lego"]
        cfg = {k: v for k, v in target.items() if k != "lego"}
        scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v).strip()]
        scripts = [v for v in scripts if v != GENERIC_LEGO]
        if lego not in scripts:
            scripts.append(lego)
        row["provider_lego_scripts"] = scripts
        options = row.get("provider_lego_options")
        if not isinstance(options, dict):
            options = {}
        options.pop(GENERIC_LEGO, None)
        options[lego] = dict(cfg)
        row["provider_lego_options"] = options
        row["proof_search_bases"] = [cfg["base"]]
        notes = row.get("notes")
        if isinstance(notes, str):
            notes = [notes]
        elif not isinstance(notes, list):
            notes = []
        note = (
            f"{MARKER}: exact live parity proves the DLE transport at {cfg['base']} "
            "(search.php -> manga_episodes_api.php -> player); provider-owned facade uses the shared fallback engine."
        )
        if note not in notes:
            notes.append(note)
        row["notes"] = notes
    return before != json.dumps(data, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    patches = data.get("provider_patches") or {}
    for pid, target in TARGETS.items():
        row = patches.get(pid) or {}
        lego = target["lego"]
        cfg = {k: v for k, v in target.items() if k != "lego"}
        scripts = row.get("provider_lego_scripts") or []
        if GENERIC_LEGO in scripts:
            raise AssertionError(f"{pid}: generic ownership Lego must not be registered")
        if lego not in scripts:
            raise AssertionError(f"{pid}: provider-owned DLE Lego missing")
        options = row.get("provider_lego_options") or {}
        if GENERIC_LEGO in options:
            raise AssertionError(f"{pid}: generic DLE options must not remain")
        actual = options.get(lego) or {}
        for key, value in cfg.items():
            if actual.get(key) != value:
                raise AssertionError(f"{pid}: DLE option drift {key}: {actual.get(key)!r} != {value!r}")
        if row.get("proof_search_bases") != [cfg["base"]]:
            raise AssertionError(f"{pid}: proof search base drift")
        if MARKER not in json.dumps(row, ensure_ascii=False):
            raise AssertionError(f"{pid}: registration marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"DLE_ANIME_RUNTIME_REGISTRATION_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
SCRIPT = "scripts/provider_patches/vidrock_runtime_v1.py"


def main() -> int:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = data.setdefault("provider_patches", {})
    row = patches.setdefault("vidrock", {})
    legos = row.get("provider_lego_scripts")
    if not isinstance(legos, list):
        legos = []
    if SCRIPT not in legos:
        legos.append(SCRIPT)
    row["provider_lego_scripts"] = legos
    options = row.get("provider_lego_options")
    if not isinstance(options, dict):
        options = {}
    options[SCRIPT] = {
        "base": "https://vidrock.ru",
        "origin": "https://vidrock.net",
        "referer": "https://vidrock.net/",
        "key_hex": "7f3e9c2a8b5d1f4e6a9c3b7d2e5f8a1c4b6d9e2f5a8c1b4d7e9f2a5c8b1d4e7f",
        "server_order": ["Atlas", "Luna", "Orion", "Astra", "Nova"],
        "max_streams": 5,
    }
    row["provider_lego_options"] = options
    row.setdefault("manifest_overrides", {})["enabled"] = True
    notes = row.get("notes")
    if not isinstance(notes, list):
        notes = []
    note = (
        "VidRock clean-v3 uses the live vidrock.ru TMDB-direct API and decrypts "
        "authenticated AES-256-GCM server tokens in NiakVIO-owned runtime code; "
        "the Cloudflare-blocked vidrock.net API remains knowledge/site authority only."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("VIDROCK_RUNTIME_DATA_WIRED base=https://vidrock.ru lego=1 enabled=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

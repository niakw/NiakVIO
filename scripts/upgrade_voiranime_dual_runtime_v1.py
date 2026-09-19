#!/usr/bin/env python3
"""Wire the proven dual VoirAnime runtime into the canonical `voiranime` provider.

The runtime keeps anime on the .homes DLE authority and uses voir-anime.to only
for the separately proven movie root -> FILM chapter contract. This script does
not alter declared capabilities or enable/disable providers.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
TARGET = "voiranime"
LEGO = "scripts/provider_patches/voiranime_homes_runtime_v1.py"


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    patches = data.setdefault("provider_patches", {})
    row = patches.get(TARGET)
    if not isinstance(row, dict):
        raise SystemExit("missing canonical voiranime provider")
    scripts = [str(x) for x in (row.get("provider_lego_scripts") or []) if str(x).strip()]
    if LEGO not in scripts:
        scripts.append(LEGO)
    row["provider_lego_scripts"] = scripts
    opts = row.setdefault("provider_lego_options", {})
    if not isinstance(opts, dict):
        opts = {}; row["provider_lego_options"] = opts
    current = opts.get(LEGO) if isinstance(opts.get(LEGO), dict) else {}
    current = dict(current)
    current.update({
        "site": "https://voiranime.homes",
        "movie_site": "https://voir-anime.to",
        "language_order": ["vf", "vostfr"],
        "max_streams": 4,
    })
    opts[LEGO] = current
    notes = row.get("notes")
    if isinstance(notes, str): notes = [notes]
    if not isinstance(notes, list): notes = []
    marker = "NIAKVIO_VOIRANIME_DUAL_RUNTIME_V1: canonical voiranime uses .homes DLE for anime and voir-anime.to root->FILM chapter for movie; capabilities unchanged."
    if marker not in notes: notes.append(marker)
    row["notes"] = notes
    patches[TARGET] = row
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("VOIRANIME_DUAL_RUNTIME_V1_OK provider=voiranime lego="+LEGO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

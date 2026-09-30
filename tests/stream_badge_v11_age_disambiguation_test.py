#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
feeds = [
    ROOT / "assets/stream-badges-fusion-v11.json",
    ROOT / "assets/stream-badges-dark-v11.json",
    ROOT / "assets/stream-badges-light-v11.json",
    ROOT / "assets/stream-badges-transparent-v11.json",
]

def compile_pattern(raw: str) -> re.Pattern[str]:
    return re.compile(raw)

for path in feeds:
    payload = json.loads(path.read_text(encoding="utf-8"))
    filters = {row["id"]: row for row in payload.get("filters") or [] if isinstance(row, dict) and row.get("id")}
    generic = compile_pattern(filters["age-12"]["pattern"])
    french = compile_pattern(filters["age-fr-12"]["pattern"])

    assert generic.search("12+")
    assert generic.search("Age 12+")
    assert not generic.search("FR 12+")
    assert not generic.search("⏱️ 1h 30 • FR 12+")
    assert french.search("FR 12+")
    assert french.search("⏱️ 1h 30 • FR 12+")

print("STREAM_BADGE_V11_AGE_DISAMBIGUATION_OK")

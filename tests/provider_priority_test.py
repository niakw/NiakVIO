#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ["anime-sama", "purstream", "goated"]
for relative in ("manifest.json", "vf/manifest.json"):
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    ids = [str(row.get("id") or "").strip().casefold() for row in payload.get("scrapers", [])[:3]]
    assert ids == EXPECTED, f"{relative}: expected {EXPECTED}, got {ids}"
print("provider priority tests passed")

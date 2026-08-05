#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
main = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
vf = json.loads((ROOT / "vf" / "manifest.json").read_text(encoding="utf-8"))
main_by_id = {str(row.get("id") or "").casefold(): row for row in main.get("scrapers", [])}

functional_fields = (
    "id",
    "version",
    "filename",
    "enabled",
    "supportedTypes",
    "hasSettings",
    "formats",
    "supportedFormats",
    "contentLanguage",
    "supportsExternalPlayer",
    "limited",
    "disabledPlatforms",
    "supportedPlatforms",
)

errors: list[str] = []
for row in vf.get("scrapers", []):
    canonical = str(row.get("id") or "").casefold()
    source = main_by_id.get(canonical)
    if source is None:
        errors.append(f"VF provider absent from principal: {canonical}")
        continue
    for field in functional_fields:
        if row.get(field) != source.get(field):
            errors.append(f"{canonical}:{field}: vf={row.get(field)!r} main={source.get(field)!r}")

if vf.get("version") != main.get("version"):
    errors.append(f"manifest version mismatch: vf={vf.get('version')} main={main.get('version')}")

if errors:
    raise SystemExit("VF projection validation failed:\n- " + "\n- ".join(errors))
print(f"VF projection validation passed ({len(vf.get('scrapers', []))} providers)")

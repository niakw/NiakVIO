#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
main = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
vf = json.loads((ROOT / "vf/manifest.json").read_text(encoding="utf-8"))

main_by_id = {str(row.get("id", "")).casefold(): row for row in main.get("scrapers", []) if isinstance(row, dict)}
fields = (
    "version",
    "enabled",
    "supportedTypes",
    "formats",
    "contentLanguage",
    "hasSettings",
    "supportsExternalPlayer",
    "disabledPlatforms",
)
errors: list[str] = []

assert main.get("name") == "NiakVIO", main.get("name")
assert vf.get("name") == "NiakVIO — VF uniquement", vf.get("name")
missing_logos = [
    str(row.get("id") or "")
    for row in main.get("scrapers", [])
    if isinstance(row, dict) and not str(row.get("logo") or "").strip()
]
assert not missing_logos, f"providers missing logo metadata: {missing_logos}"
for row in vf.get("scrapers", []):
    if not isinstance(row, dict):
        continue
    cid = str(row.get("id", "")).casefold()
    parent = main_by_id.get(cid)
    if parent is None:
        errors.append(f"{cid}: missing from general manifest")
        continue
    expected_filename = "../" + str(parent.get("filename", ""))
    if row.get("filename") != expected_filename:
        errors.append(f"{cid}: stale filename {row.get('filename')!r} != {expected_filename!r}")
    for field in fields:
        if row.get(field) != parent.get(field):
            errors.append(f"{cid}: stale {field}: vf={row.get(field)!r} general={parent.get(field)!r}")

if errors:
    raise SystemExit("VF/general manifest metadata drift:\n- " + "\n- ".join(errors))
print(f"VF/general manifest metadata consistency passed ({len(vf.get('scrapers', []))} VF providers)")

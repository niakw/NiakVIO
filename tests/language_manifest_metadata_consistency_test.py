#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_manifest_projection_rows import synced_vf

main = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
vf = json.loads((ROOT / "vf" / "manifest.json").read_text(encoding="utf-8"))
sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))

assert sources.get("repository", {}).get("name") == "NiakVIO", sources.get("repository", {}).get("name")
assert main.get("name") == f"NiakVIO v{main.get('version')}", main.get("name")
assert vf.get("name") == f"NiakVIO v{vf.get('version')} — VF uniquement", vf.get("name")
assert main.get("version") == vf.get("version"), (main.get("version"), vf.get("version"))

missing_global_logos = [
    str(row.get("id") or "")
    for row in main.get("scrapers", [])
    if isinstance(row, dict) and not str(row.get("logo") or "").strip()
]
missing_vf_logos = [
    str(row.get("id") or "")
    for row in vf.get("scrapers", [])
    if isinstance(row, dict) and not str(row.get("logo") or "").strip()
]
assert not missing_global_logos, f"Global providers missing logo metadata: {missing_global_logos}"
assert not missing_vf_logos, f"France providers missing logo metadata: {missing_vf_logos}"

expected = synced_vf(main, vf, root=ROOT)
if vf != expected:
    actual_ids = [str(row.get("id") or "") for row in vf.get("scrapers", []) if isinstance(row, dict)]
    expected_ids = [str(row.get("id") or "") for row in expected.get("scrapers", []) if isinstance(row, dict)]
    raise SystemExit(
        "VF projection metadata drift from Global+France catalogue authority: "
        f"actual={len(actual_ids)} expected={len(expected_ids)}"
    )

global_ids = {
    str(row.get("id") or "").casefold()
    for row in main.get("scrapers", [])
    if isinstance(row, dict)
}
vf_ids = {
    str(row.get("id") or "").casefold()
    for row in vf.get("scrapers", [])
    if isinstance(row, dict)
}
france_only = sorted(vf_ids - global_ids)
assert france_only, "France-only projection must remain first-class and must not leak into Global"

print(
    "VF projection metadata consistency passed "
    f"vf={len(vf_ids)} france_only={len(france_only)} authority=Global+provider_catalog"
)

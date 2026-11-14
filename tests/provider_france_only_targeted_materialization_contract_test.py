#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "materialize_provider_v3_one.py").read_text(encoding="utf-8")
catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
global_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

for marker in (
    'PROVIDER_CATALOG = ROOT / "provider_catalog.json"',
    'entry_authority = "france-only-catalog"',
    'projections.get("vf") is not True',
    'projections.get("general") is not False',
    'allmat.write_json(PROVIDER_CATALOG, catalog)',
    '"entryAuthority": entry_authority',
    'entry_authority == "france-only-catalog"',
    'value.startswith("scripts/provider_patches/")',
    'identity.get("requires_tmdb_before_run") is True',
    '{"tmdbId", "mediaType"} <= required_identity',
    'if not isinstance(static_row, dict):',
    'if not preserve_structured_data:',
    'projection-only DATA lacks executable plan',
    'projection-only DATA lacks identity execution plan',
):
    assert marker in source, marker

global_ids = {
    str(row.get("id") or "").strip().casefold()
    for row in global_manifest.get("scrapers") or []
    if isinstance(row, dict)
}
france_only = []
for record in catalog.get("providers") or []:
    if not isinstance(record, dict):
        continue
    proj = record.get("projections") or {}
    row = record.get("scraper") or {}
    if proj.get("vf") is True and proj.get("general") is False:
        cid = str(record.get("canonicalId") or row.get("id") or "").strip().casefold()
        assert cid
        assert cid not in global_ids, cid
        france_only.append(cid)

assert "webflix" in france_only
print(f"FRANCE_ONLY_TARGETED_MATERIALIZATION_CONTRACT_OK providers={len(france_only)}")

#!/usr/bin/env python3
"""Regression: Learning baseline must cover the Global + France catalogue union."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import discover_candidates as discovery  # noqa: E402


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    catalog = {
        "providers": [
            {
                "canonicalId": "global-demo",
                "scraper": {"id": "GLOBAL_DEMO", "filename": "providers/global.js", "enabled": True},
                "projections": {"general": True, "vf": True},
            },
            {
                "canonicalId": "france-only",
                "scraper": {"id": "FRANCE_ONLY", "filename": "../providers/france.js", "enabled": True},
                "projections": {"general": False, "vf": True},
            },
            {
                "canonicalId": "unprojected",
                "scraper": {"id": "UNPROJECTED", "filename": "providers/no.js", "enabled": True},
                "projections": {"general": False, "vf": False},
            },
        ]
    }
    (root / "provider_catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    rows = discovery.local_catalog_baseline_entries(root)
    assert [row["id"] for row in rows] == ["global-demo", "france-only"], rows
    assert rows[1]["filename"] == "providers/france.js"
    assert rows[1]["_catalog_projections"] == {"general": False, "vf": True}

# Real-repository invariant: every active France-only local provider is present
# in the discovery baseline. No provider identity is hard-coded in this check.
catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
rows = discovery.local_catalog_baseline_entries(ROOT)
by_id = {row["id"]: row for row in rows}
expected_france = {
    str(record.get("canonicalId") or "").strip().casefold().replace("_", "-")
    for record in catalog.get("providers") or []
    if isinstance(record, dict)
    and isinstance(record.get("scraper"), dict)
    and record["scraper"].get("enabled") is not False
    and isinstance(record.get("projections"), dict)
    and record["projections"].get("general") is False
    and record["projections"].get("vf") is True
    and str(record["scraper"].get("filename") or "").replace("../", "").startswith("providers/")
}
assert expected_france
missing = sorted(expected_france - set(by_id))
assert not missing, f"France-only active providers missing from clean reconstruction baseline: {missing}"
for provider in expected_france:
    assert by_id[provider]["_catalog_projections"] == {"general": False, "vf": True}

source = (ROOT / "scripts" / "discover_candidates.py").read_text(encoding="utf-8")
assert 'published_rows = local_catalog_baseline_entries(ROOT)' in source
assert 'for entry in published_rows:' in source
assert 'published_manifest.get("scrapers", [])' not in source

print(f"Learning catalogue-union clean reconstruction test passed france_only={len(expected_france)}")

# Targeted fast reconstruction must be able to exclude all external upstreams.
source = (ROOT / "scripts" / "discover_candidates.py").read_text(encoding="utf-8")
assert '"--local-catalog-only"' in source
assert 'config = {**config, "upstreams": {}}' in source
workflow = (ROOT / ".github" / "workflows" / "brain-learning-lab.yml").read_text(encoding="utf-8")
assert "args+=(--local-catalog-only)" in workflow
assert workflow.index("args+=(--local-catalog-only)") > workflow.index('if [ "$FAST_HANDOFF" = "true" ]')

#!/usr/bin/env python3
"""Availability must observe the same active Global+France authority as NiakVIO."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import active_provider_ids, projection_active_provider_ids  # noqa: E402

workflow = (ROOT / ".github/workflows/availability.yml").read_text(encoding="utf-8")
stage = (ROOT / "scripts/stage_published.py").read_text(encoding="utf-8")
updater = (ROOT / "scripts/update_availability.py").read_text(encoding="utf-8")

projection = projection_active_provider_ids()
global_only = active_provider_ids()
france_only = projection - global_only

assert france_only, "fixture requires active France-only providers"
assert "python scripts/stage_published.py --projection-union" in workflow
assert 'parser.add_argument(\n        "--projection-union"' in stage
assert 'projection_rows(MANIFEST_PATH, ROOT / "vf" / "manifest.json")' in stage
assert 'if isinstance(row, dict) and row.get("enabled") is not False' in stage
assert "from current_provider_scope import projection_visible_provider_rows" in updater
assert "for original in projection_visible_provider_rows():" in updater
assert "global_original_rows" in updater and "global_updates" in updater
assert "global_removed" in updater
assert 'new_manifest = {**manifest, "scrapers": new_entries}' in updater

print(
    "AVAILABILITY_PROJECTION_UNION_CONTRACT_OK "
    f"active={len(projection)} global={len(global_only)} france_only={len(france_only)}"
)

#!/usr/bin/env python3
"""Targeted publication must preserve the executable Global+France materialization union."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import projection_active_provider_ids  # noqa: E402
import reconcile_targeted_provider_publication as mod  # noqa: E402

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
global_active = {
    str(row.get("id") or "").strip().casefold().replace("_", "-")
    for row in manifest.get("scrapers") or []
    if isinstance(row, dict) and row.get("enabled") is not False
}
union_active = set(projection_active_provider_ids())

assert global_active
assert union_active >= global_active
assert union_active - global_active, "fixture repository must contain active France-only providers"
source = (ROOT / "scripts" / "reconcile_targeted_provider_publication.py").read_text(encoding="utf-8")
assert "projection_active_provider_ids()" in source
assert "set(active_provider_ids())" not in source
assert "Targeting only Global publication must never retire France-only rows." in source

print(
    "targeted publication union materialization scope passed "
    f"global={len(global_active)} union={len(union_active)} france_only={len(union_active-global_active)}"
)

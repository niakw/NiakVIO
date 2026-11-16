#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from current_provider_scope import projection_active_provider_count, projection_visible_provider_count
validation = json.loads((ROOT / "VALIDATION.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
corpus = json.loads((ROOT / ".github/triggers/rotating-popular-corpus.json").read_text(encoding="utf-8"))
native = json.loads((ROOT / "native-hub46/manifest.json").read_text(encoding="utf-8"))

assert validation["release"] == manifest["version"]
assert projection_visible_provider_count() >= len(manifest.get("scrapers") or [])
native_ids = {
    str(row.get("id") or "").strip().casefold().replace("_", "-")
    for row in native.get("scrapers") or []
    if isinstance(row, dict) and str(row.get("id") or "").strip()
}
assert len(native_ids) == projection_active_provider_count()
assert set(validation["native_sampling"]["global_lists"]) == {"movie", "tv", "anime"}
assert set(corpus.get("lists") or {}) == {"movie", "tv", "anime"}
for lane in ("movie", "tv", "anime"):
    assert len(corpus["lists"][lane]) == validation["native_sampling"]["reserve_size_per_lane"] == 32
assert validation["native_sampling"]["initial_fixtures_per_lane"] == 1
assert validation["native_sampling"]["fixed_batch"] is False
assert validation["native_sampling"]["rotate_only_on_clean_zero_streams"] is True
assert validation["core_contract"]["timeout_seconds"] == 25
assert validation["final_certification"]["status"] == "pending_frozen_candidate_sha"
assert validation["final_certification"]["requires_five_native_platforms"] is True
assert validation["final_certification"]["requires_final_native_hub46_manifest_regeneration"] is True

print(
    "VALIDATION_MACHINE_SUMMARY_CURRENT_OK "
    f"release={validation['release']} visible={projection_visible_provider_count()} active={projection_active_provider_count()} corpus=3x32 certification=pending"
)

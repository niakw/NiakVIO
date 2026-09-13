#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
validation = json.loads((ROOT / "VALIDATION.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
corpus = json.loads((ROOT / ".github/triggers/rotating-popular-corpus.json").read_text(encoding="utf-8"))
scope = json.loads((ROOT / "automation/evidence/hub-lab-matrix-46.json").read_text(encoding="utf-8"))

assert validation["release"] == manifest["version"]
assert validation["catalogue"]["provider_objects"] == len(manifest.get("scrapers") or []) == 96
scope_ids = {
    str(row.get("manifestId") or row.get("provider") or "").strip().casefold()
    for row in scope.get("rows") or []
    if isinstance(row, dict) and str(row.get("manifestId") or row.get("provider") or "").strip()
}
assert len(scope_ids) == validation["catalogue"]["physical_native_lab_scope"] == 46
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
    f"release={validation['release']} providers=96 scope=46 corpus=3x32 certification=pending"
)

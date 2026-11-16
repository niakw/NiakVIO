#!/usr/bin/env python3
"""Current Repair/activation scope must come from Global+France publication authority."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

files = {
    "canonical_repair": ROOT / "scripts/run_provider_repair_pipeline_v6.py",
    "fast_repair": ROOT / "scripts/run_provider_repair_fast_targeted_v1.py",
    "disposition": ROOT / "scripts/finalize_provider_repair_disposition_v1_impl.py",
    "activation": ROOT / "scripts/validate_activation_preservation.py",
    "cross_playback": ROOT / "scripts/check_cross_provider_playback.py",
}

sources = {name: path.read_text(encoding="utf-8") for name, path in files.items()}

for name in ("canonical_repair", "fast_repair"):
    text = sources[name]
    assert "projection_visible_provider_rows()" in text, name
    assert "projection_visible_provider_ids()" in text, name
    assert "projection_active_provider_ids()" in text, name
    assert "HUB_MATRIX" not in text, name
    assert "hub-lab-matrix-46.json" not in text, name
    assert "MATRIX_STALE" not in text, name

disposition = sources["disposition"]
assert "projection_visible_provider_ids()" in disposition
assert "projection_active_provider_ids()" in disposition
assert "HUB_MATRIX" not in disposition
assert "load(args.hub_matrix)" not in disposition
assert "MATRIX_STALE" not in disposition
assert "Deprecated compatibility input" in disposition

activation = sources["activation"]
assert "active_provider_ids()" in activation
assert "visible_provider_ids()" in activation
assert "projection_visible_provider_ids()" in activation
assert "projection_active_provider_ids()" in activation
assert "Global+France projection authority" in activation
assert "HUB_MATRIX" not in activation
assert "hub-lab-matrix-46.json" not in activation
assert "FIELD_ACTIVATION_SCOPE_REGISTRY_ONLY" in activation

cross_playback = sources["cross_playback"]
assert "projection_active_provider_rows" in cross_playback
assert "projection_active_provider_rows(repo_root)" in cross_playback
assert "verifier.load(repo_root / 'manifest.json')" not in cross_playback
assert "published_provider_contract" in cross_playback

print("provider current-scope authority contract passed: no historical Hub46 execution authority")

#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/temp-current-bytes-full-provider-census.yml").read_text(encoding="utf-8")

scale=wf.split("  scale:",1)[1].split("  census:",1)[0]
assert "scripts/detect_provider_projection_drift.py" in scale
assert 'projection_drift="$(' in scale
assert 'if [ "$projection_drift" -gt 0 ]; then' in scale
assert "should_run=false" in scale
assert "FIELD_CENSUS_PROJECTION_HANDOFF" in scale
assert "gh workflow run provider-projection-reconcile.yml" in scale

census_header=wf.split("  census:",1)[1].split("    steps:",1)[0]
assert "needs.scale.outputs.should_run == 'true'" in census_header

persist=wf.split("- name: Persist exact census evidence",1)[1]
assert "scripts/detect_provider_projection_drift.py" in persist
assert "FIELD_CURRENT_BYTES_CENSUS_DEFERRED reason=unpublished-provider-projection" in persist
assert persist.index("FIELD_CURRENT_BYTES_CENSUS_DEFERRED") < persist.index("git reset --hard")
assert "gh workflow run provider-projection-reconcile.yml" in persist

print("current-byte census projection race guard passed")

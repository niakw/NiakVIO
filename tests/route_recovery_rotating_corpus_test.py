#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
spec = importlib.util.spec_from_file_location("recovery", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

for lane in ("movie", "tv", "anime"):
    base = {str(row.get("slug") or "") for row in module.FIXTURES[lane]}
    extras = module._rotated_recovery_candidates("provider-a", lane, set(base))
    assert len(base) + len(extras) <= module.MAX_FIXTURES_PER_LANE
    assert not (base & {str(row.get("slug") or "") for row in extras})
    assert all(str(row.get("tmdbId") or "") for row in extras)

assert module._clean_catalogue_zero({
    "status": "ok", "error": None, "streams": 0, "rawStreams": 0,
    "serverSuccess": True, "network": [],
})
assert not module._clean_catalogue_zero({
    "status": "ok", "error": None, "streams": 1, "rawStreams": 1,
    "serverSuccess": True, "network": [],
})
assert not module._clean_catalogue_zero({
    "status": "runtime_error", "error": "boom", "streams": 0, "rawStreams": 0,
    "serverSuccess": False, "network": [],
})

print("route recovery rotating corpus test passed")

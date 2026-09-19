#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Make the test standalone as well as proof-first compatible.
for script in (
    "scripts/upgrade_provider_route_proof_request_spec_v1.py",
    "scripts/upgrade_route_recovery_request_specs_v1.py",
    "scripts/upgrade_route_proof_dataflow_safety_v2.py",
):
    done = subprocess.run([sys.executable, script], cwd=ROOT, capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stdout + done.stderr

sys.path.insert(0, str(ROOT / "scripts"))
from provider_route_proof import derive_request_spec  # noqa: E402
from recover_provider_routes_from_upstreams import (  # noqa: E402
    generic_execution_route,
    select_runtime_routes,
)

fixture = {
    "tmdbId": "94997",
    "mediaType": "tv",
    "title": "House of the Dragon",
    "year": 2022,
    "season": 3,
    "episode": 1,
}

# A season number embedded incidentally in a static User-Agent is not semantic DATA.
spec, meta = derive_request_spec(
    {
        "method": "GET",
        "body_kind": "none",
        "proof_headers": {
            "accept": "application/json,*/*",
            "user-agent": "Mozilla/5.0 NiakVIO/3",
        },
    },
    {"fixture": fixture},
    [],
)
assert meta["requestSpecReusable"] is True, meta
assert spec is not None, meta
assert spec["headers"]["user-agent"] == "Mozilla/5.0 NiakVIO/3", spec
assert "{season}" not in spec["headers"]["user-agent"], spec

# Conversely, arbitrary headers containing a real fixture identity are not frozen.
identity_spec, identity_meta = derive_request_spec(
    {
        "method": "GET",
        "body_kind": "none",
        "proof_headers": {"x-content-id": "94997"},
    },
    {"fixture": fixture},
    [],
)
assert identity_spec is None, identity_meta
assert identity_meta["requestSpecReusable"] is False, identity_meta
assert any(row.get("location") == "header:x-content-id" for row in identity_meta["requestSpecResidue"]), identity_meta

# Empty signed/identity parameters prove an endpoint exists but are not executable.
blank_signed = {
    "route": "/api/streams/episode?id=&season=&episode=&k=",
    "method": "GET",
    "requestSpecReusable": True,
    "requestSpec": {
        "method": "GET",
        "headers": {"user-agent": "Mozilla/5.0 NiakVIO/3"},
    },
}
assert generic_execution_route(blank_signed) is False, blank_signed

# Weak downstream observations may not replace an already-published signed chain.
baseline = [
    "/title/movie/{id}-{slug}",
    "/title/tv/{id}-{slug}",
    "/player",
    "/api/streams/{media}?id&k",
    "/api/streams/episode?id&season&episode&k",
    "/api/stream-gw",
]
routes, preserved = select_runtime_routes(
    baseline,
    list(baseline),
    ["/api/stream-gw", "/api/track-view"],
)
assert preserved is True, (routes, preserved)
assert routes == baseline, routes

# A newly proven identity-bearing execution plan remains authoritative.
new_plan = ["/search?q={query}", "/stream/{id}/episode?season={season}&episode={episode}"]
routes, preserved = select_runtime_routes(baseline, list(baseline), new_plan)
assert preserved is False, (routes, preserved)
assert routes == new_plan, routes

print("route-proof dataflow safety v2 tests passed: literal headers, blank signed routes, richer-plan preservation")

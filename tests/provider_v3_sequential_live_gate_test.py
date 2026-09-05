#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_v3_routes_sequential import (  # noqa: E402
    coverage_target,
    derive_observed_route,
    should_pass,
)

fixture = {
    "tmdbId": "157336",
    "mediaType": "movie",
    "title": "Interstellar",
    "year": 2014,
}
task = {"fixture": fixture, "semantic_type": "movie", "fixture_title": "Interstellar"}
fetch = {
    "url": "https://example.test/api/search?q=Interstellar&id=157336",
    "final_url": "https://example.test/api/search?q=Interstellar&id=157336",
    "method": "GET",
    "status": 200,
    "content_type": "application/json",
    "header_names": ["accept"],
    "body_kind": "none",
    "body_fields": [],
}
route, meta = derive_observed_route(fetch, task)
assert route == "/api/search?q={query}&id={tmdbId}", (route, meta)
assert meta["reusable"] is True, meta

assert coverage_target(1, 0.75) == 1.0
assert coverage_target(2, 0.75) == 1.0
assert coverage_target(5, 0.75) == 0.75

base = {
    "playableVerified": False,
    "providerRequestCount": 4,
    "typeComplete": True,
    "effectiveCoverageRatio": 0.75,
    "requiredCoverageRatio": 0.75,
    "unresolvedObservedRequestCount": 1,
    "observedRequestShapeCount": 4,
}
assert should_pass(base) is True, base
assert should_pass({**base, "effectiveCoverageRatio": 0.74}) is False
assert should_pass({**base, "typeComplete": False}) is False
assert should_pass({**base, "unresolvedObservedRequestCount": 2}) is False
assert should_pass({
    **base,
    "playableVerified": True,
    "providerRequestCount": 0,
    "typeComplete": False,
    "effectiveCoverageRatio": 0.0,
}) is True

source = (ROOT / "scripts" / "validate_provider_v3_routes_sequential.py").read_text(encoding="utf-8")
assert "ThreadPoolExecutor" not in source
assert "as_completed" not in source
assert "for index, provider in enumerate(queue, start=1):" in source
assert "refusing to advance to provider" in source
assert "write(knowledge_path, knowledge)" in source
assert "sequentialNoInterProviderConcurrency" in source

print(
    "Provider v3 sequential live gate tests passed: one provider at a time, "
    "75% useful coverage, no inter-provider concurrency, explicit dead/blocked exceptions."
)

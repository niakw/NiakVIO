#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bootstrap_provider_v3_routes as bootstrap  # noqa: E402


# This test intentionally starts with no routes/apiRecipe/model. It exercises the
# permanent onboarding contract independently of any existing NiakVIO provider.
provider_id = "empty-provider-test"
source = Path("/dev/null")

trace = {
    "ok": True,
    "stream_count": 1,
    "network_observations": [
        {
            "infrastructure": False,
            "route_proof_trace": True,
            "proof_url": "https://catalog.example.test/search?q=Interstellar",
            "method": "GET",
            "status": 200,
            "proof_headers": {"accept": "application/json"},
            "proof_body_kind": "none",
            "proof_body_fields": [],
            "proof_body_values": {},
            "response_value_hints": [{"key": "id", "value": "525"}],
            "content_type": "application/json",
            "duration_ms": 12,
        },
        {
            "infrastructure": False,
            "route_proof_trace": True,
            "proof_url": "https://catalog.example.test/media/525/sheet",
            "method": "GET",
            "status": 200,
            "proof_headers": {"referer": "https://catalog.example.test/"},
            "proof_body_kind": "none",
            "proof_body_fields": [],
            "proof_body_values": {},
            "response_value_hints": [],
            "content_type": "application/json",
            "duration_ms": 11,
        },
    ],
}

original = bootstrap.run_worker
try:
    bootstrap.run_worker = lambda _source, fixture, timeout: copy.deepcopy(trace)
    result = bootstrap.collect(provider_id, source, ["movie"], 30)
finally:
    bootstrap.run_worker = original

assert result["providerId"] == provider_id
assert result["routeProofVersion"] == 5
assert result["staticCandidatesExecutable"] is False
assert result["sourceProviderJavaScriptExecuted"] is True
assert "/search?q={query}" in result["routes"], result
assert "/media/{id}/sheet" in result["routes"], result
assert result["bootstrapStatus"] == "routes-proven", result
assert any(row.get("providerValueCorrelation") for row in result["routeData"] if row.get("route") == "/media/{id}/sheet")

# A literal provider id must not be promoted when the prior response did not prove it.
trace_without_id = copy.deepcopy(trace)
trace_without_id["network_observations"][0]["response_value_hints"] = []
try:
    bootstrap.run_worker = lambda _source, fixture, timeout: copy.deepcopy(trace_without_id)
    unproven = bootstrap.collect(provider_id, source, ["movie"], 30)
finally:
    bootstrap.run_worker = original
assert "/media/{id}/sheet" not in unproven["routes"], unproven

print("provider v3 empty route bootstrap tests passed")

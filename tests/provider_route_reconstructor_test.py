#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_route_reconstructor import reconstruct_all_routes, reconstruct_provider_routes


provider = {
    "model": {
        "knownSite": "https://example.invalid",
        "strategy": "mixed_embed_resolver",
        "routes": ["/legacy/{id}", "/resolvers.js"],
    },
    "knowledge": {
        "routes": ["/api/search?q={query}", "/wp-json/oembed"],
        "routeFragments": ["/player/{id}", "/data-video="],
        "recognizedContract": {
            "requests": [
                {
                    "route": "/api/search?q={query}",
                    "role": "search",
                    "method": "POST",
                    "bodyFields": ["q"],
                    "jsonEncoded": True,
                    "refererRequired": True,
                    "response": "json",
                    "executedEvidence": True,
                    "evidence": "existing-http-call",
                    "confidence": 0.97,
                }
            ]
        },
    },
}
seed = {
    "routes": ["/player/{id}"],
    "requests": [
        {
            "route": "/player/{id}",
            "role": "player",
            "method": "GET",
            "refererRequired": True,
            "response": "html-or-text",
            "executedEvidence": True,
            "evidence": "reviewed-player-call",
            "confidence": 0.99,
        }
    ],
}
patch = {"learned_routes": ["/api/source/{id}"]}
source = r'''
const BASE='https://www3.anikai.cc';
async function search(query) {
  const endpoint = BASE + '/browser?keyword=' + encodeURIComponent(query);
  return fetchText(endpoint);
}
async function episode(result, episode) {
  const endpoint = result.url + '/ep-' + episode;
  return fetchText(endpoint);
}
'''

reconstruct_provider_routes("fixture", provider, seed=seed, patch=patch, source_text=source)
model = provider["model"]
route_data = model.get("routeData")
assert isinstance(route_data, list) and route_data, route_data
assert model["routes"] == list(dict.fromkeys(row["route"] for row in route_data)), model
assert "/browser?keyword={query}" in model["routes"], model["routes"]
assert "/ep-{episode}" in model["routes"], model["routes"]
assert "/player/{id}" in model["routes"], model["routes"]
assert "/api/source/{id}" in model["routes"], model["routes"]
assert "/resolvers.js" not in model["routes"], model["routes"]
assert "/wp-json/oembed" not in model["routes"], model["routes"]
assert "/data-video=" not in model["routes"], model["routes"]

search = next(row for row in route_data if row["route"] == "/api/search?q={query}")
assert search["method"] == "POST", search
assert search["jsonEncoded"] is True, search
assert search["refererRequired"] is True, search
assert search["httpUsed"] is True, search
assert search["confidence"] == 0.97, search

for route in ("/browser?keyword={query}", "/ep-{episode}"):
    row = next(item for item in route_data if item["route"] == route)
    assert row["httpUsed"] is True, row
    assert any(str(value).startswith("fetch-expression") for value in row["evidenceSources"]), row

recognized = provider["knowledge"]["recognizedContract"]
assert recognized["version"] == 3, recognized
assert recognized["canonicalRouteData"] == "model.routeData", recognized
assert [row["route"] for row in recognized["requests"]] == [row["route"] for row in route_data], recognized
assert model["routeRecognition"]["fullProviderReconstructionRequired"] is False

# Same inputs are stable: route-only reconstruction must be safe during individual
# provider creation as well as repeated 96/96 sweeps.
first = copy.deepcopy(provider)
reconstruct_provider_routes("fixture", provider, seed=seed, patch=patch, source_text=source)
assert provider["model"]["routeData"] == first["model"]["routeData"]
assert provider["model"]["routes"] == first["model"]["routes"]

# Unknown route contract is a recognition state, never evidence that the provider
# is dead/quarantined.
unknown = {"model": {"strategy": "html_scraper"}, "knowledge": {}}
reconstruct_provider_routes("unknown", unknown)
assert unknown["model"]["routeRecognition"]["status"] == "unknown", unknown
assert unknown["model"]["routeData"] == [], unknown
assert unknown["model"]["strategy"] == "html_scraper", unknown

# Real 96/96 route-only census: every Provider Object receives the canonical field,
# compact model.routes is always derived from it, and no full provider rebuild is
# involved. Empty DATA remains an explicit unknown contract for later recognition.
knowledge = json.loads((ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8"))
seeds = json.loads((ROOT / "automation/provider-v3-recognition-seeds.json").read_text(encoding="utf-8"))
overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
reconstructed, census = reconstruct_all_routes(knowledge, seeds=seeds, overrides=overrides)
assert census["providerCount"] == 96, census
assert census["fullProviderReconstructionInvoked"] is False, census
assert census["providerJavaScriptExecuted"] is False, census
assert reconstructed["routeReconstruction"]["canonicalRouteData"] == "providers.<id>.model.routeData"
for provider_id, row in reconstructed["providers"].items():
    model = row.get("model") or {}
    data = model.get("routeData")
    assert isinstance(data, list), provider_id
    assert model.get("routes") == list(dict.fromkeys(item["route"] for item in data)), provider_id
    recognition = model.get("routeRecognition") or {}
    assert recognition.get("status") in {"recognized", "unknown"}, (provider_id, recognition)
    assert recognition.get("fullProviderReconstructionRequired") is False, provider_id

print(
    "Provider route reconstructor tests passed: canonical routeData, static source proof, "
    f"idempotence, unknown != quarantine, census=96 routes={census['routeCount']} "
    f"httpProven={census['httpProvenRouteCount']} unknown={len(census['unknownProviders'])}"
)

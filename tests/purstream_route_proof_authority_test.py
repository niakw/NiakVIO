#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
knowledge = json.loads((ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8"))
patch = (overrides.get("provider_patches") or {}).get("purstream") or {}
model = (((knowledge.get("providers") or {}).get("purstream") or {}).get("model") or {})
recipe = patch.get("api_recipe") or {}
static_recipe = model.get("apiRecipe") or {}

assert int(patch.get("route_proof_version") or 0) >= 5, patch.get("route_proof_version")
assert int(model.get("routeProofVersion") or 0) >= 5, model.get("routeProofVersion")
assert int(recipe.get("proofModelVersion") or 0) >= 5, recipe.get("proofModelVersion")
assert int(static_recipe.get("proofModelVersion") or 0) >= 5, static_recipe.get("proofModelVersion")
assert recipe.get("base") == "https://api.purstream.ad/api/v1", recipe.get("base")
assert model.get("officialApi") == "https://api.purstream.ad/api/v1", model.get("officialApi")
assert patch.get("learned_routes") == [
    "/search-bar/search/{query}",
    "/stream/{id}",
    "/stream/{id}/episode?season={season}&episode={episode}",
]
assert "api.purstream.ad" in (patch.get("proof_protected_hosts") or [])
print("purstream route/recipe proof authority contract passed")

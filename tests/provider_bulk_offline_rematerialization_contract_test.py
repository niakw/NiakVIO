#!/usr/bin/env python3
"""Regression: WAF-limited exact-byte activation must survive canonical rebuild.

This protects execution authority only. It must never manufacture route proof or
FULL/runtime evidence.
"""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_provider_v3_all.py"
spec = importlib.util.spec_from_file_location("materialize_provider_v3_all_contract", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

routes = [
    "/movies/{tmdbId}-{slug}",
    "/search?q={query}",
    "/player/{id}",
]
patch = {
    "official_site": "https://provider.example",
    "capability": "mixed_embed_resolver",
    "learned_routes": routes,
    "route_proof_version": 0,
}
offline_capability = {
    "strategy": "mixed_embed_resolver",
    "validation": "bulk_offline_contract_live_unverified",
}
static = {
    "model": {
        "routeProofVersion": 0,
        "routes": [],
        "sourceRuntimeFamily": "unknown",
    }
}

model = mod.provider_model("offline-example", patch, offline_capability, static)
assert model["routes"] == routes, model
assert model["routeProofVersion"] == 0, model
assert model["apiRecipe"] is None, model

# The same unproved routes are not executable merely because they exist in
# learned knowledge. Only the explicit exact-byte live-unverified activation
# state preserves them before native/WAF-capable proof.
pending = mod.provider_model(
    "pending-example",
    patch,
    {"strategy": "mixed_embed_resolver", "validation": "bulk_onboarding_pending"},
    static,
)
assert pending["routes"] == [], pending
assert pending["routeProofVersion"] == 0, pending

# A non identity-aware navigation route cannot acquire execution authority from
# the live-unverified flag.
bare_patch = dict(patch)
bare_patch["learned_routes"] = ["/search"]
bare = mod.provider_model("bare-example", bare_patch, offline_capability, static)
assert bare["routes"] == [], bare
assert bare["routeProofVersion"] == 0, bare

# Genuine proof authority continues to use the normal proof>=5 path.
proved_patch = dict(patch)
proved_patch["route_proof_version"] = 5
proved = mod.provider_model(
    "proved-example",
    proved_patch,
    {"strategy": "mixed_embed_resolver", "validation": "full"},
    static,
)
assert proved["routes"] == routes, proved
assert proved["routeProofVersion"] == 5, proved

print("Bulk offline rematerialization execution-authority contract passed")

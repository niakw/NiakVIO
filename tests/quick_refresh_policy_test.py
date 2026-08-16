#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "promote_refresh_candidates.py"
spec = importlib.util.spec_from_file_location("promote_refresh_candidates", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

manifest = {
    "scrapers": [
        {"id": "active", "enabled": True, "filename": "providers/active.js"},
        {"id": "historic", "enabled": False, "filename": "providers/historic.js"},
        {"id": "quarantined", "enabled": False, "filename": "providers/quarantined--nuvio-audit-quarantine--abc.js"},
        {"id": "new", "enabled": False, "filename": "providers/new.js"},
    ]
}
lkg = {"active_ids": ["active", "historic", "quarantined"]}
policy = {
    "provider_patches": {
        "quarantined": {"manifest_overrides": {"enabled": False}},
    }
}
provenance = {
    "providers": {
        "quarantined": {
            "published_filename": "providers/quarantined--nuvio-audit-quarantine--abc.js"
        }
    }
}

current = module._enabled_manifest_ids(manifest)
historical = module._historical_active_ids(lkg)
quarantined = module._quarantine_ids(policy, manifest, provenance)
positive = (current | historical) - quarantined
preserve = current - quarantined
overlay = module._refresh_policy_overlay(
    policy,
    {"active", "historic", "quarantined", "new"},
    positive,
    quarantined,
)

assert current == {"active"}
assert historical == {"active", "historic", "quarantined"}
assert quarantined == {"quarantined"}
assert positive == {"active", "historic"}
assert preserve == {"active"}
assert overlay["provider_patches"]["new"]["manifest_overrides"]["enabled"] is False
assert overlay["provider_patches"]["quarantined"]["manifest_overrides"]["enabled"] is False
assert "manifest_overrides" not in overlay["provider_patches"].get("active", {})
assert "manifest_overrides" not in overlay["provider_patches"].get("historic", {})
assert module._filtered_activation_lkg(lkg, preserve)["active_ids"] == ["active"]

print("quick refresh publication policy test passed")

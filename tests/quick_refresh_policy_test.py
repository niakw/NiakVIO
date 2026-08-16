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
        {"id": "active", "enabled": True, "filename": "providers/active-old.js", "version": "1"},
        {"id": "active-failed", "enabled": True, "filename": "providers/active-failed-old.js", "version": "1"},
        {"id": "historic", "enabled": False, "filename": "providers/historic.js", "version": "1"},
        {
            "id": "quarantined",
            "enabled": False,
            "filename": "providers/quarantined--nuvio-audit-quarantine--abc.js",
            "version": "1",
        },
    ]
}
lkg = {"active_ids": ["active", "active-failed", "historic", "quarantined"]}
policy = {
    "provider_patches": {
        "quarantined": {"manifest_overrides": {"enabled": False}},
        # Even a stale contradictory override must not let quick change the
        # activation state that is already published on main.
        "active": {"manifest_overrides": {"enabled": False}},
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
preserve = set(current)
overlay = module._refresh_policy_overlay(
    policy,
    {"active", "active-failed", "historic", "quarantined", "new"},
    current,
)

assert current == {"active", "active-failed"}
assert historical == {"active", "active-failed", "historic", "quarantined"}
assert quarantined == {"active", "quarantined"}
assert preserve == {"active", "active-failed"}
assert overlay["provider_patches"]["active"]["manifest_overrides"]["enabled"] is True
assert overlay["provider_patches"]["active-failed"]["manifest_overrides"]["enabled"] is True
assert overlay["provider_patches"]["historic"]["manifest_overrides"]["enabled"] is False
assert overlay["provider_patches"]["new"]["manifest_overrides"]["enabled"] is False
assert overlay["provider_patches"]["quarantined"]["manifest_overrides"]["enabled"] is False
assert module._filtered_activation_lkg(lkg, preserve)["active_ids"] == ["active", "active-failed"]

# Simulate canonical quick promotion output:
# - active has positive proof and a new bundle;
# - active-failed would be disabled by the promoter, so quick must keep old LKG;
# - historic would be reactivated, which quick must undo;
# - quarantine would be replaced, which quick must undo completely;
# - new provider would be enabled, which quick must force disabled;
# - a current row omitted by generated output is preserved below through a
#   dedicated second fixture.
generated = {
    "scrapers": [
        {"id": "active", "enabled": True, "filename": "providers/active-new.js", "version": "2"},
        {"id": "active-failed", "enabled": False, "filename": "providers/active-failed-bad.js", "version": "2"},
        {"id": "historic", "enabled": True, "filename": "providers/historic-new.js", "version": "2"},
        {"id": "quarantined", "enabled": False, "filename": "providers/quarantined-live.js", "version": "2"},
        {"id": "new", "enabled": True, "filename": "providers/new.js", "version": "1"},
    ]
}
preserved = module._preserve_quick_manifest(generated, manifest, quarantined)
rows = module._manifest_rows(preserved)

assert module._enabled_manifest_ids(preserved) == current
# Because `active` is in the configured quarantine set in this fixture, its
# exact current row must be retained despite generated positive proof.
assert rows["active"] == module._manifest_rows(manifest)["active"]
assert rows["active-failed"] == module._manifest_rows(manifest)["active-failed"]
assert rows["historic"]["enabled"] is False
assert rows["historic"]["filename"] == "providers/historic-new.js"
assert rows["quarantined"] == module._manifest_rows(manifest)["quarantined"]
assert rows["new"]["enabled"] is False

# Positive proof is allowed to refresh bytes for an enabled, non-quarantined
# provider without changing its activation state.
clean_policy = {"provider_patches": {}}
clean_quarantine = module._quarantine_ids(clean_policy, manifest, {"providers": {}})
clean_preserved = module._preserve_quick_manifest(generated, manifest, clean_quarantine)
clean_rows = module._manifest_rows(clean_preserved)
assert clean_rows["active"]["filename"] == "providers/active-new.js"
assert clean_rows["active"]["enabled"] is True
assert clean_rows["active-failed"]["filename"] == "providers/active-failed-old.js"
assert clean_rows["active-failed"]["enabled"] is True

missing_generated = {"scrapers": [{"id": "new", "enabled": True, "filename": "providers/new.js"}]}
missing_preserved = module._preserve_quick_manifest(missing_generated, manifest, quarantined)
missing_rows = module._manifest_rows(missing_preserved)
assert set(module._manifest_rows(manifest)).issubset(missing_rows)
assert module._enabled_manifest_ids(missing_preserved) == current

print("quick refresh publication policy test passed")

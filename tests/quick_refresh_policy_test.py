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
        {
            "id": "active",
            "enabled": True,
            "filename": "providers/active-old.js",
            "version": "1.0.7",
            "supportedTypes": ["movie", "anime"],
        },
        {
            "id": "active-failed",
            "enabled": True,
            "filename": "providers/active-failed-old.js",
            "version": "1.0.4",
            "supportedTypes": ["movie"],
        },
        {
            "id": "historic",
            "enabled": False,
            "filename": "providers/historic.js",
            "version": "1.0.2",
            "supportedTypes": ["movie"],
        },
        {
            "id": "quarantined",
            "enabled": False,
            "filename": "providers/quarantined--nuvio-audit-quarantine--abc.js",
            "version": "1.0.3",
            "supportedTypes": ["anime"],
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
    },
    "provider_capabilities": {
        "active": {"catalogue_types": ["movie", "anime"]},
        "active-failed": {"catalogue_types": ["movie"]},
        "historic": {"catalogue_types": ["movie"]},
        "quarantined": {"catalogue_types": ["anime"]},
        "new": {"catalogue_types": ["movie", "anime"]},
    },
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
# - upstream may also return older versions / non-canonical type order.
generated = {
    "scrapers": [
        {
            "id": "active",
            "enabled": True,
            "filename": "providers/active-new.js",
            "version": "1.0.6",
            "supportedTypes": ["anime", "movie"],
        },
        {
            "id": "active-failed",
            "enabled": False,
            "filename": "providers/active-failed-bad.js",
            "version": "1.0.5",
            "supportedTypes": ["movie"],
        },
        {
            "id": "historic",
            "enabled": True,
            "filename": "providers/historic-new.js",
            "version": "1.0.2",
            "supportedTypes": ["movie"],
        },
        {
            "id": "quarantined",
            "enabled": False,
            "filename": "providers/quarantined-live.js",
            "version": "1.0.4",
            "supportedTypes": ["anime"],
        },
        {
            "id": "new",
            "enabled": True,
            "filename": "providers/new.js",
            "version": "1.0.0",
            "supportedTypes": ["anime", "movie"],
        },
    ]
}
preserved = module._preserve_quick_manifest(generated, manifest, quarantined, policy)
rows = module._manifest_rows(preserved)

assert module._enabled_manifest_ids(preserved) == current
# Because `active` is in the configured quarantine set in this fixture, its
# exact current row must be retained despite generated positive proof.
assert rows["active"] == module._manifest_rows(manifest)["active"]
assert rows["active-failed"] == module._manifest_rows(manifest)["active-failed"]
assert rows["historic"]["enabled"] is False
assert rows["historic"]["filename"] == "providers/historic-new.js"
assert rows["historic"]["version"] == "1.0.3"
assert rows["quarantined"] == module._manifest_rows(manifest)["quarantined"]
assert rows["new"]["enabled"] is False
assert rows["new"]["supportedTypes"] == ["movie", "anime"]
assert rows["new"]["version"] == "1.0.1"

# Positive proof is allowed to refresh bytes for an enabled, non-quarantined
# provider without changing its activation state. The byte change requires a
# monotonic version bump and the authoritative type order must win over upstream.
clean_policy = {
    "provider_patches": {},
    "provider_capabilities": policy["provider_capabilities"],
}
clean_quarantine = module._quarantine_ids(clean_policy, manifest, {"providers": {}})
clean_preserved = module._preserve_quick_manifest(generated, manifest, clean_quarantine, clean_policy)
clean_rows = module._manifest_rows(clean_preserved)
assert clean_rows["active"]["filename"] == "providers/active-new.js"
assert clean_rows["active"]["enabled"] is True
assert clean_rows["active"]["supportedTypes"] == ["movie", "anime"]
assert clean_rows["active"]["version"] == "1.0.8"
assert clean_rows["active-failed"]["filename"] == "providers/active-failed-old.js"
assert clean_rows["active-failed"]["enabled"] is True
assert clean_rows["active-failed"]["version"] == "1.0.4"

# Exact regression from the live post-publish failure: reapply had already
# normalized Mugiwara to movie/anime and 1.0.37, while canonical quick output
# rebuilt it from upstream as anime/movie and 1.0.36. Quick merge must not undo
# that normalization, otherwise the next npm pretest dirties the repository.
mugiwara_current = {
    "scrapers": [
        {
            "id": "MUGIWARASTREAM",
            "enabled": True,
            "filename": "providers/mugiwarastream--published-baseline--08b28bc5131e3dce.js",
            "version": "1.0.37",
            "supportedTypes": ["movie", "anime"],
        }
    ]
}
mugiwara_generated_same_bytes = {
    "scrapers": [
        {
            "id": "MUGIWARASTREAM",
            "enabled": True,
            "filename": "providers/mugiwarastream--published-baseline--08b28bc5131e3dce.js",
            "version": "1.0.36",
            "supportedTypes": ["anime", "movie"],
        }
    ]
}
mugiwara_policy = {
    "provider_patches": {"mugiwarastream": {}},
    "provider_capabilities": {
        "mugiwarastream": {"catalogue_types": ["movie", "anime"]}
    },
}
mugiwara_preserved = module._preserve_quick_manifest(
    mugiwara_generated_same_bytes,
    mugiwara_current,
    set(),
    mugiwara_policy,
)
mugiwara_row = module._manifest_rows(mugiwara_preserved)["mugiwarastream"]
assert mugiwara_row["supportedTypes"] == ["movie", "anime"]
assert mugiwara_row["version"] == "1.0.37"

# If the quick repair really changes provider bytes, keep the canonical metadata
# but require one version bump above the current published row.
mugiwara_generated_new_bytes = {
    "scrapers": [
        {
            **mugiwara_generated_same_bytes["scrapers"][0],
            "filename": "providers/mugiwarastream--nuvio--newbytes.js",
        }
    ]
}
mugiwara_repaired = module._preserve_quick_manifest(
    mugiwara_generated_new_bytes,
    mugiwara_current,
    set(),
    mugiwara_policy,
)
mugiwara_repaired_row = module._manifest_rows(mugiwara_repaired)["mugiwarastream"]
assert mugiwara_repaired_row["supportedTypes"] == ["movie", "anime"]
assert mugiwara_repaired_row["version"] == "1.0.38"

missing_generated = {
    "scrapers": [
        {
            "id": "new",
            "enabled": True,
            "filename": "providers/new.js",
            "version": "1.0.0",
            "supportedTypes": ["anime", "movie"],
        }
    ]
}
missing_preserved = module._preserve_quick_manifest(missing_generated, manifest, quarantined, policy)
missing_rows = module._manifest_rows(missing_preserved)
assert set(module._manifest_rows(manifest)).issubset(missing_rows)
assert module._enabled_manifest_ids(missing_preserved) == current

print("quick refresh publication policy test passed")

#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "promote_refresh_candidates.py"
spec = importlib.util.spec_from_file_location("promote_refresh_candidates", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
assert catalog.get("sourceOfTruth") is True
assert catalog.get("policy", {}).get("repairBeforeTriage") is True
assert catalog.get("policy", {}).get("retainLastKnownGoodOnInconclusive") is True
assert catalog.get("policy", {}).get("quickRefreshMayRepairAndPublish") is True

manifest = {
    "scrapers": [
        {"id": "active", "enabled": True, "filename": "providers/active-old.js", "version": "1.0.7", "supportedTypes": ["movie"]},
        {"id": "active-failed", "enabled": True, "filename": "providers/active-failed-old.js", "version": "1.0.4", "supportedTypes": ["movie"]},
        {"id": "historic", "enabled": False, "filename": "providers/historic.js", "version": "1.0.2", "supportedTypes": ["movie"]},
        {"id": "audit-q", "enabled": False, "filename": "providers/audit-q--nuvio-audit-quarantine--abc.js", "version": "1.0.3", "supportedTypes": ["movie"]},
        {"id": "hard-q", "enabled": False, "filename": "providers/hard-q.js", "version": "1.0.3", "supportedTypes": ["movie"]},
    ]
}
policy = {
    "provider_patches": {
        "hard-q": {
            "capability": "quarantined",
            "patch_scripts": ["scripts/provider_patches/quarantine_provider_v1.py"],
            "manifest_overrides": {"enabled": False},
        },
        # Historical administrative disable: this is recoverable and must not
        # be interpreted as a safety quarantine.
        "historic": {"capability": "direct_media", "manifest_overrides": {"enabled": False}},
    },
    "provider_capabilities": {
        "active": {"catalogue_types": ["movie"]},
        "active-failed": {"catalogue_types": ["movie"]},
        "historic": {"catalogue_types": ["movie"]},
        "audit-q": {"catalogue_types": ["movie"]},
        "hard-q": {"catalogue_types": ["movie"]},
        "new": {"catalogue_types": ["movie"]},
    },
}
provenance = {
    "providers": {
        "audit-q": {"published_filename": "providers/audit-q--nuvio-audit-quarantine--abc.js"}
    }
}

current_rows = module._manifest_rows(manifest)
current_ids = set(current_rows)
current_enabled = module._enabled_manifest_ids(manifest)
hard_q = module._configured_safety_quarantine_ids(policy)
audit_q = module._publication_quarantine_ids(manifest, provenance)

overlay = module._refresh_policy_overlay(
    policy,
    {"active", "active-failed", "historic", "audit-q", "hard-q", "new"},
    current_ids,
    hard_q,
)
assert current_enabled == {"active", "active-failed"}
assert hard_q == {"hard-q"}
assert audit_q == {"audit-q"}

recovered_audit_name = {
    "scrapers": [
        {"id": "recovered", "enabled": True, "filename": "providers/recovered--nuvio-audit-quarantine--old.js"}
    ]
}
recovered_provenance = {
    "providers": {
        "recovered": {"published_filename": "providers/recovered--nuvio-audit-quarantine--old.js"}
    }
}
assert module._publication_quarantine_ids(recovered_audit_name, recovered_provenance) == set()

# Existing non-safety providers are allowed to let current proof decide.
assert "enabled" not in overlay["provider_patches"]["historic"]["manifest_overrides"]
assert "enabled" not in overlay["provider_patches"]["audit-q"]["manifest_overrides"]
# Hard quarantine and brand-new discovery stay disabled.
assert overlay["provider_patches"]["hard-q"]["manifest_overrides"]["enabled"] is False
assert overlay["provider_patches"]["new"]["manifest_overrides"]["enabled"] is False

# Canonical promoter output represents current strict decisions.
generated = {
    "scrapers": [
        {"id": "active", "enabled": True, "filename": "providers/active-new.js", "version": "1.0.7", "supportedTypes": ["movie"]},
        # Current failure: active LKG must be retained.
        {"id": "active-failed", "enabled": False, "filename": "providers/active-failed-bad.js", "version": "1.0.5", "supportedTypes": ["movie"]},
        # Existing disabled provider has fresh current proof and may recover.
        {"id": "historic", "enabled": True, "filename": "providers/historic-new.js", "version": "1.0.3", "supportedTypes": ["movie"]},
        # Publication-scoped audit quarantine has a new healthy sibling.
        {"id": "audit-q", "enabled": True, "filename": "providers/audit-q-live.js", "version": "1.0.4", "supportedTypes": ["movie"]},
        # Configured safety quarantine must never move on quick.
        {"id": "hard-q", "enabled": True, "filename": "providers/hard-q-live.js", "version": "1.0.4", "supportedTypes": ["movie"]},
        # Brand-new canonical provider remains disabled.
        {"id": "new", "enabled": True, "filename": "providers/new.js", "version": "1.0.0", "supportedTypes": ["movie"]},
    ]
}
merged = module._preserve_quick_manifest(generated, manifest, hard_q, audit_q, policy)
rows = module._manifest_rows(merged)
enabled = module._enabled_manifest_ids(merged)

assert rows["active"]["filename"] == "providers/active-new.js"
assert rows["active"]["enabled"] is True
assert rows["active"]["version"] == "1.0.8"
assert rows["active-failed"] == current_rows["active-failed"]
assert rows["historic"]["enabled"] is True
assert rows["historic"]["filename"] == "providers/historic-new.js"
assert rows["audit-q"]["enabled"] is True
assert rows["audit-q"]["filename"] == "providers/audit-q-live.js"
assert rows["hard-q"] == current_rows["hard-q"]
assert rows["new"]["enabled"] is False
assert enabled == {"active", "active-failed", "historic", "audit-q"}

# If a publication quarantine has no current proof, keep its inert row exactly.
generated_failed_audit = {
    "scrapers": [
        {"id": "audit-q", "enabled": False, "filename": "providers/audit-q-candidate.js", "version": "1.0.4", "supportedTypes": ["movie"]}
    ]
}
failed = module._preserve_quick_manifest(generated_failed_audit, manifest, hard_q, audit_q, policy)
assert module._manifest_rows(failed)["audit-q"] == current_rows["audit-q"]

print("quick refresh publication policy test passed")

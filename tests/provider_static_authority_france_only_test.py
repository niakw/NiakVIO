#!/usr/bin/env python3
import importlib.util
import base64
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT/"scripts").resolve()))
path=ROOT/"scripts/reconcile_provider_static_authority.py"
spec=importlib.util.spec_from_file_location("reconcile_provider_static_authority_france",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.active_provider_rows=lambda:[
    {"id":"global-a","enabled":True,"filename":"providers/global-a.js"},
]
mod.france_only_catalog_rows=lambda root=None:[
    {"id":"fr-a","enabled":True,"filename":"providers/fr-a.js"},
    {"id":"fr-disabled","enabled":False,"filename":"provider-disabled/fr-disabled.js"},
]
rows=mod.active_current_rows()
assert [mod.canonical_id(row.get("id")) for row in rows]==["global-a","fr-a"],rows

# Static authority spans the runtime-visible union, not only active execution.
# Retained disabled Global/France rows remain Brain reconstruction knowledge;
# pending identities are excluded by projection_runtime_visible_provider_ids.
mod.visible_provider_rows=lambda:[
    {"id":"global-a","enabled":True,"filename":"providers/global-a.js"},
    {"id":"global-disabled","enabled":False,"filename":"provider-disabled/global-disabled.js"},
]
mod.france_only_catalog_rows=lambda root=None:[
    {"id":"fr-a","enabled":True,"filename":"providers/fr-a.js"},
    {"id":"fr-disabled","enabled":False,"filename":"provider-disabled/fr-disabled.js"},
    {"id":"fr-pending","enabled":False,"filename":"provider-disabled/fr-pending.js"},
]
mod.projection_runtime_visible_provider_ids=lambda:{
    "global-a","global-disabled","fr-a","fr-disabled"
}
runtime_rows=mod.runtime_visible_current_rows()
assert [mod.canonical_id(row.get("id")) for row in runtime_rows]==[
    "global-a","global-disabled","fr-a","fr-disabled"
],runtime_rows

# Restore active-only setup for activation-authority checks below.
mod.france_only_catalog_rows=lambda root=None:[
    {"id":"fr-a","enabled":True,"filename":"providers/fr-a.js"},
    {"id":"fr-disabled","enabled":False,"filename":"provider-disabled/fr-disabled.js"},
]

# Active provider folders are activation authority. Stale lifecycle flags must
# be removed without deleting unrelated manifest overrides.
overrides={
    "provider_patches":{
        "global-a":{"manifest_overrides":{"enabled":False,"limited":True}},
        "fr-a":{"manifest_overrides":{"enabled":True}},
        "other":{"manifest_overrides":{"enabled":False}},
    }
}
changed=mod.normalize_active_activation_overrides(overrides,rows)
assert changed==["fr-a","global-a"],changed
assert overrides["provider_patches"]["global-a"]["manifest_overrides"]=={"limited":True}
assert "manifest_overrides" not in overrides["provider_patches"]["fr-a"]
assert overrides["provider_patches"]["other"]["manifest_overrides"]["enabled"] is False

mod.france_only_catalog_rows=lambda root=None:[
    {"id":"global-a","enabled":True,"filename":"providers/collision.js"},
]
try:
    mod.active_current_rows()
except ValueError as exc:
    assert "collides" in str(exc)
else:
    raise AssertionError("France-only/Global collision was accepted")

# A previously activated FULL provider that executes through a repository-owned
# Provider Lego may recover only the exact identity contract already present in
# the byte-bound activation proof. Candidate routes are never promoted here.
with tempfile.TemporaryDirectory(prefix="niakvio-full-lego-identity-") as tmp_name:
    temp_root=Path(tmp_name)
    (temp_root/"providers").mkdir(parents=True)
    provider_id="lego-a"
    fix_id="PROVIDER.LEGO-A.CONFIG.V1"
    model={
        "providerId":provider_id,
        "identityInput":{
            "mode":"tmdb_direct",
            "requiresTmdbBeforeRun":False,
            "requiredFields":["tmdbId","mediaType"],
        },
    }
    encoded=base64.urlsafe_b64encode(
        json.dumps(model,sort_keys=True,separators=(",",":")).encode()
    ).decode("ascii")
    bundle=temp_root/"providers/lego-a.js"
    bundle.write_text(
        "/* BEGIN NIAKVIO_PROVIDER */\n"
        "/* NIAKVIO_PROVIDER_ID:lego-a */\n"
        "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
        f"/* STARTFIX:{fix_id} */\n"
        f"/* FIXDATA:{fix_id}:{encoded} */\n"
        "void 0;\n"
        f"/* CLOSEFIX:{fix_id} */\n"
        "/* END NIAKVIO_PROVIDER */\n",
        encoding="utf-8",
    )
    digest=hashlib.sha256(bundle.read_bytes()).hexdigest()
    overrides={"provider_patches":{"lego-a":{
        "provider_lego_scripts":["scripts/provider_patches/example_runtime_v1.py"],
        "candidate_learned_routes":["/play/movie/{tmdbId}"],
    }}}
    provenance={"providers":{"lego-a":{
        "activation_mode":"bulk_census_full_ok",
        "bulk_activation_proof":{"providerSha256":digest},
    }}}
    mod.ROOT=temp_root
    changed=mod.reconcile_proven_provider_lego_identities(
        overrides,provenance,[{"id":"lego-a","filename":"providers/lego-a.js","enabled":True}]
    )
    assert changed==["lego-a"],changed
    assert overrides["provider_patches"]["lego-a"]["identity_input"]=={
        "mode":"tmdb_direct",
        "requires_tmdb_before_run":False,
        "required_fields":["tmdbId","mediaType"],
    }
    assert "learned_routes" not in overrides["provider_patches"]["lego-a"]

    # Exact-byte binding is mandatory: once the active bytes drift from the
    # activation proof, reconciliation must refuse to manufacture authority.
    overrides["provider_patches"]["lego-a"].pop("identity_input")
    bundle.write_text(bundle.read_text(encoding="utf-8")+"/* drift */\n",encoding="utf-8")
    changed=mod.reconcile_proven_provider_lego_identities(
        overrides,provenance,[{"id":"lego-a","filename":"providers/lego-a.js","enabled":True}]
    )
    assert changed==[],changed
    assert "identity_input" not in overrides["provider_patches"]["lego-a"]
    mod.ROOT=ROOT

with tempfile.TemporaryDirectory(prefix="niakvio-static-authority-") as tmp_name:
    temp_root = Path(tmp_name)
    (temp_root / "providers").mkdir(parents=True)
    current_bundle = temp_root / "providers" / "fr-a--current.js"
    current_bundle.write_text("current-bytes", encoding="utf-8")
    materialization = temp_root / "provider-v3-materialization.json"
    materialization.write_text(json.dumps({
        "schemaVersion": 3,
        "providers": [{
            "provider": "fr-a",
            "file": "providers/fr-a--old.js",
            "sha256": "old",
            "providerDataSha256": "old-data",
            "applied": ["historic-diagnostic"],
        }],
    }), encoding="utf-8")

    mod.ROOT = temp_root
    mod.MATERIALIZATION = materialization
    mod.active_current_rows = lambda: [{
        "id": "fr-a",
        "enabled": True,
        "filename": "providers/fr-a--current.js",
    }]
    mod.projection_active_provider_ids = lambda: {"fr-a"}
    mod.projection_runtime_visible_provider_ids = lambda: {"fr-a"}
    mod.decode_exact_model = lambda provider_id, bundle: {"providerId": provider_id}
    current_sha = hashlib.sha256(current_bundle.read_bytes()).hexdigest()
    mod._materialization_row_from_bundle = lambda provider_id, bundle, model: {
        "provider": provider_id,
        "file": "providers/fr-a--current.js",
        "sha256": current_sha,
        "providerDataSha256": "current-data",
        "applied": [],
        "fixIds": [],
        "coreCount": 0,
        "baseStrippedGeneratedCore": False,
        "deviceSpecificJs": False,
        "devices": ["tv", "mobile", "desktop"],
        "legacyProviderJsExecuted": False,
        "upstreamJsExecuted": False,
        "staticAuthorityReconciledProviders": [provider_id],
        "minimizer": {"enabled": True},
    }
    rebound = mod.reconcile_materialization_from_active_bundles(apply=True)
    assert rebound["recoveredCount"] == 0, rebound
    assert rebound["reboundCount"] == 1, rebound
    assert rebound["rebound"] == ["fr-a"], rebound
    stored = json.loads(materialization.read_text(encoding="utf-8"))["providers"][0]
    assert stored["file"] == "providers/fr-a--current.js", stored
    assert stored["sha256"] == current_sha, stored
    assert stored["providerDataSha256"] == "current-data", stored
    assert stored["applied"] == ["historic-diagnostic"], stored
    assert stored["materializationReboundFromExactPublishedBytes"] is True, stored
    expected_generation = hashlib.sha256(
        b"fr-a" + bytes.fromhex(current_sha)
    ).hexdigest()
    stored_doc = json.loads(materialization.read_text(encoding="utf-8"))
    assert stored_doc["generation"] == expected_generation, stored_doc
    assert rebound["generation"] == expected_generation, rebound

print("provider static authority covers Global + France-only current catalogue and stale-byte rebound")

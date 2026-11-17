#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/stage_provider_batch.py"
sys.path.insert(0,str(ROOT/"scripts"))
import add_provider as add_provider_module
from add_provider import staged_existing_entry, normalized_scope, relocate_pending_artifacts, relocate_bulk_pending_artifacts, pending_validation_routes, pending_runtime_family
from stage_provider_batch import safe_pending_restage_ids, preflight

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    req=td/"batch.json"; out=td/"summary.json"
    req.write_text(json.dumps({"providers":[
        {
            "id":"bulk-scale-contract-provider-zz999",
            "name":"Bulk Scale Contract Provider",
            "types":["movie","tv"],
            "languages":["en"],
            "strategy":"mixed_embed_resolver",
            "direct":"https://example.invalid"
        }
    ]}),encoding="utf-8")
    subprocess.run([
        sys.executable,str(script),"--request",str(req),"--output",str(out),"--dry-run"
    ],cwd=ROOT,check=True)
    value=json.loads(out.read_text(encoding="utf-8"))

assert value["providerCount"]==1
assert value["newProviderCount"]==1
assert value["mode"]=="dry-run"
assert value["networkDiscoveryExecuted"] is False
assert value["nativeLabExecuted"] is False
assert value["activationAttempted"] is False
assert value["strategies"]=={"mixed_embed_resolver":1}
assert value["declaredTypeCounts"]=={"movie":1,"tv":1}
assert value["scopeCounts"]=={"global":1}
assert normalized_scope("vf")=="france"
assert normalized_scope("global")=="global"

# Route Discovery may grant execution authority only to disabled pending validation,
# never proof/publication authority. Strong observed identity routes pass; static
# navigation, fixed-content examples and merely-retained route plans stay candidates.
assert pending_validation_routes({
    "routeDiscoveryEvidence": {
        "reason": "observed_identity_executable_routes",
        "transport": "residential-exit",
        "routeCount": 3,
    }
}, ["/play/movie/{tmdbId}", "/play/tv/{tmdbId}/{season}/{episode}", "/anime/{tmdbId}"]) == [
    "/play/movie/{tmdbId}", "/play/tv/{tmdbId}/{season}/{episode}", "/anime/{tmdbId}"
]
assert pending_validation_routes({
    "routeDiscoveryEvidence": {
        "reason": "existing_identity_executable_route_plan",
        "transport": "request-existing",
        "routeCount": 2,
    }
}, ["/movie/{tmdbId}", "/anime/{tmdbId}"]) == []
assert pending_validation_routes({
    "routeDiscoveryEvidence": {
        "reason": "observed_identity_executable_routes",
        "transport": "github-hosted",
        "routeCount": 3,
    }
}, ["/embed/sw.js", "/search", "/movie/157336-interstellar"]) == []


# Executable TMDB-bound routes establish a deterministic direct runtime family;
# provider-local/search/slug plans remain catalogue families. Candidate-only
# routes never participate because staging passes only validation_routes here.
assert pending_runtime_family("mixed_embed_resolver", [
    "/play/movie/{tmdbId}",
    "/play/tv/{tmdbId}/{season}/{episode}",
    "/anime/{tmdbId}",
]) == "tmdb-direct-api"
assert pending_runtime_family("mixed_embed_resolver", ["/watch/{slug}", "/embed/{id}"]) == "catalogue-html-embed"
assert pending_runtime_family("mixed_embed_resolver", []) == "unknown"

# Global and France-only identities are distinct authorities and collisions fail closed.
with tempfile.TemporaryDirectory(prefix="niakvio-onboard-scope-") as td:
    root=Path(td)
    france={
        "id":"france-reserved",
        "name":"France reserved",
        "filename":"providers/france-reserved--v3.js",
        "enabled":False,
        "contentLanguage":["fr"],
        "supportedTypes":["movie"],
        "disabledPlatforms":[],
    }
    (root/"provider_catalog.json").write_text(json.dumps({
        "sourceOfTruth":True,
        "providers":[{
            "canonicalId":"france-reserved",
            "scraper":france,
            "projections":{"general":False,"vf":True},
        }],
    }),encoding="utf-8")
    manifest={"scrapers":[{"id":"global-existing","filename":"providers/global-existing.js"}]}
    assert staged_existing_entry("new-global",manifest,replace_existing=False,root=root)=={}
    assert staged_existing_entry("global-existing",manifest,replace_existing=True,root=root)["id"]=="global-existing"
    try:
        staged_existing_entry("global-existing",manifest,replace_existing=False,root=root)
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Global duplicate accepted without replace_existing")
    for replace in (False,True):
        try:
            staged_existing_entry("france-reserved",manifest,replace_existing=replace,root=root)
        except ValueError as exc:
            assert "France-only catalog scope" in str(exc)
        else:
            raise AssertionError("France-only identity leaked into Global staging")

    vf_manifest={"scrapers":[france]}
    assert staged_existing_entry("france-reserved",manifest,replace_existing=True,root=root,scope="france",vf_manifest=vf_manifest)["id"]=="france-reserved"
    assert staged_existing_entry("new-france",manifest,replace_existing=False,root=root,scope="france",vf_manifest=vf_manifest)=={}
    try:
        staged_existing_entry("global-existing",manifest,replace_existing=False,root=root,scope="france",vf_manifest=vf_manifest)
    except ValueError as exc:
        assert "Global scope" in str(exc)
    else:
        raise AssertionError("Global identity duplicated into France-only staging")

with tempfile.TemporaryDirectory(prefix="niakvio-bulk-pending-path-") as td:
    root=Path(td)
    (root/"providers").mkdir()
    (root/"provider-bases").mkdir()
    published=root/"providers/demo--nuvio--abc.js"
    base=root/"provider-bases/demo--base--abc.js"
    published.write_bytes(b"provider")
    base.write_bytes(b"base")
    relative=relocate_pending_artifacts(
        "providers/demo--nuvio--abc.js",
        "provider-bases/demo--base--abc.js",
        root=root,
    )
    assert relative=="provider-disabled/demo--nuvio--abc.js"
    assert not published.exists() and not base.exists()
    assert (root/relative).read_bytes()==b"provider"
    assert (root/"provider-disabled/provider-bases/demo--base--abc.js").read_bytes()==b"base"

# Every single-provider onboarding stage is disabled/pending too. The Site Probe
# must never manufacture enabled=false + providers/... while inspecting a request.
source=(ROOT/"scripts/add_provider.py").read_text(encoding="utf-8")
assert "published_relative = relocate_pending_artifacts(published_relative, base_relative)" in source
stage_tail=source.split("published_relative, published_sha, published_patches = materialize_onboarding_bundle",1)[1].split('entry["filename"]',1)[0]
assert "if bulk:" not in stage_tail, stage_tail
assert "def relocate_bulk_pending_artifacts(" in source

print("Bulk provider onboarding dry-run + Global/France-only scope contract passed")

# Single-provider finalize must retain France-only authority and must not
# manufacture strict/native proof from the bounded onboarding Quick Lab.
with tempfile.TemporaryDirectory(prefix="niakvio-onboard-finalize-france-") as td:
    root=Path(td)
    work=root/".provider-onboarding"; work.mkdir()
    manifest=root/"manifest.json"; vf_manifest=root/"vf/manifest.json"; vf_manifest.parent.mkdir()
    overrides=root/"provider-overrides.json"; provenance=root/"PROVENANCE.json"
    manifest.write_text(json.dumps({"scrapers":[{"id":"global-existing","enabled":True}]}),encoding="utf-8")
    vf_manifest.write_text(json.dumps({"scrapers":[{"id":"france-new","enabled":False}]}),encoding="utf-8")
    overrides.write_text(json.dumps({
        "provider_patches":{"france-new":{"manifest_overrides":{"enabled":False}}},
        "provider_capabilities":{"france-new":{"validation":"onboarding_pending"}},
    }),encoding="utf-8")
    provenance.write_text(json.dumps({"providers":{"france-new":{
        "activation_mode":"onboarding_pending",
        "strict_activation_eligible":False,
        "runtime_evidence_eligible":False,
    }}}),encoding="utf-8")
    (work/"current.json").write_text(json.dumps({"id":"france-new","scope":"france"}),encoding="utf-8")
    report=root/"report.json"
    report.write_text(json.dumps({
        "clients":["tv","desktop","mobile"],
        "providers":[{
            "id":"france-new",
            "clients":{
                "tv":{"verdict":"playable","identity_match_count":1,"identity_contradiction_count":0},
                "desktop":{"verdict":"playable","identity_match_count":1,"identity_contradiction_count":0},
                "mobile":{"verdict":"playable","identity_match_count":1,"identity_contradiction_count":0},
            },
        }],
        "policy":{"safety_blocking_pass":True},
    }),encoding="utf-8")

    old=(add_provider_module.WORK,add_provider_module.MANIFEST,add_provider_module.VF_MANIFEST,
         add_provider_module.OVERRIDES,add_provider_module.PROVENANCE)
    add_provider_module.WORK=work
    add_provider_module.MANIFEST=manifest
    add_provider_module.VF_MANIFEST=vf_manifest
    add_provider_module.OVERRIDES=overrides
    add_provider_module.PROVENANCE=provenance
    try:
        assert add_provider_module.finalize("france-new",report) is True
    finally:
        (add_provider_module.WORK,add_provider_module.MANIFEST,add_provider_module.VF_MANIFEST,
         add_provider_module.OVERRIDES,add_provider_module.PROVENANCE)=old

    assert json.loads(manifest.read_text(encoding="utf-8"))["scrapers"][0]["id"]=="global-existing"
    vf_row=json.loads(vf_manifest.read_text(encoding="utf-8"))["scrapers"][0]
    assert vf_row["id"]=="france-new" and vf_row["enabled"] is True
    prov=json.loads(provenance.read_text(encoding="utf-8"))["providers"]["france-new"]
    assert prov["check_status"]=="live_unverified"
    assert prov["activation_mode"]=="onboarding_quick_live_unverified"
    assert prov["activation_eligible"] is True
    assert prov["strict_activation_eligible"] is False
    assert prov["runtime_evidence_eligible"] is False
    assert prov["activation_blockers"]==["live_native_validation_pending"]
    proof=prov["onboarding_quick_lab"]
    assert proof["scope"]=="france"
    assert proof["full_ok_claimed"] is False

print("Single-provider France-only finalize + live-unverified authority contract passed")

# Transport-playable output without positive content identity remains pending.
with tempfile.TemporaryDirectory(prefix="niakvio-onboard-identity-unknown-") as td:
    root=Path(td); work=root/".provider-onboarding"; work.mkdir()
    manifest=root/"manifest.json"; vf_manifest=root/"vf/manifest.json"; vf_manifest.parent.mkdir()
    overrides=root/"provider-overrides.json"; provenance=root/"PROVENANCE.json"
    manifest.write_text(json.dumps({"scrapers":[]}),encoding="utf-8")
    vf_manifest.write_text(json.dumps({"scrapers":[{"id":"identity-unknown","enabled":False}]}),encoding="utf-8")
    overrides.write_text(json.dumps({
        "provider_patches":{"identity-unknown":{"manifest_overrides":{"enabled":False}}},
        "provider_capabilities":{"identity-unknown":{"validation":"onboarding_pending"}},
    }),encoding="utf-8")
    provenance.write_text(json.dumps({"providers":{"identity-unknown":{"activation_mode":"onboarding_pending"}}}),encoding="utf-8")
    (work/"current.json").write_text(json.dumps({"id":"identity-unknown","scope":"france"}),encoding="utf-8")
    report=root/"report.json"
    report.write_text(json.dumps({
        "clients":["tv","desktop","mobile"],
        "providers":[{"id":"identity-unknown","clients":{
            "tv":{"verdict":"playable","identity_match_count":0,"identity_contradiction_count":0},
            "desktop":{"verdict":"playable","identity_match_count":0,"identity_contradiction_count":0},
            "mobile":{"verdict":"playable","identity_match_count":0,"identity_contradiction_count":0},
        }}],
        "policy":{"safety_blocking_pass":True},
    }),encoding="utf-8")
    old=(add_provider_module.WORK,add_provider_module.MANIFEST,add_provider_module.VF_MANIFEST,
         add_provider_module.OVERRIDES,add_provider_module.PROVENANCE)
    add_provider_module.WORK=work; add_provider_module.MANIFEST=manifest
    add_provider_module.VF_MANIFEST=vf_manifest; add_provider_module.OVERRIDES=overrides
    add_provider_module.PROVENANCE=provenance
    try:
        assert add_provider_module.finalize("identity-unknown",report) is False
    finally:
        (add_provider_module.WORK,add_provider_module.MANIFEST,add_provider_module.VF_MANIFEST,
         add_provider_module.OVERRIDES,add_provider_module.PROVENANCE)=old
    assert json.loads(vf_manifest.read_text(encoding="utf-8"))["scrapers"][0]["enabled"] is False
    prov=json.loads(provenance.read_text(encoding="utf-8"))["providers"]["identity-unknown"]
    assert prov["check_status"]=="pending_learning"
    assert prov["activation_eligible"] is False
    assert prov["strict_activation_eligible"] is False
    assert prov["runtime_evidence_eligible"] is False

print("Onboarding playable-without-identity remains pending")

pending_manifest={"scrapers":[{"id":"pending-demo","enabled":False,"filename":"provider-disabled/pending-demo.js"},{"id":"disabled-demo","enabled":False,"filename":"provider-disabled/disabled-demo.js"},{"id":"active-demo","enabled":True,"filename":"providers/active-demo.js"}]}
pending_provenance={"providers":{"pending-demo":{"activation_mode":"bulk_onboarding_pending"},"disabled-demo":{"activation_mode":"disabled_retained"},"active-demo":{"activation_mode":"bulk_onboarding_pending"}}}
assert safe_pending_restage_ids(pending_manifest,{"scrapers":[]},pending_provenance)=={"pending-demo"}
print("Bulk pending restage authority is fail-closed outside inactive onboarding identities")

with tempfile.TemporaryDirectory(prefix="niakvio-pending-restage-preflight-") as td:
    root=Path(td)
    manifest=root/"manifest.json"
    vf_manifest=root/"vf-manifest.json"
    provenance=root/"PROVENANCE.json"
    manifest.write_text(json.dumps(pending_manifest),encoding="utf-8")
    vf_manifest.write_text(json.dumps({"scrapers":[]}),encoding="utf-8")
    provenance.write_text(json.dumps(pending_provenance),encoding="utf-8")
    old_paths=(add_provider_module.MANIFEST,add_provider_module.VF_MANIFEST,add_provider_module.PROVENANCE)
    add_provider_module.MANIFEST=manifest
    add_provider_module.VF_MANIFEST=vf_manifest
    add_provider_module.PROVENANCE=provenance
    try:
        summary=preflight([{
            "id":"pending-demo",
            "scope":"global",
            "types":["movie"],
            "strategy":"mixed_embed_resolver",
        }],allow_replace_existing=False)
        assert summary["replaceProviders"]==["pending-demo"],summary
        assert summary["safePendingRestageProviders"]==["pending-demo"],summary
        try:
            preflight([{
                "id":"active-demo",
                "scope":"global",
                "types":["movie"],
                "strategy":"mixed_embed_resolver",
            }],allow_replace_existing=False)
        except ValueError as exc:
            assert "already exists" in str(exc),exc
        else:
            raise AssertionError("active provider was implicitly replaceable")
    finally:
        add_provider_module.MANIFEST,add_provider_module.VF_MANIFEST,add_provider_module.PROVENANCE=old_paths
print("Bulk pending restage is implicit only for the same disabled onboarding authority")

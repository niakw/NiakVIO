#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADD = (ROOT / ".github/workflows/add-provider.yml").read_text(encoding="utf-8")
BRANDING = (ROOT / ".github/workflows/provider-branding-assets.yml").read_text(encoding="utf-8")
SCRIPT = (ROOT / "scripts/add_provider.py").read_text(encoding="utf-8")

for token in ("provider_id:", "hub:", "direct:", "telegram:", "api:", "search_queries:", "routes:", "types:", "replace_existing:"):
    assert token in ADD, token

dispatch_inputs = ADD.split("permissions:", 1)[0]
assert "logo_url:" not in dispatch_inputs
assert "emoji:" not in dispatch_inputs
assert "logo_url = normalized_url" not in SCRIPT
assert 'request.get("emoji")' not in SCRIPT
assert 'request.get("replace_existing")' in SCRIPT
assert "provider already exists" in SCRIPT
assert "and not replace_existing" in SCRIPT
stage_body = SCRIPT.split("def stage(", 1)[1].split("\ndef refresh(", 1)[0]
assert stage_body.index("manifest = load_json(MANIFEST, {})") < stage_body.index("description = str(")
assert "existing_entry = staged_existing_entry(" in stage_body
assert 'target_manifest = vf_manifest if scope == "france" else manifest' in stage_body

assert "Delegate automatic defaults to Provider branding assets engine" in ADD
assert "scripts/provider_branding_assets.py" in ADD
assert "--logo-url" not in ADD
assert "--emoji" not in ADD
assert "logo_url:" in BRANDING
assert "emoji:" in BRANDING
assert "--logo-url" in BRANDING
assert "--emoji" in BRANDING

for full_lab in (
    "native-tv-route-reader.yml",
    "native-mobile-android-reader.yml",
    "native-mobile-ios-reader.yml",
    "native-desktop-reader-acceptance.yml",
):
    assert full_lab not in ADD, full_lab
assert "Run bounded onboarding Lab on first declared type" in ADD
assert "Verify exact rebuilt provider on first declared type" in ADD
assert "Rebuild publication after exact verification" in ADD
assert ADD.count("nuvio_client_lab.cjs") >= 2
assert ADD.index("Rebuild exact publication after activation decision") < ADD.index("Verify exact rebuilt provider on first declared type")
assert ADD.index("Verify exact rebuilt provider on first declared type") < ADD.index("Rebuild publication after exact verification")
assert ADD.index("Rebuild publication after exact verification") < ADD.index("Validate onboarding contracts")
assert "group: nuvio-provider-onboarding-stage-main" in ADD
assert "group: nuvio-provider-publish-main" in ADD
assert "Package validated provider transaction" in ADD
assert "Download validated provider transaction" in ADD
assert "git diff --cached --binary --full-index" in ADD
assert "git apply --3way --index" in ADD
# ProviderBase is derived automatically by NiakVIO onboarding. A provider may
# never enter catalogue staging with a manually-authored/missing base prerequisite.
assert "Stage clean NiakVIO ProviderBase and structured route knowledge" in ADD
assert "python scripts/add_provider.py stage --request" in ADD
assert "base_store.persist_clean_provider_seed(" in SCRIPT
assert "materialize_onboarding_bundle(" in SCRIPT
assert SCRIPT.index("base_store.persist_clean_provider_seed(") < SCRIPT.index("materialize_onboarding_bundle(")
assert '"clean_reconstruction_required": False' in SCRIPT
assert '"clean_reconstruction_verified": True' in SCRIPT

finalize_body = SCRIPT.split("def finalize(", 1)[1].split("\ndef main()", 1)[0]
assert 'scope = normalized_scope(current.get("scope") or "global")' in finalize_body
assert 'target_manifest_path = VF_MANIFEST if scope == "france" else MANIFEST' in finalize_body
assert 'prov["check_status"] = "live_unverified" if active else "pending_learning"' in finalize_body
assert 'prov["strict_activation_eligible"] = False' in finalize_body
assert 'prov["runtime_evidence_eligible"] = False' in finalize_body
assert '"onboarding_quick_live_unverified" if active' in finalize_body
assert '["live_native_validation_pending"]' in finalize_body
assert '"full_ok_claimed": False' in finalize_body

assert "site_structure_knowledge()" in SCRIPT
assert "VOLATILE_ROUTE_QUERY_KEYS" in SCRIPT
assert 'report.get("runtime_routes")' in SCRIPT
assert '"runtime_api_patterns"' in SCRIPT
assert '"discovered_routes"' in SCRIPT
assert '"routes": routes' in SCRIPT
PROBE = (ROOT / "scripts/probe_provider_site_structure.py").read_text(encoding="utf-8")
assert "useful_absolute_urls" in PROBE
assert '"image.tmdb.org"' in PROBE
assert "TMDB_HINT" not in PROBE

print("add provider workflow contract passed: routing=full-auto branding=dedicated full_native_labs=false")

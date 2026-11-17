#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-projection-reconcile.yml").read_text(encoding="utf-8")

assert wf.startswith("name: PROVIDERS - Projection Reconcile")
assert "group: niakvio-provider-projection-main" in wf
assert "cancel-in-progress: false" in wf, "projection lane must queue latest work without cancelling its in-flight publication"
assert "cancel-in-progress: true" not in wf, "projection lane must preserve the in-flight writer and requeue superseded work"
assert "FIELD_PROVIDER_PROJECTION_REQUEUED" in wf
assert "FIELD_PROVIDER_PROJECTION_SUPERSEDED" in wf
assert "FIELD_PROVIDER_PROJECTION_SUPERSEDED_DURING_REBUILD" in wf
assert "require_current_projection_head" in wf
assert "processed % 4" in wf
assert "processed=$((processed + 1))" in wf
assert "git fetch --no-tags origin main" in wf
for required in (
    "detect_provider_projection_drift.py",
    "materialize_provider_v3_one.py",
    "reconcile_targeted_provider_publication.py",
    "reindex_provider_publication_fingerprints.py",
    "publication_contract_fingerprint_test.py",
    "provider_publication_fingerprint_union_test.py",
    "provider_projection_drift_detector_test.py",
    "audit_provider_v3_static.py",
    "Prepare canonical durable static authority",
    "sanitize_provider_v3_core_metadata_routes.py",
    "provider_v3_core_metadata_route_sanitizer_test.py",
    "reconcile_provider_static_authority.py --apply",
    "materialize_provider_base_v3_store.py",
    "provider_base_store.py validate",
    "provider_clean_reconstruction_contract_test.py",
    "provider_stream_multiplicity_contract_test.py",
    "global_core_runtime_ownership_test.py",
    "provider_static_authority_france_only_test.py",
    "automation/provider-v3-static-knowledge.json",
    "reapply_published_overrides.py --check",
    "published_provider_lego_contract_test.py",
    "provider_js_lego_ownership_test.py",
    "build_hub46_native_manifest.py",
    "validate_release_integrity.py",
    'CURRENT_SHA="$(git rev-parse origin/main)"',
    'git merge-base --is-ancestor "$GITHUB_SHA" "$CURRENT_SHA"',
    "domain_refresh_publication_drift_gate.py",
    "git merge --no-ff --no-edit",
    "FIELD_PROVIDER_PROJECTION_PUBLISH_BLOCKED reason=executable_main_drift",
    "git push origin HEAD:main",
    "temp-current-bytes-full-provider-census.yml",
    'gh workflow run github-actions-gate.yml --repo "$GITHUB_REPOSITORY" --ref main',
    'gh workflow run release-finalize.yml --repo "$GITHUB_REPOSITORY" --ref main',
    'FIELD_PROVIDER_PROJECTION_RELEASE_HANDOFF sha=$FINAL_SHA',
    "--preserve-structured-data",
    "Projection reconcile mutated accepted provider-overrides.json.",
):
    assert required in wf, required

prepare = wf.split("- name: Prepare canonical durable static authority", 1)[1].split("- name: Detect exact published projection drift", 1)[0]
assert "python scripts/reconcile_provider_static_authority.py --apply" in prepare
assert "python scripts/sanitize_provider_v3_core_metadata_routes.py" in prepare
assert "python scripts/materialize_provider_base_v3_store.py" in prepare
assert "python scripts/provider_base_store.py validate" in prepare
assert "python tests/provider_clean_reconstruction_contract_test.py" in prepare
assert prepare.index("python scripts/sanitize_provider_v3_core_metadata_routes.py") < prepare.index("python scripts/materialize_provider_base_v3_store.py")
assert prepare.index("python scripts/materialize_provider_base_v3_store.py") < prepare.index("python tests/provider_clean_reconstruction_contract_test.py")
assert "python tests/provider_v3_core_metadata_route_sanitizer_test.py" in prepare
assert wf.index("- name: Prepare canonical durable static authority") < wf.index("- name: Detect exact published projection drift")

prove = wf.split("- name: Prove projection fixed point", 1)[1].split("- name: Build atomic provider publication", 1)[0]
assert prove.count("reindex_provider_publication_fingerprints.py") == 1, prove
assert prove.index("validate_published_provider_config.py") < prove.index("reconcile_provider_static_authority.py --apply"), prove
assert prove.index("reconcile_provider_static_authority.py --apply") < prove.index("sanitize_provider_v3_core_metadata_routes.py"), prove
assert prove.index("sanitize_provider_v3_core_metadata_routes.py") < prove.index("provider_v3_core_metadata_route_sanitizer_test.py"), prove
assert prove.index("provider_v3_core_metadata_route_sanitizer_test.py") < prove.index("reindex_provider_publication_fingerprints.py"), prove
assert prove.index("reindex_provider_publication_fingerprints.py") < prove.index("detect_provider_projection_drift.py"), prove
assert prove.index("detect_provider_projection_drift.py") < prove.index("audit_provider_v3_static.py"), prove
assert "python tests/provider_publication_fingerprint_union_test.py" in prove

publisher=wf.split("- name: Publish exact reconciled projection", 1)[1].split("- name: Report no-op", 1)[0]
assert publisher.index("git merge-base --is-ancestor") < publisher.index("domain_refresh_publication_drift_gate.py")
assert publisher.index("domain_refresh_publication_drift_gate.py") < publisher.index("git merge --no-ff --no-edit")
assert publisher.index("git merge --no-ff --no-edit") < publisher.index("git push origin HEAD:main")
assert "git rebase" not in publisher and "git push --force" not in publisher
assert "for attempt in 1 2 3 4" in publisher
assert "python scripts/validate_release_integrity.py" in publisher

assert "materialize_provider_v3_all.py" not in wf
assert 'steps.drift.outputs.count != \'0\'' in wf
assert "Projection reconcile staged a forbidden path." in wf
assert "PROVENANCE.json provider-overrides.json provider-v3-materialization.json" in wf
assert "provider-version-floors.json" in wf
assert "provider-version-floors\\.json" in wf
assert "automation/provider-v3-static-knowledge.json provider-bases/" in wf
assert "provider-bases/[^/]+" in wf
assert '"git","diff","--name-only","--","PROVENANCE.json","provider-bases/"' in wf
assert "from current_provider_scope import projection_active_provider_ids" in wf
assert 'print("provider_base_forced=true")' in wf
assert "ProviderBase durable store changed but active projection union is empty" in wf
assert "automation/provider-v3-static-knowledge.json" in wf
assert "Reconcile durable static authority at projection fixed point" in wf
static_fixed=wf.split("- name: Reconcile durable static authority at projection fixed point",1)[1].split("- name: Report projection byte no-op",1)[0]
assert "if: steps.drift.outputs.count == '0'" in static_fixed
assert "Static-authority preparation mutated a forbidden path." in static_fixed
assert "python scripts/reconcile_provider_static_authority.py --apply" in static_fixed
assert "python scripts/sanitize_provider_v3_core_metadata_routes.py" in static_fixed
assert "python tests/provider_v3_core_metadata_route_sanitizer_test.py" in static_fixed
assert "Static-authority reconciliation mutated a forbidden path." in static_fixed
assert "automation/provider-v3-static-knowledge\\.json|provider-v3-materialization\\.json" in static_fixed
assert 'CURRENT_SHA="$(git rev-parse origin/main)"' in static_fixed
assert 'if [ "$CURRENT_SHA" != "$GITHUB_SHA" ]; then' in static_fixed
assert "git push origin HEAD:main" in static_fixed
assert "FIELD_PROVIDER_STATIC_AUTHORITY_PUBLISHED" in static_fixed
print("provider projection reconcile workflow contract passed")

from sys import path as _pythonpath
_pythonpath.insert(0, str(ROOT / "scripts"))
from domain_refresh_publication_drift_gate import classify_drift
known_evidence = [
    "automation/provider-census-proof-history.json",
    "automation/provider-repair-batch-plan-latest.json",
    "automation/provider-census-sharded-42301845438.json",
    "automation/provider-waf-browser-session-42301845438.json",
    "automation/provider-waf-browser-session-latest.json",
]
assert classify_drift(known_evidence) == (True, []), "census evidence cannot starve provider publication"
for required_trigger in (
    "provider-overrides.json",
    "scripts/apply_provider_overrides.py",
    "scripts/normalize_core_media_policy.py",
    "scripts/provider_base_store.py",
    "scripts/provider_patches/**",
):
    assert required_trigger in wf, f"projection reconcile must auto-follow byte input {required_trigger}"

for source in ("provider-overrides.json", "manifest.json", "scripts/provider_base_store.py",
               "automation/provider-v3-static-knowledge.json", ".github/workflows/provider-projection-reconcile.yml"):
    assert classify_drift([*known_evidence, source]) == (False, [source]), source

# The workflow is transaction-critical; duplicated or truncated tail blocks can
# make GitHub reject the YAML before any run is created.
assert wf.count("- name: Build atomic provider publication") == 1
assert wf.count("- name: Publish exact reconciled projection") == 1
assert wf.count("- name: Finalize integrity and dispatch exact-head validation") == 1
final_handoff=wf.split("- name: Finalize integrity and dispatch exact-head validation",1)[1]
assert 'gh workflow run release-finalize.yml --repo "$GITHUB_REPOSITORY" --ref main' in final_handoff
assert '-f expected_sha="$FINAL_SHA" -F post_census=true' in final_handoff
assert final_handoff.index('gh workflow run security-final-gate.yml') < final_handoff.index('gh workflow run release-finalize.yml')
assert wf.count("- name: Prepare canonical durable static authority") == 1
assert wf.count("- name: Reconcile durable static authority at projection fixed point") == 1
assert wf.count("- name: Report projection byte no-op") == 1
assert "nuvio-client-id-state\\.json)$'; then" in wf

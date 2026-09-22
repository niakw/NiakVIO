#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-projection-reconcile.yml").read_text(encoding="utf-8")

assert wf.startswith("name: PROVIDERS - Projection Reconcile")
assert "group: niakvio-core-release-mutation-main" in wf
assert "cancel-in-progress: false" in wf
for required in (
    "detect_provider_projection_drift.py",
    "materialize_provider_v3_one.py",
    "reconcile_targeted_provider_publication.py",
    "reindex_provider_publication_fingerprints.py",
    "publication_contract_fingerprint_test.py",
    "provider_projection_drift_detector_test.py",
    "audit_provider_v3_static.py",
    "reapply_published_overrides.py --check",
    "published_provider_lego_contract_test.py",
    "provider_js_lego_ownership_test.py",
    "build_hub46_native_manifest.py",
    "validate_release_integrity.py",
    'CURRENT_SHA="$(git rev-parse origin/main)"',
    'if [ "$CURRENT_SHA" != "$GITHUB_SHA" ]',
    "git push origin HEAD:main",
    "temp-current-bytes-full-provider-census.yml",
    "--preserve-structured-data",
    "Projection reconcile mutated accepted provider-overrides.json.",
):
    assert required in wf, required

prove = wf.split("- name: Prove projection fixed point", 1)[1].split("- name: Build atomic provider publication", 1)[0]
assert prove.index("reindex_provider_publication_fingerprints.py") < prove.index("detect_provider_projection_drift.py"), prove
assert prove.count("reindex_provider_publication_fingerprints.py") == 1, prove

assert "materialize_provider_v3_all.py" not in wf
assert 'steps.drift.outputs.count != \'0\'' in wf
assert "Projection reconcile staged a forbidden path." in wf
assert "PROVENANCE.json provider-overrides.json provider-v3-materialization.json" not in wf
print("provider projection reconcile workflow contract passed")

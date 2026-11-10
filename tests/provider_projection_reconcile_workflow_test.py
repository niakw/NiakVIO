#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-projection-reconcile.yml").read_text(encoding="utf-8")

assert wf.startswith("name: PROVIDERS - Projection Reconcile")
assert "group: niakvio-core-release-mutation-main" in wf
assert "cancel-in-progress: false" in wf, "shared release mutation concurrency must never cancel finalization"
assert "cancel-in-progress: true" not in wf, "projection must queue; exact-head/drift guard rejects stale after acquisition"
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
    'git merge-base --is-ancestor "$GITHUB_SHA" "$CURRENT_SHA"',
    "domain_refresh_publication_drift_gate.py",
    "git merge --no-ff --no-edit",
    "FIELD_PROVIDER_PROJECTION_PUBLISH_BLOCKED reason=executable_main_drift",
    "git push origin HEAD:main",
    "temp-current-bytes-full-provider-census.yml",
    "--preserve-structured-data",
    "Projection reconcile mutated accepted provider-overrides.json.",
):
    assert required in wf, required

prove = wf.split("- name: Prove projection fixed point", 1)[1].split("- name: Build atomic provider publication", 1)[0]
assert prove.index("reindex_provider_publication_fingerprints.py") < prove.index("detect_provider_projection_drift.py"), prove
assert prove.count("reindex_provider_publication_fingerprints.py") == 1, prove

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
assert "PROVENANCE.json provider-overrides.json provider-v3-materialization.json" not in wf
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
for source in ("provider-overrides.json", "manifest.json", "scripts/provider_base_store.py",
               "automation/provider-v3-static-knowledge.json", ".github/workflows/provider-projection-reconcile.yml"):
    assert classify_drift([*known_evidence, source]) == (False, [source]), source

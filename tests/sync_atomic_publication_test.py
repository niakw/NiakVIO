#!/usr/bin/env python3
"""Guard ARCHI2 publication as one atomic main-branch transaction."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")
activation_adapter = (ROOT / "scripts" / "activation_preservation_core_rehash.py").read_text(encoding="utf-8")

assert workflow.count("git push origin HEAD:main") == 1, (
    "ARCHI2 must have exactly one main push after all publication gates"
)
assert 'git commit -m "chore: publish validated ARCHI2 provider transaction"' in workflow
assert "Publish atomic ARCHI2 transaction" in workflow
assert "Build canonical publication transaction" in workflow
assert "Audit content identity and media" in workflow
assert "provider_catalog.json" in workflow
assert workflow.count("python scripts/sync_release_versions.py") >= 2
assert workflow.count("--manifest manifest.json") >= 2
assert workflow.count('--previous "$NUVIO_PUBLISHED_MANIFEST_BASELINE"') >= 2
assert "Capture published manifest baseline" in workflow
assert workflow.count("      - 'scripts/activation_preservation_core_rehash.py'") == 2, (
    "Sync must run on preservation-adapter changes for both PR and main push"
)
assert workflow.count("      - 'tests/patched_provider_runtime_smoke.test.cjs'") == 2, (
    "Sync must run on provider runtime smoke changes for both PR and main push"
)

assert workflow.count("      - 'tests/sync_atomic_publication_test.py'") == 2, (
    "Sync must run on its publication contract test changes for both PR and main push"
)

stage_block = workflow[workflow.index("  stage-and-test:"):workflow.index("\n  publish:\n")]
publish_block = workflow[workflow.index("\n  publish:\n"):]

# Long validation is latest-wins and may be cancelled, but the actual main writer
# lane is publication-only, shared with Add Provider, and never cancels an active writer.
assert "group: nuvio-provider-stage-${{ github.event_name == 'pull_request' && github.event.pull_request.number || 'main' }}" in stage_block
assert "cancel-in-progress: true" in stage_block
assert "group: nuvio-provider-publish-main" in publish_block
assert "cancel-in-progress: false" in publish_block
assert "if: github.event_name != 'pull_request'" in publish_block, (
    "PR validation must never publish provider transactions to main"
)
assert "validated_sha: ${{ steps.validated-tree.outputs.sha }}" in stage_block
assert "Reject stale validated transaction" in publish_block
assert 'VALIDATED_SHA: ${{ needs.stage-and-test.outputs.validated_sha }}' in publish_block
assert 'FIELD_PROVIDER_PUBLICATION_SKIPPED reason=main_advanced' in publish_block
assert "steps.freshness.outputs.stale != 'true'" in publish_block

assert "ref: ${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || 'main' }}" in stage_block, (
    "serialized main runs must validate the current main tree when they actually start"
)
assert "fetch-depth: 0" in stage_block, (
    "full history is required so delayed push runs can still resolve github.event.before for Deep detection"
)

for forbidden_dns_coupling in [
    "scripts/provider_dns_preflight.mjs",
    "scripts/apply_dns_migration_overrides.py",
    "NUVIO_DNS_PREFLIGHT_RESULTS",
    "dns-preflight-report.json",
]:
    assert forbidden_dns_coupling not in workflow, forbidden_dns_coupling

build = workflow.index("Build canonical publication transaction")
first_version = workflow.index("python scripts/sync_release_versions.py", build)
first_activation = workflow.index("python scripts/activation_preservation_core_rehash.py", first_version)
audit = workflow.index("Audit content identity and media", first_activation)
final_version = workflow.index("python scripts/sync_release_versions.py", audit)
final_activation = workflow.index("python scripts/activation_preservation_core_rehash.py", final_version)
final_catalog = workflow.index("node engine_v2/scripts/bootstrap-provider-catalog.mjs", final_activation)
hashes = workflow.index("python scripts/generate_release_hashes.py", final_catalog)
commit = workflow.index('git commit -m "chore: publish validated ARCHI2 provider transaction"', hashes)
rebase = workflow.index("git rebase origin/main", commit)
post_rebase_hashes = workflow.index("python scripts/generate_release_hashes.py", rebase)
post_rebase_integrity = workflow.index("python scripts/validate_release_integrity.py", post_rebase_hashes)
push = workflow.index("git push origin HEAD:main", post_rebase_integrity)
verify = workflow.index("Verify exact published main", push)

assert build < first_version < first_activation < audit < final_version < final_activation < final_catalog < hashes < commit < rebase < post_rebase_hashes < post_rebase_integrity < push < verify
assert "git add -A providers" in workflow
assert "git add -A provider-bases" in workflow
assert workflow.index("git add -A providers", hashes) < commit
assert workflow.index("git add -A provider-bases", hashes) < commit
assert workflow.index("git add FILE-HASHES.json PATCH-SHA256SUMS.txt SHA256SUMS.json", rebase) < push
assert workflow.index("git commit --amend --no-edit", rebase) < push

assert "_baseline_matches_checked_out_head" in activation_adapter
assert "FIELD_ACTIVATION_PRESERVATION_BASELINE_STALE" in activation_adapter
assert "_rematerialize_current_core_after_restore()" in activation_adapter
assert '[sys.executable, "scripts/reapply_published_overrides.py", "--check"]' in activation_adapter

print("atomic ARCHI2 publication workflow test passed")

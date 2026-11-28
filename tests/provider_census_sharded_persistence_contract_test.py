#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/provider-census-sharded.yml").read_text(encoding="utf-8")

required = [
    "LEARN - Brain Repair Lab",
    ".github/triggers/provider-census-sharded.json",
    "FIELD_SHARDED_CENSUS_NOT_PERSISTED authority_schema_v3_required",
    'assert int(state.get("schemaVersion") or 0) >= 3',
    '"authorityRepairEligible" in row and "authorityAction" in row',
    "cp automation/provider-authority-status.json /tmp/provider-authority-status.json",
    "cp /tmp/provider-authority-status.json automation/provider-authority-status.json",
    "git add",
    "automation/provider-authority-status.json",
    "--sharded-census automation/provider-census-sharded-merged.json",
    "--sharded-census /tmp/provider-census-sharded.json",
    "--fallback-sharded-census automation/provider-census-sharded-latest.json",
    "shard_count: ${{ steps.pin.outputs.shard_count }}",
    "shards_json: ${{ steps.pin.outputs.shards_json }}",
    "target_providers: ${{ steps.pin.outputs.target_providers }}",
    "allow_pending_targets: ${{ steps.pin.outputs.allow_pending_targets }}",
    "FIELD_SHARDED_PENDING_BYTES_VERIFIED",
    "--allow-pending-targets",
    "fromJSON(needs.prepare.outputs.shards_json)",
    '--shard-count "${{ needs.prepare.outputs.shard_count }}"',
    "TARGET_PROVIDERS: ${{ needs.prepare.outputs.target_providers }}",
    "FIELD_SHARDED_CENSUS_PARTITION",
]
for needle in required:
    assert needle in workflow, f"missing sharded census authority persistence contract: {needle}"

assert "(github.event_name == 'push' || github.event_name == 'workflow_dispatch') && github.sha || 'main'" in workflow, (
    "push/dispatch census prepare must pin the exact event SHA"
)
assert "projection_runtime_visible_provider_count" in workflow
assert "[ \"$count\" -gt 120 ]" not in workflow, "causal push must not self-cancel on historical Global-only cardinality"
assert "authority=projection-runtime-visible" in workflow
assert "'.github/workflows/provider-census-sharded.yml'" in workflow
assert "provider-census-${{ github.event_name == 'workflow_run'" in workflow
assert "'routine' || 'proof' }}-main" in workflow
assert "github.event.workflow_run.name != 'PROVIDER - Bulk Onboarding'" in workflow
assert "github.event.workflow_run.name != 'PROVIDER - Bulk Activation'" in workflow

for required_trigger_guard in (
    "changed_paths=",
    ".github/triggers/provider-census-sharded.json",
    "explicit_trigger=true",
    'FIELD_SHARDED_CENSUS_PREPARE should_run=true',
    'census_scope="$trigger_scope"',
    'CENSUS_SCOPE: ${{ needs.prepare.outputs.census_scope }}',
):
    assert required_trigger_guard in workflow, f"missing explicit census trigger bypass: {required_trigger_guard}"

# Unresolved/targeted census is allowed to refresh current repair status, but it
# must never erase the last all-provider fan-out authority used by Brain.
assert workflow.count('CENSUS_SCOPE: ${{ needs.prepare.outputs.census_scope }}') >= 2
for marker in (
    'if [ "$CENSUS_SCOPE" = "all" ] && [ -z "$TARGET_PROVIDERS" ]; then',
    'FIELD_SHARDED_GLOBAL_FANOUT retained=true replaced=false',
    'FIELD_SHARDED_GLOBAL_FANOUT retained=false replaced=true scope=all',
    'd=json.load(open("/tmp/provider-census-sharded-summary.json"))',
):
    assert marker in workflow, f"missing global fan-out persistence guard: {marker}"

latest_copy = workflow.index("cp /tmp/provider-census-sharded.json automation/provider-census-sharded-latest.json")
scope_guard = workflow.rfind('if [ "$CENSUS_SCOPE" = "all" ] && [ -z "$TARGET_PROVIDERS" ]; then', 0, latest_copy)
assert scope_guard >= 0 and scope_guard < latest_copy

for required_stale_requeue in (
    'persist_base="$(git rev-parse HEAD)"',
    "FIELD_SHARDED_CENSUS_PERSIST_BASE",
    "FIELD_SHARDED_CENSUS_STALE",
    'echo "stale=true" >> "$GITHUB_OUTPUT"',
    "Requeue census on current main after concurrent advance",
    "steps.persist.outputs.stale == 'true'",
    "gh workflow run provider-census-sharded.yml",
    "-f persist=true",
    "FIELD_SHARDED_CENSUS_REQUEUE",
):
    assert required_stale_requeue in workflow, f"missing stale census requeue contract: {required_stale_requeue}"

for required_convergence in (
    "persist:",
    "inputs.persist == true",
    'id: persist',
    'echo "ok=true" >> "$GITHUB_OUTPUT"',
    "Continue Provider Lifecycle from fresh census",
    "FIELD_SHARDED_CENSUS_LIFECYCLE",
    "event_driven=false",
    "trigger=workflow_dispatch",
    "gh workflow run provider-disabled-lifecycle.yml",
    "dispatched=false reason=token-dispatch-denied",
    "Brain Autopilot must not run on an unstabilized active catalogue",
):
    assert required_convergence in workflow, f"missing sharded census convergence contract: {required_convergence}"

copy_status = workflow.index("cp automation/provider-census-sharded-status.json /tmp/provider-census-status.json")
guard = workflow.index("FIELD_SHARDED_CENSUS_NOT_PERSISTED authority_schema_v3_required")
reset = workflow.index("git reset --hard origin/main", guard)
rebuild_batch = workflow.index("--sharded-census /tmp/provider-census-sharded.json", reset)
fallback_batch = workflow.index("--fallback-sharded-census automation/provider-census-sharded-latest.json", rebuild_batch)
restore_authority = workflow.index("cp /tmp/provider-authority-status.json automation/provider-authority-status.json", fallback_batch)
persist_base = workflow.index('persist_base="$(git rev-parse HEAD)"', reset)
byte_stale_guard = workflow.index("reason=active-provider-byte-drift", persist_base)
remote_stale_guard = workflow.index("action=requeue-current-main", byte_stale_guard)
push = workflow.index("git push origin HEAD:main", remote_stale_guard)
requeue = workflow.index("Requeue census on current main after concurrent advance", push)
assert (
    copy_status < guard < reset < persist_base < byte_stale_guard
    < rebuild_batch < fallback_batch < restore_authority
    < remote_stale_guard < push < requeue
)
assert "cp /tmp/provider-repair-batch-plan.json automation/provider-repair-batch-plan-latest.json" not in workflow

# A source-pinned census can finish after newer WAF/residential evidence landed
# on main. Persistence must rebase that durable transport ledger onto the
# candidate status before canonical copy and batch-plan reconstruction.
persist_waf_merge = workflow.index(
    "python scripts/merge_waf_latest_evidence.py",
    persist_base,
)
transport_rebase = workflow.index(
    "--waf automation/provider-waf-browser-session-latest.json",
    persist_waf_merge,
)
transport_rebase_output = workflow.index(
    "--output /tmp/provider-census-status-current-waf.json",
    transport_rebase,
)
transport_rebase_move = workflow.index(
    "mv /tmp/provider-census-status-current-waf.json /tmp/provider-census-status.json",
    transport_rebase_output,
)
canonical_copy_after_rebase = workflow.index(
    "cp /tmp/provider-census-status.json automation/provider-census-status.json",
    transport_rebase_move,
)
rebuild_after_rebase = workflow.index(
    "python scripts/build_provider_repair_batch_plan.py",
    canonical_copy_after_rebase,
)
assert (
    reset < persist_waf_merge < transport_rebase < transport_rebase_output
    < transport_rebase_move < canonical_copy_after_rebase < rebuild_after_rebase
)
assert "FIELD_SHARDED_CENSUS_TRANSPORT_REBASE" in workflow
assert "source=current-main-waf-rebased-state" in workflow

merge_start = workflow.index("  merge:")
merge_steps = workflow.index("    steps:", merge_start)
merge_header = workflow[merge_start:merge_steps]
assert "contents: write" in merge_header
assert "actions: write" in merge_header, "census merge must be allowed to dispatch Provider Lifecycle after persisted evidence"

assert "automation/provider-waf-browser-session-effective.json" in workflow
probe_pos = workflow.index("python scripts/probe_waf_browser_session.py")
effective_merge_pos = workflow.index("python scripts/merge_waf_latest_evidence.py", probe_pos)
final_render_pos = workflow.index("--waf-browser-evidence automation/provider-waf-browser-session-effective.json", effective_merge_pos)
batch_plan_pos = workflow.index("python scripts/build_provider_repair_batch_plan.py", final_render_pos)
transport_merge_pos = workflow.index("python scripts/merge_waf_census_transport.py", final_render_pos)
state_render_pos = workflow.index("python scripts/render_provider_census_status_from_state.py", transport_merge_pos)
assert probe_pos < effective_merge_pos < final_render_pos < transport_merge_pos < state_render_pos < batch_plan_pos
assert "--waf automation/provider-waf-browser-session-effective.json" in workflow
assert "--status automation/provider-census-sharded-status.json" in workflow

print("provider sharded census authority persistence contract passed")

assert "gh workflow run provider-disabled-lifecycle.yml" in workflow
assert "gh workflow run provider-brain-autopilot.yml" not in workflow


# Targeted/partial validation must not pay the eight-shard full-census cost.
for marker in (
    'if [ -n "$target_providers" ]; then',
    'if [ "$target_count" -le 4 ]; then shard_count=1; else shard_count=2; fi',
    'elif [ "$census_scope" = "all" ]; then',
    'shard_count=8',
    'shard_count=4',
    'if [ -n "$TARGET_PROVIDERS" ]; then',
    'args+=(--provider "$TARGET_PROVIDERS")',
    'ALLOW_PENDING_TARGETS: ${{ needs.prepare.outputs.allow_pending_targets }}',
    'expected="${{ needs.prepare.outputs.shard_count }}"',
):
    assert marker in workflow, f"missing bounded sharded census latency contract: {marker}"

# Pending onboarding proof is explicitly targeted and never rematerializes/promotes staged bytes.
assert 'mode=pending-exact-staged-bytes' in workflow
assert 'allowPendingTargets requires explicit targetProviders' in workflow
assert 'source_workflow\" = \"PROVIDER - Bulk Onboarding' in workflow
print("pending onboarding sharded proof handoff contract passed")

for forbidden in (
    "python scripts/materialize_provider_v3_all.py",
    "python scripts/materialize_provider_v3_one.py",
    "python scripts/materialize_provider_base_v3_store.py",
    "python scripts/generate_language_manifests.py --manifest manifest.json --report health-report.json",
):
    assert forbidden not in workflow, forbidden
for marker in (
    "mode=active-all-exact-published-bytes-no-rematerialization",
    "mode=active-target-exact-published-bytes-no-rematerialization",
    "FIELD_SHARDED_SOURCE_BYTE_HASHES",
    "--verify-existing",
    "reason=active-provider-byte-drift",
    "authority=source-tested-hash-verified",
):
    assert marker in workflow, marker

# Pending onboarding evidence is isolated from canonical production freshness.
for marker in (
    "automation/provider-onboarding-pending-status-latest.json",
    "automation/provider-onboarding-pending-census-latest.json",
    "FIELD_PENDING_ONBOARDING_PROOF_ISOLATED",
    'if [ "$ALLOW_PENDING_TARGETS" = "true" ]; then',
    '-f target_providers="$TARGET_PROVIDERS"',
    '-f allow_pending_targets="$ALLOW_PENDING_TARGETS"',
):
    assert marker in workflow, marker
pending_branch=workflow.index('FIELD_PENDING_ONBOARDING_PROOF_ISOLATED')
canonical_copy=workflow.index('cp /tmp/provider-census-status.json automation/provider-census-status.json')
assert pending_branch < canonical_copy
assert "steps.persist.outputs.pending != 'true'" in workflow
assert "FIELD_SHARDED_ALL_SCOPE_FRESHNESS_LEDGER" in workflow
assert "stamp_provider_census_artifact_hashes.py" in workflow
assert "provider-census-all-status-latest.json" in workflow

# Authority must consume the same transaction's exact-byte FULL proof on all-scope
# runs. Classifying against the previously persisted ledger creates a one-run lag
# that can mark freshly FULL providers as architecture-nonfunctional.
preauthority = workflow.index("--json-output /tmp/provider-census-preauthority.json")
candidate_stamp = workflow.index("--output /tmp/provider-census-current-freshness.json", preauthority)
candidate_classify = workflow.index('"${authority_args[@]}"', candidate_stamp)
final_authority_render = workflow.index("--authority-status automation/provider-authority-status.json", candidate_classify)
assert preauthority < candidate_stamp < candidate_classify < final_authority_render
for marker in (
    "--census-status /tmp/provider-census-preauthority.json",
    "--production-freshness-status /tmp/provider-census-current-freshness.json",
    "FIELD_SHARDED_AUTHORITY_FRESHNESS source=current-candidate-all-scope",
    "FIELD_SHARDED_AUTHORITY_FRESHNESS source=persisted-all-scope",
):
    assert marker in workflow, f"missing same-transaction authority freshness contract: {marker}"

print("pending onboarding proof remains isolated from canonical active freshness")

# The sharded canonical status must not outrun raw schema-v6 exact-byte proof:
# on the SAME production commit, persist full selected-lane observations and a
# summary bound to this runId/SOURCE_SHA. Pending onboarding proof stays isolated.
canonical_status_copy = workflow.index("cp /tmp/provider-census-status.json automation/provider-census-status.json")
full_evidence_copy = workflow.index('cp /tmp/provider-census-sharded.json "automation/current-bytes-full-provider-census-${run_id}.json"')
current_summary = workflow.index("python scripts/summarize_current_census.py", full_evidence_copy)
latest_summary = workflow.index("automation/current-bytes-full-provider-census-latest-summary.json", current_summary)
canonical_stage = workflow.index('"automation/current-bytes-full-provider-census-${run_id}.json"', latest_summary)
canonical_push = workflow.index("git push origin HEAD:main", canonical_stage)
assert canonical_status_copy < full_evidence_copy < current_summary < latest_summary < canonical_stage < canonical_push
guard = workflow.rfind('if [ "$ALLOW_PENDING_TARGETS" != "true" ]; then', 0, full_evidence_copy)
assert guard > canonical_status_copy, "pending/onboarding observations must not become canonical current-byte proof"
summary_block = workflow[current_summary:latest_summary]
assert '--report "automation/current-bytes-full-provider-census-${run_id}.json"' in summary_block
assert "--state automation/provider-census-status.json" in summary_block
assert '--run-id "$run_id" --sha "$SOURCE_SHA"' in summary_block
assert "FIELD_SHARDED_CURRENT_BYTES_EVIDENCE_PUBLISHED" in workflow


# Targeted active-provider census is a row overlay, never a new fleet-wide
# freshness authority.
target_merge = workflow.index("python scripts/merge_targeted_provider_census_status.py")
target_base = workflow.index("--base automation/provider-census-status.json", target_merge)
target_candidate = workflow.index("--candidate /tmp/provider-census-status.json", target_merge)
target_marker = workflow.index("FIELD_SHARDED_TARGETED_CENSUS_OVERLAY", target_merge)
target_copy = workflow.index("cp /tmp/provider-census-status.json automation/provider-census-status.json", target_marker)
assert transport_rebase_move < target_merge < target_base < target_candidate < target_marker < target_copy
assert "FIELD_SHARDED_TARGETED_AUTHORITY_PRESERVED" in workflow
assert "FIELD_SHARDED_TARGETED_LATEST_SUMMARY_PRESERVED" in workflow
assert "python tests/targeted_provider_census_state_merge_test.py" in workflow
global_guard = 'if [ "$CENSUS_SCOPE" = "all" ] && [ -z "$TARGET_PROVIDERS" ]; then'
assert workflow.count(global_guard) >= 2
print("targeted active-provider census preserves fleet authority")


# Targeted run-specific evidence summary must use the target run's own state,
# while canonical fleet state/latest-summary stay row-scoped and fleet-owned.
target_state_copy = workflow.index(
    "cp /tmp/provider-census-status.json /tmp/provider-census-status-targeted-run-state.json"
)
target_summary_marker = workflow.index("FIELD_SHARDED_TARGETED_RUN_SUMMARY_STATE")
target_summary_state = workflow.index(
    'summary_state="/tmp/provider-census-status-targeted-run-state.json"',
    target_state_copy,
)
summary_call = workflow.index("python scripts/summarize_current_census.py", target_summary_state)
assert target_state_copy < target_summary_state < target_summary_marker < summary_call
assert '--state "$summary_state"' in workflow[summary_call:summary_call + 600]

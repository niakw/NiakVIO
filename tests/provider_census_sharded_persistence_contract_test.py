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
]
for needle in required:
    assert needle in workflow, f"missing sharded census authority persistence contract: {needle}"

assert "github.event_name == 'push' && github.sha || 'main'" in workflow, "push census prepare must pin the exact event SHA"

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
    'if [ "$CENSUS_SCOPE" = "all" ]; then',
    'FIELD_SHARDED_GLOBAL_FANOUT retained=true replaced=false',
    'FIELD_SHARDED_GLOBAL_FANOUT retained=false replaced=true scope=all',
    'd=json.load(open("/tmp/provider-census-sharded-summary.json"))',
):
    assert marker in workflow, f"missing global fan-out persistence guard: {marker}"

latest_copy = workflow.index("cp /tmp/provider-census-sharded.json automation/provider-census-sharded-latest.json")
scope_guard = workflow.rfind('if [ "$CENSUS_SCOPE" = "all" ]; then', 0, latest_copy)
assert scope_guard >= 0 and scope_guard < latest_copy

for required_convergence in (
    "persist:",
    "inputs.persist == true",
    'id: persist',
    'echo "ok=true" >> "$GITHUB_OUTPUT"',
    "Continue Brain Autopilot from fresh census",
    "FIELD_SHARDED_CENSUS_AUTOPILOT",
    "event_driven=true",
    "trigger=workflow_run",
):
    assert required_convergence in workflow, f"missing sharded census convergence contract: {required_convergence}"

copy_status = workflow.index("cp automation/provider-census-sharded-status.json /tmp/provider-census-status.json")
guard = workflow.index("FIELD_SHARDED_CENSUS_NOT_PERSISTED authority_schema_v3_required")
reset = workflow.index("git reset --hard origin/main", guard)
rebuild_batch = workflow.index("--sharded-census /tmp/provider-census-sharded.json", reset)
restore_authority = workflow.index("cp /tmp/provider-authority-status.json automation/provider-authority-status.json", rebuild_batch)
push = workflow.index("git push origin HEAD:main", restore_authority)
assert copy_status < guard < reset < rebuild_batch < restore_authority < push
assert "cp /tmp/provider-repair-batch-plan.json automation/provider-repair-batch-plan-latest.json" not in workflow

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

assert "gh workflow run provider-brain-autopilot.yml" not in workflow

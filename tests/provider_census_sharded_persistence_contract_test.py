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
]
for needle in required:
    assert needle in workflow, f"missing sharded census authority persistence contract: {needle}"

for required_trigger_guard in (
    "changed_paths=",
    ".github/triggers/provider-census-sharded.json",
    "explicit_trigger=true",
    'FIELD_SHARDED_CENSUS_PREPARE should_run=true',
):
    assert required_trigger_guard in workflow, f"missing explicit census trigger bypass: {required_trigger_guard}"

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
restore_authority = workflow.index("cp /tmp/provider-authority-status.json automation/provider-authority-status.json", reset)
push = workflow.index("git push origin HEAD:main", restore_authority)
assert copy_status < guard < reset < restore_authority < push

assert "automation/provider-waf-browser-session-effective.json" in workflow
probe_pos = workflow.index("python scripts/probe_waf_browser_session.py")
effective_merge_pos = workflow.index("python scripts/merge_waf_latest_evidence.py", probe_pos)
final_render_pos = workflow.index("--waf-browser-evidence automation/provider-waf-browser-session-effective.json", effective_merge_pos)
batch_plan_pos = workflow.index("python scripts/build_provider_repair_batch_plan.py", final_render_pos)
assert probe_pos < effective_merge_pos < final_render_pos < batch_plan_pos

print("provider sharded census authority persistence contract passed")

assert "gh workflow run provider-brain-autopilot.yml" not in workflow

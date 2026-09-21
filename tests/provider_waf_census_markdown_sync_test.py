#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/provider-waf-browser-session.yml").read_text(encoding="utf-8")

required = [
    "scripts/render_provider_census_status_from_state.py",
    "--status automation/provider-census-status.json",
    "--output PROVIDER_CENSUS_STATUS.md",
    "automation/provider-repair-batch-plan-latest.json \\",
    "PROVIDER_CENSUS_STATUS.md",
]

for needle in required:
    assert needle in workflow, f"missing WAF census Markdown sync contract: {needle}"

merge_pos = workflow.index("scripts/merge_waf_census_transport.py")
render_pos = workflow.index("scripts/render_provider_census_status_from_state.py", merge_pos)
git_add_pos = workflow.index("git add", render_pos)
markdown_add_pos = workflow.index("PROVIDER_CENSUS_STATUS.md", git_add_pos)
assert merge_pos < render_pos < git_add_pos < markdown_add_pos

print("provider WAF census Markdown synchronization contract passed")

state_renderer=(ROOT/"scripts/render_provider_census_status_from_state.py").read_text(encoding="utf-8")
assert "Residential probe" in state_renderer
assert "⚠️ unavailable · GitHub-only" in state_renderer
assert "residentialExitNodeEvidence" in state_renderer

assert "Residential replay" in state_renderer
assert "residentialProviderReplayClass" in state_renderer
assert "Network differential" in state_renderer
assert "networkDifferentialClass" in state_renderer

assert "Authority" in state_renderer
assert "lifecycleDisabledQueue" in state_renderer
assert "authorityRediscoveryQueue" in state_renderer
assert "authorityRepairEligible" in state_renderer
assert "--authority-status automation/provider-authority-status.json" in workflow

# Canonical census interpretation owns status generation. Changing that renderer
# must not launch a transport-only writer against an older persisted schema.
assert "'scripts/render_provider_census_status.py'" not in workflow
assert "'tests/provider_census_status_markdown_test.py'" not in workflow
assert "FIELD_WAF_CENSUS_BASE_NOT_READY authority_schema_v3_required" in workflow
assert 'assert int(state.get("schemaVersion") or 0) >= 3' in workflow
assert '"authorityRepairEligible" in row and "authorityAction" in row' in workflow

# Transport overlay writer must not auto-run from code/test pushes now that Repair owns WAF end-to-end.
assert "workflow_dispatch:" in workflow
assert "\n  push:" not in workflow.split("permissions:",1)[0]

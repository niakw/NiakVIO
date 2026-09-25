#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")

required=[
    "id-token: write",
    "group: provider-repair-main-v3",
    "Decide reusable Repair WAF evidence",
    "FIELD_REPAIR_WAF_REUSE",
    "select_provider_materialization_scope.py",
    "Prepare integrated Repair WAF/network qualification",
    "scripts/classify_provider_authority.py",
    'row.get("repairEligible") is True',
    "FIELD_REPAIR_WAF_SCOPE",
    "DISPATCH_TARGET_PROVIDER",
    'trigger.get("targetProviders")',
    "FIELD_REPAIR_RESIDENTIAL_REPLAY_SCOPE",
    "audit_provider_quick_yield_targeted.py",
    "probe_waf_browser_session.py",
    "Connect optional Repair Tailscale transport",
    "continue-on-error: true",
    "Select optional Repair residential exit",
    "FIELD_REPAIR_TAILSCALE_FALLBACK",
    "Replay Repair providers through residential exit when available",
    "merge_residential_provider_replay.py",
    "Apply integrated WAF qualification to Repair census",
    "merge_waf_census_transport.py",
    "--authority-status automation/provider-authority-status.json",
    "FIELD_REPAIR_WAF_QUALIFIED",
    "Reapply integrated WAF qualification after canonical Repair",
    "FIELD_REPAIR_WAF_FINAL",
    "automation/provider-waf-browser-session-latest.json",
]
for needle in required:
    assert needle in wf, f"missing Repair/WAF integration contract: {needle}"

reuse=wf.index("- name: Decide reusable Repair WAF evidence")
prepare=wf.index("- name: Prepare integrated Repair WAF/network qualification")
authority=wf.index("scripts/classify_provider_authority.py",prepare)
pre_render=wf.index("scripts/render_provider_census_status.py /tmp/provider-repair-waf-network.json",prepare)
connect=wf.index("- name: Connect optional Repair Tailscale transport")
merge=wf.index("- name: Apply integrated WAF qualification to Repair census")
canonical=wf.index("- name: Run canonical recognition and correction only for unresolved providers")
final_merge=wf.index("- name: Reapply integrated WAF qualification after canonical Repair")
persist=wf.index("- name: Persist Repair census state")
assert reuse < prepare < authority < pre_render < connect < merge < canonical < final_merge < persist
prepare_block=wf[prepare:connect]
assert "steps.repair_waf_reuse.outputs.reuse != 'true'" in prepare_block
assert 'providers=sorted(set(providers)&requested)' in prepare_block
assert 'DISPATCH_TARGET_PROVIDER' in prepare_block
assert "import os" in prepare_block
reuse_block=wf[reuse:prepare]
assert 'git log -1 --format=%H -- "$waf"' in reuse_block
assert '--base "$source"' in reuse_block
assert '"mode") or "all"' in reuse_block
assert 'residential.get("available") is True' in reuse_block
assert 'replay.get("available") is True' in reuse_block
final_block=wf[final_merge:persist]
assert "if: ${{ always() }}" in final_block
assert "merge_waf_census_transport.py" in final_block
assert "render_provider_census_status_from_state.py" in final_block
assert "FIELD_REPAIR_WAF_FINAL" in final_block
assert "Reject superseded Repair SHA before expensive work" in wf
assert "FIELD_REPAIR_SUPERSEDED_EARLY" in wf

# Tailscale is enhancement, never a prerequisite for Repair.
connect_block=wf[connect:merge]
assert "continue-on-error: true" in connect_block
assert "timeout-minutes: 4" in connect_block
assert "--unavailable-reason" in connect_block
assert 'scope_path=Path("/tmp/repair-waf-targets.json")' in connect_block
assert 'selected["providerCount"]=len(providers)' in connect_block
assert "tailscale-not-configured" in connect_block
assert "tailscale-offline-or-unavailable" in connect_block

# WAF evidence must be part of the durable Repair evidence commit.
persist_block=wf[persist:]
assert 'cp automation/provider-waf-browser-session-latest.json "$tmp/provider-waf-browser-session-latest.json"' in persist_block
assert 'cp "$tmp/provider-waf-browser-session-latest.json" automation/provider-waf-browser-session-latest.json' in persist_block
assert "git add automation/provider-waf-browser-session-latest.json" in persist_block
assert "FIELD_REPAIR_CANONICAL_LEDGER_STALE" in persist_block
assert "FIELD_REPAIR_CANONICAL_LEDGER_SKIPPED" in persist_block
assert "FIELD_REPAIR_FRESH_CENSUS_DISPATCH" in persist_block
assert "FIELD_REPAIR_CONCURRENT_PROVIDER_DRIFT" in persist_block
assert "FIELD_REPAIR_FRESH_CENSUS_SKIPPED" in persist_block
assert "select_provider_materialization_scope.py" in persist_block
assert "provider_input_drift=0" in persist_block
assert '[ "$provider_input_drift" = "1" ]' in persist_block

print("Repair-integrated WAF/Tailscale qualification workflow contract passed")

pipeline=(ROOT/"scripts/run_provider_repair_pipeline_v6.py").read_text(encoding="utf-8")
assert 'WAF_STATUS = ROOT / "automation" / "provider-waf-browser-session-latest.json"' in pipeline
assert pipeline.count('"--waf-browser-evidence", str(WAF_STATUS.relative_to(ROOT))') >= 2
assert pipeline.count('"--authority-status", str(AUTHORITY_STATUS.relative_to(ROOT))') >= 2

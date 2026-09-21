#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")

required=[
    "id-token: write",
    "group: provider-census-waf-main",
    "Prepare integrated Repair WAF/network qualification",
    "FIELD_REPAIR_WAF_SCOPE",
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
    "FIELD_REPAIR_WAF_QUALIFIED",
    "automation/provider-waf-browser-session-latest.json",
]
for needle in required:
    assert needle in wf, f"missing Repair/WAF integration contract: {needle}"

prepare=wf.index("- name: Prepare integrated Repair WAF/network qualification")
connect=wf.index("- name: Connect optional Repair Tailscale transport")
merge=wf.index("- name: Apply integrated WAF qualification to Repair census")
canonical=wf.index("- name: Run canonical recognition and correction only for unresolved providers")
assert prepare < connect < merge < canonical

# Tailscale is enhancement, never a prerequisite for Repair.
connect_block=wf[connect:merge]
assert "continue-on-error: true" in connect_block
assert "--unavailable-reason" in connect_block
assert "tailscale-not-configured" in connect_block
assert "tailscale-offline-or-unavailable" in connect_block

# WAF evidence must be part of the durable Repair evidence commit.
persist=wf.index("- name: Persist Repair census state")
persist_block=wf[persist:]
assert 'cp automation/provider-waf-browser-session-latest.json "$tmp/provider-waf-browser-session-latest.json"' in persist_block
assert 'cp "$tmp/provider-waf-browser-session-latest.json" automation/provider-waf-browser-session-latest.json' in persist_block
assert "git add automation/provider-waf-browser-session-latest.json" in persist_block

print("Repair-integrated WAF/Tailscale qualification workflow contract passed")

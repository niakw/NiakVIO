#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-waf-browser-session.yml").read_text(encoding="utf-8")

required=[
    "id-token: write",
    "TS_OAUTH_CLIENT_ID: ${{ secrets.TS_OAUTH_CLIENT_ID }}",
    "TS_AUDIENCE: ${{ secrets.TS_AUDIENCE }}",
    "TS_EXIT_NODE: ${{ secrets.TS_EXIT_NODE }}",
    "TS_TAG_NAME: ${{ secrets.TS_TAG_NAME }}",
    "Normalize private Tailscale CI tag",
    'raw="${TS_TAG_NAME:-niakvio-ci}"',
    '*) normalized="tag:$raw" ;;',
    "TS_ACTION_TAG=%s",
    "tailscale/github-action@306e68a486fd2350f2bfc3b19fcd143891a4a2d8",
    "oauth-client-id: ${{ env.TS_OAUTH_CLIENT_ID }}",
    "audience: ${{ env.TS_AUDIENCE }}",
    "args: --accept-dns=false",
    'sudo tailscale set --exit-node="$TS_EXIT_NODE" --exit-node-allow-lan-access=false',
    "tag:niakvio-ci -> autogroup:internet policy",
    "id: tailscale_connect",
    "continue-on-error: true",
    "timeout-minutes: 4",
    "steps.tailscale_connect.outcome == 'success'",
    "id: select_residential_exit",
    "id: residential_probe",
    "--unavailable-reason \"$reason\"",
    "tailscale-connect-failed",
    "exit-node-unavailable",
    "residential-probe-failed",
    "scripts/merge_waf_network_profiles.py",
    "--status automation/provider-census-status.json",
    "Resolve explicit transport target cohort",
    "push-triggered WAF qualification requires targetProviders",
    "targeted WAF cohort is capped at 12",
    "FIELD_WAF_EXPLICIT_TARGETS",
    "WAF_ATTEMPTS=1",
    "WAF_WORKERS=4",
    "Merge targeted refresh into complete WAF evidence ledger",
    "scripts/merge_targeted_waf_refresh.py",
    "reuseExistingEvidence",
    "WAF_REUSE_EXISTING",
    "WAF_EVIDENCE_SOURCE_SHA",
    "Validate existing WAF evidence reuse against unchanged provider bytes",
    "select_provider_materialization_scope.py",
    "FIELD_WAF_EVIDENCE_REUSE_SAFE",
]
for needle in required:
    assert needle in wf, f"missing Tailscale WAF contract: {needle}"

for forbidden in (
    "oauth-secret:",
    "ifconfig.me",
    "api.ipify.org",
    "icanhazip",
    "curl -s https://ip",
    "tailscale status --json",
    "tailscale ping --timeout",
    "log-mode:",
    'echo "$TS_EXIT_NODE"',
):
    assert forbidden not in wf, f"privacy/security regression: {forbidden}"

baseline=wf.index("Reprobe persisted WAF lanes on GitHub-hosted network")
connect=wf.index("Connect ephemeral Tailscale diagnostic node")
activate=wf.index("Select private residential exit node")
residential=wf.index("Reprobe WAF lanes through private residential exit")
merge=wf.index("Merge residential exit evidence without node identity")
assert connect < baseline < activate < residential < merge

print("Tailscale residential WAF workflow contract passed")

assert wf.count("--network-report provider-v3-quick-yield.json") == 2

# WAF/Tailscale is now its own explicit transport lane. Full/sharded census
# may still serialize census work, but they no longer own the canonical WAF
# latest and must not block residential qualification.
temp=(ROOT/".github/workflows/temp-current-bytes-full-provider-census.yml").read_text(encoding="utf-8")
sharded=(ROOT/".github/workflows/provider-census-sharded.yml").read_text(encoding="utf-8")
repair=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
assert "group: provider-waf-transport-main" in wf
assert "cancel-in-progress: true" in wf
assert "group: provider-census-waf-main" in temp
assert "cancel-in-progress: true" in temp
assert "group: provider-census-waf-main" in sharded
assert "cancel-in-progress: false" in sharded
assert "group: provider-repair-main-v2" in repair, repair[:600]
assert "cancel-in-progress: ${{ github.event_name == 'push' }}" in repair, repair[:600]
assert "workflow_dispatch:" in temp
assert "FIELD_REPAIR_CANONICAL_LEDGER_STALE" in repair
assert "FIELD_REPAIR_CANONICAL_LEDGER_SKIPPED" in repair
assert "FIELD_REPAIR_FRESH_CENSUS_DISPATCH" in repair
assert "gh workflow run temp-current-bytes-full-provider-census.yml" in repair
assert "gh workflow run provider-waf-browser-session.yml --ref main" not in temp
assert "gh workflow run provider-waf-browser-session.yml --ref main" not in sharded
assert "Prepare integrated Repair WAF/network qualification" in repair
assert "if: ${{ github.ref == 'refs/heads/main' }}" in wf

assert "FIELD_REPAIR_SUPERSEDED_EARLY" in repair

# WAF remains explicit: manual or a dedicated trigger-file push only. Ordinary
# repository pushes still cannot start transport qualification.
assert "workflow_dispatch:" in wf
header=wf.split("permissions:",1)[0]
assert "\n  push:" in header
assert "'.github/triggers/provider-waf-browser-session'" in header

# Reusing existing WAF evidence is allowed only after provider-impact drift is
# proven absent, and expensive network/native setup must be skipped.
reuse=wf.index("Validate existing WAF evidence reuse against unchanged provider bytes")
setup_java=wf.index("actions/setup-java@")
connect=wf.index("Connect ephemeral Tailscale diagnostic node")
assert reuse < setup_java < connect
assert "env.WAF_REUSE_EXISTING != '1'" in wf[setup_java:connect]

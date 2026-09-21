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
    "steps.tailscale_connect.outcome == 'success'",
    "id: select_residential_exit",
    "id: residential_probe",
    "--unavailable-reason \"$reason\"",
    "tailscale-connect-failed",
    "exit-node-unavailable",
    "residential-probe-failed",
    "scripts/merge_waf_network_profiles.py",
    "--status automation/provider-census-status.json",
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

# Census + standalone WAF share an observational serialization lane. Repair
# owns integrated transport qualification and uses a separate lane so GitHub's
# one-pending-run concurrency slot cannot starve a Repair behind census pushes.
temp=(ROOT/".github/workflows/temp-current-bytes-full-provider-census.yml").read_text(encoding="utf-8")
sharded=(ROOT/".github/workflows/provider-census-sharded.yml").read_text(encoding="utf-8")
repair=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
for source in (wf,temp,sharded):
    assert "group: provider-census-waf-main" in source, source[:400]
    assert "cancel-in-progress: false" in source, source[:400]
assert "group: provider-repair-main" in repair, repair[:600]
assert "cancel-in-progress: false" in repair, repair[:600]
assert "workflow_dispatch:" in temp
assert "FIELD_REPAIR_CANONICAL_LEDGER_STALE" in repair
assert "FIELD_REPAIR_CANONICAL_LEDGER_SKIPPED" in repair
assert "FIELD_REPAIR_FRESH_CENSUS_DISPATCH" in repair
assert "gh workflow run temp-current-bytes-full-provider-census.yml" in repair
assert "gh workflow run provider-waf-browser-session.yml --ref main" not in temp
assert "gh workflow run provider-waf-browser-session.yml --ref main" not in sharded
assert "Prepare integrated Repair WAF/network qualification" in repair
assert "if: ${{ github.ref == 'refs/heads/main' }}" in wf

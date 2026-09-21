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

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
    "tailscale/github-action@306e68a486fd2350f2bfc3b19fcd143891a4a2d8",
    "oauth-client-id: ${{ env.TS_OAUTH_CLIENT_ID }}",
    "audience: ${{ env.TS_AUDIENCE }}",
    "log-mode: quiet",
    'tailscale ping --timeout=10s "$TS_EXIT_NODE" >/dev/null',
    'sudo tailscale set --exit-node="$TS_EXIT_NODE" --exit-node-allow-lan-access=false',
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
    'echo "$TS_EXIT_NODE"',
):
    assert forbidden not in wf, f"privacy/security regression: {forbidden}"

baseline=wf.index("Reprobe persisted WAF lanes on GitHub-hosted network")
connect=wf.index("Connect ephemeral Tailscale diagnostic node")
activate=wf.index("Select private residential exit node")
residential=wf.index("Reprobe WAF lanes through private residential exit")
merge=wf.index("Merge residential exit evidence without node identity")
assert baseline < connect < activate < residential < merge

print("Tailscale residential WAF workflow contract passed")

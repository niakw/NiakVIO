#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/native-corpus-device-targeted.yml").read_text(encoding="utf-8")

required = (
    "target_providers:",
    "residential_exit:",
    ".github/triggers/native-residential-transport-targeted.json",
    "id-token: write",
    "TS_OAUTH_CLIENT_ID: ${{ secrets.TS_OAUTH_CLIENT_ID }}",
    "TS_AUDIENCE: ${{ secrets.TS_AUDIENCE }}",
    "TS_EXIT_NODE: ${{ secrets.TS_EXIT_NODE }}",
    "TS_TAG_NAME: ${{ secrets.TS_TAG_NAME }}",
    "tailscale/github-action@306e68a486fd2350f2bfc3b19fcd143891a4a2d8",
    "Select residential exit immediately before native runtime",
    'sudo tailscale set --exit-node="$TS_EXIT_NODE" --exit-node-allow-lan-access=false',
    "FIELD_NATIVE_RESIDENTIAL_EXIT active=true",
    "native-target-provider-scope.json",
    "NIAKVIO_PROVIDER_SCOPE_MATRIX=",
    "NIAKVIO_TARGET_PROVIDER=",
    'if residential and not providers:',
    'raise SystemExit("residential native transport proof requires explicit target provider(s)")',
    "targeted native provider cohort is capped at 8",
    "native-corpus-${{ matrix.device }}-${{ matrix.provider }}-${{ matrix.fixture }}-${{ github.run_id }}",
    "inputs.device == 'all' && inputs.target_providers == ''",
)
for needle in required:
    assert needle in workflow, needle

connect = workflow.index("Connect native client host to Tailscale")
exit_node = workflow.index("Select residential exit immediately before native runtime")
prepare = workflow.index("Prepare exact upstream client checkout")
mobile_snapshot = workflow.index("Create Mobile AVD snapshot on cache miss")
tv_snapshot = workflow.index("Create TV AVD snapshot on cache miss")
desktop_runtime = workflow.index("Execute six works across every provider in official Desktop runtime")
mobile_runtime = workflow.index("Execute six works across every provider in isolated Mobile emulator")
tv_runtime = workflow.index("Execute six works across every provider in isolated Android TV emulator")
assert connect < prepare < mobile_snapshot < exit_node
assert connect < prepare < tv_snapshot < exit_node
assert exit_node < desktop_runtime < mobile_runtime < tv_runtime

assert "continue-on-error: true" not in workflow[connect:exit_node], "native residential connection must fail closed"
assert "matrix.residential == true" in workflow

print("native targeted residential transport workflow contract passed")

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
    "tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c",
    "Select and attest residential exit immediately before native runtime",
    "scripts/verify_waf_exit_route.py baseline",
    "scripts/verify_waf_exit_route.py verify",
    'sudo tailscale set --exit-node="$TS_EXIT_NODE" --exit-node-allow-lan-access=false',
    "FIELD_NATIVE_RESIDENTIAL_EXIT active=true egress_attested=true",
    "FIELD_NATIVE_RESIDENTIAL_DNS tailscale_accept_dns=false resolver_equivalence=unverified",
    "native-target-provider-scope.json",
    "Enable targeted Mobile same-source engine differential",
    "NIAKVIO_NATIVE_COMPARE_ENGINES=1",
    "FIELD_NATIVE_ENGINE_COMPARE_MODE enabled=true",
    "native_manifest_projection import active_provider_manifest",
    '"manifest": "manifest.json"',
    '"manifest": "vf/manifest.json"',
    '--manifest "$NIAKVIO_TARGET_MANIFEST"',
    "NIAKVIO_PROVIDER_SCOPE_MATRIX=",
    "NIAKVIO_TARGET_PROVIDER=",
    'if residential and not providers:',
    'raise SystemExit("residential native transport proof requires explicit target provider(s)")',
    "targeted native provider cohort is capped at 8",
    "native-corpus-${{ matrix.device }}-${{ matrix.provider }}-${{ matrix.projection }}-${{ matrix.fixture }}-${{ github.run_id }}",
    "inputs.device == 'all' && inputs.target_providers == ''",
)
for needle in required:
    assert needle in workflow, needle

connect = workflow.index("Connect native client host to Tailscale")
exit_node = workflow.index("Select and attest residential exit immediately before native runtime")
prepare = workflow.index("Checkout accepted official client and stage corpus once")
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
assert "matrix.device == 'mobile' && matrix.provider != 'declared-type'" in workflow
assert "manifest-hub46.json" not in workflow
assert "native-hub46/manifest.json" not in workflow
assert workflow.count('--manifest "$NIAKVIO_TARGET_MANIFEST"') == 3
assert "matrix.manifest" in workflow and "matrix.projection" in workflow
assert "Prime Android adb server" in workflow
assert "prime_android_lab_adb.sh" in workflow
assert "avd-v5-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in workflow
assert "avd-v5-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in workflow
assert "~/.android/debug.keystore" in workflow
assert "avd-v2-" not in workflow
assert "harden_nuvio_mobile_device_test.py" not in workflow
assert "prepare_native_corpus_client.py mobile" in workflow

print("native targeted residential transport workflow contract passed")

#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/native-corpus-device-targeted.yml").read_text(encoding="utf-8")

required = (
    "target_providers:",
    "target_fixture:",
    "residential_exit:",
    ".github/triggers/native-residential-transport-targeted.json",
    "id-token: write",
    "TS_OAUTH_CLIENT_ID: ${{ secrets.TS_OAUTH_CLIENT_ID }}",
    "TS_AUDIENCE: ${{ secrets.TS_AUDIENCE }}",
    "TS_EXIT_NODE: ${{ secrets.TS_EXIT_NODE }}",
    "TS_TAG_NAME: ${{ secrets.TS_TAG_NAME }}",
    "tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c",
    "Snapshot pre-Tailscale DNS policy and baseline egress",
    "scripts/preserve_runner_dns.py snapshot",
    "Restore pre-Tailscale DNS policy before native runtime",
    "scripts/preserve_runner_dns.py restore",
    "Select and attest residential exit immediately before native runtime",
    "scripts/verify_waf_exit_route.py baseline",
    "scripts/verify_waf_exit_route.py verify",
    "tests/waf_exit_route_attestation_test.py",
    'scripts/verify_waf_exit_route.py select --exit-node "$TS_EXIT_NODE" --attempts 3',
    "FIELD_NATIVE_RESIDENTIAL_EXIT active=true egress_attested=true",
    "FIELD_NATIVE_RESIDENTIAL_DNS tailscale_accept_dns=false action_override_restored=true resolver_equivalence=runner_pre_tailnet",
    "native-target-provider-scope.json",
    "Enable targeted Mobile same-source engine differential",
    "NIAKVIO_NATIVE_COMPARE_ENGINES=1",
    "FIELD_NATIVE_ENGINE_COMPARE_MODE enabled=true",
    "NIAKVIO_NATIVE_PLAYER_GATE_BLOCKING=1",
    "FIELD_NATIVE_PLAYER_GATE_MODE blocking=true requirement=production_playback_verified",
    "native_manifest_projection import active_provider_manifest",
    '"manifest": "manifest.json"',
    '"manifest": "vf/manifest.json"',
    '--manifest "$NIAKVIO_TARGET_MANIFEST"',
    "NIAKVIO_PROVIDER_SCOPE_MATRIX=",
    "NIAKVIO_TARGET_PROVIDER=",
    "NIAKVIO_TARGET_FIXTURE: ${{ matrix.fixture }}",
    'target_fixture = str(payload.get("targetFixture") or "").strip()',
    'raise SystemExit(f"unknown native target fixture: {target_fixture}")',
    'if residential and not providers:',
    'raise SystemExit("residential native transport proof requires explicit target provider(s)")',
    "targeted native provider cohort is capped at 8",
    "native-corpus-${{ matrix.device }}-${{ matrix.provider }}-${{ matrix.projection }}-${{ matrix.fixture }}-${{ github.run_id }}",
    "inputs.device == 'all' && inputs.target_providers == '' && inputs.target_fixture == ''",
    "Diagnose sanitized targeted native evidence for Brain",
    "engine_v2/scripts/diagnose-native-reader.mjs",
    "FIELD_NATIVE_TARGETED_BRAIN_DIAGNOSIS",
    "${{ matrix.device }}-native-corpus-*-brain.json",
    "retention-days: 8",
)
for needle in required:
    assert needle in workflow, needle

dns_snapshot = workflow.index("Snapshot pre-Tailscale DNS policy and baseline egress")
connect = workflow.index("Connect native client host to Tailscale")
dns_restore = workflow.index("Restore pre-Tailscale DNS policy before native runtime")
exit_node = workflow.index("Select and attest residential exit immediately before native runtime")
prepare = workflow.index("Checkout accepted official client and stage corpus once")
mobile_snapshot = workflow.index("Create Mobile AVD snapshot on cache miss")
tv_snapshot = workflow.index("Create TV AVD snapshot on cache miss")
desktop_runtime = workflow.index("Execute focused provider in official macOS Desktop runtime")
mobile_runtime = workflow.index("Execute six works across every provider in isolated Mobile emulator")
tv_runtime = workflow.index("Execute six works across every provider in isolated Android TV emulator")
assert prepare < mobile_snapshot < dns_snapshot < connect < dns_restore < exit_node
assert prepare < tv_snapshot < dns_snapshot < connect < dns_restore < exit_node
assert exit_node < desktop_runtime < mobile_runtime < tv_runtime

assert "continue-on-error: true" not in workflow[connect:exit_node], "native residential connection must fail closed"
connect_block = workflow[connect:dns_restore]
attest_block = workflow[exit_node:desktop_runtime]
assert "timeout-minutes: 4" in connect_block, "Tailscale connect must be wall-clock bounded"
assert "timeout-minutes: 2" in attest_block, "residential egress attestation must be wall-clock bounded"
assert "matrix.residential == true" in workflow
assert "matrix.device == 'mobile' && matrix.provider != 'declared-type'" in workflow
assert "manifest-hub46.json" not in workflow
assert "native-hub46/manifest.json" not in workflow
# TV now prepares the official TMDB BuildConfig capability before the
# usual Desktop/Mobile/TV staging; all four calls must preserve the same
# canonical Global/VF projection, not a retired hub46 route.
assert workflow.count('--manifest "$NIAKVIO_TARGET_MANIFEST"') == 4
assert 'prepare_native_tv_tmdb_contract.py --repo-root niakvio --client-root nuvio-tv' in workflow
assert "matrix.manifest" in workflow and "matrix.projection" in workflow
assert "Prime Android adb server" in workflow
assert "prime_android_lab_adb.sh" in workflow
assert "avd-v5-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in workflow
assert "avd-v5-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in workflow
assert "~/.android/debug.keystore" in workflow
assert "avd-v2-" not in workflow
assert "harden_nuvio_mobile_device_test.py" not in workflow
assert "prepare_native_corpus_client.py mobile" in workflow
assert "matrix.device == 'desktop' && 'macos-15' || 'ubuntu-latest'" in workflow
assert "git -C nuvio-desktop lfs pull" in workflow
assert "native_desktop_upstream_test_compat.py nuvio-desktop" in workflow
assert ":composeApp:buildMacosPlayerBridge" in workflow
assert ":composeApp:prepareMacosPlayerRuntime" in workflow
assert "run_native_corpus_desktop_suite.sh" in workflow
assert 'test "$(uname -s)" = "Darwin"' in workflow
assert 'restage_native_corpus_client.py desktop --fixture "$fixture"' not in workflow
assert '--provider "$NIAKVIO_TARGET_PROVIDER" --manifest "$NIAKVIO_TARGET_MANIFEST"' in workflow
assert '"fixture": target_fixture or "all"' in workflow
connect_tailnet = workflow.index("Connect native client host to Tailscale")
setup_jdk = workflow.index("Set up JDK")
checkout_client = workflow.index("Checkout accepted official client and stage corpus once")
setup_gradle = workflow.index("Set up Gradle runtime")
attest_exit = workflow.index("Select and attest residential exit immediately before native runtime")
desktop_runtime = workflow.index("Execute focused provider in official macOS Desktop runtime")
clear_exit = workflow.index("Clear native residential exit and transient network state")
brain_diag = workflow.index("Diagnose sanitized targeted native evidence for Brain")
upload = workflow.index("Upload sanitized native corpus logs")
assert setup_jdk < checkout_client < setup_gradle < dns_snapshot < connect_tailnet < dns_restore < attest_exit < desktop_runtime < clear_exit
assert clear_exit < brain_diag < upload
assert workflow.count("Connect native client host to Tailscale") == 1
assert "verify_waf_exit_route.py clear || true" in workflow
assert workflow.count("verify_waf_exit_route.py baseline") == 1
assert workflow.index("verify_waf_exit_route.py baseline") < connect_tailnet
assert 'rm -f "${NIAKVIO_NATIVE_DNS_STATE:-}" "${NIAKVIO_NATIVE_EGRESS_STATE:-}"' in workflow
assert "for attempt in 1 2 3 4 5" not in workflow

print("native targeted residential transport workflow contract passed")

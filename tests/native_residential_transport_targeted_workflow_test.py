#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/native-corpus-device-targeted.yml").read_text(encoding="utf-8")

required = (
    "Resolve latest official client HEADs (audit contract drift first)",
    "scripts/check_nuvio_client_upstreams.py",
    "--clients nuvio-tv nuvio-mobile nuvio-desktop",
    "--paths-only --no-fail",
    "scripts/resolve_nuvio_lab_heads.py",
    "health-output/native-target-current-client-drift.json",
    "health-output/native-target-current-client-heads.json",
    "latest_official_head=true accepted_ref_only_for_audit=true",
    "steps.heads.outputs.tv_sha",
    "steps.heads.outputs.mobile_sha",
    "steps.heads.outputs.desktop_sha",
    "target_providers:",
    "target_fixture:",
    "residential_exit:",
    "source_sha:",
    "brain_candidate_experiment_json:",
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

assert "steps.resolve.outputs.tv_sha" not in workflow
assert "steps.resolve.outputs.desktop_sha" not in workflow
assert 'ref = str((clients.get(key) or {}).get("accepted_ref") or "")' not in workflow
assert workflow.index("Resolve latest official client HEADs") < workflow.index("Resolve selected devices and manifests")
assert "no stale fallback" not in workflow or "latest official" in workflow

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
assert workflow.count('--manifest "$NIAKVIO_TARGET_MANIFEST"') == 6  # Four canonical stage calls + two isolated candidate byte checks
assert 'prepare_native_tv_tmdb_contract.py --repo-root niakvio --client-root nuvio-tv' in workflow
assert "matrix.manifest" in workflow and "matrix.projection" in workflow
assert "Prime Android adb server" in workflow
assert "prime_android_lab_adb.sh" in workflow
# A cached guest's adb authorized key must match the already-running host
# daemon. The fresh runner used to start ADB before restoring ~/.android/adb*;
# it then booted successfully but remained "adb: device unauthorized" for
# ten minutes (native run 44762494993, both isolated TV jobs).
for device in ("Mobile", "TV"):
    cache = workflow.index(f"Restore {device} AVD snapshot and matching debug signing key")
    rebind = workflow.index(f"Rebind {device} adb authorization after AVD cache restore")
    create = workflow.index(f"Create {device} AVD snapshot on cache miss")
    assert cache < rebind < create
    block = workflow[rebind:create]
    assert "bash niakvio/scripts/prime_android_lab_adb.sh" in block
    assert "guest_auth_bypass=false" in block
assert workflow.count("FIELD_NATIVE_ADB_AUTH_REBOUND client=") == 2
assert workflow.count("bash niakvio/scripts/prime_android_lab_adb.sh") == 3
assert "adb disable-verity" not in workflow
assert "adb root" not in workflow
assert "avd-v6-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in workflow
assert "avd-v6-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in workflow
assert "~/.android/adb*" in workflow
assert "~/.android/debug.keystore" in workflow
assert "avd-v5-" not in workflow
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

# Transient candidate runs must never contaminate the published-device evidence.
helper = (ROOT / "scripts/prepare_native_candidate_remat.py").read_text(encoding="utf-8")
for needle in (
    "NIAKVIO_PROVIDER_NATIVE_PLAYER_HEDGE_V27",
    "NIAKVIO_HLS_TS_WRAPPED_AAC_RENDITION_V20",
    "NIAKVIO_PROVIDER_NATIVE_FETCH_CAPABILITY_GATE_V28",
    "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29",
    "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29",
    "requiredCoreMarker",
    "unsupported source-owned native candidate marker",
    "candidate did not materialize required source-owned Core marker",
    "candidateJsSha256",
    "publishedBaselineJsSha256",
    "officialTvTestAssetByteMatched",
    "productionPlaybackVerified",
    "publicationAllowed",
    "generatedByBrain",
    "sha256(asset) != candidate_sha",
    "NIAKVIO_PROVIDER_SCOPE_MATRIX",
    "app/src/androidTest/assets/niakvio/p000.js",
    "candidate staging scope must contain exactly the requested provider",
):
    assert needle in helper, needle
assert "candidate_rematerialize:" in workflow
assert "candidate_required_marker:" in workflow
assert "source_sha:" in workflow
assert "brain_candidate_experiment_json:" in workflow
assert "candidateRequiredMarker" in workflow
assert "candidate marker without isolated candidate materialization" in workflow
assert "Brain candidate experiment exceeds bounded input" in workflow
assert "Brain candidate experiment requires isolated V29, V30 or V31 materialization" in workflow
assert "NIAKVIO_PROVIDER_NATIVE_HLS_ROOT_RECEIPT_V30" in workflow
assert "NIAKVIO_PROVIDER_NATIVE_HLS_RECEIPT_DEDUPE_V31" in workflow
assert "NIAKVIO_PROVIDER_NATIVE_HLS_RECEIPT_DEDUPE_V31" in helper
assert 'ref: ${{ inputs.source_sha || github.sha }}' in workflow
assert 'ref: ${{ matrix.sourceSha }}' in workflow
assert 'NIAKVIO_SOURCE_SHA: ${{ matrix.sourceSha }}' in workflow
assert '--brain-experiment-json "$NIAKVIO_BRAIN_CANDIDATE_EXPERIMENT_JSON"' in workflow
assert '--source-sha "$NIAKVIO_SOURCE_SHA"' in workflow
assert workflow.count('--required-marker "$NIAKVIO_CANDIDATE_REQUIRED_MARKER"') == 2
assert workflow.count('NIAKVIO_CANDIDATE_REQUIRED_MARKER: ${{ matrix.candidateRequiredMarker }}') == 2
assert "candidateRematerialize" in workflow
assert "candidate native replay requires TV, one active provider and an exact fixture" in workflow
assert "matrix.candidateRematerialize == true" in workflow
assert "scripts/prepare_native_candidate_remat.py --verify-staging" in workflow
assert workflow.index("Rematerialize isolated ProviderBase candidate for official TV test") < workflow.index("Checkout accepted official client and stage corpus once")
assert workflow.index("Checkout accepted official client and stage corpus once") < workflow.index("Verify candidate bytes in official TV instrumentation assets")
assert "always() && matrix.candidateRematerialize != true" in workflow
assert "name: native-candidate-" in workflow
assert 'NIAKVIO_MANIFEST_URL=https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${NIAKVIO_SOURCE_SHA}/${NIAKVIO_TARGET_MANIFEST}' in workflow
assert 'NIAKVIO_ALLOW_LOCAL_MANIFEST=0' in workflow
assert "published_manifest_https=true" in workflow
assert "candidate_asset_local=true playback_authority=false" in workflow
assert "niakvio/automation/native-candidate-remat-proof.json" in workflow
assert workflow.count("name: native-corpus-${{ matrix.device }}-") == 1
assert "native-hub46" not in workflow

# Staging alone is not execution: the official manager downloads the published
# repository bytes. Candidate runs instead require a separate SHA-attested
# real-PluginRuntime oracle, explicitly denied production playback authority.
assert "NIAKVIO_NATIVE_CANDIDATE_SHA256=$CANDIDATE_SHA" in workflow
assert 'proof["officialTvTestAssetByteMatched"] is True' in workflow
assert workflow.index("Verify candidate bytes in official TV instrumentation assets") < workflow.index("Set up Gradle runtime")
tv_suite = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text(encoding="utf-8")
tv_loader = (ROOT / "scripts/augment_native_provider_loading.py").read_text(encoding="utf-8")
for needle in (
    "--candidate-execution-sha256",
    "NIAKVIO_NATIVE_CANDIDATE_SHA256",
    "FIELD_NATIVE_CANDIDATE_ORACLE_FAILED",
    "FIELD_NATIVE_CANDIDATE_ORACLE_OBSERVED",
    "FIELD_NATIVE_CANDIDATE_RESTORED",
    "official_plugin_manager=true",
    "production_playback_authority=false",
):
    assert needle in tv_suite, needle
for needle in (
    "candidate_execution_sha256",
    "native local candidate oracle requires TV and exact SHA256",
    "FIELD_NATIVE_CANDIDATE_RUNTIME_BYTE_CHECK",
    "FIELD_NATIVE_CANDIDATE_RUNTIME_RESULT",
    "officialPluginManager.executeScraper(loadedScraper",
    "candidateStore.saveScraperCode(",
    "candidateStore.getScraperCode(",
    "candidateStore.deleteScraperCode(",
    "FIELD_NATIVE_CANDIDATE_RESTORE_FAILED",
    "restoredCode != previousCode",
    "kotlinx.coroutines.NonCancellable",
    "runtime=official_plugin_manager",
    "authority=diagnostic_only",
):
    assert needle in tv_loader, needle

print("native targeted residential transport workflow contract passed")

#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/native-android-route-reader.yml").read_text(encoding="utf-8")
prime = (ROOT / "scripts/prime_android_lab_adb.sh").read_text(encoding="utf-8")
prebuild = (ROOT / "scripts/prebuild_native_android_reader_suite.sh").read_text(encoding="utf-8")
tv_suite = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text(encoding="utf-8")
mobile_suite = (ROOT / "scripts/run_native_corpus_mobile_suite.sh").read_text(encoding="utf-8")
corpus_generator = (ROOT / "scripts/prepare_native_corpus_validation.py").read_text(encoding="utf-8")
corpus_client = (ROOT / "scripts/prepare_native_corpus_client.py").read_text(encoding="utf-8")
request_contract = (ROOT / "scripts/augment_native_corpus_request_contract.py").read_text(encoding="utf-8")

# The emulator image/snapshot is a Lab infrastructure artifact. It must not be
# invalidated whenever an official Nuvio app commit advances; the guest userdata
# is deliberately retained so a warm Lab can reuse the installed client/profile
# and provider cache instead of recreating the device on every run.
assert "avd-v5-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in workflow
assert "avd-v5-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in workflow
for line in workflow.splitlines():
    if "key: avd-v5-" in line:
        assert "needs.resolve.outputs.mobile_sha" not in line
        assert "needs.resolve.outputs.tv_sha" not in line
        assert "needs.resolve.outputs.runtime_fingerprint" not in line

# A warm guest may already contain a debug-signed Nuvio package. Keep the
# signing key in the same persistent Lab generation and restore it before
# building the official client APK, otherwise Android rejects the update.
assert workflow.count("~/.android/debug.keystore") == 3
assert workflow.index("Restore TV AVD snapshot and matching debug signing key") < workflow.index("Checkout latest official NuvioTV HEAD and stage first route")
assert workflow.index("Restore Mobile AVD snapshot and matching debug signing key") < workflow.index("Checkout latest official NuvioMobile HEAD and stage first route")
assert workflow.index("Restore TV AVD snapshot and matching debug signing key for candidate retest") < workflow.index("Checkout latest official NuvioTV HEAD for candidate retest")

# A cache miss must not attempt to load a snapshot that cannot exist yet. The
# representative run cold-boots the newly-created AVD directly, while a warm
# cache may load its saved default snapshot without overwriting it on exit.
assert workflow.count("-no-snapshot-load -no-window -gpu swiftshader_indirect -noaudio -no-boot-anim") >= 3
assert workflow.count("-no-snapshot-save -no-window -gpu swiftshader_indirect -noaudio -no-boot-anim") >= 3
assert "Create Mobile AVD snapshot on cache miss" not in workflow
assert "Create TV AVD snapshot on cache miss" not in workflow
assert "Create TV AVD snapshot on candidate cache miss" not in workflow

# Expensive main/PR Android generations are latest-wins so obsolete emulator
# work cannot pile up. Explicit workflow_dispatch runs stay isolated.
assert "github.event_name == 'workflow_dispatch' && github.run_id || github.event.pull_request.number || 'main'" in workflow
assert "cancel-in-progress: ${{ github.event_name != 'workflow_dispatch' }}" in workflow

# Player/read failures are observations for Brain/Deep, never publication locks.
# The historical YAML request flag is inert unless an explicit global blocking
# gate is enabled; normal Labs must keep that gate disabled. Missing/corrupt Lab
# evidence remains independently fatal in gate_native_player_reached.cjs.
for suite in (tv_suite, mobile_suite):
    assert 'PLAYER_OUTCOME_GLOBAL_GATE="${NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE:-0}"' in suite
    assert 'REQUIRE_READER_SUCCESS=0' in suite
    assert 'if [[ "$PLAYER_OUTCOME_GLOBAL_GATE" = "1" && "$REQUESTED_READER_SUCCESS" = "1" ]]' in suite
    assert 'blocking=false' in suite
assert "NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE: \"1\"" not in workflow

# Compile/package the official Android clients before QEMU starts. The hosted
# runner has to accommodate both a 2 GiB emulator and Gradle; allowing the first
# package task to happen inside the emulator window previously exhausted the
# Gradle daemon heap during NuvioTV :app:packageFullDebug.
assert workflow.count("prebuild_native_android_reader_suite.sh") >= 3
assert 'NIAKVIO_SKIP_ANDROID_PREBUILD: "1"' in workflow
assert workflow.index("Prebuild TV reader before QEMU") < workflow.index("Execute representative routes in one TV boot")
assert workflow.index("Prebuild Mobile reader before QEMU") < workflow.index("Execute representative routes in one Mobile boot")
assert workflow.index("Prebuild TV candidate retest before QEMU") < workflow.index("Re-read mutated providers plus deterministic sentinels after Brain mutation")
assert prebuild.count("--max-workers=1") >= 2
assert "--max-workers=1" in tv_suite
assert "--max-workers=1" in mobile_suite

# Every Android emulator path primes adb before the emulator action. GitHub's
# hosted image can expose sdkmanager while platform-tools/adb is still absent,
# so the preflight must install platform-tools itself before QEMU is launched.
# This remains Lab-only and best-effort: a transient host-side failure does not
# mutate Nuvio and the emulator action still gets a chance to establish ADB.
assert workflow.count("bash niakvio/scripts/prime_android_lab_adb.sh") >= 3
assert "sdkmanager" in prime
assert "--install platform-tools" in prime
assert "ANDROID_SDK_ROOT" in prime
assert "ANDROID_HOME" in prime
assert "unset ADB_SERVER_SOCKET" in prime
assert "adb kill-server" in prime
assert "adb start-server" in prime
assert "adb devices" in prime
assert "fallback=emulator_runner" in prime
assert "status=degraded" in prime
assert "runtime_mutation=false" in prime

# Provider logos are part of the manifest/client contract. Native tests persist
# only booleans, status/content-type and host; a targeted single-provider run may
# probe image loadability from the actual device without leaking the full URL.
assert '"logo": str(row.get("logo") or "").strip()' in corpus_client
assert '"logo": str(row.get("logo") or "").strip()' in corpus_generator
assert "FIELD_NATIVE_ADDON_LOGO" in request_contract
assert corpus_generator.count("val logo: String") >= 2
assert "providers.size == 1" in request_contract
assert "configured_not_probed" in corpus_generator
assert "raw.githubusercontent.com" not in request_contract

# Dependency downloads happen before QEMU. Hosted runner/CDN bursts such as the
# Maven Central 403 observed in run 32644909456 are infrastructure transients.
# The prebuild may retry those network-shaped failures, but deterministic Gradle
# failures must still return immediately and therefore remain visible as red CI.
assert "run_gradle_with_network_retry" in prebuild
assert "Could not (GET|HEAD)" in prebuild
assert "Received status code (403|408|425|429|5[0-9][0-9])" in prebuild
assert "FIELD_NATIVE_ANDROID_PREBUILD_NETWORK_RETRY" in prebuild
assert "attempt=$attempt status=exhausted" in prebuild
assert "return \"$status\"" in prebuild
assert prebuild.count("--stacktrace") >= 2

print("native Android AVD persistence + cold-boot/adb/dependency + nonblocking-reader contract passed")

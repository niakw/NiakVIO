#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/native-android-route-reader.yml").read_text(encoding="utf-8")
prime = (ROOT / "scripts/prime_android_lab_adb.sh").read_text(encoding="utf-8")
prebuild = (ROOT / "scripts/prebuild_native_android_reader_suite.sh").read_text(encoding="utf-8")

# The emulator image/snapshot is a Lab infrastructure artifact. It must not be
# invalidated whenever an official Nuvio app commit advances; the guest userdata
# is deliberately retained so a warm Lab can reuse the installed client/profile
# and provider cache instead of recreating the device on every run.
assert "avd-v4-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in workflow
assert "avd-v4-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in workflow
for line in workflow.splitlines():
    if "key: avd-v4-" in line:
        assert "needs.resolve.outputs.mobile_sha" not in line
        assert "needs.resolve.outputs.tv_sha" not in line
        assert "needs.resolve.outputs.runtime_fingerprint" not in line

# A cache miss must not attempt to load a snapshot that cannot exist yet. The
# representative run cold-boots the newly-created AVD directly, while a warm
# cache may load its saved default snapshot without overwriting it on exit.
assert workflow.count("-no-snapshot-load -no-window -gpu swiftshader_indirect -noaudio -no-boot-anim") >= 3
assert workflow.count("-no-snapshot-save -no-window -gpu swiftshader_indirect -noaudio -no-boot-anim") >= 3
assert "Create Mobile AVD snapshot on cache miss" not in workflow
assert "Create TV AVD snapshot on cache miss" not in workflow
assert "Create TV AVD snapshot on candidate cache miss" not in workflow

# Long main/workflow_dispatch native proofs are authoritative and must not be
# killed by a later main commit. Only stale revisions of the same pull request
# may cancel one another.
assert "github.event.pull_request.number || github.run_id" in workflow
assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in workflow

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

print("native Android AVD persistence + cold-boot/adb/dependency resilience contract passed")

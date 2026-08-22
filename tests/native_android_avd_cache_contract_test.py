#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/native-android-route-reader.yml").read_text(encoding="utf-8")
prime = (ROOT / "scripts/prime_android_lab_adb.sh").read_text(encoding="utf-8")

# The emulator image/snapshot is a Lab infrastructure artifact. It must not be
# invalidated whenever an official Nuvio app commit advances; the app is built
# and installed after the AVD is available.
assert "avd-v3-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in workflow
assert "avd-v3-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in workflow
for line in workflow.splitlines():
    if "key: avd-v3-" in line:
        assert "needs.resolve.outputs.mobile_sha" not in line
        assert "needs.resolve.outputs.tv_sha" not in line
        assert "needs.resolve.outputs.runtime_fingerprint" not in line

# Every Android emulator path primes adb before the emulator action. The
# preflight repairs common hosted-runner ADB state, but it is intentionally not
# an acceptance gate: ReactiveCircus is still allowed to launch the AVD and
# establish its own bridge when host-side adb priming is transiently degraded.
assert workflow.count("bash niakvio/scripts/prime_android_lab_adb.sh") >= 3
assert "unset ADB_SERVER_SOCKET" in prime
assert "adb kill-server" in prime
assert "adb start-server" in prime
assert "adb devices" in prime
assert "fallback=emulator_runner" in prime
assert "status=degraded" in prime
assert "runtime_mutation=false" in prime

print("native Android AVD cache + resilient adb bootstrap contract passed")

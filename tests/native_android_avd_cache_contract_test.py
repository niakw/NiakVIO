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

# Every Android emulator path primes adb before the emulator action. This
# addresses the observed hosted-runner failure where emulator startup reported
# no adb daemon on port 5037 before a cold boot was terminated.
assert workflow.count("bash niakvio/scripts/prime_android_lab_adb.sh") >= 3
assert "adb kill-server" in prime
assert "adb start-server" in prime
assert "adb devices" in prime
assert "runtime_mutation=false" in prime

print("native Android AVD cache + adb bootstrap contract passed")

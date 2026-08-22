#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/native-android-route-reader.yml").read_text(encoding="utf-8")
prime = (ROOT / "scripts/prime_android_lab_adb.sh").read_text(encoding="utf-8")

# The emulator image/snapshot is a Lab infrastructure artifact. It must not be
# invalidated whenever an official Nuvio app commit advances; the guest userdata
# is deliberately retained so a warm Lab can reuse the installed client/profile
# and provider cache instead of recreating the device on every run.
assert "avd-v3-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in workflow
assert "avd-v3-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in workflow
for line in workflow.splitlines():
    if "key: avd-v3-" in line:
        assert "needs.resolve.outputs.mobile_sha" not in line
        assert "needs.resolve.outputs.tv_sha" not in line
        assert "needs.resolve.outputs.runtime_fingerprint" not in line

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

print("native Android AVD persistence + resilient adb bootstrap contract passed")
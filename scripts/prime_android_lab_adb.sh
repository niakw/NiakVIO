#!/usr/bin/env bash
set -euo pipefail

# Hosted Android readers can enter the emulator action while the SDK bridge is
# absent, stale, or temporarily unable to bind port 5037. This preflight is
# deliberately best-effort: the emulator runner remains the authority for ADB
# availability once an AVD is launched. A transient host-side ADB failure must
# therefore never prevent the real native reader from being attempted.
#
# Lab-only orchestration: this never changes Nuvio runtime code, app manifests,
# provider JS, player behavior, or network behavior.
#
# GitHub hosted Android images expose sdkmanager before platform-tools in some
# runner revisions. Installing platform-tools here avoids launching QEMU before
# an adb daemon exists. The emulator action will see the already-installed SDK
# component and treats this as an idempotent no-op on warm runners.
if ! command -v adb >/dev/null 2>&1; then
  SDKMANAGER="$(command -v sdkmanager 2>/dev/null || true)"
  if [[ -z "$SDKMANAGER" ]]; then
    for candidate in \
      "${ANDROID_SDK_ROOT:-}/cmdline-tools/latest/bin/sdkmanager" \
      "${ANDROID_HOME:-}/cmdline-tools/latest/bin/sdkmanager" \
      "/usr/local/lib/android/sdk/cmdline-tools/latest/bin/sdkmanager"; do
      if [[ -n "$candidate" && -x "$candidate" ]]; then
        SDKMANAGER="$candidate"
        break
      fi
    done
  fi

  if [[ -n "$SDKMANAGER" ]]; then
    echo "FIELD_NATIVE_ADB_BOOTSTRAP action=install_platform_tools runtime_mutation=false"
    yes | "$SDKMANAGER" --licenses >/dev/null 2>&1 || true
    "$SDKMANAGER" --install platform-tools >/tmp/niakvio-sdkmanager-platform-tools.txt 2>&1 || true
  fi

  for sdk_root in "${ANDROID_SDK_ROOT:-}" "${ANDROID_HOME:-}" "/usr/local/lib/android/sdk"; do
    if [[ -n "$sdk_root" && -x "$sdk_root/platform-tools/adb" ]]; then
      export PATH="$sdk_root/platform-tools:$PATH"
      break
    fi
  done
fi

if ! command -v adb >/dev/null 2>&1; then
  cat /tmp/niakvio-sdkmanager-platform-tools.txt >&2 2>/dev/null || true
  echo "FIELD_NATIVE_ADB_PRIME status=missing_adb fallback=emulator_runner runtime_mutation=false" >&2
  exit 0
fi

# A hosted runner may inherit a custom server socket or a stale daemon. Force
# the normal local SDK bridge and clean up only host-side adb state.
unset ADB_SERVER_SOCKET || true
adb kill-server >/dev/null 2>&1 || true
pkill -f '(^|/)adb( |$).*server' >/dev/null 2>&1 || true

ready=0
: > /tmp/niakvio-adb-error.txt
for _attempt in 1 2 3 4 5; do
  if adb start-server >/tmp/niakvio-adb-start.txt 2>>/tmp/niakvio-adb-error.txt \
    && adb devices >/tmp/niakvio-adb-devices.txt 2>>/tmp/niakvio-adb-error.txt; then
    ready=1
    break
  fi
  adb kill-server >/dev/null 2>&1 || true
  sleep 2
done

if [ "$ready" -ne 1 ]; then
  cat /tmp/niakvio-adb-error.txt >&2 || true
  echo "FIELD_NATIVE_ADB_PRIME status=degraded fallback=emulator_runner runtime_mutation=false" >&2
  exit 0
fi

echo "FIELD_NATIVE_ADB_PRIME status=ready port=5037 runtime_mutation=false"
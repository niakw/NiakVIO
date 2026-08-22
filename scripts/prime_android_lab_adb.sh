#!/usr/bin/env bash
set -euo pipefail

# Hosted Android readers occasionally enter the emulator action with no adb
# daemon listening on 5037. Prime the production SDK bridge before an AVD is
# launched. This is Lab-only orchestration: it never changes Nuvio runtime code,
# app manifests, provider JS or player/network behavior.
if ! command -v adb >/dev/null 2>&1; then
  echo "FIELD_NATIVE_ADB_PRIME status=missing_adb runtime_mutation=false" >&2
  exit 1
fi

adb kill-server >/dev/null 2>&1 || true
adb start-server >/dev/null

ready=0
for _attempt in 1 2 3 4 5; do
  if adb devices >/tmp/niakvio-adb-devices.txt 2>/tmp/niakvio-adb-error.txt; then
    ready=1
    break
  fi
  sleep 1
done

if [ "$ready" -ne 1 ]; then
  cat /tmp/niakvio-adb-error.txt >&2 || true
  echo "FIELD_NATIVE_ADB_PRIME status=unavailable runtime_mutation=false" >&2
  exit 1
fi

echo "FIELD_NATIVE_ADB_PRIME status=ready port=5037 runtime_mutation=false"

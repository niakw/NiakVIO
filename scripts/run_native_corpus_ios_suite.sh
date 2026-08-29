#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
NIAKVIO_ROOT="${NIAKVIO_ROOT:-$WORKSPACE/niakvio}"
NUVIO_MOBILE_ROOT="${NUVIO_MOBILE_ROOT:-$WORKSPACE/nuvio-mobile}"
DERIVED="${NIAKVIO_IOS_DERIVED_DATA:-$WORKSPACE/ios-derived}"
LOG="${NIAKVIO_IOS_LOG:-$WORKSPACE/mobile-ios-native-corpus.log}"
MANIFEST_URL="${NIAKVIO_MANIFEST_URL:?NIAKVIO_MANIFEST_URL is required}"

cd "$NUVIO_MOBILE_ROOT"
./scripts/prepare-ios-dependencies.sh

export NUVIO_IOS_DISTRIBUTION=full
export GRADLE_OPTS="${GRADLE_OPTS:--Dfile.encoding=UTF-8}"
export ORG_GRADLE_PROJECT_org_gradle_jvmargs="${ORG_GRADLE_PROJECT_org_gradle_jvmargs:--Xmx4608M -Dfile.encoding=UTF-8 -XX:MaxMetaspaceSize=768M}"
export ORG_GRADLE_PROJECT_kotlin_native_jvmArgs="${ORG_GRADLE_PROJECT_kotlin_native_jvmArgs:--Xmx4608M}"

xcodebuild   -project iosApp/iosApp.xcodeproj   -scheme iosApp   -configuration Debug   -sdk iphonesimulator   -destination 'generic/platform=iOS Simulator'   -derivedDataPath "$DERIVED"   CODE_SIGNING_ALLOWED=NO   CODE_SIGNING_REQUIRED=NO   CODE_SIGN_IDENTITY=   build

APP="$(find "$DERIVED/Build/Products" -maxdepth 2 -type d -name 'Nuvio.app' -path '*Debug-iphonesimulator*' -print -quit)"
if [[ -z "$APP" || ! -d "$APP" ]]; then
  echo "iOS simulator build did not produce Nuvio.app" >&2
  exit 2
fi
BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Info.plist")"

DEVICE_JSON="$(xcrun simctl list devices available -j)"
UDID="$(DEVICE_JSON="$DEVICE_JSON" python3 - <<'PY'
import json, os
data=json.loads(os.environ["DEVICE_JSON"])
booted=[]
available=[]
for rows in data.get("devices", {}).values():
    for row in rows:
        if not row.get("isAvailable", True):
            continue
        name=str(row.get("name") or "")
        if not name.startswith("iPhone"):
            continue
        udid=str(row.get("udid") or "")
        state=str(row.get("state") or "")
        if udid:
            (booted if state == "Booted" else available).append(udid)
choice=booted or available
if not choice:
    raise SystemExit("no available iPhone simulator")
print(choice[0])
PY
)"

xcrun simctl boot "$UDID" >/dev/null 2>&1 || true
xcrun simctl bootstatus "$UDID" -b
xcrun simctl install "$UDID" "$APP"

rm -f "$LOG"
set +e
SIMCTL_CHILD_NIAKVIO_IOS_LAB=1 SIMCTL_CHILD_NIAKVIO_MANIFEST_URL="$MANIFEST_URL"   xcrun simctl launch --console-pty "$UDID" "$BUNDLE_ID" >"$LOG" 2>&1 &
LAUNCH_PID=$!
set -e

STATUS=0
DONE=0
for _ in $(seq 1 7200); do
  if grep -q 'FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=completed' "$LOG" 2>/dev/null; then
    DONE=1
    STATUS=0
    break
  fi
  if grep -q 'FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error' "$LOG" 2>/dev/null; then
    DONE=1
    STATUS=2
    break
  fi
  if ! kill -0 "$LAUNCH_PID" 2>/dev/null; then
    wait "$LAUNCH_PID" || STATUS=$?
    break
  fi
  sleep 1
done

kill "$LAUNCH_PID" >/dev/null 2>&1 || true
wait "$LAUNCH_PID" >/dev/null 2>&1 || true
cat "$LOG"

if [[ "$DONE" -ne 1 ]]; then
  echo "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=no_terminal_marker" >&2
  STATUS=2
fi
exit "$STATUS"

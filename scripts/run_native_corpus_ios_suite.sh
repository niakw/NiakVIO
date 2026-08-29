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
# --console is intentionally foreground/non-PTY in CI. On macOS 26 the PTY
# variant can return after launch while the simulator app is still running,
# which made the Lab kill its own evidence collection after the first marker.
SIMCTL_CHILD_NIAKVIO_IOS_LAB=1 SIMCTL_CHILD_NIAKVIO_MANIFEST_URL="$MANIFEST_URL" \
  xcrun simctl launch --console "$UDID" "$BUNDLE_ID" >"$LOG" 2>&1
LAUNCH_STATUS=$?
set -e

cat "$LOG"

if grep -q 'FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=completed' "$LOG"; then
  exit 0
fi
if grep -q 'FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error' "$LOG"; then
  exit 2
fi

echo "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=app_exited_without_terminal_marker launch_status=$LAUNCH_STATUS" | tee -a "$LOG" >&2
exit 2

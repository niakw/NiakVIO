#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
NIAKVIO_ROOT="${NIAKVIO_ROOT:-$WORKSPACE/niakvio}"
NUVIO_MOBILE_ROOT="${NUVIO_MOBILE_ROOT:-$WORKSPACE/nuvio-mobile}"
DERIVED="${NIAKVIO_IOS_DERIVED_DATA:-$WORKSPACE/ios-derived}"
MANIFEST_URL="${NIAKVIO_MANIFEST_URL:?NIAKVIO_MANIFEST_URL is required}"
MODE="${NIAKVIO_IOS_LAB_MODE:-full}"
TARGET_PROVIDER="${NIAKVIO_IOS_TARGET_PROVIDER:-}"
SESSION_STATE="${NIAKVIO_IOS_SESSION_STATE:-$WORKSPACE/ios-learning-session.env}"
PROVIDER_TIMEOUT_MS="${NIAKVIO_IOS_PROVIDER_TIMEOUT_MS:-}"
PLAYER_TIMEOUT_MS="${NIAKVIO_IOS_PLAYER_TIMEOUT_MS:-}"
WAIT_SECONDS="${NIAKVIO_IOS_WAIT_SECONDS:-}"
LAUNCH_RETRY_TIMEOUT_SECONDS="${NIAKVIO_IOS_LAUNCH_RETRY_TIMEOUT_SECONDS:-}"

case "$MODE" in
  full) ;;
  learning|quick)
    if [[ -z "$TARGET_PROVIDER" ]]; then
      echo "iOS $MODE Lab requires NIAKVIO_IOS_TARGET_PROVIDER" >&2
      exit 2
    fi
    ;;
  *)
    echo "unsupported iOS Lab mode: $MODE" >&2
    exit 2
    ;;
esac

if [[ -z "$WAIT_SECONDS" ]]; then
  if [[ "$MODE" = "full" ]]; then WAIT_SECONDS=7200; else WAIT_SECONDS=120; fi
fi
if [[ -z "$LAUNCH_RETRY_TIMEOUT_SECONDS" ]]; then
  if [[ "$MODE" = "full" ]]; then LAUNCH_RETRY_TIMEOUT_SECONDS=600; else LAUNCH_RETRY_TIMEOUT_SECONDS=300; fi
fi
if [[ "$MODE" = "full" ]]; then
  LOG="${NIAKVIO_IOS_LOG:-$WORKSPACE/mobile-ios-native-corpus.log}"
else
  SAFE_TARGET="$(printf '%s' "$TARGET_PROVIDER" | tr -cd 'A-Za-z0-9._-' | cut -c1-80)"
  LOG="${NIAKVIO_IOS_LOG:-$WORKSPACE/mobile-ios-native-corpus-${SAFE_TARGET:-target}.log}"
fi

cd "$NUVIO_MOBILE_ROOT"

export NUVIO_IOS_DISTRIBUTION=full
export GRADLE_OPTS="${GRADLE_OPTS:--Dfile.encoding=UTF-8}"
export ORG_GRADLE_PROJECT_org_gradle_jvmargs="${ORG_GRADLE_PROJECT_org_gradle_jvmargs:--Xmx4608M -Dfile.encoding=UTF-8 -XX:MaxMetaspaceSize=768M}"
export ORG_GRADLE_PROJECT_kotlin_native_jvmArgs="${ORG_GRADLE_PROJECT_kotlin_native_jvmArgs:--Xmx4608M}"

load_session() {
  [[ -s "$SESSION_STATE" ]] || return 1
  # shellcheck disable=SC1090
  source "$SESSION_STATE"
  [[ -n "${UDID:-}" && -n "${BUNDLE_ID:-}" && -n "${APP:-}" && -d "$APP" ]] || return 1
  xcrun simctl list devices available -j | grep -Fq "$UDID" || return 1
  return 0
}

create_session() {
  ./scripts/prepare-ios-dependencies.sh
  xcodebuild \
    -project iosApp/iosApp.xcodeproj \
    -scheme iosApp \
    -configuration Debug \
    -sdk iphonesimulator \
    -destination 'generic/platform=iOS Simulator' \
    -derivedDataPath "$DERIVED" \
    CODE_SIGNING_ALLOWED=NO \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGN_IDENTITY= \
    build

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

  # CoreSimulatorBridge defaults to a 120s launch retry window. On fresh
  # macOS runners the first iOS boot can spend longer than that in app/runtime
  # initialization even after bootstatus is terminal, causing simctl to detach
  # just as the Lab begins. Keep this launch-only allowance separate from the
  # provider/player probe budgets.
  defaults write com.apple.CoreSimulatorBridge LaunchRetryTimeout -float "$LAUNCH_RETRY_TIMEOUT_SECONDS" || true
  xcrun simctl spawn "$UDID" defaults write com.apple.CoreSimulatorBridge LaunchRetryTimeout -float "$LAUNCH_RETRY_TIMEOUT_SECONDS" || true
  echo "FIELD_NATIVE_IOS_SIM_LAUNCH_TIMEOUT seconds=$LAUNCH_RETRY_TIMEOUT_SECONDS mode=$MODE"

  if [[ "$MODE" != "full" ]]; then
    mkdir -p "$(dirname "$SESSION_STATE")"
    {
      printf 'UDID=%q\n' "$UDID"
      printf 'BUNDLE_ID=%q\n' "$BUNDLE_ID"
      printf 'APP=%q\n' "$APP"
    } > "$SESSION_STATE"
    echo "FIELD_NATIVE_IOS_SESSION state=warm-created mode=$MODE udid=$UDID bundle=$BUNDLE_ID"
  fi
}

if [[ "$MODE" != "full" ]] && load_session; then
  xcrun simctl boot "$UDID" >/dev/null 2>&1 || true
  xcrun simctl bootstatus "$UDID" -b
  defaults write com.apple.CoreSimulatorBridge LaunchRetryTimeout -float "$LAUNCH_RETRY_TIMEOUT_SECONDS" || true
  xcrun simctl spawn "$UDID" defaults write com.apple.CoreSimulatorBridge LaunchRetryTimeout -float "$LAUNCH_RETRY_TIMEOUT_SECONDS" || true
  echo "FIELD_NATIVE_IOS_SIM_LAUNCH_TIMEOUT seconds=$LAUNCH_RETRY_TIMEOUT_SECONDS mode=$MODE"
  echo "FIELD_NATIVE_IOS_SESSION state=warm-reused mode=$MODE udid=$UDID bundle=$BUNDLE_ID"
else
  if [[ "$MODE" != "full" ]]; then rm -f "$SESSION_STATE"; fi
  create_session
fi

rm -f "$LOG"
set +e
SIMCTL_CHILD_NIAKVIO_IOS_LAB=1 \
SIMCTL_CHILD_NIAKVIO_MANIFEST_URL="$MANIFEST_URL" \
SIMCTL_CHILD_NIAKVIO_IOS_LAB_MODE="$MODE" \
SIMCTL_CHILD_NIAKVIO_IOS_TARGET_PROVIDER="$TARGET_PROVIDER" \
SIMCTL_CHILD_NIAKVIO_IOS_PROVIDER_TIMEOUT_MS="$PROVIDER_TIMEOUT_MS" \
SIMCTL_CHILD_NIAKVIO_IOS_PLAYER_TIMEOUT_MS="$PLAYER_TIMEOUT_MS" \
  xcrun simctl launch --terminate-running-process --console-pty "$UDID" "$BUNDLE_ID" >"$LOG" 2>&1 &
LAUNCH_PID=$!
set -e

STATUS=0
DONE=0
for _ in $(seq 1 "$WAIT_SECONDS"); do
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
  echo "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=no_terminal_marker mode=$MODE target=$TARGET_PROVIDER" >&2
  STATUS=2
fi
exit "$STATUS"

#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
NIAKVIO_ROOT="${NIAKVIO_ROOT:-$WORKSPACE/niakvio}"
NUVIO_MOBILE_ROOT="${NUVIO_MOBILE_ROOT:-$WORKSPACE/nuvio-mobile}"
DERIVED="${NIAKVIO_IOS_DERIVED_DATA:-$WORKSPACE/ios-derived}"
MANIFEST_URL="${NIAKVIO_MANIFEST_URL:?NIAKVIO_MANIFEST_URL is required}"
if [[ -n "${NIAKVIO_PROVIDER_SCOPE_MATRIX:-}" && -f "${NIAKVIO_ROOT}/native-hub46/manifest.json" ]]; then
  SOURCE_REPOSITORY="${GITHUB_REPOSITORY:-niakw/NiakVIO}"
  SOURCE_SHA="${GITHUB_SHA:-$(git -C "$NIAKVIO_ROOT" rev-parse HEAD)}"
  MANIFEST_URL="https://raw.githubusercontent.com/${SOURCE_REPOSITORY}/${SOURCE_SHA}/native-hub46/manifest.json"
  echo "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE manifest=native-hub46/manifest.json providers=46 authority=${NIAKVIO_PROVIDER_SCOPE_MATRIX}"
fi
MODE="${NIAKVIO_IOS_LAB_MODE:-full}"
TARGET_PROVIDER="${NIAKVIO_IOS_TARGET_PROVIDER:-}"
SESSION_STATE="${NIAKVIO_IOS_SESSION_STATE:-$WORKSPACE/ios-learning-session.env}"
PROVIDER_TIMEOUT_MS="${NIAKVIO_IOS_PROVIDER_TIMEOUT_MS:-}"
PLAYER_TIMEOUT_MS="${NIAKVIO_IOS_PLAYER_TIMEOUT_MS:-}"
WAIT_SECONDS="${NIAKVIO_IOS_WAIT_SECONDS:-}"
IDLE_TIMEOUT_SECONDS="${NIAKVIO_IOS_IDLE_TIMEOUT_SECONDS:-}"
LAUNCH_RETRY_TIMEOUT_SECONDS="${NIAKVIO_IOS_LAUNCH_RETRY_TIMEOUT_SECONDS:-}"
WATCHDOG_DRAIN_SECONDS="${NIAKVIO_IOS_WATCHDOG_DRAIN_SECONDS:-3}"

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
if [[ -z "$IDLE_TIMEOUT_SECONDS" ]]; then
  if [[ "$MODE" = "full" ]]; then IDLE_TIMEOUT_SECONDS=120; else IDLE_TIMEOUT_SECONDS=60; fi
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
RESUME_FIXTURE=""
RESUME_AFTER_PROVIDER=""
WATCHDOG_RESTARTS=0
MAX_WATCHDOG_RESTARTS="${NIAKVIO_IOS_MAX_WATCHDOG_RESTARTS:-240}"
LAUNCH_PID=""

launch_lab() {
  set +e
  SIMCTL_CHILD_NIAKVIO_IOS_LAB=1 \
  SIMCTL_CHILD_NIAKVIO_MANIFEST_URL="$MANIFEST_URL" \
  SIMCTL_CHILD_NIAKVIO_IOS_LAB_MODE="$MODE" \
  SIMCTL_CHILD_NIAKVIO_IOS_TARGET_PROVIDER="$TARGET_PROVIDER" \
  SIMCTL_CHILD_NIAKVIO_IOS_PROVIDER_TIMEOUT_MS="$PROVIDER_TIMEOUT_MS" \
  SIMCTL_CHILD_NIAKVIO_IOS_PLAYER_TIMEOUT_MS="$PLAYER_TIMEOUT_MS" \
  SIMCTL_CHILD_NIAKVIO_IOS_RESUME_FIXTURE="$RESUME_FIXTURE" \
  SIMCTL_CHILD_NIAKVIO_IOS_RESUME_AFTER_PROVIDER="$RESUME_AFTER_PROVIDER" \
    xcrun simctl launch --terminate-running-process --console "$UDID" "$BUNDLE_ID" > >(tee -a "$LOG") 2>&1 &
  LAUNCH_PID=$!
  set -e
}

stop_lab() {
  xcrun simctl terminate "$UDID" "$BUNDLE_ID" >/dev/null 2>&1 || true
  if [[ -n "${LAUNCH_PID:-}" ]]; then
    kill "$LAUNCH_PID" >/dev/null 2>&1 || true
    wait "$LAUNCH_PID" >/dev/null 2>&1 || true
  fi
}

drain_lab_output() {
  local previous_size current_size stable=0
  previous_size="$(wc -c < "$LOG" 2>/dev/null || echo 0)"
  for _ in $(seq 1 "$WATCHDOG_DRAIN_SECONDS"); do
    sleep 1
    current_size="$(wc -c < "$LOG" 2>/dev/null || echo 0)"
    if [[ "$current_size" = "$previous_size" ]]; then
      stable=$((stable + 1))
    else
      stable=0
      previous_size="$current_size"
    fi
  done
  echo "FIELD_NATIVE_IOS_WATCHDOG action=drained bytes=$previous_size stable_seconds=$stable" | tee -a "$LOG"
}

provider_end_after_line() {
  local begin_line="$1" fixture="$2" provider="$3"
  tail -n "+$((begin_line + 1))" "$LOG" 2>/dev/null | \
    grep -Fq "FIELD_NATIVE_IOS_PROVIDER_END fixture=$fixture provider=$provider "
}

launch_lab

STATUS=0
DONE=0
LAST_SIZE=0
IDLE_SECONDS=0
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
  SIZE="$(wc -c < "$LOG" 2>/dev/null || echo 0)"
  if [[ "$SIZE" =~ ^[0-9]+$ ]] && (( SIZE > LAST_SIZE )); then
    LAST_SIZE="$SIZE"
    IDLE_SECONDS=0
  else
    IDLE_SECONDS=$((IDLE_SECONDS + 1))
  fi
  if (( IDLE_SECONDS >= IDLE_TIMEOUT_SECONDS )); then
    if [[ "$MODE" != "full" ]]; then
      echo "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=log_idle_timeout idle_seconds=$IDLE_SECONDS mode=$MODE target=$TARGET_PROVIDER" | tee -a "$LOG"
      DONE=1
      STATUS=2
      break
    fi
    LAST_BEGIN_WITH_LINE="$(grep -n 'FIELD_NATIVE_IOS_PROVIDER_BEGIN ' "$LOG" 2>/dev/null | tail -n 1 || true)"
    BLOCKED_BEGIN_LINE="${LAST_BEGIN_WITH_LINE%%:*}"
    LAST_BEGIN="${LAST_BEGIN_WITH_LINE#*:}"
    BLOCKED_FIXTURE="$(printf '%s\n' "$LAST_BEGIN" | sed -n 's/.* fixture=\([^ ]*\).*/\1/p')"
    BLOCKED_PROVIDER="$(printf '%s\n' "$LAST_BEGIN" | sed -n 's/.* provider=\([^ ]*\).*/\1/p')"
    if [[ -z "$BLOCKED_BEGIN_LINE" || ! "$BLOCKED_BEGIN_LINE" =~ ^[0-9]+$ || -z "$BLOCKED_FIXTURE" || -z "$BLOCKED_PROVIDER" ]]; then
      echo "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=idle_without_provider_context idle_seconds=$IDLE_SECONDS mode=$MODE" | tee -a "$LOG"
      DONE=1
      STATUS=2
      break
    fi
    WATCHDOG_RESTARTS=$((WATCHDOG_RESTARTS + 1))
    if (( WATCHDOG_RESTARTS > MAX_WATCHDOG_RESTARTS )); then
      echo "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=watchdog_restart_budget_exhausted restarts=$WATCHDOG_RESTARTS fixture=$BLOCKED_FIXTURE provider=$BLOCKED_PROVIDER" | tee -a "$LOG"
      DONE=1
      STATUS=2
      break
    fi
    echo "FIELD_NATIVE_IOS_WATCHDOG action=restart fixture=$BLOCKED_FIXTURE provider=$BLOCKED_PROVIDER begin_line=$BLOCKED_BEGIN_LINE idle_seconds=$IDLE_SECONDS restart=$WATCHDOG_RESTARTS" | tee -a "$LOG"

    # Stop the current generation first, then allow its console pipe to drain.
    # The old implementation relaunched immediately: late PROVIDER_END lines from
    # generation N could then appear after PROVIDER_BEGIN from generation N+1 and
    # be mistaken for the new provider's terminal state.
    stop_lab
    drain_lab_output

    RESUME_FIXTURE="$BLOCKED_FIXTURE"
    if provider_end_after_line "$BLOCKED_BEGIN_LINE" "$BLOCKED_FIXTURE" "$BLOCKED_PROVIDER"; then
      # The provider completed while the watchdog was stopping/draining the old
      # process. Do not manufacture a watchdog timeout for it. Restart the same
      # fixture from a clean generation; duplicate completed observations are
      # harmless and are merged by the native evidence gate.
      RESUME_AFTER_PROVIDER=""
      echo "FIELD_NATIVE_IOS_WATCHDOG action=late_terminal fixture=$BLOCKED_FIXTURE provider=$BLOCKED_PROVIDER resume=fixture_restart restart=$WATCHDOG_RESTARTS" | tee -a "$LOG"
    else
      # No terminal exists after the exact BEGIN that triggered this watchdog.
      # Resume after the blocked provider so the generated iOS Lab records the
      # intentional watchdog timeout exactly once.
      RESUME_AFTER_PROVIDER="$BLOCKED_PROVIDER"
      echo "FIELD_NATIVE_IOS_WATCHDOG action=confirmed_timeout fixture=$BLOCKED_FIXTURE provider=$BLOCKED_PROVIDER resume=after_provider restart=$WATCHDOG_RESTARTS" | tee -a "$LOG"
    fi

    launch_lab
    LAST_SIZE="$(wc -c < "$LOG" 2>/dev/null || echo 0)"
    IDLE_SECONDS=0
  fi
  sleep 1
done

stop_lab

if [[ "$DONE" -ne 1 ]]; then
  echo "FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=no_terminal_marker mode=$MODE target=$TARGET_PROVIDER" | tee -a "$LOG" >&2
  STATUS=2
fi
exit "$STATUS"
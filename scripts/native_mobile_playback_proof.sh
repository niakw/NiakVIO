#!/usr/bin/env bash
set -euo pipefail

# Use the SDK environment provisioned by android-emulator-runner. This proof is
# intentionally restricted to the injected NiakVIO instrumentation class.
echo "ANDROID_HOME=${ANDROID_HOME:-missing}"
ls -1 "${ANDROID_HOME:-/nonexistent}/platforms" 2>/dev/null || true

MOBILE_REPORT_DIR="$GITHUB_WORKSPACE/nuvio-mobile/composeApp/build/reports/androidTests/niakvio"
MOBILE_GRADLE_LOG="$MOBILE_REPORT_DIR/mobile-gradle.log"
MOBILE_LOGCAT="$MOBILE_REPORT_DIR/mobile-logcat.log"
RESULT="$GITHUB_WORKSPACE/mobile-final-native-results.log"
mkdir -p "$MOBILE_REPORT_DIR"
rm -f "$MOBILE_GRADLE_LOG" "$MOBILE_LOGCAT" "$RESULT"

adb logcat -c
adb logcat -v brief -s NiakvioRealLab:I '*:S' > "$MOBILE_LOGCAT" 2>&1 &
LOGCAT_PID=$!
cleanup_logcat() {
  kill "$LOGCAT_PID" 2>/dev/null || true
  wait "$LOGCAT_PID" 2>/dev/null || true
}
trap cleanup_logcat EXIT

TASKS=$("$GITHUB_WORKSPACE/nuvio-mobile/gradlew" -p "$GITHUB_WORKSPACE/nuvio-mobile" :composeApp:tasks --all -Pnuvio.android.distribution=full --console=plain)
TASK=$(printf '%s\n' "$TASKS" | awk 'tolower($1) ~ /connected.*device.*test/ {print $1; exit}')
if [[ -z "$TASK" ]]; then
  TASK=$(printf '%s\n' "$TASKS" | awk 'tolower($1) ~ /device.*test/ && tolower($0) ~ /connected/ {print $1; exit}')
fi
test -n "$TASK"
echo "Resolved NuvioMobile task: $TASK"

mobile_streamzo_proof_present() {
  local combined
  combined=$(mktemp)
  {
    cat "$MOBILE_LOGCAT" 2>/dev/null || true
    grep -E 'FIELD_MOBILE_' "$MOBILE_GRADLE_LOG" 2>/dev/null || true
  } > "$combined"
  if grep -Eq 'FIELD_MOBILE_NATIVE provider=streamzo .* count=[1-9][0-9]*' "$combined" \
    && grep -Eq 'FIELD_MOBILE_NATIVE_ROW provider=streamzo .* type=hls([[:space:]]|$)' "$combined"; then
    rm -f "$combined"
    return 0
  fi
  rm -f "$combined"
  return 1
}

MOBILE_STATUS=1
MOBILE_PROOF_OK=0
for ATTEMPT in 1 2; do
  echo "FIELD_MOBILE_PROOF_ATTEMPT attempt=$ATTEMPT max=2" | tee -a "$MOBILE_GRADLE_LOG"
  set +e
  "$GITHUB_WORKSPACE/nuvio-mobile/gradlew" -p "$GITHUB_WORKSPACE/nuvio-mobile" ":composeApp:$TASK" \
    -Pnuvio.android.distribution=full \
    '-Pandroid.testInstrumentationRunnerArguments.class=com.nuvio.app.features.plugins.NiakvioFinalNativeMobileTest' \
    --no-daemon --console=plain 2>&1 | tee -a "$MOBILE_GRADLE_LOG"
  MOBILE_STATUS=${PIPESTATUS[0]}
  set -e

  sleep 1
  if [[ "$MOBILE_STATUS" -eq 0 ]] && mobile_streamzo_proof_present; then
    MOBILE_PROOF_OK=1
    break
  fi

  if [[ "$ATTEMPT" -lt 2 ]]; then
    if [[ "$MOBILE_STATUS" -ne 0 ]]; then
      echo "FIELD_MOBILE_PROOF_RETRY reason=instrumentation_failure status=$MOBILE_STATUS" | tee -a "$MOBILE_GRADLE_LOG"
    else
      echo "FIELD_MOBILE_PROOF_RETRY reason=streamzo_proof_missing status=0" | tee -a "$MOBILE_GRADLE_LOG"
    fi
    sleep 3
  fi
done

sleep 1
cleanup_logcat
trap - EXIT

{
  cat "$MOBILE_LOGCAT" 2>/dev/null || true
  grep -E 'FIELD_MOBILE_' "$MOBILE_GRADLE_LOG" 2>/dev/null || true
} | awk '!seen[$0]++' > "$RESULT"
cat "$RESULT"

if [[ "$MOBILE_STATUS" -ne 0 ]]; then
  exit "$MOBILE_STATUS"
fi
if [[ "$MOBILE_PROOF_OK" -ne 1 ]]; then
  echo "StreamZo Mobile native proof missing after 2 bounded attempts" >&2
  exit 1
fi

grep -Eq 'FIELD_MOBILE_NATIVE provider=streamzo .* count=[1-9][0-9]*' "$RESULT"
grep -Eq 'FIELD_MOBILE_NATIVE_ROW provider=streamzo .* type=hls([[:space:]]|$)' "$RESULT"

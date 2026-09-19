#!/usr/bin/env bash
set -euo pipefail

# Use the SDK environment provisioned by android-emulator-runner. This proof is
# intentionally restricted to the injected NiakVIO instrumentation class.
echo "ANDROID_HOME=${ANDROID_HOME:-missing}"
ls -1 "${ANDROID_HOME:-/nonexistent}/platforms" 2>/dev/null || true

TV_REPORT_DIR="$GITHUB_WORKSPACE/nuvio-tv/app/build/reports/androidTests/niakvio"
TV_GRADLE_LOG="$TV_REPORT_DIR/tv-gradle.log"
TV_LOGCAT="$TV_REPORT_DIR/tv-logcat.log"
RESULT="$GITHUB_WORKSPACE/tv-final-native-results.log"
mkdir -p "$TV_REPORT_DIR"
rm -f "$TV_GRADLE_LOG" "$TV_LOGCAT" "$RESULT"

# Android TV emulator images may report ro.build.characteristics=emulator.
# Validate the platform by Android's declared TV/Leanback features instead.
adb shell getprop ro.build.characteristics | tee "$TV_REPORT_DIR/tv-build-characteristics.log"
adb shell pm list features | tee "$TV_REPORT_DIR/tv-platform-features.log"
grep -Eq 'feature:android\.software\.leanback|feature:android\.hardware\.type\.television' "$TV_REPORT_DIR/tv-platform-features.log"
adb devices -l | tee "$TV_REPORT_DIR/tv-adb-devices.log"

adb logcat -c
adb logcat -v brief -s NiakvioRealLab:I '*:S' > "$TV_LOGCAT" 2>&1 &
LOGCAT_PID=$!
cleanup_logcat() {
  kill "$LOGCAT_PID" 2>/dev/null || true
  wait "$LOGCAT_PID" 2>/dev/null || true
}
trap cleanup_logcat EXIT

tv_streamzo_proof_present() {
  local combined
  combined=$(mktemp)
  {
    cat "$TV_LOGCAT" 2>/dev/null || true
    grep -E 'FIELD_TV_' "$TV_GRADLE_LOG" 2>/dev/null || true
  } > "$combined"
  if grep -Eq 'FIELD_TV_NATIVE provider=streamzo .* count=[1-9][0-9]*' "$combined" \
    && grep -Eq 'FIELD_TV_NATIVE_ROW provider=streamzo .* type=hls([[:space:]]|$)' "$combined"; then
    rm -f "$combined"
    return 0
  fi
  rm -f "$combined"
  return 1
}

TV_STATUS=1
TV_PROOF_OK=0
for ATTEMPT in 1 2; do
  echo "FIELD_TV_PROOF_ATTEMPT attempt=$ATTEMPT max=2" | tee -a "$TV_GRADLE_LOG"
  set +e
  "$GITHUB_WORKSPACE/nuvio-tv/gradlew" -p "$GITHUB_WORKSPACE/nuvio-tv" :app:connectedFullDebugAndroidTest \
    '-Pandroid.testInstrumentationRunnerArguments.class=com.nuvio.tv.core.plugin.NiakvioFinalNativeTvTest' \
    --no-daemon --console=plain 2>&1 | tee -a "$TV_GRADLE_LOG"
  TV_STATUS=${PIPESTATUS[0]}
  set -e

  sleep 1
  if [[ "$TV_STATUS" -eq 0 ]] && tv_streamzo_proof_present; then
    TV_PROOF_OK=1
    break
  fi

  if [[ "$ATTEMPT" -lt 2 ]]; then
    if [[ "$TV_STATUS" -ne 0 ]]; then
      echo "FIELD_TV_PROOF_RETRY reason=instrumentation_failure status=$TV_STATUS" | tee -a "$TV_GRADLE_LOG"
    else
      echo "FIELD_TV_PROOF_RETRY reason=streamzo_proof_missing status=0" | tee -a "$TV_GRADLE_LOG"
    fi
    sleep 3
  fi
done

sleep 1
cleanup_logcat
trap - EXIT

{
  cat "$TV_LOGCAT" 2>/dev/null || true
  grep -E 'FIELD_TV_' "$TV_GRADLE_LOG" 2>/dev/null || true
} | awk '!seen[$0]++' > "$RESULT"
cat "$RESULT"

if [[ "$TV_STATUS" -ne 0 ]]; then
  exit "$TV_STATUS"
fi
if [[ "$TV_PROOF_OK" -ne 1 ]]; then
  echo "StreamZo TV native proof missing after 2 bounded attempts" >&2
  exit 1
fi

grep -Eq 'FIELD_TV_NATIVE provider=streamzo .* count=[1-9][0-9]*' "$RESULT"
grep -Eq 'FIELD_TV_NATIVE_ROW provider=streamzo .* type=hls([[:space:]]|$)' "$RESULT"

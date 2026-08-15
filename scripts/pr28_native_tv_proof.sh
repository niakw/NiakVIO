#!/usr/bin/env bash
set -euo pipefail

SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
test -x "$SDKMANAGER"
yes | "$SDKMANAGER" --licenses > /dev/null || true
"$SDKMANAGER" --install 'platforms;android-36' 'build-tools;36.0.0'

adb logcat -c
TV_REPORT_DIR="$GITHUB_WORKSPACE/nuvio-tv/app/build/reports/androidTests/niakvio"
TV_GRADLE_LOG="$TV_REPORT_DIR/tv-gradle.log"
RESULT="$GITHUB_WORKSPACE/tv-final-native-results.log"
mkdir -p "$TV_REPORT_DIR"

adb shell getprop ro.build.characteristics | tee "$TV_REPORT_DIR/tv-build-characteristics.log"
grep -Eq 'tv|television' "$TV_REPORT_DIR/tv-build-characteristics.log"
adb devices -l | tee "$TV_REPORT_DIR/tv-adb-devices.log"

set +e
"$GITHUB_WORKSPACE/nuvio-tv/gradlew" -p "$GITHUB_WORKSPACE/nuvio-tv" :app:connectedFullDebugAndroidTest \
  '-Pandroid.testInstrumentationRunnerArguments.class=com.nuvio.tv.core.plugin.NiakvioFinalNativeTvTest' \
  --no-daemon --console=plain 2>&1 | tee "$TV_GRADLE_LOG"
TV_STATUS=${PIPESTATUS[0]}
set -e

adb logcat -d -s NiakvioRealLab:I '*:S' > "$RESULT" || true
cat "$RESULT" || true
if [[ "$TV_STATUS" -ne 0 ]]; then
  exit "$TV_STATUS"
fi

grep -Eq 'FIELD_TV_NATIVE provider=streamzo .* count=[1-9][0-9]*' "$RESULT"
grep -Eq 'FIELD_TV_NATIVE_ROW provider=streamzo .* type=hls([[:space:]]|$)' "$RESULT"

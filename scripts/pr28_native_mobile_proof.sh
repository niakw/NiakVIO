#!/usr/bin/env bash
set -euo pipefail

# The historical native lab already compiled and ran this pinned NuvioMobile
# revision on the emulator-runner SDK environment. Do not guess/install future
# Android platforms here: doing so can fail before Gradle or the provider runs.
echo "ANDROID_HOME=${ANDROID_HOME:-missing}"
ls -1 "${ANDROID_HOME:-/nonexistent}/platforms" 2>/dev/null || true

adb logcat -c
TASKS=$("$GITHUB_WORKSPACE/nuvio-mobile/gradlew" -p "$GITHUB_WORKSPACE/nuvio-mobile" :composeApp:tasks --all -Pnuvio.android.distribution=full --console=plain)
TASK=$(printf '%s\n' "$TASKS" | awk 'tolower($1) ~ /connected.*device.*test/ {print $1; exit}')
if [[ -z "$TASK" ]]; then
  TASK=$(printf '%s\n' "$TASKS" | awk 'tolower($1) ~ /device.*test/ && tolower($0) ~ /connected/ {print $1; exit}')
fi
test -n "$TASK"
echo "Resolved NuvioMobile task: $TASK"

"$GITHUB_WORKSPACE/nuvio-mobile/gradlew" -p "$GITHUB_WORKSPACE/nuvio-mobile" ":composeApp:$TASK" \
  -Pnuvio.android.distribution=full --no-daemon --console=plain

RESULT="$GITHUB_WORKSPACE/mobile-final-native-results.log"
adb logcat -d -s NiakvioRealLab:I '*:S' > "$RESULT"
cat "$RESULT"
grep -Eq 'FIELD_MOBILE_NATIVE provider=streamzo .* count=[1-9][0-9]*' "$RESULT"
grep -Eq 'FIELD_MOBILE_NATIVE_ROW provider=streamzo .* type=hls([[:space:]]|$)' "$RESULT"

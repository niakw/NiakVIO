#!/usr/bin/env bash
set -euo pipefail

SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
test -x "$SDKMANAGER"
yes | "$SDKMANAGER" --licenses > /dev/null || true
"$SDKMANAGER" --install 'platforms;android-37' 'build-tools;37.0.0'

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

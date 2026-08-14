#!/usr/bin/env bash
set -u

MOBILE_ROOT="${GITHUB_WORKSPACE}/nuvio-mobile"
TV_ROOT="${GITHUB_WORKSPACE}/nuvio-tv"
MOBILE_LOG="${GITHUB_WORKSPACE}/mobile-final-native-results.log"
TV_LOG="${GITHUB_WORKSPACE}/tv-final-native-results.log"

MOBILE_STATUS=0
TV_STATUS=0

adb logcat -c || true

if [[ ! -x "$MOBILE_ROOT/gradlew" ]]; then
  echo "NuvioMobile gradlew missing: $MOBILE_ROOT/gradlew" >&2
  MOBILE_STATUS=98
else
  TASKS=$("$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" :composeApp:tasks --all -Pnuvio.android.distribution=full --console=plain) || MOBILE_STATUS=$?
  if [[ "$MOBILE_STATUS" -eq 0 ]]; then
    MOBILE_TASK=$(printf '%s\n' "$TASKS" | awk 'tolower($1) ~ /connected.*device.*test/ {print $1; exit}')
    if [[ -z "$MOBILE_TASK" ]]; then
      MOBILE_TASK=$(printf '%s\n' "$TASKS" | awk 'tolower($1) ~ /device.*test/ && tolower($0) ~ /connected/ {print $1; exit}')
    fi
    if [[ -z "$MOBILE_TASK" ]]; then
      echo "Unable to resolve NuvioMobile connected device-test task" >&2
      MOBILE_STATUS=97
    else
      echo "Resolved NuvioMobile task: $MOBILE_TASK"
      "$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" ":composeApp:$MOBILE_TASK" -Pnuvio.android.distribution=full --no-daemon --console=plain || MOBILE_STATUS=$?
    fi
  fi
fi

echo "===== EXACT MOBILE NATIVE RESULTS ====="
adb logcat -d -s NiakvioRealLab:I '*:S' > "$MOBILE_LOG" || true
cat "$MOBILE_LOG" || true

adb logcat -c || true

if [[ ! -x "$TV_ROOT/gradlew" ]]; then
  echo "NuvioTV gradlew missing: $TV_ROOT/gradlew" >&2
  TV_STATUS=98
else
  "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --no-daemon --console=plain || TV_STATUS=$?
fi

echo "===== EXACT TV NATIVE RESULTS ====="
adb logcat -d -s NiakvioRealLab:I '*:S' > "$TV_LOG" || true
cat "$TV_LOG" || true

# Android TV is a publication target, not a diagnostic-only compatibility tier.
# StreamZo's positive sentinel must traverse the real site -> player/embed ->
# final-media path and end in a direct HLS result. A catalogue page or iframe is
# not sufficient, and an empty result blocks promotion.
TV_STREAMZO_COUNT=$(grep 'FIELD_TV_NATIVE provider=streamzo ' "$TV_LOG" | tail -n 1 | sed -n 's/.* count=\([0-9][0-9]*\).*/\1/p')
TV_STREAMZO_HLS=0
if grep -Eq 'FIELD_TV_NATIVE_ROW provider=streamzo .* type=hls([[:space:]]|$)' "$TV_LOG"; then
  TV_STREAMZO_HLS=1
fi
if [[ -z "$TV_STREAMZO_COUNT" || "$TV_STREAMZO_COUNT" -le 0 || "$TV_STREAMZO_HLS" -ne 1 ]]; then
  echo "FIELD_TV_STREAMZO_SENTINEL status=failed expected=resolved path=site_player_media count=${TV_STREAMZO_COUNT:-missing} hls=$TV_STREAMZO_HLS" >&2
  echo "StreamZo must resolve Mon ninja et moi 3 through site -> player -> media on Android TV" >&2
  TV_STATUS=96
else
  echo "FIELD_TV_STREAMZO_SENTINEL status=resolved expected=resolved path=site_player_media count=$TV_STREAMZO_COUNT hls=$TV_STREAMZO_HLS"
fi

echo "FIELD_ANDROID_NATIVE_STATUS mobile=$MOBILE_STATUS tv=$TV_STATUS"
if [[ "$MOBILE_STATUS" -ne 0 || "$TV_STATUS" -ne 0 ]]; then
  exit 1
fi

#!/usr/bin/env bash
set -u

FIXTURE="${1:?fixture slug required}"
MOBILE_ROOT="${GITHUB_WORKSPACE}/nuvio-mobile"
TV_ROOT="${GITHUB_WORKSPACE}/nuvio-tv"
MOBILE_LOG="${GITHUB_WORKSPACE}/mobile-native-corpus-${FIXTURE}.log"
TV_LOG="${GITHUB_WORKSPACE}/tv-native-corpus-${FIXTURE}.log"

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

adb logcat -d -s NiakvioCorpus:I '*:S' > "$MOBILE_LOG" || true
echo "===== MOBILE NATIVE CORPUS: $FIXTURE ====="
cat "$MOBILE_LOG" || true

adb logcat -c || true

if [[ ! -x "$TV_ROOT/gradlew" ]]; then
  echo "NuvioTV gradlew missing: $TV_ROOT/gradlew" >&2
  TV_STATUS=98
else
  "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --no-daemon --console=plain || TV_STATUS=$?
fi

adb logcat -d -s NiakvioCorpus:I '*:S' > "$TV_LOG" || true
echo "===== TV NATIVE CORPUS: $FIXTURE ====="
cat "$TV_LOG" || true

echo "FIELD_NATIVE_CORPUS_ANDROID_STATUS fixture=$FIXTURE mobile=$MOBILE_STATUS tv=$TV_STATUS"
if [[ "$MOBILE_STATUS" -ne 0 || "$TV_STATUS" -ne 0 ]]; then
  exit 1
fi

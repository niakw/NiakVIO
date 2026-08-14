#!/usr/bin/env bash
set -u

WORKSPACE="${GITHUB_WORKSPACE}"
NIAKVIO="${WORKSPACE}/niakvio"
MOBILE_ROOT="${WORKSPACE}/nuvio-mobile"
TV_ROOT="${WORKSPACE}/nuvio-tv"
ANALYZER="${NIAKVIO}/scripts/analyze_native_corpus_results.cjs"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_fixture.py"
FIXTURES=(
  interstellar
  mon-ninja-et-moi-3
  breaking-bad-s01e01
  revenant-s01e01
  jujutsu-kaisen-s01e01
  mushoku-tensei-s01e01
)

STATUS=0

resolve_mobile_task() {
  local tasks
  tasks=$("$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" :composeApp:tasks --all -Pnuvio.android.distribution=full --console=plain) || return $?
  MOBILE_TASK=$(printf '%s\n' "$tasks" | awk 'tolower($1) ~ /connected.*device.*test/ {print $1; exit}')
  if [[ -z "${MOBILE_TASK:-}" ]]; then
    MOBILE_TASK=$(printf '%s\n' "$tasks" | awk 'tolower($1) ~ /device.*test/ && tolower($0) ~ /connected/ {print $1; exit}')
  fi
  if [[ -z "${MOBILE_TASK:-}" ]]; then
    echo "Unable to resolve NuvioMobile connected device-test task" >&2
    return 97
  fi
  echo "Resolved NuvioMobile task once for corpus suite: $MOBILE_TASK"
}

if ! resolve_mobile_task; then
  exit $?
fi

for fixture in "${FIXTURES[@]}"; do
  echo "===== MOBILE CORPUS FIXTURE: $fixture ====="
  python3 "$RESTAGE" android --fixture "$fixture" --workspace "$WORKSPACE" || { STATUS=1; continue; }
  adb logcat -c || true
  MOBILE_STATUS=0
  "$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" ":composeApp:$MOBILE_TASK" \
    -Pnuvio.android.distribution=full --no-daemon --console=plain || MOBILE_STATUS=$?
  MOBILE_LOG="${WORKSPACE}/mobile-native-corpus-${fixture}.log"
  adb logcat -d -s NiakvioCorpus:I '*:S' > "$MOBILE_LOG" || true
  cat "$MOBILE_LOG" || true
  ANALYSIS_STATUS=0
  node "$ANALYZER" "$fixture" "$MOBILE_LOG" || ANALYSIS_STATUS=$?
  echo "FIELD_NATIVE_CORPUS_MOBILE_STATUS fixture=$fixture runtime=$MOBILE_STATUS analysis=$ANALYSIS_STATUS"
  if [[ "$MOBILE_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 ]]; then STATUS=1; fi
done

for fixture in "${FIXTURES[@]}"; do
  echo "===== TV CORPUS FIXTURE: $fixture ====="
  python3 "$RESTAGE" android --fixture "$fixture" --workspace "$WORKSPACE" || { STATUS=1; continue; }
  adb logcat -c || true
  TV_STATUS=0
  "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --no-daemon --console=plain || TV_STATUS=$?
  TV_LOG="${WORKSPACE}/tv-native-corpus-${fixture}.log"
  adb logcat -d -s NiakvioCorpus:I '*:S' > "$TV_LOG" || true
  cat "$TV_LOG" || true
  ANALYSIS_STATUS=0
  node "$ANALYZER" "$fixture" "$TV_LOG" || ANALYSIS_STATUS=$?
  echo "FIELD_NATIVE_CORPUS_TV_STATUS fixture=$fixture runtime=$TV_STATUS analysis=$ANALYSIS_STATUS"
  if [[ "$TV_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 ]]; then STATUS=1; fi
done

echo "FIELD_NATIVE_CORPUS_ANDROID_SUITE_STATUS status=$STATUS fixtures=${#FIXTURES[@]} clients=2"
exit "$STATUS"

#!/usr/bin/env bash
set -u

WORKSPACE="${GITHUB_WORKSPACE}"
NIAKVIO="${WORKSPACE}/niakvio"
TV_ROOT="${WORKSPACE}/nuvio-tv"
ANALYZER="${NIAKVIO}/scripts/analyze_native_corpus_collection.cjs"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
FIXTURES=(interstellar mon-ninja-et-moi-3 breaking-bad-s01e01 revenant-s01e01 jujutsu-kaisen-s01e01 mushoku-tensei-s01e01)
STATUS=0

for fixture in "${FIXTURES[@]}"; do
  echo "===== TV CORPUS FIXTURE: $fixture ====="
  python3 "$RESTAGE" tv --fixture "$fixture" --workspace "$WORKSPACE" || { STATUS=1; continue; }
  adb logcat -c || true
  RUNTIME_STATUS=0
  "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --no-daemon --console=plain || RUNTIME_STATUS=$?
  LOG="${WORKSPACE}/tv-native-corpus-${fixture}.log"
  adb logcat -d -s NiakvioCorpus:I '*:S' > "$LOG" || true
  cat "$LOG" || true
  ANALYSIS_STATUS=0
  node "$ANALYZER" "$fixture" "$LOG" || ANALYSIS_STATUS=$?
  echo "FIELD_NATIVE_CORPUS_TV_STATUS fixture=$fixture runtime=$RUNTIME_STATUS collection=$ANALYSIS_STATUS"
  if [[ "$RUNTIME_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 ]]; then STATUS=1; fi
done

echo "FIELD_NATIVE_CORPUS_TV_SUITE_STATUS status=$STATUS fixtures=${#FIXTURES[@]} clients=1"
exit "$STATUS"

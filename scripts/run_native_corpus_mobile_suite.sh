#!/usr/bin/env bash
set -u

WORKSPACE="${GITHUB_WORKSPACE}"
NIAKVIO="${WORKSPACE}/niakvio"
MOBILE_ROOT="${WORKSPACE}/nuvio-mobile"
ANALYZER="${NIAKVIO}/scripts/analyze_native_corpus_collection.cjs"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
DEFAULT_FIXTURES=(sinners-2025 interstellar mon-ninja-et-moi-3 breaking-bad-s01e01 revenant-s01e01 jujutsu-kaisen-s01e01 mushoku-tensei-s01e01)
TARGET_FIXTURE="${NIAKVIO_TARGET_FIXTURE:-}"
TARGET_PROVIDER="${NIAKVIO_TARGET_PROVIDER:-}"
PLAYER_PROBES="${NIAKVIO_PLAYER_PROBES:-1}"
if [[ -n "$TARGET_FIXTURE" && "$TARGET_FIXTURE" != "all" ]]; then FIXTURES=("$TARGET_FIXTURE"); else FIXTURES=("${DEFAULT_FIXTURES[@]}"); fi
STATUS=0
PROVIDER_ARGS=()
if [[ -n "$TARGET_PROVIDER" && "$TARGET_PROVIDER" != "all" ]]; then PROVIDER_ARGS=(--provider "$TARGET_PROVIDER"); fi

tasks=$("$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" :composeApp:tasks --all -Pnuvio.android.distribution=full --console=plain) || exit $?
MOBILE_TASK=$(printf '%s\n' "$tasks" | awk 'tolower($1) ~ /connected.*device.*test/ {print $1; exit}')
if [[ -z "${MOBILE_TASK:-}" ]]; then MOBILE_TASK=$(printf '%s\n' "$tasks" | awk 'tolower($1) ~ /device.*test/ && tolower($0) ~ /connected/ {print $1; exit}'); fi
if [[ -z "${MOBILE_TASK:-}" ]]; then echo "Unable to resolve NuvioMobile connected device-test task" >&2; exit 97; fi
echo "Resolved NuvioMobile task once for corpus suite: $MOBILE_TASK"
echo "FIELD_NATIVE_CORPUS_MOBILE_PROFILE fixtures=${#FIXTURES[@]} provider=${TARGET_PROVIDER:-all} player_probes=$PLAYER_PROBES reuse_avd=true reuse_gradle_daemon=true"

for fixture in "${FIXTURES[@]}"; do
  echo "===== MOBILE CORPUS FIXTURE: $fixture ====="
  python3 "$RESTAGE" mobile --fixture "$fixture" --workspace "$WORKSPACE" "${PROVIDER_ARGS[@]}" --player-probes "$PLAYER_PROBES" || { STATUS=1; continue; }
  adb logcat -c || true
  RUNTIME_STATUS=0
  "$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" ":composeApp:$MOBILE_TASK" -Pnuvio.android.distribution=full --console=plain || RUNTIME_STATUS=$?
  LOG="${WORKSPACE}/mobile-native-corpus-${fixture}.log"
  adb logcat -d -s NiakvioCorpus:I '*:S' > "$LOG" || true
  cat "$LOG" || true
  ANALYSIS_STATUS=0
  node "$ANALYZER" "$fixture" "$LOG" || ANALYSIS_STATUS=$?
  echo "FIELD_NATIVE_CORPUS_MOBILE_STATUS fixture=$fixture runtime=$RUNTIME_STATUS collection=$ANALYSIS_STATUS"
  if [[ "$RUNTIME_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 ]]; then STATUS=1; fi
done

echo "FIELD_NATIVE_CORPUS_MOBILE_SUITE_STATUS status=$STATUS fixtures=${#FIXTURES[@]} clients=1 provider=${TARGET_PROVIDER:-all}"
exit "$STATUS"

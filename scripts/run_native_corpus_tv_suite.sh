#!/usr/bin/env bash
# PR reader trigger: route-list execution stays inside this shell so one emulator boot is reused.
set -u

if [[ "${GITHUB_EVENT_NAME:-}" = "pull_request" ]]; then
  export NIAKVIO_PR_PROVIDER_LIMIT="${NIAKVIO_PR_PROVIDER_LIMIT:-8}"
fi

WORKSPACE="${GITHUB_WORKSPACE}"
NIAKVIO="${WORKSPACE}/niakvio"
TV_ROOT="${WORKSPACE}/nuvio-tv"
ANALYZER="${NIAKVIO}/scripts/analyze_native_corpus_collection.cjs"
READER_GATE="${NIAKVIO}/scripts/gate_native_reader_result.cjs"
COVERAGE_GATE="${NIAKVIO}/scripts/gate_native_reader_coverage.cjs"
SMOKE_GATE="${NIAKVIO}/scripts/gate_native_player_reached.cjs"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
ACCEPTANCE_PREPARE="${NIAKVIO}/scripts/prepare_native_reader_acceptance.py"
INSTRUMENTER="${NIAKVIO}/scripts/instrument_native_client_evidence.py"
REPOSITORY_HTTP_INSTRUMENTER="${NIAKVIO}/scripts/instrument_native_repository_http_evidence.py"
REQUEST_CONTRACT="${NIAKVIO}/scripts/augment_native_corpus_request_contract.py"
PROVIDER_LOADING="${NIAKVIO}/scripts/augment_native_provider_loading_compat.py"
TV_HILT_FINALIZER="${NIAKVIO}/scripts/finalize_native_tv_test_entrypoint.py"
REPOSITORY_RESOLVER="${NIAKVIO}/scripts/resolve_native_repository.sh"
LAB_TRANSPORT="${NIAKVIO}/scripts/configure_native_android_lab_transport.py"
FRONTEND_CAPTURE="${NIAKVIO}/scripts/capture_native_device_frontend.sh"
FRONTEND_WATCHER="${NIAKVIO}/scripts/watch_native_device_frontend.sh"
EVIDENCE_ROOT="${WORKSPACE}/native-evidence/tv"
TEST_SOURCE="${TV_ROOT}/app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
DEFAULT_FIXTURES=(sinners-2025 interstellar mon-ninja-et-moi-3 colony-2021 breaking-bad-s01e01 revenant-s01e01 jujutsu-kaisen-s01e01 mushoku-tensei-s01e01 failure-frame-s01e01 hell-teacher-nube-2025-s01e01)
TARGET_FIXTURE="${NIAKVIO_TARGET_FIXTURE:-}"
TARGET_FIXTURES="${NIAKVIO_TARGET_FIXTURES:-}"
TARGET_PROVIDER="${NIAKVIO_TARGET_PROVIDER:-}"
TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"
PLAYER_PROBES="${NIAKVIO_PLAYER_PROBES:-1}"
REQUESTED_READER_SUCCESS="${NIAKVIO_REQUIRE_READER_SUCCESS:-0}"
PLAYER_OUTCOME_GLOBAL_GATE="${NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE:-0}"
REQUIRE_READER_SUCCESS=0
if [[ "$PLAYER_OUTCOME_GLOBAL_GATE" = "1" && "$REQUESTED_READER_SUCCESS" = "1" ]]; then
  REQUIRE_READER_SUCCESS=1
fi
READER_ACCEPTANCE="${NIAKVIO_READER_ACCEPTANCE:-0}"
PRIMARY_FIXTURE="${NIAKVIO_PRIMARY_FIXTURE:-sinners-2025}"
PRIMARY_STREAM_SCOPE="${NIAKVIO_PRIMARY_STREAM_SCOPE:-all}"
REGRESSION_STREAM_SCOPE="${NIAKVIO_REGRESSION_STREAM_SCOPE:-2}"
SOURCE_SHA="${NIAKVIO_SOURCE_SHA:-$(git -C "$NIAKVIO" rev-parse HEAD)}"
SOURCE_REPOSITORY="${GITHUB_REPOSITORY:-niakw/NiakVIO}"
source "$REPOSITORY_RESOLVER"
resolve_native_repository tv 10.0.2.2 18765 || exit $?
trap cleanup_native_repository EXIT
MANIFEST_URL="$NIAKVIO_RESOLVED_MANIFEST_URL"
ALLOW_LOCAL_MANIFEST="$NIAKVIO_RESOLVED_ALLOW_LOCAL"
PROVIDER_LOADING_URL_ARGS=()
if [[ "$ALLOW_LOCAL_MANIFEST" = "1" ]]; then PROVIDER_LOADING_URL_ARGS+=(--allow-local-lab-url); fi
CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE="$(python3 - <<'PY' 2>/dev/null || true
import json
import os
from pathlib import Path
path = Path(os.environ['GITHUB_WORKSPACE']) / 'niakvio/.github/triggers/nuvio-client-lab.json'
try:
    data = json.loads(path.read_text(encoding='utf-8'))
    print(str((data.get('native_reader_acceptance') or {}).get('provider_scope') or 'fixture'))
except Exception:
    print('fixture')
PY
)"
CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE="${CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE:-fixture}"
if [[ -n "$TARGET_FIXTURES" ]]; then
  FIXTURES=()
  for fixture in $TARGET_FIXTURES; do FIXTURES+=("$fixture"); done
elif [[ -n "$TARGET_FIXTURE" && "$TARGET_FIXTURE" != "all" ]]; then
  FIXTURES=("$TARGET_FIXTURE")
else
  FIXTURES=("${DEFAULT_FIXTURES[@]}")
fi

# TV is the primary user-impact signal. On the production manifest baseline, always
# append the small collision/remake regression set even when the caller requests only
# the generic representative movie/series/anime trio. Candidate Brain retests use a
# different manifest path and intentionally keep their bounded original fixture set.
TV_PRIORITY_FIXTURES=()
if [[ "$TARGET_MANIFEST" = "manifest.json" ]]; then
  while IFS= read -r fixture; do
    [[ -n "$fixture" ]] && TV_PRIORITY_FIXTURES+=("$fixture")
  done < <(python3 - <<'PY' 2>/dev/null || true
import json
import os
from pathlib import Path
path = Path(os.environ['GITHUB_WORKSPACE']) / 'niakvio/.github/triggers/nuvio-client-lab.json'
try:
    data = json.loads(path.read_text(encoding='utf-8'))
    for fixture in (data.get('native_reader_acceptance') or {}).get('tv_priority_regressions') or []:
        print(str(fixture))
except Exception:
    pass
PY
)
  for priority_fixture in "${TV_PRIORITY_FIXTURES[@]}"; do
    already=false
    for existing_fixture in "${FIXTURES[@]}"; do
      if [[ "$existing_fixture" = "$priority_fixture" ]]; then already=true; break; fi
    done
    if [[ "$already" != "true" ]]; then FIXTURES+=("$priority_fixture"); fi
  done
fi

SOFT_FAILURES=0
PROVIDER_ARGS=()
if [[ -n "$TARGET_PROVIDER" && "$TARGET_PROVIDER" != "all" && "$TARGET_PROVIDER" != "fixture" ]]; then PROVIDER_ARGS=(--provider "$TARGET_PROVIDER"); fi

mkdir -p "$EVIDENCE_ROOT"
python3 "$LAB_TRANSPORT" "$TV_ROOT/app/src/androidTest/AndroidManifest.xml" || exit $?
python3 "$INSTRUMENTER" tv "$TV_ROOT" || exit $?
python3 "$REPOSITORY_HTTP_INSTRUMENTER" tv "$TV_ROOT" || exit $?
if [[ -n "${GITHUB_ENV:-}" ]]; then echo "NIAKVIO_BRAIN_NONBLOCKING=1" >> "$GITHUB_ENV"; fi

echo "FIELD_NATIVE_CORPUS_TV_PROFILE fixtures=${#FIXTURES[@]} tv_priority_fixtures=${#TV_PRIORITY_FIXTURES[@]} provider=${TARGET_PROVIDER:-all} configured_acceptance_provider_scope=$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE manifest=$TARGET_MANIFEST player_probes=$PLAYER_PROBES requested_reader_success=$REQUESTED_READER_SUCCESS require_reader_success=$REQUIRE_READER_SUCCESS player_outcome_global_gate=$PLAYER_OUTCOME_GLOBAL_GATE reader_acceptance=$READER_ACCEPTANCE primary_stream_scope=$PRIMARY_STREAM_SCOPE regression_stream_scope=$REGRESSION_STREAM_SCOPE reuse_avd=true reuse_gradle_daemon=true full_backend_evidence=true repository_http_evidence=true frontend_timeline=true official_repository_loading=true local_manifest=$ALLOW_LOCAL_MANIFEST smoke_gate=player_reached pr_provider_limit=${NIAKVIO_PR_PROVIDER_LIMIT:-default}"
for fixture in "${FIXTURES[@]}"; do
  echo "===== TV CORPUS FIXTURE: $fixture ====="
  STREAM_SCOPE="$REGRESSION_STREAM_SCOPE"
  if [[ "$fixture" = "$PRIMARY_FIXTURE" ]]; then STREAM_SCOPE="$PRIMARY_STREAM_SCOPE"; fi
  if [[ "$READER_ACCEPTANCE" = "1" ]]; then
    PROVIDER_SCOPE="$TARGET_PROVIDER"
    if [[ -z "$PROVIDER_SCOPE" || "$PROVIDER_SCOPE" = "fixture" ]]; then PROVIDER_SCOPE="$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE"; fi
    if [[ -z "$PROVIDER_SCOPE" ]]; then PROVIDER_SCOPE="fixture"; fi
    python3 "$ACCEPTANCE_PREPARE" tv --fixture "$fixture" --workspace "$WORKSPACE" --provider "$PROVIDER_SCOPE" --streams "$STREAM_SCOPE" --manifest "$TARGET_MANIFEST" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  else
    python3 "$RESTAGE" tv --fixture "$fixture" --workspace "$WORKSPACE" "${PROVIDER_ARGS[@]}" --player-probes "$PLAYER_PROBES" --manifest "$TARGET_MANIFEST" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  fi

  python3 "$REQUEST_CONTRACT" tv --fixture "$fixture" --manifest "$TARGET_MANIFEST" --source "$TEST_SOURCE" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  python3 "$PROVIDER_LOADING" tv --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" "${PROVIDER_LOADING_URL_ARGS[@]}" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  python3 "$TV_HILT_FINALIZER" "$TEST_SOURCE" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }

  FRONT_DIR="${EVIDENCE_ROOT}/${fixture}"
  FRONT_LOG="${WORKSPACE}/tv-native-frontend-${fixture}.log"
  GRADLE_LOG="${FRONT_DIR}/gradle.log"
  mkdir -p "$FRONT_DIR"
  rm -f "$FRONT_LOG" "$GRADLE_LOG"
  adb logcat -c || true
  bash "$FRONTEND_WATCHER" tv "$FRONT_DIR" "$FRONTEND_CAPTURE" > "$FRONT_LOG" 2>&1 &
  WATCH_PID=$!

  RUNTIME_STATUS=0
  "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --console=plain 2>&1 | tee "$GRADLE_LOG"
  RUNTIME_STATUS=${PIPESTATUS[0]}
  sleep 1
  kill "$WATCH_PID" 2>/dev/null || true
  wait "$WATCH_PID" 2>/dev/null || true

  LOG="${WORKSPACE}/tv-native-corpus-${fixture}.log"
  adb logcat -d -v brief -s NiakvioCorpus:I NiakvioEvidence:I '*:S' > "$LOG" || true
  echo "FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=tv" >> "$LOG"
  cat "$FRONT_LOG" >> "$LOG" 2>/dev/null || true
  cat "$LOG" || true

  ANALYSIS_STATUS=0
  node "$ANALYZER" "$fixture" "$LOG" || ANALYSIS_STATUS=$?
  COVERAGE_STATUS=0
  if [[ "$READER_ACCEPTANCE" = "1" ]]; then
    node "$COVERAGE_GATE" --streams "$STREAM_SCOPE" "$LOG" || COVERAGE_STATUS=$?
  fi
  OBSERVED_READER_STATUS=0
  node "$READER_GATE" "$LOG" || OBSERVED_READER_STATUS=$?
  if [[ "$RUNTIME_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 || "$COVERAGE_STATUS" -ne 0 || "$OBSERVED_READER_STATUS" -ne 0 ]]; then
    SOFT_FAILURES=$((SOFT_FAILURES+1))
  fi
  echo "FIELD_NATIVE_CORPUS_TV_STATUS fixture=$fixture runtime=$RUNTIME_STATUS collection=$ANALYSIS_STATUS coverage=$COVERAGE_STATUS reader_observed=$OBSERVED_READER_STATUS blocking=false stream_scope=$STREAM_SCOPE frontend_dir=$FRONT_DIR"
done

for fixture in "${FIXTURES[@]}"; do
  LOG="${WORKSPACE}/tv-native-corpus-${fixture}.log"
  if [[ ! -s "$LOG" ]]; then
    printf 'FIELD_NATIVE_SMOKE_DIAGNOSTIC_PLACEHOLDER client=tv fixture=%s reason=no_route_log\n' "$fixture" > "$LOG"
  fi
done

LOGS=("${WORKSPACE}"/tv-native-corpus-*.log)
SMOKE_STATUS=0
node "$SMOKE_GATE" "${LOGS[@]}" || SMOKE_STATUS=$?
echo "FIELD_NATIVE_CORPUS_TV_SUITE_STATUS status=$SMOKE_STATUS soft_failures=$SOFT_FAILURES fixtures=${#FIXTURES[@]} clients=1 provider=${TARGET_PROVIDER:-all} configured_acceptance_provider_scope=$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE manifest=$TARGET_MANIFEST gate=production_player_reached evidence_root=$EVIDENCE_ROOT"
exit "$SMOKE_STATUS"

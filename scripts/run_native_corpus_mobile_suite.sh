#!/usr/bin/env bash
set -u

WORKSPACE="${GITHUB_WORKSPACE}"
NIAKVIO="${WORKSPACE}/niakvio"
MOBILE_ROOT="${WORKSPACE}/nuvio-mobile"
ANALYZER="${NIAKVIO}/scripts/analyze_native_corpus_collection.cjs"
READER_GATE="${NIAKVIO}/scripts/gate_native_reader_result.cjs"
COVERAGE_GATE="${NIAKVIO}/scripts/gate_native_reader_coverage.cjs"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
ACCEPTANCE_PREPARE="${NIAKVIO}/scripts/prepare_native_reader_acceptance.py"
INSTRUMENTER="${NIAKVIO}/scripts/instrument_native_client_evidence.py"
REPOSITORY_HTTP_INSTRUMENTER="${NIAKVIO}/scripts/instrument_native_repository_http_evidence.py"
REQUEST_CONTRACT="${NIAKVIO}/scripts/augment_native_corpus_request_contract.py"
PROVIDER_LOADING="${NIAKVIO}/scripts/augment_native_provider_loading.py"
REPOSITORY_RESOLVER="${NIAKVIO}/scripts/resolve_native_repository.sh"
FRONTEND_CAPTURE="${NIAKVIO}/scripts/capture_native_device_frontend.sh"
FRONTEND_WATCHER="${NIAKVIO}/scripts/watch_native_device_frontend.sh"
EVIDENCE_ROOT="${WORKSPACE}/native-evidence/mobile"
TEST_SOURCE="${MOBILE_ROOT}/composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
DEFAULT_FIXTURES=(sinners-2025 interstellar mon-ninja-et-moi-3 breaking-bad-s01e01 revenant-s01e01 jujutsu-kaisen-s01e01 mushoku-tensei-s01e01)
TARGET_FIXTURE="${NIAKVIO_TARGET_FIXTURE:-}"
TARGET_PROVIDER="${NIAKVIO_TARGET_PROVIDER:-}"
TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"
PLAYER_PROBES="${NIAKVIO_PLAYER_PROBES:-1}"
REQUIRE_READER_SUCCESS="${NIAKVIO_REQUIRE_READER_SUCCESS:-0}"
READER_ACCEPTANCE="${NIAKVIO_READER_ACCEPTANCE:-0}"
PRIMARY_FIXTURE="${NIAKVIO_PRIMARY_FIXTURE:-sinners-2025}"
PRIMARY_STREAM_SCOPE="${NIAKVIO_PRIMARY_STREAM_SCOPE:-all}"
REGRESSION_STREAM_SCOPE="${NIAKVIO_REGRESSION_STREAM_SCOPE:-2}"
SOURCE_SHA="${NIAKVIO_SOURCE_SHA:-$(git -C "$NIAKVIO" rev-parse HEAD)}"
SOURCE_REPOSITORY="${GITHUB_REPOSITORY:-niakw/NiakVIO}"
source "$REPOSITORY_RESOLVER"
resolve_native_repository mobile 10.0.2.2 18766 || exit $?
trap cleanup_native_repository EXIT
MANIFEST_URL="$NIAKVIO_RESOLVED_MANIFEST_URL"
ALLOW_LOCAL_MANIFEST="$NIAKVIO_RESOLVED_ALLOW_LOCAL"
PROVIDER_LOADING_URL_ARGS=()
if [[ "$ALLOW_LOCAL_MANIFEST" = "1" ]]; then PROVIDER_LOADING_URL_ARGS+=(--allow-local-lab-url); fi
CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE="$(python3 - <<'PY' 2>/dev/null || true
import json
from pathlib import Path
path = Path(__import__('os').environ['GITHUB_WORKSPACE']) / 'niakvio/.github/triggers/nuvio-client-lab.json'
try:
    data = json.loads(path.read_text(encoding='utf-8'))
    print(str((data.get('native_reader_acceptance') or {}).get('provider_scope') or 'fixture'))
except Exception:
    print('fixture')
PY
)"
CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE="${CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE:-fixture}"
if [[ -n "$TARGET_FIXTURE" && "$TARGET_FIXTURE" != "all" ]]; then FIXTURES=("$TARGET_FIXTURE"); else FIXTURES=("${DEFAULT_FIXTURES[@]}"); fi
STATUS=0
PROVIDER_ARGS=()
if [[ -n "$TARGET_PROVIDER" && "$TARGET_PROVIDER" != "all" && "$TARGET_PROVIDER" != "fixture" ]]; then PROVIDER_ARGS=(--provider "$TARGET_PROVIDER"); fi

python3 "$INSTRUMENTER" mobile "$MOBILE_ROOT" || exit $?
python3 "$REPOSITORY_HTTP_INSTRUMENTER" mobile "$MOBILE_ROOT" || exit $?

tasks=$("$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" :composeApp:tasks --all -Pnuvio.android.distribution=full --console=plain) || exit $?
MOBILE_TASK=$(printf '%s\n' "$tasks" | awk 'tolower($1) ~ /connected.*device.*test/ {print $1; exit}')
if [[ -z "${MOBILE_TASK:-}" ]]; then MOBILE_TASK=$(printf '%s\n' "$tasks" | awk 'tolower($1) ~ /device.*test/ && tolower($0) ~ /connected/ {print $1; exit}'); fi
if [[ -z "${MOBILE_TASK:-}" ]]; then echo "Unable to resolve NuvioMobile connected device-test task" >&2; exit 97; fi
mkdir -p "$EVIDENCE_ROOT"
echo "Resolved NuvioMobile task once for corpus suite: $MOBILE_TASK"
echo "FIELD_NATIVE_CORPUS_MOBILE_PROFILE fixtures=${#FIXTURES[@]} provider=${TARGET_PROVIDER:-all} configured_acceptance_provider_scope=$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE manifest=$TARGET_MANIFEST player_probes=$PLAYER_PROBES require_reader_success=$REQUIRE_READER_SUCCESS reader_acceptance=$READER_ACCEPTANCE primary_stream_scope=$PRIMARY_STREAM_SCOPE regression_stream_scope=$REGRESSION_STREAM_SCOPE reuse_avd=true reuse_gradle_daemon=true full_backend_evidence=true repository_http_evidence=true frontend_timeline=true official_repository_loading=true local_manifest=$ALLOW_LOCAL_MANIFEST"

for fixture in "${FIXTURES[@]}"; do
  echo "===== MOBILE CORPUS FIXTURE: $fixture ====="
  STREAM_SCOPE="$REGRESSION_STREAM_SCOPE"
  if [[ "$fixture" = "$PRIMARY_FIXTURE" ]]; then STREAM_SCOPE="$PRIMARY_STREAM_SCOPE"; fi
  if [[ "$READER_ACCEPTANCE" = "1" ]]; then
    PROVIDER_SCOPE="$TARGET_PROVIDER"
    if [[ -z "$PROVIDER_SCOPE" || "$PROVIDER_SCOPE" = "fixture" ]]; then PROVIDER_SCOPE="$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE"; fi
    if [[ -z "$PROVIDER_SCOPE" ]]; then PROVIDER_SCOPE="fixture"; fi
    python3 "$ACCEPTANCE_PREPARE" mobile --fixture "$fixture" --workspace "$WORKSPACE" --provider "$PROVIDER_SCOPE" --streams "$STREAM_SCOPE" --manifest "$TARGET_MANIFEST" || { STATUS=1; continue; }
  else
    python3 "$RESTAGE" mobile --fixture "$fixture" --workspace "$WORKSPACE" "${PROVIDER_ARGS[@]}" --player-probes "$PLAYER_PROBES" --manifest "$TARGET_MANIFEST" || { STATUS=1; continue; }
  fi

  python3 "$REQUEST_CONTRACT" mobile --fixture "$fixture" --manifest "$TARGET_MANIFEST" --source "$TEST_SOURCE" || { STATUS=1; continue; }
  python3 "$PROVIDER_LOADING" mobile --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" "${PROVIDER_LOADING_URL_ARGS[@]}" || { STATUS=1; continue; }

  FRONT_DIR="${EVIDENCE_ROOT}/${fixture}"
  FRONT_LOG="${WORKSPACE}/mobile-native-frontend-${fixture}.log"
  mkdir -p "$FRONT_DIR"
  rm -f "$FRONT_LOG"
  adb logcat -c || true
  bash "$FRONTEND_WATCHER" mobile "$FRONT_DIR" "$FRONTEND_CAPTURE" > "$FRONT_LOG" 2>&1 &
  WATCH_PID=$!

  RUNTIME_STATUS=0
  "$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" ":composeApp:$MOBILE_TASK" -Pnuvio.android.distribution=full --console=plain || RUNTIME_STATUS=$?
  sleep 1
  kill "$WATCH_PID" 2>/dev/null || true
  wait "$WATCH_PID" 2>/dev/null || true

  LOG="${WORKSPACE}/mobile-native-corpus-${fixture}.log"
  # Persist only NiakVIO's structured evidence. Official PluginRepository/runtime
  # debug lines may contain raw provider URLs and are intentionally excluded.
  adb logcat -d -v brief -s NiakvioCorpus:I NiakvioEvidence:I '*:S' > "$LOG" || true
  echo "FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=mobile" >> "$LOG"
  cat "$FRONT_LOG" >> "$LOG" 2>/dev/null || true
  cat "$LOG" || true

  ANALYSIS_STATUS=0
  node "$ANALYZER" "$fixture" "$LOG" || ANALYSIS_STATUS=$?
  COVERAGE_STATUS=0
  if [[ "$READER_ACCEPTANCE" = "1" ]]; then
    node "$COVERAGE_GATE" --streams "$STREAM_SCOPE" "$LOG" || COVERAGE_STATUS=$?
  fi
  READER_STATUS=0
  if [[ "$REQUIRE_READER_SUCCESS" = "1" ]]; then
    node "$READER_GATE" "$LOG" || READER_STATUS=$?
  fi
  echo "FIELD_NATIVE_CORPUS_MOBILE_STATUS fixture=$fixture runtime=$RUNTIME_STATUS collection=$ANALYSIS_STATUS coverage=$COVERAGE_STATUS reader=$READER_STATUS stream_scope=$STREAM_SCOPE frontend_dir=$FRONT_DIR"
  if [[ "$RUNTIME_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 || "$COVERAGE_STATUS" -ne 0 || "$READER_STATUS" -ne 0 ]]; then STATUS=1; fi
done

echo "FIELD_NATIVE_CORPUS_MOBILE_SUITE_STATUS status=$STATUS fixtures=${#FIXTURES[@]} clients=1 provider=${TARGET_PROVIDER:-all} configured_acceptance_provider_scope=$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE manifest=$TARGET_MANIFEST require_reader_success=$REQUIRE_READER_SUCCESS reader_acceptance=$READER_ACCEPTANCE evidence_root=$EVIDENCE_ROOT"
exit "$STATUS"

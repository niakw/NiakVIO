#!/usr/bin/env bash
set -u

if [[ "${GITHUB_EVENT_NAME:-}" = "pull_request" ]]; then
  export NIAKVIO_PR_PROVIDER_LIMIT="${NIAKVIO_PR_PROVIDER_LIMIT:-8}"
fi

WORKSPACE="${GITHUB_WORKSPACE}"
NIAKVIO="${WORKSPACE}/niakvio"
DESKTOP_ROOT="${WORKSPACE}/nuvio-desktop"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
ANALYZER="${NIAKVIO}/scripts/analyze_native_corpus_collection.cjs"
READER_GATE="${NIAKVIO}/scripts/gate_native_reader_result.cjs"
COVERAGE_GATE="${NIAKVIO}/scripts/gate_native_reader_coverage.cjs"
SMOKE_GATE="${NIAKVIO}/scripts/gate_native_player_reached.cjs"
INSTRUMENTER="${NIAKVIO}/scripts/instrument_native_desktop_evidence.py"
REPOSITORY_HTTP_INSTRUMENTER="${NIAKVIO}/scripts/instrument_native_repository_http_evidence.py"
REQUEST_CONTRACT="${NIAKVIO}/scripts/augment_native_corpus_request_contract.py"
PROVIDER_LOADING="${NIAKVIO}/scripts/augment_native_provider_loading_compat.py"
REPOSITORY_RESOLVER="${NIAKVIO}/scripts/resolve_native_repository.sh"
PLAYER_AUGMENT="${NIAKVIO}/scripts/augment_native_desktop_player.py"
FRONTEND_PHASES="${NIAKVIO}/scripts/complete_native_desktop_frontend_phases.py"
DESKTOP_TEST_JVM_INIT="${NIAKVIO}/scripts/nuvio_desktop_test_jvm.init.gradle"
TEST_SOURCE="${DESKTOP_ROOT}/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
DEFAULT_FIXTURES=(sinners-2025 interstellar mon-ninja-et-moi-3 breaking-bad-s01e01 revenant-s01e01 jujutsu-kaisen-s01e01 mushoku-tensei-s01e01)
TARGET_FIXTURE="${NIAKVIO_TARGET_FIXTURE:-}"
TARGET_PROVIDER="${NIAKVIO_TARGET_PROVIDER:-all}"
TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"
PRIMARY_FIXTURE="${NIAKVIO_PRIMARY_FIXTURE:-sinners-2025}"
PRIMARY_STREAM_SCOPE="${NIAKVIO_PRIMARY_STREAM_SCOPE:-all}"
REGRESSION_STREAM_SCOPE="${NIAKVIO_REGRESSION_STREAM_SCOPE:-2}"
REQUESTED_READER_SUCCESS="${NIAKVIO_REQUIRE_READER_SUCCESS:-0}"
PLAYER_OUTCOME_GLOBAL_GATE="${NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE:-0}"
REQUIRE_READER_SUCCESS=0
if [[ "$PLAYER_OUTCOME_GLOBAL_GATE" = "1" && "$REQUESTED_READER_SUCCESS" = "1" ]]; then
  REQUIRE_READER_SUCCESS=1
fi
SOURCE_SHA="${NIAKVIO_SOURCE_SHA:-$(git -C "$NIAKVIO" rev-parse HEAD)}"
SOURCE_REPOSITORY="${GITHUB_REPOSITORY:-niakw/NiakVIO}"
source "$REPOSITORY_RESOLVER"
resolve_native_repository desktop 127.0.0.1 18767 || exit $?
trap cleanup_native_repository EXIT
MANIFEST_URL="$NIAKVIO_RESOLVED_MANIFEST_URL"
ALLOW_LOCAL_MANIFEST="$NIAKVIO_RESOLVED_ALLOW_LOCAL"

case "$(uname -s)" in
  Darwin) HOST_OS="macos" ;;
  MINGW*|MSYS*|CYGWIN*) HOST_OS="windows" ;;
  *) echo "FIELD_NATIVE_DESKTOP_READER_UNSUPPORTED os=$(uname -s) reason=official_nuvio_desktop_player_is_stub" >&2; exit 96 ;;
esac

if [[ "$(id -u)" == "0" ]]; then
  echo "FIELD_NATIVE_DESKTOP_READER_INFRA_ERROR os=$HOST_OS reason=root_execution_forbidden" >&2
  exit 97
fi

if [[ -n "$TARGET_FIXTURE" && "$TARGET_FIXTURE" != "all" ]]; then
  FIXTURES=("$TARGET_FIXTURE")
else
  FIXTURES=("${DEFAULT_FIXTURES[@]}")
fi

python3 "$INSTRUMENTER" "$DESKTOP_ROOT" || exit $?
python3 "$REPOSITORY_HTTP_INSTRUMENTER" desktop "$DESKTOP_ROOT" || exit $?
if [[ -n "${GITHUB_ENV:-}" ]]; then echo "NIAKVIO_BRAIN_NONBLOCKING=1" >> "$GITHUB_ENV"; fi

SOFT_FAILURES=0

echo "FIELD_NATIVE_CORPUS_DESKTOP_PROFILE os=$HOST_OS fixtures=${#FIXTURES[@]} provider=${TARGET_PROVIDER:-all} manifest=$TARGET_MANIFEST primary_stream_scope=$PRIMARY_STREAM_SCOPE regression_stream_scope=$REGRESSION_STREAM_SCOPE requested_reader_success=$REQUESTED_READER_SUCCESS require_reader_success=$REQUIRE_READER_SUCCESS player_outcome_global_gate=$PLAYER_OUTCOME_GLOBAL_GATE official_player=production_path official_repository_loading=true repository_http_evidence=true local_manifest=$ALLOW_LOCAL_MANIFEST observational=true privilege=ordinary-user smoke_gate=player_reached pr_provider_limit=${NIAKVIO_PR_PROVIDER_LIMIT:-default}"
for fixture in "${FIXTURES[@]}"; do
  STREAM_SCOPE="$REGRESSION_STREAM_SCOPE"
  if [[ "$fixture" = "$PRIMARY_FIXTURE" ]]; then STREAM_SCOPE="$PRIMARY_STREAM_SCOPE"; fi
  echo "===== DESKTOP NATIVE READER FIXTURE: $fixture ($HOST_OS) ====="

  if [[ -n "$TARGET_PROVIDER" && "$TARGET_PROVIDER" != "all" && "$TARGET_PROVIDER" != "fixture" ]]; then
    python3 "$RESTAGE" desktop --fixture "$fixture" --workspace "$WORKSPACE" --provider "$TARGET_PROVIDER" --manifest "$TARGET_MANIFEST" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  else
    python3 "$RESTAGE" desktop --fixture "$fixture" --workspace "$WORKSPACE" --manifest "$TARGET_MANIFEST" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  fi
  python3 "$REQUEST_CONTRACT" desktop --fixture "$fixture" --manifest "$TARGET_MANIFEST" --source "$TEST_SOURCE" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  if [[ "$ALLOW_LOCAL_MANIFEST" = "1" ]]; then
    python3 "$PROVIDER_LOADING" desktop --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" --platform "$HOST_OS" --allow-local-lab-url || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  else
    python3 "$PROVIDER_LOADING" desktop --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" --platform "$HOST_OS" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  fi
  EXPECTED_MINUTES="$(python3 - "$fixture" "$NIAKVIO/.github/triggers/nuvio-client-lab.json" <<'PY'
import json, sys
slug, path = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding='utf-8'))
for row in data.get('fixtures', []):
    if row.get('slug') == slug:
        print(int((row.get('fixture') or {}).get('expectedDurationMinutes') or 0))
        break
else:
    raise SystemExit(f'fixture not found: {slug}')
PY
)" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  python3 "$PLAYER_AUGMENT" --source "$TEST_SOURCE" --expected-minutes "$EXPECTED_MINUTES" --streams "$STREAM_SCOPE" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }
  python3 "$FRONTEND_PHASES" "$TEST_SOURCE" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }

  BASE_LOG="${WORKSPACE}/desktop-native-corpus-${fixture}.log"
  LOG="${WORKSPACE}/desktop-native-corpus-${HOST_OS}-${fixture}.log"
  GRADLE_LOG="${WORKSPACE}/desktop-native-gradle-${HOST_OS}-${fixture}.log"
  HTTP_LOG="${WORKSPACE}/desktop-native-http-evidence.log"
  rm -f "$BASE_LOG" "$LOG" "$GRADLE_LOG" "$HTTP_LOG"
  RUNTIME_STATUS=0
  # The test source is regenerated for every fixture. Gradle's build cache can
  # otherwise restore desktopTest outputs from an earlier injected source and make
  # the native corpus appear to execute while producing no corpus/player markers.
  # Force this one lab test to run from the exact source just staged above.
  if [[ "$HOST_OS" = "windows" ]]; then
    "$DESKTOP_ROOT/gradlew.bat" -p "$DESKTOP_ROOT" --init-script "$DESKTOP_TEST_JVM_INIT" :composeApp:desktopTest --tests 'com.nuvio.app.features.plugins.NiakvioNativeCorpusDesktopTest' --rerun-tasks --no-build-cache --no-configuration-cache --console=plain 2>&1 | tee "$GRADLE_LOG"
    RUNTIME_STATUS=${PIPESTATUS[0]}
  else
    "$DESKTOP_ROOT/gradlew" -p "$DESKTOP_ROOT" --init-script "$DESKTOP_TEST_JVM_INIT" :composeApp:desktopTest --tests 'com.nuvio.app.features.plugins.NiakvioNativeCorpusDesktopTest' --rerun-tasks --no-build-cache --no-configuration-cache --console=plain 2>&1 | tee "$GRADLE_LOG"
    RUNTIME_STATUS=${PIPESTATUS[0]}
  fi

  if [[ -s "$BASE_LOG" ]]; then cp "$BASE_LOG" "$LOG"; else : > "$LOG"; fi
  if [[ -s "$HTTP_LOG" ]]; then cat "$HTTP_LOG" >> "$LOG"; fi
  rm -f "$HTTP_LOG" "$GRADLE_LOG"
  echo "FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=desktop" >> "$LOG"
  cat "$LOG" || true

  ANALYSIS_STATUS=0
  node "$ANALYZER" "$fixture" "$LOG" || ANALYSIS_STATUS=$?
  COVERAGE_STATUS=0
  node "$COVERAGE_GATE" --streams "$STREAM_SCOPE" "$LOG" || COVERAGE_STATUS=$?
  OBSERVED_READER_STATUS=0
  node "$READER_GATE" "$LOG" || OBSERVED_READER_STATUS=$?
  if [[ "$RUNTIME_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 || "$COVERAGE_STATUS" -ne 0 || "$OBSERVED_READER_STATUS" -ne 0 ]]; then
    SOFT_FAILURES=$((SOFT_FAILURES+1))
  fi
  echo "FIELD_NATIVE_CORPUS_DESKTOP_STATUS os=$HOST_OS fixture=$fixture runtime=$RUNTIME_STATUS collection=$ANALYSIS_STATUS coverage=$COVERAGE_STATUS reader_observed=$OBSERVED_READER_STATUS blocking=false stream_scope=$STREAM_SCOPE"
done

for fixture in "${FIXTURES[@]}"; do
  LOG="${WORKSPACE}/desktop-native-corpus-${HOST_OS}-${fixture}.log"
  if [[ ! -s "$LOG" ]]; then
    printf 'FIELD_NATIVE_SMOKE_DIAGNOSTIC_PLACEHOLDER client=desktop fixture=%s reason=no_route_log\n' "$fixture" > "$LOG"
  fi
done

LOGS=("${WORKSPACE}"/desktop-native-corpus-${HOST_OS}-*.log)
SMOKE_STATUS=0
node "$SMOKE_GATE" "${LOGS[@]}" || SMOKE_STATUS=$?
echo "FIELD_NATIVE_CORPUS_DESKTOP_SUITE_STATUS os=$HOST_OS status=$SMOKE_STATUS soft_failures=$SOFT_FAILURES fixtures=${#FIXTURES[@]} provider=${TARGET_PROVIDER:-all} manifest=$TARGET_MANIFEST gate=production_player_reached"
exit "$SMOKE_STATUS"

#!/usr/bin/env bash
set -u

WORKSPACE="${GITHUB_WORKSPACE}"
NIAKVIO="${WORKSPACE}/niakvio"
TV_ROOT="${WORKSPACE}/nuvio-tv"
ANALYZER="${NIAKVIO}/scripts/analyze_native_corpus_collection.cjs"
READER_GATE="${NIAKVIO}/scripts/gate_native_reader_result.cjs"
COVERAGE_GATE="${NIAKVIO}/scripts/gate_native_reader_coverage.cjs"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
ACCEPTANCE_PREPARE="${NIAKVIO}/scripts/prepare_native_reader_acceptance.py"
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

echo "FIELD_NATIVE_CORPUS_TV_PROFILE fixtures=${#FIXTURES[@]} provider=${TARGET_PROVIDER:-all} configured_acceptance_provider_scope=$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE manifest=$TARGET_MANIFEST player_probes=$PLAYER_PROBES require_reader_success=$REQUIRE_READER_SUCCESS reader_acceptance=$READER_ACCEPTANCE primary_stream_scope=$PRIMARY_STREAM_SCOPE regression_stream_scope=$REGRESSION_STREAM_SCOPE reuse_avd=true reuse_gradle_daemon=true"
for fixture in "${FIXTURES[@]}"; do
  echo "===== TV CORPUS FIXTURE: $fixture ====="
  STREAM_SCOPE="$REGRESSION_STREAM_SCOPE"
  if [[ "$fixture" = "$PRIMARY_FIXTURE" ]]; then STREAM_SCOPE="$PRIMARY_STREAM_SCOPE"; fi
  if [[ "$READER_ACCEPTANCE" = "1" ]]; then
    PROVIDER_SCOPE="$TARGET_PROVIDER"
    if [[ -z "$PROVIDER_SCOPE" || "$PROVIDER_SCOPE" = "fixture" ]]; then PROVIDER_SCOPE="$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE"; fi
    if [[ -z "$PROVIDER_SCOPE" ]]; then PROVIDER_SCOPE="fixture"; fi
    python3 "$ACCEPTANCE_PREPARE" tv --fixture "$fixture" --workspace "$WORKSPACE" --provider "$PROVIDER_SCOPE" --streams "$STREAM_SCOPE" --manifest "$TARGET_MANIFEST" || { STATUS=1; continue; }
  else
    python3 "$RESTAGE" tv --fixture "$fixture" --workspace "$WORKSPACE" "${PROVIDER_ARGS[@]}" --player-probes "$PLAYER_PROBES" --manifest "$TARGET_MANIFEST" || { STATUS=1; continue; }
  fi
  adb logcat -c || true
  RUNTIME_STATUS=0
  "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --console=plain || RUNTIME_STATUS=$?
  LOG="${WORKSPACE}/tv-native-corpus-${fixture}.log"
  adb logcat -d -s NiakvioCorpus:I '*:S' > "$LOG" || true
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
  echo "FIELD_NATIVE_CORPUS_TV_STATUS fixture=$fixture runtime=$RUNTIME_STATUS collection=$ANALYSIS_STATUS coverage=$COVERAGE_STATUS reader=$READER_STATUS stream_scope=$STREAM_SCOPE"
  if [[ "$RUNTIME_STATUS" -ne 0 || "$ANALYSIS_STATUS" -ne 0 || "$COVERAGE_STATUS" -ne 0 || "$READER_STATUS" -ne 0 ]]; then STATUS=1; fi
done

echo "FIELD_NATIVE_CORPUS_TV_SUITE_STATUS status=$STATUS fixtures=${#FIXTURES[@]} clients=1 provider=${TARGET_PROVIDER:-all} configured_acceptance_provider_scope=$CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE manifest=$TARGET_MANIFEST require_reader_success=$REQUIRE_READER_SUCCESS reader_acceptance=$READER_ACCEPTANCE"
exit "$STATUS"

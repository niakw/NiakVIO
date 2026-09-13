#!/usr/bin/env bash
set -u

FIXTURE="${1:?fixture required}"
PROVIDER_FILE="${2:?provider file required}"
STREAM_SCOPE="${3:-2}"
WORKSPACE="${GITHUB_WORKSPACE:?}"
NIAKVIO="${WORKSPACE}/niakvio"
TV_ROOT="${WORKSPACE}/nuvio-tv"
TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-native-hub46/manifest.json}"
TEST_SOURCE="${TV_ROOT}/app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
REQUEST_CONTRACT="${NIAKVIO}/scripts/augment_native_corpus_request_contract.py"
PROVIDER_LOADING="${NIAKVIO}/scripts/augment_native_provider_loading_compat.py"
TV_HILT_FINALIZER="${NIAKVIO}/scripts/finalize_native_tv_test_entrypoint.py"
FRONTEND_CAPTURE="${NIAKVIO}/scripts/capture_native_device_frontend.sh"
FRONTEND_WATCHER="${NIAKVIO}/scripts/watch_native_device_frontend.sh"
MANIFEST_URL="${NIAKVIO_RESOLVED_MANIFEST_URL:?resolved manifest URL required}"
ALLOW_LOCAL_MANIFEST="${NIAKVIO_RESOLVED_ALLOW_LOCAL:-0}"
ROUTE_TIMEOUT_MINUTES="${NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES:-45}"
PROVIDER_LOADING_URL_ARGS=()
if [[ "$ALLOW_LOCAL_MANIFEST" = "1" ]]; then PROVIDER_LOADING_URL_ARGS+=(--allow-local-lab-url); fi

python3 "$RESTAGE" tv --fixture "$FIXTURE" --workspace "$WORKSPACE" --provider-file "$PROVIDER_FILE" --player-probes 1 --manifest "$TARGET_MANIFEST" || exit $?
python3 "$REQUEST_CONTRACT" tv --fixture "$FIXTURE" --manifest "$TARGET_MANIFEST" --source "$TEST_SOURCE" || exit $?
python3 "$PROVIDER_LOADING" tv --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" "${PROVIDER_LOADING_URL_ARGS[@]}" || exit $?
python3 "$TV_HILT_FINALIZER" "$TEST_SOURCE" || exit $?

EVIDENCE_ROOT="${WORKSPACE}/native-evidence/tv"
FRONT_DIR="${EVIDENCE_ROOT}/${FIXTURE}"
FRONT_LOG="${WORKSPACE}/tv-native-frontend-${FIXTURE}.log"
GRADLE_LOG="${FRONT_DIR}/gradle.log"
LOG="${WORKSPACE}/tv-native-corpus-${FIXTURE}.log"
mkdir -p "$FRONT_DIR"
rm -f "$FRONT_LOG" "$GRADLE_LOG" "$LOG"
adb logcat -c || true
adb logcat -v brief NiakvioCorpus:V NiakvioEvidence:V PluginRuntime:V Plugin:V '*:S' > >(tee "$LOG") 2>&1 &
LOGCAT_PID=$!
bash "$FRONTEND_WATCHER" tv "$FRONT_DIR" "$FRONTEND_CAPTURE" > >(tee "$FRONT_LOG") 2>&1 &
WATCH_PID=$!
RUNTIME_STATUS=0
timeout --signal=TERM --kill-after=2m "${ROUTE_TIMEOUT_MINUTES}m" "$TV_ROOT/gradlew" -p "$TV_ROOT" :app:connectedFullDebugAndroidTest --console=plain --max-workers=1 2>&1 | tee "$GRADLE_LOG"
RUNTIME_STATUS=${PIPESTATUS[0]}
sleep 1
kill "$WATCH_PID" 2>/dev/null || true
wait "$WATCH_PID" 2>/dev/null || true
kill "$LOGCAT_PID" 2>/dev/null || true
wait "$LOGCAT_PID" 2>/dev/null || true
echo "FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=tv adaptive_fallback=true" | tee -a "$LOG"
cat "$FRONT_LOG" >> "$LOG" 2>/dev/null || true
echo "FIELD_NATIVE_ADAPTIVE_FALLBACK client=tv fixture=$FIXTURE providers=$(grep -cve '^$' "$PROVIDER_FILE" || true) runtime=$RUNTIME_STATUS" | tee -a "$LOG"
exit "$RUNTIME_STATUS"

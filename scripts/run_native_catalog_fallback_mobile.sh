#!/usr/bin/env bash
set -u

FIXTURE="${1:?fixture required}"
PROVIDER_FILE="${2:?provider file required}"
STREAM_SCOPE="${3:-all}"
WORKSPACE="${GITHUB_WORKSPACE:?}"
NIAKVIO="${WORKSPACE}/niakvio"
MOBILE_ROOT="${WORKSPACE}/nuvio-mobile"
TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-native-hub46/manifest.json}"
MOBILE_TASK="${NIAKVIO_MOBILE_TASK:?NIAKVIO_MOBILE_TASK required}"
TEST_SOURCE="${MOBILE_ROOT}/composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
REQUEST_CONTRACT="${NIAKVIO}/scripts/augment_native_corpus_request_contract.py"
PROVIDER_LOADING="${NIAKVIO}/scripts/augment_native_provider_loading_compat.py"
FRONTEND_CAPTURE="${NIAKVIO}/scripts/capture_native_device_frontend.sh"
FRONTEND_WATCHER="${NIAKVIO}/scripts/watch_native_device_frontend.sh"
MANIFEST_URL="${NIAKVIO_RESOLVED_MANIFEST_URL:?resolved manifest URL required}"
ALLOW_LOCAL_MANIFEST="${NIAKVIO_RESOLVED_ALLOW_LOCAL:-0}"
PROVIDER_LOADING_URL_ARGS=()
if [[ "$ALLOW_LOCAL_MANIFEST" = "1" ]]; then PROVIDER_LOADING_URL_ARGS+=(--allow-local-lab-url); fi

python3 "$RESTAGE" mobile --fixture "$FIXTURE" --workspace "$WORKSPACE" --provider-file "$PROVIDER_FILE" --player-probes 1 --manifest "$TARGET_MANIFEST" || exit $?
python3 "$REQUEST_CONTRACT" mobile --fixture "$FIXTURE" --manifest "$TARGET_MANIFEST" --source "$TEST_SOURCE" || exit $?
python3 "$PROVIDER_LOADING" mobile --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" "${PROVIDER_LOADING_URL_ARGS[@]}" || exit $?

EVIDENCE_ROOT="${WORKSPACE}/native-evidence/mobile"
FRONT_DIR="${EVIDENCE_ROOT}/${FIXTURE}"
FRONT_LOG="${WORKSPACE}/mobile-native-frontend-${FIXTURE}.log"
LOG="${WORKSPACE}/mobile-native-corpus-${FIXTURE}.log"
mkdir -p "$FRONT_DIR"
rm -f "$FRONT_LOG" "$LOG"
adb logcat -c || true
adb logcat -v brief -s NiakvioCorpus:I NiakvioEvidence:I '*:S' > >(tee "$LOG") 2>&1 &
LOGCAT_PID=$!
bash "$FRONTEND_WATCHER" mobile "$FRONT_DIR" "$FRONTEND_CAPTURE" > >(tee "$FRONT_LOG") 2>&1 &
WATCH_PID=$!
RUNTIME_STATUS=0
"$MOBILE_ROOT/gradlew" -p "$MOBILE_ROOT" ":composeApp:$MOBILE_TASK" -Pnuvio.android.distribution=full --console=plain || RUNTIME_STATUS=$?
sleep 1
kill "$WATCH_PID" 2>/dev/null || true
wait "$WATCH_PID" 2>/dev/null || true
kill "$LOGCAT_PID" 2>/dev/null || true
wait "$LOGCAT_PID" 2>/dev/null || true
echo "FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=mobile adaptive_fallback=true" | tee -a "$LOG"
cat "$FRONT_LOG" >> "$LOG" 2>/dev/null || true
echo "FIELD_NATIVE_ADAPTIVE_FALLBACK client=mobile fixture=$FIXTURE providers=$(grep -cve '^$' "$PROVIDER_FILE" || true) runtime=$RUNTIME_STATUS" | tee -a "$LOG"
exit "$RUNTIME_STATUS"

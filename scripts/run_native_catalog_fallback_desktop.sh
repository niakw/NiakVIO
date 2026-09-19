#!/usr/bin/env bash
set -u

FIXTURE="${1:?fixture required}"
PROVIDER_FILE="${2:?provider file required}"
STREAM_SCOPE="${3:-all}"
WORKSPACE="${GITHUB_WORKSPACE:?}"
NIAKVIO="${WORKSPACE}/niakvio"
DESKTOP_ROOT="${WORKSPACE}/nuvio-desktop"
TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-native-hub46/manifest.json}"
TEST_SOURCE="${DESKTOP_ROOT}/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
RESTAGE="${NIAKVIO}/scripts/restage_native_corpus_client.py"
REQUEST_CONTRACT="${NIAKVIO}/scripts/augment_native_corpus_request_contract.py"
PROVIDER_LOADING="${NIAKVIO}/scripts/augment_native_provider_loading_compat.py"
RUNTIME_DIAGNOSTICS="${NIAKVIO}/scripts/augment_native_desktop_runtime_diagnostics.py"
PLAYER_AUGMENT="${NIAKVIO}/scripts/augment_native_desktop_player.py"
FRONTEND_PHASES="${NIAKVIO}/scripts/complete_native_desktop_frontend_phases.py"
DESKTOP_TEST_JVM_INIT="${NIAKVIO}/scripts/nuvio_desktop_test_jvm.init.gradle"
MANIFEST_URL="${NIAKVIO_RESOLVED_MANIFEST_URL:?resolved manifest URL required}"
ALLOW_LOCAL_MANIFEST="${NIAKVIO_RESOLVED_ALLOW_LOCAL:-0}"

case "$(uname -s)" in
  Darwin) HOST_OS="macos" ;;
  MINGW*|MSYS*|CYGWIN*) HOST_OS="windows" ;;
  *) exit 96 ;;
esac

python3 "$RESTAGE" desktop --fixture "$FIXTURE" --workspace "$WORKSPACE" --provider-file "$PROVIDER_FILE" --manifest "$TARGET_MANIFEST" || exit $?
python3 "$REQUEST_CONTRACT" desktop --fixture "$FIXTURE" --manifest "$TARGET_MANIFEST" --source "$TEST_SOURCE" || exit $?
if [[ "$ALLOW_LOCAL_MANIFEST" = "1" ]]; then
  python3 "$PROVIDER_LOADING" desktop --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" --platform "$HOST_OS" --allow-local-lab-url || exit $?
else
  python3 "$PROVIDER_LOADING" desktop --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" --platform "$HOST_OS" || exit $?
fi
python3 "$RUNTIME_DIAGNOSTICS" --source "$TEST_SOURCE" || exit $?
EXPECTED_MINUTES="$(PYTHONPATH="${NIAKVIO}/scripts" python3 - "$FIXTURE" <<'PY'
import sys
from rotating_corpus import fixture_by_slug
print(int(fixture_by_slug(sys.argv[1]).get('expectedDurationMinutes') or 0))
PY
)" || exit $?
python3 "$PLAYER_AUGMENT" --source "$TEST_SOURCE" --expected-minutes "$EXPECTED_MINUTES" --streams "$STREAM_SCOPE" || exit $?
python3 "$FRONTEND_PHASES" "$TEST_SOURCE" || exit $?

BASE_LOG="${WORKSPACE}/desktop-native-corpus-${FIXTURE}.log"
LOG="${WORKSPACE}/desktop-native-corpus-${HOST_OS}-${FIXTURE}.log"
GRADLE_LOG="${WORKSPACE}/desktop-native-gradle-${HOST_OS}-${FIXTURE}.log"
HTTP_LOG="${WORKSPACE}/desktop-native-http-evidence.log"
rm -f "$BASE_LOG" "$LOG" "$GRADLE_LOG" "$HTTP_LOG"
RUNTIME_STATUS=0
if [[ "$HOST_OS" = "windows" ]]; then
  "$DESKTOP_ROOT/gradlew.bat" -p "$DESKTOP_ROOT" --init-script "$DESKTOP_TEST_JVM_INIT" :composeApp:desktopTest --tests 'com.nuvio.app.features.plugins.NiakvioNativeCorpusDesktopTest' --no-build-cache --no-configuration-cache --console=plain 2>&1 | tee "$GRADLE_LOG"
  RUNTIME_STATUS=${PIPESTATUS[0]}
else
  "$DESKTOP_ROOT/gradlew" -p "$DESKTOP_ROOT" --init-script "$DESKTOP_TEST_JVM_INIT" :composeApp:desktopTest --tests 'com.nuvio.app.features.plugins.NiakvioNativeCorpusDesktopTest' --no-build-cache --no-configuration-cache --console=plain 2>&1 | tee "$GRADLE_LOG"
  RUNTIME_STATUS=${PIPESTATUS[0]}
fi
if [[ -s "$BASE_LOG" ]]; then cp "$BASE_LOG" "$LOG"; else : > "$LOG"; fi
if [[ -s "$HTTP_LOG" ]]; then cat "$HTTP_LOG" >> "$LOG"; fi
rm -f "$HTTP_LOG"
echo "FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=desktop adaptive_fallback=true" >> "$LOG"
echo "FIELD_NATIVE_ADAPTIVE_FALLBACK client=desktop fixture=$FIXTURE providers=$(grep -cve '^$' "$PROVIDER_FILE" || true) runtime=$RUNTIME_STATUS" | tee -a "$LOG"
exit "$RUNTIME_STATUS"

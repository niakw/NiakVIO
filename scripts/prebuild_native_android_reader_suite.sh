#!/usr/bin/env bash
# Precompile the first real native-reader route before QEMU starts. Hosted runners
# otherwise make Gradle packaging and a 2 GiB emulator fight for the same memory.
set -euo pipefail

CLIENT="${1:-}"
WORKSPACE="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"
NIAKVIO="${WORKSPACE}/niakvio"
FIXTURE="${NIAKVIO_PRIMARY_FIXTURE:-sinners-2025}"
TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"
TARGET_PROVIDER="${NIAKVIO_TARGET_PROVIDER:-all}"
STREAM_SCOPE="${NIAKVIO_PRIMARY_STREAM_SCOPE:-all}"
SOURCE_SHA="${NIAKVIO_SOURCE_SHA:-$(git -C "$NIAKVIO" rev-parse HEAD)}"
SOURCE_REPOSITORY="${GITHUB_REPOSITORY:-niakw/NiakVIO}"
export SOURCE_SHA SOURCE_REPOSITORY
REPOSITORY_RESOLVER="${NIAKVIO}/scripts/resolve_native_repository.sh"
LAB_TRANSPORT="${NIAKVIO}/scripts/configure_native_android_lab_transport.py"
INSTRUMENTER="${NIAKVIO}/scripts/instrument_native_client_evidence.py"
REPOSITORY_HTTP_INSTRUMENTER="${NIAKVIO}/scripts/instrument_native_repository_http_evidence.py"
REQUEST_CONTRACT="${NIAKVIO}/scripts/augment_native_corpus_request_contract.py"
PROVIDER_LOADING="${NIAKVIO}/scripts/augment_native_provider_loading.py"
ACCEPTANCE_PREPARE="${NIAKVIO}/scripts/prepare_native_reader_acceptance.py"
MOBILE_HARDEN="${NIAKVIO}/scripts/harden_nuvio_mobile_device_test.py"

case "$CLIENT" in
  tv)
    ROOT="${WORKSPACE}/nuvio-tv"
    TEST_SOURCE="${ROOT}/app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
    TEST_MANIFEST="${ROOT}/app/src/androidTest/AndroidManifest.xml"
    PORT=18765
    ;;
  mobile)
    ROOT="${WORKSPACE}/nuvio-mobile"
    TEST_SOURCE="${ROOT}/composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
    TEST_MANIFEST="${ROOT}/composeApp/src/androidDeviceTest/AndroidManifest.xml"
    PORT=18766
    ;;
  *) echo "usage: $0 tv|mobile" >&2; exit 64 ;;
esac

source "$REPOSITORY_RESOLVER"
resolve_native_repository "$CLIENT" 10.0.2.2 "$PORT"
trap cleanup_native_repository EXIT
MANIFEST_URL="$NIAKVIO_RESOLVED_MANIFEST_URL"
URL_ARGS=()
if [[ "$NIAKVIO_RESOLVED_ALLOW_LOCAL" = "1" ]]; then URL_ARGS+=(--allow-local-lab-url); fi

# Mobile hardening changes only test packaging/Sentry startup. Apply it before the
# prebuild so QEMU never has to invalidate and rebuild the device-test APK later.
if [[ "$CLIENT" = "mobile" ]]; then
  python3 "$MOBILE_HARDEN" "$ROOT"
fi
python3 "$LAB_TRANSPORT" "$TEST_MANIFEST"
python3 "$INSTRUMENTER" "$CLIENT" "$ROOT"
python3 "$REPOSITORY_HTTP_INSTRUMENTER" "$CLIENT" "$ROOT"
python3 "$ACCEPTANCE_PREPARE" "$CLIENT" --fixture "$FIXTURE" --workspace "$WORKSPACE" --provider "$TARGET_PROVIDER" --streams "$STREAM_SCOPE" --manifest "$TARGET_MANIFEST"
python3 "$REQUEST_CONTRACT" "$CLIENT" --fixture "$FIXTURE" --manifest "$TARGET_MANIFEST" --source "$TEST_SOURCE"
python3 "$PROVIDER_LOADING" "$CLIENT" --manifest "$TARGET_MANIFEST" --manifest-url "$MANIFEST_URL" --source "$TEST_SOURCE" "${URL_ARGS[@]}"

if [[ "$CLIENT" = "tv" ]]; then
  "$ROOT/gradlew" -p "$ROOT" :app:assembleFullDebug :app:assembleFullDebugAndroidTest --console=plain
else
  "$ROOT/gradlew" -p "$ROOT" :androidApp:assembleFullDebug :composeApp:packageAndroidDeviceTest -Pnuvio.android.distribution=full --console=plain
fi

echo "FIELD_NATIVE_ANDROID_PREBUILD client=$CLIENT fixture=$FIXTURE manifest=$TARGET_MANIFEST provider=$TARGET_PROVIDER streams=$STREAM_SCOPE source_sha=$SOURCE_SHA status=ready"

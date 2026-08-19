#!/usr/bin/env bash
set -euo pipefail

CLIENT="${1:?client required}"
OUT_DIR="${2:?output directory required}"
CAPTURE="${3:?capture script required}"
mkdir -p "$OUT_DIR"

declare -A SEEN=()

capture_once() {
  local phase="$1"
  if [[ -n "${SEEN[$phase]:-}" ]]; then return 0; fi
  SEEN[$phase]=1
  "$CAPTURE" "$CLIENT" "$phase" "$OUT_DIR" || {
    echo "FIELD_NATIVE_FRONTEND_ERROR client=$CLIENT phase=$phase reason=capture_failed"
    return 0
  }
}

# The watcher is deliberately phase-based, not provider-count based. Backend logs
# retain every provider/request/reader event; screenshots prove the visible client
# state at each human stage without generating hundreds of redundant framebuffers.
adb logcat -v brief -s NiakvioCorpus:I NiakvioEvidence:I PluginRuntime:I PluginManager:D PluginRepository:D '*:S' | while IFS= read -r line; do
  case "$line" in
    *FIELD_NATIVE_UI_LAUNCHED*) capture_once "ui-launched" ;;
    *FIELD_NATIVE_REPOSITORY_LOAD_BEGIN*) capture_once "repository-load" ;;
    *FIELD_NATIVE_REPOSITORY_LOAD_RESULT*) capture_once "repository-loaded" ;;
    *FIELD_NATIVE_REPOSITORY_LOAD_ERROR*) capture_once "repository-load-error" ;;
    *FIELD_NATIVE_PROVIDER_LOAD_RESULT*|*FIELD_NATIVE_PROVIDER_LOAD_ERROR*|*FIELD_NATIVE_PROVIDER_LOAD_SKIPPED*) capture_once "provider-load-state" ;;
    *FIELD_NATIVE_CORPUS_BEGIN*) capture_once "corpus-begin" ;;
    *FIELD_NATIVE_PROVIDER_BEGIN*) capture_once "provider-loading" ;;
    *FIELD_NATIVE_HTTP_REQUEST*) capture_once "provider-http-request" ;;
    *FIELD_NATIVE_HTTP_RESPONSE*|*FIELD_NATIVE_HTTP_ERROR*) capture_once "provider-http-response" ;;
    *FIELD_NATIVE_RESULT*) capture_once "provider-result" ;;
    *FIELD_NATIVE_PLAYER_BEGIN*) capture_once "player-start" ;;
    *FIELD_NATIVE_PLAYER*) capture_once "player-result" ;;
    *FIELD_NATIVE_ERROR*) capture_once "provider-error" ;;
    *FIELD_NATIVE_CORPUS_END*) capture_once "corpus-end" ;;
  esac
done

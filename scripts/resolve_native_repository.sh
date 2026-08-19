#!/usr/bin/env bash
# Source this file from a native client suite after WORKSPACE, NIAKVIO,
# TARGET_MANIFEST, SOURCE_SHA and SOURCE_REPOSITORY are defined.

NIAKVIO_RESOLVED_MANIFEST_URL=""
NIAKVIO_RESOLVED_ALLOW_LOCAL="0"
NIAKVIO_LOCAL_REPOSITORY_PID=""
NIAKVIO_LOCAL_REPOSITORY_LOG=""

resolve_native_repository() {
  local client="${1:?client required}"
  local device_host="${2:?device-visible host required}"
  local port="${3:?port required}"

  if [[ -n "${NIAKVIO_MANIFEST_URL:-}" ]]; then
    NIAKVIO_RESOLVED_MANIFEST_URL="$NIAKVIO_MANIFEST_URL"
    NIAKVIO_RESOLVED_ALLOW_LOCAL="${NIAKVIO_ALLOW_LOCAL_MANIFEST:-0}"
    echo "FIELD_NATIVE_REPOSITORY_SOURCE client=$client mode=explicit local=$NIAKVIO_RESOLVED_ALLOW_LOCAL"
    return 0
  fi

  # raw.githubusercontent.com resolves repository-relative provider filenames only
  # when the manifest itself is at the repository root. It must also be a tracked,
  # unchanged file from the exact SOURCE_SHA under test.
  local pinned=false
  if [[ "$TARGET_MANIFEST" != */* ]] \
    && git -C "$NIAKVIO" ls-files --error-unmatch "$TARGET_MANIFEST" >/dev/null 2>&1 \
    && git -C "$NIAKVIO" cat-file -e "$SOURCE_SHA:$TARGET_MANIFEST" 2>/dev/null \
    && git -C "$NIAKVIO" diff --quiet "$SOURCE_SHA" -- "$TARGET_MANIFEST"; then
    pinned=true
  fi

  if [[ "$pinned" == true ]]; then
    NIAKVIO_RESOLVED_MANIFEST_URL="https://raw.githubusercontent.com/${SOURCE_REPOSITORY}/${SOURCE_SHA}/${TARGET_MANIFEST}"
    NIAKVIO_RESOLVED_ALLOW_LOCAL="0"
    echo "FIELD_NATIVE_REPOSITORY_SOURCE client=$client mode=pinned_github local=0"
    return 0
  fi

  # Generated, modified, or nested manifests are materialized as a root repository
  # and served only on the runner's loopback bridge. Android emulators reach the
  # host at 10.0.2.2; Desktop uses 127.0.0.1.
  local serve_root="${WORKSPACE}/native-candidate-repository-${client}"
  local server_log="${WORKSPACE}/native-candidate-repository-${client}.server.log"
  python3 "$NIAKVIO/scripts/prepare_native_candidate_repository.py" \
    --manifest "$TARGET_MANIFEST" \
    --serve-root "$serve_root" || return $?

  rm -f "$server_log"
  python3 -m http.server "$port" --bind 0.0.0.0 --directory "$serve_root" >"$server_log" 2>&1 &
  NIAKVIO_LOCAL_REPOSITORY_PID=$!
  NIAKVIO_LOCAL_REPOSITORY_LOG="$server_log"

  local ready=0
  local attempt
  for attempt in $(seq 1 40); do
    if python3 - "$port" <<'PY' >/dev/null 2>&1
import sys, urllib.request
port = int(sys.argv[1])
with urllib.request.urlopen(f"http://127.0.0.1:{port}/manifest.json", timeout=1.0) as response:
    if response.status != 200:
        raise SystemExit(1)
    response.read(64)
PY
    then
      ready=1
      break
    fi
    sleep 0.2
  done
  if [[ "$ready" != "1" ]]; then
    echo "FIELD_NATIVE_REPOSITORY_SOURCE_ERROR client=$client reason=local_server_not_ready" >&2
    cat "$server_log" >&2 2>/dev/null || true
    kill "$NIAKVIO_LOCAL_REPOSITORY_PID" 2>/dev/null || true
    return 2
  fi

  NIAKVIO_RESOLVED_MANIFEST_URL="http://${device_host}:${port}/manifest.json"
  NIAKVIO_RESOLVED_ALLOW_LOCAL="1"
  echo "FIELD_NATIVE_REPOSITORY_SOURCE client=$client mode=local_candidate local=1 port=$port"
}

cleanup_native_repository() {
  if [[ -n "${NIAKVIO_LOCAL_REPOSITORY_PID:-}" ]]; then
    kill "$NIAKVIO_LOCAL_REPOSITORY_PID" 2>/dev/null || true
    wait "$NIAKVIO_LOCAL_REPOSITORY_PID" 2>/dev/null || true
    NIAKVIO_LOCAL_REPOSITORY_PID=""
  fi
  if [[ -n "${NIAKVIO_LOCAL_REPOSITORY_LOG:-}" ]]; then
    rm -f "$NIAKVIO_LOCAL_REPOSITORY_LOG"
  fi
}

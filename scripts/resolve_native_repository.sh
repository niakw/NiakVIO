#!/usr/bin/env bash
# Source this file from a native client suite after WORKSPACE, NIAKVIO,
# TARGET_MANIFEST, SOURCE_SHA and SOURCE_REPOSITORY are defined.

NIAKVIO_RESOLVED_MANIFEST_URL=""
NIAKVIO_RESOLVED_ALLOW_LOCAL="0"
NIAKVIO_LOCAL_REPOSITORY_PID=""
NIAKVIO_LOCAL_REPOSITORY_LOG=""
NIAKVIO_LOCAL_REPOSITORY_ROOT=""
NIAKVIO_LOCAL_REPOSITORY_KEY=""
NIAKVIO_LOCAL_REPOSITORY_PRIVILEGED_CLIENT="0"

probe_native_repository_loopback() {
  local port="${1:?port required}"
  local candidate_dir="${2:?candidate dir required}"
  local use_privileged_client="${3:-0}"
  local python_args=(python3 - "$port" "$candidate_dir")

  if [[ "$use_privileged_client" == "1" ]]; then
    sudo -n "${python_args[@]}" <<'PY'
import http.client
import sys

port = int(sys.argv[1])
candidate = sys.argv[2]
connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)
try:
    connection.request("GET", f"/{candidate}/manifest.json", headers={"Connection": "close"})
    response = connection.getresponse()
    if response.status != 200:
        raise SystemExit(1)
    response.read(64)
finally:
    connection.close()
PY
  else
    "${python_args[@]}" <<'PY'
import http.client
import sys

port = int(sys.argv[1])
candidate = sys.argv[2]
connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)
try:
    connection.request("GET", f"/{candidate}/manifest.json", headers={"Connection": "close"})
    response = connection.getresponse()
    if response.status != 200:
        raise SystemExit(1)
    response.read(64)
finally:
    connection.close()
PY
  fi
}

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
  # unchanged file from the exact SOURCE_SHA under test. The SHA in the URL makes
  # Nuvio's persistent repository/provider cache safe across CI runs.
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
    echo "FIELD_NATIVE_REPOSITORY_SOURCE client=$client mode=pinned_github local=0 cache_key=${SOURCE_SHA}"
    return 0
  fi

  # Generated, modified, or nested manifests are materialized as a root repository
  # and served only on the runner bridge. Android emulators must reach the host at
  # 10.0.2.2, so they bind all interfaces. Desktop only consumes 127.0.0.1 and is
  # deliberately bound to loopback; this avoids macOS Local Network Privacy treating
  # an otherwise local-only CI repository as a LAN listener.
  #
  # IMPORTANT: the URL path is content-addressed from manifest + every provider
  # byte. A persisted AVD/profile may therefore reuse the cache for the exact same
  # candidate, but can never silently reuse old JS after the candidate changes.
  local serve_root="${WORKSPACE}/native-candidate-repository-${client}"
  local prepared_root="${serve_root}.prepared"
  local server_log="${WORKSPACE}/native-candidate-repository-${client}.server.log"
  rm -rf "$prepared_root" "$serve_root"
  python3 "$NIAKVIO/scripts/prepare_native_candidate_repository.py" \
    --manifest "$TARGET_MANIFEST" \
    --serve-root "$prepared_root" || return $?

  local content_key
  content_key="$(python3 - "$prepared_root" <<'PY'
from pathlib import Path
import hashlib, sys
root = Path(sys.argv[1]).resolve()
h = hashlib.sha256()
files = sorted((p for p in root.rglob('*') if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
if not files:
    raise SystemExit('candidate repository contains no files')
for path in files:
    relative = path.relative_to(root).as_posix().encode('utf-8')
    payload = path.read_bytes()
    h.update(len(relative).to_bytes(4, 'big'))
    h.update(relative)
    h.update(len(payload).to_bytes(8, 'big'))
    h.update(payload)
print(h.hexdigest()[:32])
PY
)" || return $?
  if [[ ! "$content_key" =~ ^[0-9a-f]{32}$ ]]; then
    echo "FIELD_NATIVE_REPOSITORY_SOURCE_ERROR client=$client reason=invalid_content_key" >&2
    rm -rf "$prepared_root"
    return 2
  fi

  local candidate_dir="candidate-${content_key}"
  mkdir -p "$serve_root"
  mv "$prepared_root" "$serve_root/$candidate_dir"
  NIAKVIO_LOCAL_REPOSITORY_ROOT="$serve_root"
  NIAKVIO_LOCAL_REPOSITORY_KEY="$content_key"

  local bind_host="0.0.0.0"
  if [[ "$client" == "desktop" && ( "$device_host" == "127.0.0.1" || "$device_host" == "localhost" ) ]]; then
    bind_host="127.0.0.1"
  fi

  rm -f "$server_log"
  python3 -m http.server "$port" --bind "$bind_host" --directory "$serve_root" >"$server_log" 2>&1 &
  NIAKVIO_LOCAL_REPOSITORY_PID=$!
  NIAKVIO_LOCAL_REPOSITORY_LOG="$server_log"

  # Readiness always starts through the same unprivileged loopback path the client
  # should use. On macOS CI only, sudo is a bounded fallback after several ordinary
  # attempts; it is never required just because the runner happens to be macOS.
  local allow_privileged_probe=0
  if [[ "$client" == "desktop" && "$(uname -s)" == "Darwin" && "${CI:-}" == "true" ]]; then
    if sudo -n true >/dev/null 2>&1; then
      allow_privileged_probe=1
    fi
  fi

  local ready=0
  local attempt
  for attempt in $(seq 1 40); do
    if ! kill -0 "$NIAKVIO_LOCAL_REPOSITORY_PID" 2>/dev/null; then
      echo "FIELD_NATIVE_REPOSITORY_SOURCE_ERROR client=$client reason=local_server_exited cache_key=$content_key bind_host=$bind_host" >&2
      cat "$server_log" >&2 2>/dev/null || true
      rm -rf "$serve_root"
      NIAKVIO_LOCAL_REPOSITORY_PID=""
      return 2
    fi
    if probe_native_repository_loopback "$port" "$candidate_dir" 0 >/dev/null 2>&1; then
      ready=1
      break
    fi
    if [[ "$allow_privileged_probe" == "1" && "$attempt" -ge 5 ]] \
      && probe_native_repository_loopback "$port" "$candidate_dir" 1 >/dev/null 2>&1; then
      ready=1
      NIAKVIO_LOCAL_REPOSITORY_PRIVILEGED_CLIENT="1"
      break
    fi
    sleep 0.2
  done
  if [[ "$ready" != "1" ]]; then
    echo "FIELD_NATIVE_REPOSITORY_SOURCE_ERROR client=$client reason=local_server_not_ready cache_key=$content_key bind_host=$bind_host privileged_fallback=$allow_privileged_probe" >&2
    cat "$server_log" >&2 2>/dev/null || true
    kill "$NIAKVIO_LOCAL_REPOSITORY_PID" 2>/dev/null || true
    rm -rf "$serve_root"
    return 2
  fi

  NIAKVIO_RESOLVED_MANIFEST_URL="http://${device_host}:${port}/${candidate_dir}/manifest.json"
  NIAKVIO_RESOLVED_ALLOW_LOCAL="1"
  echo "FIELD_NATIVE_REPOSITORY_SOURCE client=$client mode=local_candidate local=1 port=$port bind_host=$bind_host cache_key=$content_key privileged_client=$NIAKVIO_LOCAL_REPOSITORY_PRIVILEGED_CLIENT"
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
  if [[ -n "${NIAKVIO_LOCAL_REPOSITORY_ROOT:-}" ]]; then
    rm -rf "$NIAKVIO_LOCAL_REPOSITORY_ROOT"
    NIAKVIO_LOCAL_REPOSITORY_ROOT=""
  fi
}

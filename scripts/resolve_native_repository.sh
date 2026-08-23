#!/usr/bin/env bash
# Source from a native client suite after WORKSPACE, NIAKVIO, TARGET_MANIFEST,
# SOURCE_SHA and SOURCE_REPOSITORY are defined.
#
# Human-UX invariant: repository staging may make the NiakVIO candidate reachable,
# but it must never grant the Nuvio process privileges or network capabilities that
# a normal user process does not have. No sudo/root, proxy, DNS, TLS or OS-policy
# bypass belongs here. If ordinary process access cannot reach the staged candidate,
# the evidence is infrastructure-invalid and the suite must fail closed.

NIAKVIO_RESOLVED_MANIFEST_URL=""
NIAKVIO_RESOLVED_ALLOW_LOCAL="0"
NIAKVIO_LOCAL_REPOSITORY_PID=""
NIAKVIO_LOCAL_REPOSITORY_LOG=""
NIAKVIO_LOCAL_REPOSITORY_ROOT=""
NIAKVIO_LOCAL_REPOSITORY_KEY=""

probe_native_repository_loopback() {
  local port="${1:?port required}"
  local candidate_dir="${2:?candidate dir required}"
  python3 - "$port" "$candidate_dir" <<'PY'
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
}

resolve_native_repository() {
  local client="${1:?client required}"
  local device_host="${2:?device-visible host required}"
  local port="${3:?port required}"

  if [[ -n "${NIAKVIO_MANIFEST_URL:-}" ]]; then
    NIAKVIO_RESOLVED_MANIFEST_URL="$NIAKVIO_MANIFEST_URL"
    NIAKVIO_RESOLVED_ALLOW_LOCAL="${NIAKVIO_ALLOW_LOCAL_MANIFEST:-0}"
    echo "FIELD_NATIVE_REPOSITORY_SOURCE client=$client mode=explicit local=$NIAKVIO_RESOLVED_ALLOW_LOCAL observational=true"
    return 0
  fi

  # Prefer the exact SHA-pinned public repository whenever the selected manifest is
  # a tracked unchanged root file. This is closest to what a real Nuvio user loads.
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
    echo "FIELD_NATIVE_REPOSITORY_SOURCE client=$client mode=pinned_github local=0 cache_key=${SOURCE_SHA} observational=true"
    return 0
  fi

  # Android production clients intentionally reject cleartext HTTP. Never convert a
  # dirty/unpinned acceptance checkout into a 10.0.2.2 lab transport behind their
  # back: that both invalidates the production-path evidence and deterministically
  # fails NuvioMobile's network security policy. A caller that truly needs a custom
  # candidate must provide an explicit reachable NIAKVIO_MANIFEST_URL; normal
  # acceptance must remain SHA-pinned HTTPS.
  if [[ "$client" == "mobile" || "$client" == "tv" ]]; then
    echo "FIELD_NATIVE_REPOSITORY_SOURCE_ERROR client=$client reason=unpinned_android_repository_requires_explicit_https target_manifest=$TARGET_MANIFEST source_sha=$SOURCE_SHA" >&2
    return 2
  fi

  # Generated/modified Desktop manifests must still resolve repository-relative
  # provider filenames. Materialize manifest + every provider into a content-addressed
  # loopback repository. Desktop runs on the same host, so ordinary loopback HTTP is
  # an observational transport rather than an Android network-policy bypass.
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
import hashlib
import sys

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
    if probe_native_repository_loopback "$port" "$candidate_dir" >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 0.2
  done
  if [[ "$ready" != "1" ]]; then
    echo "FIELD_NATIVE_REPOSITORY_SOURCE_ERROR client=$client reason=local_server_not_ready_unprivileged cache_key=$content_key bind_host=$bind_host" >&2
    cat "$server_log" >&2 2>/dev/null || true
    kill "$NIAKVIO_LOCAL_REPOSITORY_PID" 2>/dev/null || true
    rm -rf "$serve_root"
    NIAKVIO_LOCAL_REPOSITORY_PID=""
    return 2
  fi

  NIAKVIO_RESOLVED_MANIFEST_URL="http://${device_host}:${port}/${candidate_dir}/manifest.json"
  NIAKVIO_RESOLVED_ALLOW_LOCAL="1"
  echo "FIELD_NATIVE_REPOSITORY_SOURCE client=$client mode=local_candidate local=1 port=$port bind_host=$bind_host cache_key=$content_key observational=true privileged=false"
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

#!/usr/bin/env bash
# Adaptive native-Lab catalogue fallback: one title at a time, same lane only.
# Called after the three initial global fixtures have run in one client session.
set -u

CLIENT="${1:?client required}"
shift
SEEDS=("$@")
WORKSPACE="${GITHUB_WORKSPACE:?}"
NIAKVIO="${WORKSPACE}/niakvio"
PLANNER="${NIAKVIO}/scripts/native_catalog_miss_rotation.py"
STREAM_SCOPE="${NIAKVIO_ADAPTIVE_STREAM_SCOPE:-1}"
SEED="${NIAKVIO_CORPUS_SEED:-${GITHUB_RUN_ID:-0}}"
STATE_ROOT="${WORKSPACE}/native-evidence/${CLIENT}/adaptive-catalog"
mkdir -p "$STATE_ROOT"

case "$CLIENT" in
  desktop)
    case "$(uname -s)" in
      Darwin) HOST_OS=macos ;;
      MINGW*|MSYS*|CYGWIN*) HOST_OS=windows ;;
      *) echo "unsupported desktop host for adaptive fallback" >&2; exit 96 ;;
    esac
    FALLBACK="${NIAKVIO}/scripts/run_native_catalog_fallback_desktop.sh"
    log_for() { printf '%s/desktop-native-corpus-%s-%s.log' "$WORKSPACE" "$HOST_OS" "$1"; }
    ;;
  mobile)
    FALLBACK="${NIAKVIO}/scripts/run_native_catalog_fallback_mobile.sh"
    log_for() { printf '%s/mobile-native-corpus-%s.log' "$WORKSPACE" "$1"; }
    ;;
  tv)
    FALLBACK="${NIAKVIO}/scripts/run_native_catalog_fallback_tv.sh"
    log_for() { printf '%s/tv-native-corpus-%s.log' "$WORKSPACE" "$1"; }
    ;;
  *) echo "unsupported client: $CLIENT" >&2; exit 2 ;;
esac

is_global_seed() {
  local fixture="$1"
  python3 - "$fixture" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('niakvio/scripts').resolve()))
from rotating_corpus import canonical_lane, fixture_by_slug, fixtures_by_lane
slug=sys.argv[1]
row=fixture_by_slug(slug)
lane=canonical_lane(row)
raise SystemExit(0 if any(item['slug']==slug for item in fixtures_by_lane(lane)) else 1)
PY
}

TOTAL_ROTATIONS=0
for seed_fixture in "${SEEDS[@]}"; do
  [[ -n "$seed_fixture" ]] || continue
  if ! is_global_seed "$seed_fixture"; then
    echo "FIELD_NATIVE_ADAPTIVE_CATALOG_SKIP client=$CLIENT fixture=$seed_fixture reason=not_global_recent_pool"
    continue
  fi
  current="$seed_fixture"
  USED=("$seed_fixture")
  attempt=0
  while true; do
    current_log="$(log_for "$current")"
    if [[ ! -s "$current_log" ]]; then
      echo "FIELD_NATIVE_ADAPTIVE_CATALOG_STOP client=$CLIENT fixture=$current reason=missing_log"
      break
    fi
    providers_file="${STATE_ROOT}/${seed_fixture}-attempt-${attempt}-providers.txt"
    next_file="${STATE_ROOT}/${seed_fixture}-attempt-${attempt}-next.txt"
    json_file="${STATE_ROOT}/${seed_fixture}-attempt-${attempt}.json"
    used_args=()
    for used in "${USED[@]}"; do used_args+=(--used "$used"); done
    python3 "$PLANNER" \
      --fixture "$current" \
      --log "$current_log" \
      --seed "$SEED" \
      "${used_args[@]}" \
      --providers-out "$providers_file" \
      --fixture-out "$next_file" \
      --json-out "$json_file" || exit $?
    clean_count="$(grep -cve '^$' "$providers_file" 2>/dev/null || true)"
    next_fixture="$(tr -d '\r\n' < "$next_file" 2>/dev/null || true)"
    if [[ "$clean_count" -eq 0 ]]; then
      echo "FIELD_NATIVE_ADAPTIVE_CATALOG_STOP client=$CLIENT seed=$seed_fixture fixture=$current reason=no_clean_miss rotations=$attempt"
      break
    fi
    if [[ -z "$next_fixture" ]]; then
      echo "FIELD_NATIVE_ADAPTIVE_CATALOG_EXHAUSTED client=$CLIENT seed=$seed_fixture fixture=$current providers=$clean_count rotations=$attempt"
      break
    fi
    echo "FIELD_NATIVE_ADAPTIVE_CATALOG_ROTATE client=$CLIENT seed=$seed_fixture from=$current to=$next_fixture providers=$clean_count attempt=$((attempt+1))"
    NIAKVIO_TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-native-hub46/manifest.json}" \
    NIAKVIO_RESOLVED_MANIFEST_URL="${NIAKVIO_RESOLVED_MANIFEST_URL:-}" \
    NIAKVIO_RESOLVED_ALLOW_LOCAL="${NIAKVIO_RESOLVED_ALLOW_LOCAL:-0}" \
    NIAKVIO_MOBILE_TASK="${NIAKVIO_MOBILE_TASK:-}" \
    NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES="${NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES:-45}" \
      bash "$FALLBACK" "$next_fixture" "$providers_file" "$STREAM_SCOPE" || true
    USED+=("$next_fixture")
    current="$next_fixture"
    attempt=$((attempt + 1))
    TOTAL_ROTATIONS=$((TOTAL_ROTATIONS + 1))
  done
done

echo "FIELD_NATIVE_ADAPTIVE_CATALOG_DONE client=$CLIENT seeds=${#SEEDS[@]} rotations=$TOTAL_ROTATIONS fixed_batch=false rule=clean_zero_only"

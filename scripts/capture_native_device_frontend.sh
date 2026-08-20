#!/usr/bin/env bash
set -euo pipefail

CLIENT="${1:?client required}"
PHASE="${2:?phase required}"
OUT_DIR="${3:?output directory required}"
mkdir -p "$OUT_DIR"

safe_phase="$(printf '%s' "$PHASE" | tr -cs 'A-Za-z0-9._-' '_' | cut -c1-120)"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
prefix="$OUT_DIR/${CLIENT}-${stamp}-${safe_phase}"

# The framebuffer is the canonical front-end proof. Keep this synchronous path
# intentionally tiny: uiautomator/dumpsys waits used to block logcat consumption,
# build a multi-minute backlog, and assign otherwise genuine screenshots to the
# wrong corpus fixture. The structured runtime markers already carry the exact
# backend phase; the screenshot proves what the official client displayed then.
adb exec-out screencap -p > "${prefix}.png"
if [[ ! -s "${prefix}.png" ]]; then
  echo "FIELD_NATIVE_FRONTEND_ERROR client=$CLIENT phase=$safe_phase reason=empty_screenshot" >&2
  exit 2
fi

bytes="$(wc -c < "${prefix}.png" | tr -d ' ')"
echo "FIELD_NATIVE_FRONTEND_CAPTURE client=$CLIENT phase=$safe_phase screenshot=$(basename "${prefix}.png") bytes=$bytes"

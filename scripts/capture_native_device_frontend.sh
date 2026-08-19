#!/usr/bin/env bash
set -euo pipefail

CLIENT="${1:?client required}"
PHASE="${2:?phase required}"
OUT_DIR="${3:?output directory required}"
mkdir -p "$OUT_DIR"

safe_phase="$(printf '%s' "$PHASE" | tr -cs 'A-Za-z0-9._-' '_' | cut -c1-120)"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
prefix="$OUT_DIR/${CLIENT}-${stamp}-${safe_phase}"

# Front-end proof: exact framebuffer plus UI hierarchy/top-activity metadata.
# Failure to obtain a screenshot is evidence that the visual lab is incomplete.
adb exec-out screencap -p > "${prefix}.png"
if [[ ! -s "${prefix}.png" ]]; then
  echo "FIELD_NATIVE_FRONTEND_ERROR client=$CLIENT phase=$safe_phase reason=empty_screenshot" >&2
  exit 2
fi

remote="/sdcard/niakvio-ui-${CLIENT}-${stamp}.xml"
if adb shell uiautomator dump "$remote" >/dev/null 2>&1; then
  adb pull "$remote" "${prefix}.xml" >/dev/null 2>&1 || true
  adb shell rm -f "$remote" >/dev/null 2>&1 || true
fi
adb shell dumpsys window windows 2>/dev/null \
  | grep -E 'mCurrentFocus|mFocusedApp|mTopActivity' \
  | head -n 20 > "${prefix}.window.txt" || true
adb shell dumpsys activity activities 2>/dev/null \
  | grep -E 'mResumedActivity|topResumedActivity|ResumedActivity' \
  | head -n 20 >> "${prefix}.window.txt" || true

bytes="$(wc -c < "${prefix}.png" | tr -d ' ')"
echo "FIELD_NATIVE_FRONTEND_CAPTURE client=$CLIENT phase=$safe_phase screenshot=$(basename "${prefix}.png") bytes=$bytes"

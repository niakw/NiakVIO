#!/usr/bin/env bash
set -euo pipefail

CLIENT="${1:?client required}"
PHASE="${2:?phase required}"
OUT_DIR="${3:?output directory required}"
mkdir -p "$OUT_DIR"

safe_phase="$(printf '%s' "$PHASE" | tr -cs 'A-Za-z0-9._-' '_' | cut -c1-120)"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
prefix="$OUT_DIR/${CLIENT}-${stamp}-${safe_phase}"

# Keep the watcher realtime. A full `uiautomator dump` waits for Android UI-idle
# and can block for many seconds; doing that synchronously for every HTTP/provider
# marker lets logcat build a multi-minute backlog and assigns screenshots to the
# wrong corpus fixture. The framebuffer is the canonical visual proof. Window and
# resumed-activity metadata are bounded best-effort sidecars and must never delay
# the structured evidence stream.
adb exec-out screencap -p > "${prefix}.png"
if [[ ! -s "${prefix}.png" ]]; then
  echo "FIELD_NATIVE_FRONTEND_ERROR client=$CLIENT phase=$safe_phase reason=empty_screenshot" >&2
  exit 2
fi

if command -v timeout >/dev/null 2>&1; then
  timeout 2s adb shell dumpsys window windows 2>/dev/null \
    | grep -E 'mCurrentFocus|mFocusedApp|mTopActivity' \
    | head -n 20 > "${prefix}.window.txt" || true
  timeout 2s adb shell dumpsys activity activities 2>/dev/null \
    | grep -E 'mResumedActivity|topResumedActivity|ResumedActivity' \
    | head -n 20 >> "${prefix}.window.txt" || true
else
  adb shell dumpsys window windows 2>/dev/null \
    | grep -E 'mCurrentFocus|mFocusedApp|mTopActivity' \
    | head -n 20 > "${prefix}.window.txt" || true
fi

bytes="$(wc -c < "${prefix}.png" | tr -d ' ')"
echo "FIELD_NATIVE_FRONTEND_CAPTURE client=$CLIENT phase=$safe_phase screenshot=$(basename "${prefix}.png") bytes=$bytes"

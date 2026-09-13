#!/usr/bin/env python3
"""Wire clean-miss adaptive catalogue fallback into Desktop/Mobile/TV suites."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INSERTIONS = {
    "scripts/run_native_corpus_desktop_suite.sh": (
        'for fixture in "${FIXTURES[@]}"; do\n  LOG="${WORKSPACE}/desktop-native-corpus-${HOST_OS}-${fixture}.log"\n',
        '''# Adaptive catalogue fallback is not a fixed batch. Each current fixture is
# evaluated once; only clean-zero providers advance to another title in the same
# global lane. Positive/error providers disappear from the retry allowlist.
export NIAKVIO_TARGET_MANIFEST="$TARGET_MANIFEST"
export NIAKVIO_RESOLVED_MANIFEST_URL="$MANIFEST_URL"
export NIAKVIO_RESOLVED_ALLOW_LOCAL="$ALLOW_LOCAL_MANIFEST"
bash "${NIAKVIO}/scripts/run_native_adaptive_catalog_fallbacks.sh" desktop "${FIXTURES[@]}" || SOFT_FAILURES=$((SOFT_FAILURES+1))

for fixture in "${FIXTURES[@]}"; do
  LOG="${WORKSPACE}/desktop-native-corpus-${HOST_OS}-${fixture}.log"
''',
    ),
    "scripts/run_native_corpus_mobile_suite.sh": (
        'for fixture in "${FIXTURES[@]}"; do\n  LOG="${WORKSPACE}/mobile-native-corpus-${fixture}.log"\n',
        '''# One-at-a-time adaptive fallback. Reuse the same emulator/app/Gradle task;
# only providers with a clean zero-stream result are restaged for the next title.
export NIAKVIO_TARGET_MANIFEST="$TARGET_MANIFEST"
export NIAKVIO_RESOLVED_MANIFEST_URL="$MANIFEST_URL"
export NIAKVIO_RESOLVED_ALLOW_LOCAL="$ALLOW_LOCAL_MANIFEST"
export NIAKVIO_MOBILE_TASK="$MOBILE_TASK"
bash "${NIAKVIO}/scripts/run_native_adaptive_catalog_fallbacks.sh" mobile "${FIXTURES[@]}" || SOFT_FAILURES=$((SOFT_FAILURES+1))

for fixture in "${FIXTURES[@]}"; do
  LOG="${WORKSPACE}/mobile-native-corpus-${fixture}.log"
''',
    ),
    "scripts/run_native_corpus_tv_suite.sh": (
        'for fixture in "${FIXTURES[@]}"; do\n  LOG="${WORKSPACE}/tv-native-corpus-${fixture}.log"\n',
        '''# One-at-a-time adaptive fallback. Keep the current emulator boot; only clean
# zero-stream providers advance to another recent title from the same global lane.
export NIAKVIO_TARGET_MANIFEST="$TARGET_MANIFEST"
export NIAKVIO_RESOLVED_MANIFEST_URL="$MANIFEST_URL"
export NIAKVIO_RESOLVED_ALLOW_LOCAL="$ALLOW_LOCAL_MANIFEST"
export NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES="$ROUTE_TIMEOUT_MINUTES"
bash "${NIAKVIO}/scripts/run_native_adaptive_catalog_fallbacks.sh" tv "${FIXTURES[@]}" || SOFT_FAILURES=$((SOFT_FAILURES+1))

for fixture in "${FIXTURES[@]}"; do
  LOG="${WORKSPACE}/tv-native-corpus-${fixture}.log"
''',
    ),
}


def patch(path: Path, anchor: str, replacement: str) -> bool:
    text = path.read_text(encoding="utf-8")
    marker = "run_native_adaptive_catalog_fallbacks.sh"
    if marker in text:
        return False
    if text.count(anchor) != 1:
        raise AssertionError(f"adaptive catalogue anchor count={text.count(anchor)} path={path}")
    path.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
    return True


def main() -> int:
    changed = []
    for relative, (anchor, replacement) in INSERTIONS.items():
        path = ROOT / relative
        if patch(path, anchor, replacement):
            changed.append(relative)
    print("NATIVE_ADAPTIVE_CATALOG_V1_OK changed=" + (",".join(changed) if changed else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

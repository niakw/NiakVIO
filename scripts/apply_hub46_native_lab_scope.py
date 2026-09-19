#!/usr/bin/env python3
"""Make all native Lab clients consume the physical active-scope manifest.

This is intentionally an idempotent source transformation used only by the repair
campaign branch. The recoverable catalogue remains unchanged.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

TARGET_ANCHOR = 'TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"'
TARGET_BLOCK = '''TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"
if [[ -n "${NIAKVIO_PROVIDER_SCOPE_MATRIX:-}" && -f "${NIAKVIO}/manifest-hub46.json" ]]; then
  TARGET_MANIFEST="manifest-hub46.json"
  echo "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE manifest=$TARGET_MANIFEST providers=active-scope authority=${NIAKVIO_PROVIDER_SCOPE_MATRIX}"
fi'''

LEGACY_DURATION = '''  EXPECTED_MINUTES="$(python3 - "$fixture" "$NIAKVIO/.github/triggers/nuvio-client-lab.json" <<'PY'
import json, sys
slug, path = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding='utf-8'))
for row in data.get('fixtures', []):
    if row.get('slug') == slug:
        print(int((row.get('fixture') or {}).get('expectedDurationMinutes') or 0))
        break
else:
    raise SystemExit(f'fixture not found: {slug}')
PY
)" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }'''

ROTATING_DURATION = '''  EXPECTED_MINUTES="$(PYTHONPATH="${NIAKVIO}/scripts" python3 - "$fixture" <<'PY'
import sys
from rotating_corpus import fixture_by_slug
print(int(fixture_by_slug(sys.argv[1]).get("expectedDurationMinutes") or 0))
PY
)" || { SOFT_FAILURES=$((SOFT_FAILURES+1)); continue; }'''

IOS_ANCHOR = 'MANIFEST_URL="${NIAKVIO_MANIFEST_URL:?NIAKVIO_MANIFEST_URL is required}"'
IOS_BLOCK = '''MANIFEST_URL="${NIAKVIO_MANIFEST_URL:?NIAKVIO_MANIFEST_URL is required}"
if [[ -n "${NIAKVIO_PROVIDER_SCOPE_MATRIX:-}" && -f "${NIAKVIO_ROOT}/manifest-hub46.json" ]]; then
  SOURCE_REPOSITORY="${GITHUB_REPOSITORY:-niakw/NiakVIO}"
  SOURCE_SHA="${GITHUB_SHA:-$(git -C "$NIAKVIO_ROOT" rev-parse HEAD)}"
  MANIFEST_URL="https://raw.githubusercontent.com/${SOURCE_REPOSITORY}/${SOURCE_SHA}/manifest-hub46.json"
  echo "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE manifest=manifest-hub46.json providers=active-scope authority=${NIAKVIO_PROVIDER_SCOPE_MATRIX}"
fi'''


def replace_once_or_assert(text: str, old: str, new: str, marker: str, label: str) -> str:
    if marker in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: anchor count={count}")
    return text.replace(old, new, 1)


def patch_target_manifest(name: str) -> None:
    path = SCRIPTS / name
    text = path.read_text(encoding="utf-8")
    text = replace_once_or_assert(
        text,
        TARGET_ANCHOR,
        TARGET_BLOCK,
        "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE manifest=$TARGET_MANIFEST providers=active-scope",
        name,
    )
    path.write_text(text, encoding="utf-8")


def patch_desktop_duration() -> None:
    path = SCRIPTS / "run_native_corpus_desktop_suite.sh"
    text = path.read_text(encoding="utf-8")
    if ROTATING_DURATION not in text:
        count = text.count(LEGACY_DURATION)
        if count != 1:
            raise SystemExit(f"desktop legacy duration block count={count}")
        text = text.replace(LEGACY_DURATION, ROTATING_DURATION, 1)
    if '"$NIAKVIO/.github/triggers/nuvio-client-lab.json"' in text.split("EXPECTED_MINUTES=", 1)[-1].split("python3 \"$PLAYER_AUGMENT\"", 1)[0]:
        raise SystemExit("desktop legacy fixture duration lookup survived")
    path.write_text(text, encoding="utf-8")


def patch_ios() -> None:
    path = SCRIPTS / "run_native_corpus_ios_suite.sh"
    text = path.read_text(encoding="utf-8")
    text = replace_once_or_assert(
        text,
        IOS_ANCHOR,
        IOS_BLOCK,
        "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE manifest=manifest-hub46.json providers=active-scope",
        "iOS",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    for name in (
        "run_native_corpus_desktop_suite.sh",
        "run_native_corpus_mobile_suite.sh",
        "run_native_corpus_tv_suite.sh",
    ):
        patch_target_manifest(name)
    patch_desktop_duration()
    patch_ios()
    print("FIELD_HUB46_NATIVE_SCOPE_APPLIED clients=desktop,mobile,tv,ios providers=active-scope")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

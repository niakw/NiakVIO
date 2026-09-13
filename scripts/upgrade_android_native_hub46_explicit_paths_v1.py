#!/usr/bin/env python3
"""Make Android native workflow explicitly consume the physical Hub-46 manifest."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".github" / "workflows" / "native-mobile-android-reader.yml"
OLD = "manifest.json"
NEW = "native-hub46/manifest.json"


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    before = text
    replacements = {
        '--manifest manifest.json': f'--manifest {NEW}',
        'NIAKVIO_TARGET_MANIFEST: manifest.json': f'NIAKVIO_TARGET_MANIFEST: {NEW}',
        '--manifest niakvio/manifest.json': f'--manifest niakvio/{NEW}',
    }
    counts = {}
    for old, new in replacements.items():
        counts[old] = text.count(old)
        text = text.replace(old, new)
    if text != before:
        PATH.write_text(text, encoding="utf-8")
    value = PATH.read_text(encoding="utf-8")
    assert '--manifest manifest.json' not in value
    assert 'NIAKVIO_TARGET_MANIFEST: manifest.json' not in value
    assert '--manifest niakvio/manifest.json' not in value
    assert value.count(NEW) >= 6
    print('ANDROID_NATIVE_HUB46_EXPLICIT_PATHS_V1_OK changed='+str(text!=before).lower()+f' occurrences={value.count(NEW)} previous={counts}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

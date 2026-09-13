#!/usr/bin/env python3
"""Make Android native preparation obey the physical Hub-46 transport globally."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/prepare_native_reader_acceptance.py"
MARKER = "NATIVE_ANDROID_HUB46_MANIFEST_V1"


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    anchor = '''    workspace = Path(args.workspace).resolve()\n    manifest_path = client_prepare._manifest_path(args.manifest).resolve()\n'''
    replacement = '''    workspace = Path(args.workspace).resolve()\n    # NATIVE_ANDROID_HUB46_MANIFEST_V1\n    # Scope ownership is global: historical workflows may still pass manifest.json,\n    # but a physical Hub-46 campaign must prepare the exact same terminal-name-safe\n    # repository consumed by the native suite.\n    requested_manifest = args.manifest\n    if (\n        os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()\n        and (ROOT / "native-hub46/manifest.json").is_file()\n    ):\n        requested_manifest = "native-hub46/manifest.json"\n    manifest_path = client_prepare._manifest_path(requested_manifest).resolve()\n'''
    if text.count(anchor) != 1:
        raise AssertionError(f"android Hub46 manifest anchor count={text.count(anchor)}")
    text = text.replace(anchor, replacement, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    required = (
        MARKER,
        'os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()',
        'requested_manifest = "native-hub46/manifest.json"',
        "client_prepare._manifest_path(requested_manifest).resolve()",
    )
    missing = [needle for needle in required if needle not in value]
    if missing:
        raise AssertionError("Android physical manifest ownership missing: " + ",".join(missing))


def main() -> int:
    changed = patch()
    validate()
    print(f"NATIVE_ANDROID_HUB46_MANIFEST_V1_OK changed={str(changed).lower()} scope_global=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

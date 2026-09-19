#!/usr/bin/env python3
"""Make Android native preparation/prebuild obey physical Hub-46 transport globally."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts/prepare_native_reader_acceptance.py"
PREBUILD = ROOT / "scripts/prebuild_native_android_reader_suite.sh"
MARKER = "NATIVE_ANDROID_HUB46_MANIFEST_V1"
PREBUILD_MARKER = "NATIVE_ANDROID_HUB46_PREBUILD_V1"


def patch_prepare() -> bool:
    text = PREPARE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_prepare(text)
        return False
    anchor = '''    workspace = Path(args.workspace).resolve()\n    manifest_path = client_prepare._manifest_path(args.manifest).resolve()\n'''
    replacement = '''    workspace = Path(args.workspace).resolve()\n    # NATIVE_ANDROID_HUB46_MANIFEST_V1\n    # Scope ownership is global: historical workflows may still pass manifest.json,\n    # but a physical Hub-46 campaign must prepare the exact same terminal-name-safe\n    # repository consumed by the native suite.\n    requested_manifest = args.manifest\n    if (\n        os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()\n        and (ROOT / "native-hub46/manifest.json").is_file()\n    ):\n        requested_manifest = "native-hub46/manifest.json"\n    manifest_path = client_prepare._manifest_path(requested_manifest).resolve()\n'''
    if text.count(anchor) != 1:
        raise AssertionError(f"android Hub46 manifest anchor count={text.count(anchor)}")
    text = text.replace(anchor, replacement, 1)
    PREPARE.write_text(text, encoding="utf-8")
    validate_prepare(text)
    return True


def patch_prebuild() -> bool:
    text = PREBUILD.read_text(encoding="utf-8")
    if PREBUILD_MARKER in text:
        validate_prebuild(text)
        return False
    anchor = 'TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"\n'
    replacement = '''TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"\n# NATIVE_ANDROID_HUB46_PREBUILD_V1\n# Keep prebuild repository resolution on the same physical Hub-46 manifest as the\n# runtime suite even when historical workflow env still says manifest.json.\nif [[ -n "${NIAKVIO_PROVIDER_SCOPE_MATRIX:-}" && -f "${NIAKVIO}/native-hub46/manifest.json" ]]; then\n  TARGET_MANIFEST="native-hub46/manifest.json"\n  echo "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE phase=prebuild manifest=$TARGET_MANIFEST providers=46 authority=${NIAKVIO_PROVIDER_SCOPE_MATRIX}"\nfi\n'''
    # PREBUILD defines NIAKVIO only after TARGET_MANIFEST in historical layout, so
    # move the block to immediately after NIAKVIO assignment if needed.
    if text.count(anchor) != 1:
        raise AssertionError(f"android Hub46 prebuild target anchor count={text.count(anchor)}")
    text = text.replace(anchor, 'TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"\n', 1)
    niak_anchor = 'NIAKVIO="${WORKSPACE}/niakvio"\n'
    if text.count(niak_anchor) != 1:
        raise AssertionError(f"android Hub46 prebuild NiakVIO anchor count={text.count(niak_anchor)}")
    block = '''NIAKVIO="${WORKSPACE}/niakvio"\n# NATIVE_ANDROID_HUB46_PREBUILD_V1\n# Keep prebuild repository resolution on the same physical Hub-46 manifest as the\n# runtime suite even when historical workflow env still says manifest.json.\nif [[ -n "${NIAKVIO_PROVIDER_SCOPE_MATRIX:-}" && -f "${NIAKVIO}/native-hub46/manifest.json" ]]; then\n  TARGET_MANIFEST="native-hub46/manifest.json"\n  echo "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE phase=prebuild manifest=$TARGET_MANIFEST providers=46 authority=${NIAKVIO_PROVIDER_SCOPE_MATRIX}"\nfi\n'''
    text = text.replace(niak_anchor, block, 1)
    PREBUILD.write_text(text, encoding="utf-8")
    validate_prebuild(text)
    return True


def validate_prepare(text: str | None = None) -> None:
    value = text if text is not None else PREPARE.read_text(encoding="utf-8")
    required = (
        MARKER,
        'os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()',
        'requested_manifest = "native-hub46/manifest.json"',
        "client_prepare._manifest_path(requested_manifest).resolve()",
    )
    missing = [needle for needle in required if needle not in value]
    if missing:
        raise AssertionError("Android physical manifest ownership missing: " + ",".join(missing))


def validate_prebuild(text: str | None = None) -> None:
    value = text if text is not None else PREBUILD.read_text(encoding="utf-8")
    required = (
        PREBUILD_MARKER,
        'NIAKVIO_PROVIDER_SCOPE_MATRIX:-',
        'TARGET_MANIFEST="native-hub46/manifest.json"',
        'phase=prebuild manifest=$TARGET_MANIFEST providers=46',
    )
    missing = [needle for needle in required if needle not in value]
    if missing:
        raise AssertionError("Android prebuild Hub-46 ownership missing: " + ",".join(missing))
    if value.index('NIAKVIO="${WORKSPACE}/niakvio"') > value.index('TARGET_MANIFEST="native-hub46/manifest.json"'):
        raise AssertionError("prebuild Hub-46 switch must run after NIAKVIO path is defined")


def main() -> int:
    prepare_changed = patch_prepare()
    prebuild_changed = patch_prebuild()
    validate_prepare()
    validate_prebuild()
    print(
        "NATIVE_ANDROID_HUB46_MANIFEST_V1_OK "
        f"prepare_changed={str(prepare_changed).lower()} prebuild_changed={str(prebuild_changed).lower()} "
        "scope_global=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

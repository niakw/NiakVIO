#!/usr/bin/env python3
"""Migrate Hub-46 native Labs to a terminal-name-safe immutable manifest.

The official Nuvio repository loaders derive a base by removing the literal
``/manifest.json`` suffix. The former ``manifest-hub46.json`` transport therefore
made relative provider filenames resolve under a nonexistent base and every native
platform failed repository installation with HTTP 404 before provider execution.

This migration changes NiakVIO Lab plumbing only. Official Nuvio source behavior is
not patched.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSPORT = "native-hub46/manifest.json"


def replace_once(path: Path, old: str, new: str) -> bool:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0:
        if new in text:
            return False
        raise RuntimeError(f"{path}: migration anchor missing: {old!r}")
    if count != 1:
        raise RuntimeError(f"{path}: migration anchor count={count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def replace_all(path: Path, old: str, new: str, minimum: int = 1) -> bool:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0:
        if new in text:
            return False
        if minimum:
            raise RuntimeError(f"{path}: migration anchor missing: {old!r}")
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    return True


def patch_resolver() -> bool:
    path = ROOT / "scripts/resolve_native_repository.sh"
    text = path.read_text(encoding="utf-8")
    old = '''  local pinned=false
  if [[ "$TARGET_MANIFEST" != */* ]] \\
    && git -C "$NIAKVIO" ls-files --error-unmatch "$TARGET_MANIFEST" >/dev/null 2>&1 \\
    && git -C "$NIAKVIO" cat-file -e "$SOURCE_SHA:$TARGET_MANIFEST" 2>/dev/null \\
    && git -C "$NIAKVIO" diff --quiet "$SOURCE_SHA" -- "$TARGET_MANIFEST"; then
'''
    new = '''  local pinned=false
  if git -C "$NIAKVIO" ls-files --error-unmatch "$TARGET_MANIFEST" >/dev/null 2>&1 \\
    && git -C "$NIAKVIO" cat-file -e "$SOURCE_SHA:$TARGET_MANIFEST" 2>/dev/null \\
    && git -C "$NIAKVIO" diff --quiet "$SOURCE_SHA" -- "$TARGET_MANIFEST"; then
'''
    if old not in text:
        if new in text:
            return False
        raise RuntimeError("resolve_native_repository.sh nested-manifest anchor drifted")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def main() -> int:
    changed: list[str] = []
    if patch_resolver():
        changed.append("scripts/resolve_native_repository.sh")

    for rel in (
        "scripts/run_native_corpus_desktop_suite.sh",
        "scripts/run_native_corpus_mobile_suite.sh",
        "scripts/run_native_corpus_tv_suite.sh",
    ):
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        next_text = text.replace(
            '&& -f "${NIAKVIO}/manifest-hub46.json"',
            '&& -f "${NIAKVIO}/native-hub46/manifest.json"',
        ).replace(
            'TARGET_MANIFEST="manifest-hub46.json"',
            f'TARGET_MANIFEST="{TRANSPORT}"',
        )
        if next_text != text:
            path.write_text(next_text, encoding="utf-8")
            changed.append(rel)
        if TRANSPORT not in path.read_text(encoding="utf-8"):
            raise RuntimeError(f"{rel}: Hub-46 transport not installed")

    ios = ROOT / ".github/workflows/native-mobile-ios-reader.yml"
    ios_text = ios.read_text(encoding="utf-8")
    next_ios = ios_text.replace(
        '${{ github.sha }}/manifest.json',
        '${{ github.sha }}/native-hub46/manifest.json',
    ).replace(
        '--manifest niakvio/manifest.json',
        '--manifest niakvio/native-hub46/manifest.json',
    )
    if next_ios != ios_text:
        ios.write_text(next_ios, encoding="utf-8")
        changed.append(str(ios.relative_to(ROOT)))

    # Align the workflow-level declared target manifest as well. The suite scripts
    # still enforce the scope independently, so this is defense in depth.
    for rel in (
        ".github/workflows/native-desktop-reader-acceptance.yml",
        ".github/workflows/native-mobile-android-reader.yml",
    ):
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        next_text = text.replace(
            "NIAKVIO_TARGET_MANIFEST: manifest.json",
            f"NIAKVIO_TARGET_MANIFEST: {TRANSPORT}",
        ).replace(
            "--manifest manifest.json",
            f"--manifest {TRANSPORT}",
        ).replace(
            "--manifest niakvio/manifest.json",
            f"--manifest niakvio/{TRANSPORT}",
        )
        if next_text != text:
            path.write_text(next_text, encoding="utf-8")
            changed.append(rel)

    print(
        "FIELD_NATIVE_HUB46_TRANSPORT_MIGRATION "
        f"changed={len(changed)} files={','.join(changed) if changed else 'none'} "
        f"transport={TRANSPORT} official_client_patched=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the current native Global+France projection-union transport.

This file is retained as a compatibility entry point for the historical Hub46
migration. It is intentionally validation-only: current native suites already
own the projection-union transport and this helper must never rewrite them back
to the old Global-only or manifest-hub46 paths.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

SUITES = (
    "run_native_corpus_desktop_suite.sh",
    "run_native_corpus_mobile_suite.sh",
    "run_native_corpus_tv_suite.sh",
)


def require_current_suite(name: str) -> None:
    path = SCRIPTS / name
    text = path.read_text(encoding="utf-8")
    required = (
        'TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-native-hub46/manifest.json}"',
        'TARGET_MANIFEST="native-hub46/manifest.json"',
        "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE",
    )
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise SystemExit(f"{name}: current projection-union contract missing: {missing}")
    forbidden = (
        'TARGET_MANIFEST="${NIAKVIO_TARGET_MANIFEST:-manifest.json}"',
        'TARGET_MANIFEST="manifest-hub46.json"',
    )
    for needle in forbidden:
        if needle in text:
            raise SystemExit(f"{name}: retired native manifest authority survived: {needle}")


def require_current_ios() -> None:
    path = SCRIPTS / "run_native_corpus_ios_suite.sh"
    text = path.read_text(encoding="utf-8")
    required = (
        "native-hub46/manifest.json",
        "FIELD_NATIVE_PHYSICAL_PROVIDER_SCOPE",
    )
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise SystemExit(f"iOS: current projection-union contract missing: {missing}")
    if "manifest-hub46.json" in text:
        raise SystemExit("iOS: retired manifest-hub46 transport survived")


def main() -> int:
    for name in SUITES:
        require_current_suite(name)
    require_current_ios()
    print(
        "FIELD_HUB46_NATIVE_SCOPE_APPLIED "
        "clients=desktop,mobile,tv,ios providers=current-active "
        "authority=projection-active-union mode=validation-only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

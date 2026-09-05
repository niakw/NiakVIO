#!/usr/bin/env python3
"""Apply the smallest test-only compatibility shim to an official NuvioDesktop checkout.

NuvioDesktop Dev currently declares PlayerEngineController.applyAudioLanguagePreferences
as abstract while PlayerExitOrderingTest's anonymous fake predates that method. The
result is a compile-time Lab-infrastructure failure on both macOS and Windows before
any NiakVIO provider executes.

This shim touches only the upstream commonTest fake. It never edits production runtime,
player, network, provider, manifest, or OS behavior. It is strict, idempotent, and
fails closed if the known upstream signature changes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

INTERFACE = Path(
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerEngine.kt"
)
TEST = Path(
    "composeApp/src/commonTest/kotlin/com/nuvio/app/features/player/PlayerExitOrderingTest.kt"
)
METHOD = "fun applyAudioLanguagePreferences(languages: List<String>)"
OVERRIDE = "override fun applyAudioLanguagePreferences(languages: List<String>) = Unit"

ANCHOR = (
    "        override fun getSubtitleTracks() = emptyList<SubtitleTrack>()\n"
    "        override fun selectAudioTrack(index: Int) = Unit"
)
REPLACEMENT = (
    "        override fun getSubtitleTracks() = emptyList<SubtitleTrack>()\n"
    "        override fun applyAudioLanguagePreferences(languages: List<String>) = Unit\n"
    "        override fun selectAudioTrack(index: Int) = Unit"
)


def patch(checkout: Path) -> str:
    checkout = checkout.resolve()
    interface_path = checkout / INTERFACE
    test_path = checkout / TEST
    if not interface_path.is_file() or not test_path.is_file():
        raise ValueError(
            "NuvioDesktop compatibility target missing: "
            f"interface={interface_path.is_file()} test={test_path.is_file()}"
        )

    interface = interface_path.read_text(encoding="utf-8")
    test = test_path.read_text(encoding="utf-8")

    if OVERRIDE in test:
        print(
            "FIELD_NATIVE_DESKTOP_TEST_COMPAT_PATCH "
            f"status=already_compatible path={TEST.as_posix()}"
        )
        return "already_compatible"

    if METHOD not in interface:
        raise ValueError(
            "NuvioDesktop PlayerEngineController contract changed; "
            "refusing stale Lab compatibility patch"
        )

    if test.count(ANCHOR) != 1:
        raise ValueError(
            "NuvioDesktop PlayerExitOrderingTest structure changed; "
            "refusing non-exact Lab compatibility patch"
        )

    updated = test.replace(ANCHOR, REPLACEMENT, 1)
    if updated.count(OVERRIDE) != 1:
        raise ValueError("test-only compatibility override cardinality is not one")
    test_path.write_text(updated, encoding="utf-8")

    print(
        "FIELD_NATIVE_DESKTOP_TEST_COMPAT_PATCH "
        f"status=applied path={TEST.as_posix()} "
        "reason=upstream_PlayerEngineController_test_contract_drift "
        "runtime_mutation=false"
    )
    return "applied"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    patch(args.checkout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

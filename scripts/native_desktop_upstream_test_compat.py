#!/usr/bin/env python3
"""Apply the smallest test-only compatibility shim required by NuvioDesktop labs.

This script is intentionally narrow. It may update only the upstream
PlayerExitOrderingTest fake PlayerEngineController when the production interface has
added applyAudioLanguagePreferences but that upstream test fake has not caught up.
It never edits commonMain/desktopMain runtime code, Gradle, networking or the player.
"""
from __future__ import annotations

import argparse
from pathlib import Path

INTERFACE = Path("composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerEngine.kt")
STALE_TEST = Path("composeApp/src/commonTest/kotlin/com/nuvio/app/features/player/PlayerExitOrderingTest.kt")
REQUIRED_SIGNATURE = "fun applyAudioLanguagePreferences(languages: List<String>)"
OVERRIDE = "        override fun applyAudioLanguagePreferences(languages: List<String>) = Unit\n"
ANCHOR = "        override fun getSubtitleTracks() = emptyList<SubtitleTrack>()\n"


def patch_checkout(repo: Path) -> str:
    repo = Path(repo).resolve()
    interface = repo / INTERFACE
    stale_test = repo / STALE_TEST
    if not interface.is_file() or not stale_test.is_file():
        raise SystemExit("NuvioDesktop compatibility targets are missing")

    interface_text = interface.read_text(encoding="utf-8")
    test_text = stale_test.read_text(encoding="utf-8")

    if REQUIRED_SIGNATURE not in interface_text:
        print("FIELD_NATIVE_DESKTOP_TEST_COMPAT required=false reason=interface-does-not-require-method")
        return "not-required"
    if "override fun applyAudioLanguagePreferences(languages: List<String>)" in test_text:
        print("FIELD_NATIVE_DESKTOP_TEST_COMPAT required=false reason=upstream-test-already-compatible")
        return "already-compatible"
    if test_text.count(ANCHOR) != 1:
        raise SystemExit(
            "refusing NuvioDesktop test compatibility shim: expected one exact test-only anchor, "
            f"found {test_text.count(ANCHOR)}"
        )

    stale_test.write_text(test_text.replace(ANCHOR, ANCHOR + OVERRIDE, 1), encoding="utf-8")
    print(
        "FIELD_NATIVE_DESKTOP_TEST_COMPAT required=true applied=true "
        f"path={STALE_TEST.as_posix()} runtime_mutation=false"
    )
    return "patched"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    args = parser.parse_args()
    patch_checkout(Path(args.repo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

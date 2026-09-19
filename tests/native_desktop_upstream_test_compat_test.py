#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "desktop_compat", ROOT / "scripts/native_desktop_upstream_test_compat.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

INTERFACE_TEXT = """interface PlayerEngineController {
    fun getSubtitleTracks(): List<SubtitleTrack>
    fun applyAudioLanguagePreferences(languages: List<String>)
}
"""
TEST_TEXT = """private fun testController() = object : PlayerEngineController {
        override fun getSubtitleTracks() = emptyList<SubtitleTrack>()
        override fun selectAudioTrack(index: Int) = Unit
}
"""


def checkout(interface_text: str = INTERFACE_TEXT, test_text: str = TEST_TEXT):
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    interface = root / mod.INTERFACE
    test = root / mod.STALE_TEST
    interface.parent.mkdir(parents=True, exist_ok=True)
    test.parent.mkdir(parents=True, exist_ok=True)
    interface.write_text(interface_text, encoding="utf-8")
    test.write_text(test_text, encoding="utf-8")
    return td, root, interface, test


def main() -> int:
    td, root, interface, test = checkout()
    try:
        assert mod.patch_checkout(root) == "patched"
        patched = test.read_text(encoding="utf-8")
        assert patched.count("override fun applyAudioLanguagePreferences(languages: List<String>) = Unit") == 1
        assert interface.read_text(encoding="utf-8") == INTERFACE_TEXT
        assert mod.patch_checkout(root) == "already-compatible"
        assert test.read_text(encoding="utf-8") == patched
    finally:
        td.cleanup()

    td, root, _, test = checkout(interface_text="interface PlayerEngineController {}\n")
    try:
        before = test.read_text(encoding="utf-8")
        assert mod.patch_checkout(root) == "not-required"
        assert test.read_text(encoding="utf-8") == before
    finally:
        td.cleanup()

    td, root, _, _ = checkout(test_text="private fun testController() = object : PlayerEngineController {}\n")
    try:
        try:
            mod.patch_checkout(root)
        except SystemExit as exc:
            assert "expected one exact test-only anchor" in str(exc)
        else:
            raise AssertionError("changed upstream test shape must fail closed")
    finally:
        td.cleanup()

    source = (ROOT / "scripts/native_desktop_upstream_test_compat.py").read_text(encoding="utf-8")
    for forbidden in (
        "commonMain/kotlin/com/nuvio/app/features/player/PlayerEngine.desktop",
        "desktopMain/kotlin/com/nuvio/app/features/player/PlayerEngine",
        "setRequestProperty",
        "usesCleartextTraffic",
        "NativePlayerController(",
    ):
        assert forbidden not in source, forbidden

    print("native desktop upstream test compatibility tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

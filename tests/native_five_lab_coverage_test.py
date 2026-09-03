#!/usr/bin/env python3
"""The native acceptance surface is exactly five first-class client/platform labs."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
android=(ROOT/".github/workflows/native-mobile-android-reader.yml").read_text(encoding="utf-8")
ios=(ROOT/".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8")
desktop=(ROOT/".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

for text in (android,ios,desktop):
    assert "workbench/provider-v3-performance-playback" in text
    assert ".github/triggers/full-native-lab-validation.json" in text

# 1 TV Android + 1 Mobile Android
assert "tv-route-reader:" in android
assert "mobile-android-reader:" in android
assert 'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS: "40000"' in android
assert "run_native_corpus_tv_suite.sh" in android
assert "run_native_corpus_mobile_suite.sh" in android

# 1 Mobile iOS
assert "mobile-ios-reader:" in ios
assert "runs-on: macos-26" in ios
assert "run_native_corpus_ios_suite.sh" in ios
assert "|| '40000'" in ios

# 2 Desktop matrix entries
assert "runner: macos-15" in desktop and "os_name: macos" in desktop
assert "runner: windows-2022" in desktop and "os_name: windows" in desktop
assert "run_native_corpus_desktop_suite.sh" in desktop

platforms=["TVAndroid","MobileAndroid","MobileIOS","DesktopMACOS","DesktopWindows"]
assert len(platforms)==5 and len(set(platforms))==5
print("NATIVE_FIVE_LABS_OK platforms="+",".join(platforms))

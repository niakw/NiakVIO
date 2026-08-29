#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TV = (ROOT / ".github/workflows/native-tv-route-reader.yml").read_text(encoding="utf-8")
ANDROID = (ROOT / ".github/workflows/native-mobile-android-reader.yml").read_text(encoding="utf-8")
IOS = (ROOT / ".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8")
prime = (ROOT / "scripts/prime_android_lab_adb.sh").read_text(encoding="utf-8")
prebuild = (ROOT / "scripts/prebuild_native_android_reader_suite.sh").read_text(encoding="utf-8")
tv_suite = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text(encoding="utf-8")
mobile_suite = (ROOT / "scripts/run_native_corpus_mobile_suite.sh").read_text(encoding="utf-8")

assert "avd-v5-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in TV
assert "avd-v5-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in ANDROID
for workflow in (TV, ANDROID):
    for line in workflow.splitlines():
        if "key: avd-v5-" in line:
            assert "needs.resolve.outputs" not in line
    assert "~/.android/debug.keystore" in workflow
    assert "-no-snapshot-load -no-window -gpu swiftshader_indirect -noaudio -no-boot-anim" in workflow
    assert "-no-snapshot-save -no-window -gpu swiftshader_indirect -noaudio -no-boot-anim" in workflow
    assert "force-avd-creation: false" in workflow
    assert "bash niakvio/scripts/prime_android_lab_adb.sh" in workflow
    assert "prebuild_native_android_reader_suite.sh" in workflow
    assert "NIAKVIO_SKIP_ANDROID_PREBUILD: \"1\"" in workflow

assert "matrix:" not in TV
assert "Execute movie TV anime in one TV boot" in TV
assert "Execute movie TV anime in one Mobile Android boot" in ANDROID

for suite in (tv_suite, mobile_suite):
    assert 'PLAYER_OUTCOME_GLOBAL_GATE="${NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE:-0}"' in suite
    assert 'REQUIRE_READER_SUCCESS=0' in suite
    assert 'blocking=false' in suite
assert "NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE: \"1\"" not in TV
assert "NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE: \"1\"" not in ANDROID

assert "sdkmanager" in prime
assert "--install platform-tools" in prime
assert "adb start-server" in prime
assert prebuild.count("--max-workers=1") >= 2

assert "runs-on: macos-26" in IOS
assert "iphonesimulator" in (ROOT / "scripts/run_native_corpus_ios_suite.sh").read_text(encoding="utf-8")
assert "NuvioPlayerBridgeFactory" in (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")
assert "PluginRepository.executeScraper" in (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")

print("native platform persistence contract passed: tv_single_boot=true android_single_boot=true ios_simulator=true")

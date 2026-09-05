#!/usr/bin/env python3
"""Native Labs must observe official Nuvio clients as-is, including upstream reds."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "automation/native-human-ux-policy.json").read_text(encoding="utf-8"))
DESKTOP_WORKFLOW = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")
ANDROID_WORKFLOW = (ROOT / ".github/workflows/native-mobile-android-reader.yml").read_text(encoding="utf-8")

assert POLICY["version"] >= 9
assert POLICY["mode"] == "human-ux-observation-only"
assert "patch official Nuvio test/commonTest sources to bypass compile or test failures" in POLICY["forbidden_behaviors"]
assert "patch official Nuvio build/dependency/packaging conflicts to bypass upstream failures" in POLICY["forbidden_behaviors"]
assert "exact committed published NiakVIO provider bytes" in POLICY["persistent_profiles"]["common"]["provider_transaction"]
assert "never rematerialize" in POLICY["persistent_profiles"]["common"]["provider_transaction"]

profiles = POLICY["persistent_profiles"]
desktop = profiles["desktop"]
assert desktop["allowed_test_plumbing"] == [
    "composeApp/src/desktopTest/",
    "local.properties",
]
assert "official commonTest/test source patches" in desktop["forbidden_retouch"]
assert POLICY["allowed_checkout_changes"]["desktop"] == [
    "composeApp/src/desktopTest/",
    "local.properties",
]

mobile = profiles["mobile"]
assert mobile["allowed_test_plumbing"] == [
    "composeApp/src/androidDeviceTest/",
    "composeApp/build.gradle.kts device-test runner and test dependencies",
    "local.properties",
]
assert "upstream build/dependency/packaging failures" in mobile["forbidden_retouch"]
assert not any("pickFirst" in value or "libc++" in value for value in mobile["allowed_test_plumbing"])
assert not any("pickFirst" in value or "libc++" in value or value in {"packaging {", "jniLibs {"} for value in POLICY["allowed_gradle_additions"]["mobile"])
assert not any("commonTest" in value or "duplicate C++ runtime" in value for value in POLICY["allowed_change_intent"])

blockers = {
    row["id"]: row
    for row in POLICY["job_blocker_memory"]["entries"]
    if isinstance(row, dict) and row.get("id")
}
desktop_drift = blockers["desktop-player-language-preference-test-contract-drift"]
assert desktop_drift["status"] == "external-upstream-blocker"
assert "retain the official compile failure as external evidence" in desktop_drift["resolution"]
assert "do not patch the NuvioDesktop commonTest fake" in desktop_drift["never_repeat"]

mobile_packaging = blockers["mobile-device-test-libcxx-packaging-conflict"]
assert mobile_packaging["status"] == "external-upstream-blocker"
assert "retain the official build failure as external evidence" in mobile_packaging["resolution"]
assert "must not inject a Gradle packaging pickFirst" in mobile_packaging["resolution"]
assert "do not inject pickFirsts for libc++_shared.so" in mobile_packaging["never_repeat"]

# Desktop may add NiakVIO-owned desktopTest diagnostics, but must not patch
# upstream commonTest/production sources to get past an official failure.
for forbidden in (
    "patch_nuvio_desktop_test_compat.py",
    "PlayerExitOrderingTest.kt",
    "commonTest/kotlin/com/nuvio/app/features/player",
):
    assert forbidden not in DESKTOP_WORKFLOW, forbidden

# Mobile may enable the official device-test surface, but it must not patch
# upstream packaging/dependencies or test-process runtime to manufacture a build.
for forbidden in (
    "harden_nuvio_mobile_device_test.py",
    'pickFirsts.add("lib/*/libc++_shared.so")',
    "SentryInitProvider",
    "tools:node=remove",
):
    assert forbidden not in ANDROID_WORKFLOW, forbidden

assert not (ROOT / "scripts/patch_nuvio_desktop_test_compat.py").exists()
assert not (ROOT / "tests/patch_nuvio_desktop_test_compat_test.py").exists()
assert not (ROOT / "scripts/harden_nuvio_mobile_device_test.py").exists()

print("native Lab official-client read-only contract passed")

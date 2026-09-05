#!/usr/bin/env python3
"""Native Labs must observe official Nuvio clients as-is, including upstream reds."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "automation/native-human-ux-policy.json").read_text(encoding="utf-8"))
DESKTOP_WORKFLOW = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

assert POLICY["version"] >= 8
assert POLICY["mode"] == "human-ux-observation-only"
assert "patch official Nuvio test/commonTest sources to bypass compile or test failures" in POLICY["forbidden_behaviors"]

profile = POLICY["persistent_profiles"]["desktop"]
assert profile["allowed_test_plumbing"] == [
    "composeApp/src/desktopTest/",
    "local.properties",
]
assert "official commonTest/test source patches" in profile["forbidden_retouch"]
assert POLICY["allowed_checkout_changes"]["desktop"] == [
    "composeApp/src/desktopTest/",
    "local.properties",
]
assert not any("commonTest" in value for value in POLICY["allowed_change_intent"])

blockers = {
    row["id"]: row
    for row in POLICY["job_blocker_memory"]["entries"]
    if isinstance(row, dict) and row.get("id")
}
drift = blockers["desktop-player-language-preference-test-contract-drift"]
assert drift["status"] == "external-upstream-blocker"
assert "retain the official compile failure as external evidence" in drift["resolution"]
assert "do not patch the NuvioDesktop commonTest fake" in drift["never_repeat"]

# The Desktop Lab may add NiakVIO-owned desktopTest diagnostics, but it must not
# modify upstream commonTest/production sources to get past an official failure.
for forbidden in (
    "patch_nuvio_desktop_test_compat.py",
    "PlayerExitOrderingTest.kt",
    "commonTest/kotlin/com/nuvio/app/features/player",
):
    assert forbidden not in DESKTOP_WORKFLOW, forbidden

assert not (ROOT / "scripts/patch_nuvio_desktop_test_compat.py").exists()
assert not (ROOT / "tests/patch_nuvio_desktop_test_compat_test.py").exists()

print("native Lab official-client read-only contract passed")

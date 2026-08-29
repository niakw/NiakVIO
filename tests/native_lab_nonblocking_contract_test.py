#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = (ROOT / ".github/workflows/native-android-route-reader.yml").read_text(encoding="utf-8")
DESKTOP = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

for name, workflow in (("android", ANDROID), ("desktop", DESKTOP)):
    assert "\n  pull_request:" not in workflow, f"{name} native Lab must not block PR flow"
    assert "\n  push:" in workflow, f"{name} native Lab must collect evidence from main"
    assert "workflow_dispatch:" in workflow, f"{name} native Lab must remain manually runnable"
    assert "github.event.pull_request" not in workflow, f"{name} native Lab retained PR-only logic"

assert "NIAKVIO_TARGET_PROVIDER: declared-type" in ANDROID
assert "NIAKVIO_TARGET_PROVIDER: declared-type" in DESKTOP
assert 'NIAKVIO_REPRESENTATIVE_FIXTURES: "interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01"' in ANDROID
assert "interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01" in DESKTOP
assert "NIAKVIO_PR_PROVIDER_LIMIT" not in DESKTOP

# Generous ceilings remain fail-safe only; they do not define work size.
# Real work is bounded by one fixture per declared type and the per-provider timeout.
assert ANDROID.count("timeout-minutes: 160") == 1
assert ANDROID.count("timeout-minutes: 180") == 2
assert DESKTOP.count("timeout-minutes: 240") == 1

print("native Lab nonblocking contract passed: main-only=true manual=true type_bounded_1_1_1=true")

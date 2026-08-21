#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
android = (ROOT / ".github/workflows/native-android-route-reader.yml").read_text(encoding="utf-8")
desktop = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

android_reader_timeout = "timeout-minutes: ${{ github.event_name == 'pull_request' && 55 || 180 }}"
android_brain_timeout = "timeout-minutes: ${{ github.event_name == 'pull_request' && 75 || 180 }}"
desktop_reader_timeout = "timeout-minutes: ${{ github.event_name == 'pull_request' && 55 || 240 }}"

assert android.count(android_reader_timeout) == 2, "TV and Mobile PR jobs must each be capped at 55 minutes"
assert android.count(android_brain_timeout) == 1, "3-route Brain PR sandbox must be capped at 75 minutes"
assert desktop.count(desktop_reader_timeout) == 1, "Desktop PR reader matrix must be capped at 55 minutes"

# Exhaustive/deep budgets remain available outside PRs through the right-hand
# branch of each event-aware expression; artifact persistence must remain fail-safe.
for workflow, deep_values in ((android, ("180",)), (desktop, ("240",))):
    for value in deep_values:
        assert f"|| {value} }}" in workflow, f"deep native budget {value} minutes was lost"
    assert "if: always()" in workflow, "native evidence artifacts/diagnosis must survive failures"

print("native PR timeout contract tests passed")

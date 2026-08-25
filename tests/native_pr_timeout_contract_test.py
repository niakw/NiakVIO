#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
android = (ROOT / ".github/workflows/native-android-route-reader.yml").read_text(encoding="utf-8")
desktop = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

# Official Android clients compile before the emulator is useful. PR jobs keep a
# 100 minute ceiling. Outside PRs the sharded TV reader has a lower 160 minute
# budget, while Mobile and the Brain retest retain 180 minutes.
android_tv_timeout = "timeout-minutes: ${{ github.event_name == 'pull_request' && 100 || 160 }}"
android_mobile_brain_timeout = "timeout-minutes: ${{ github.event_name == 'pull_request' && 100 || 180 }}"
# macOS also runs explicit TV wrong-media witness routes (Colony, Failure Frame,
# Nube) in addition to the representative trio, so retain a bounded 75m PR budget
# while deep/non-PR desktop acceptance remains 240m.
desktop_reader_timeout = "timeout-minutes: ${{ github.event_name == 'pull_request' && 75 || 240 }}"

assert android.count(android_tv_timeout) == 1, "sharded TV reader must keep its 100m PR / 160m main budget"
assert android.count(android_mobile_brain_timeout) == 2, "Mobile and Brain retest must each keep a 100m PR / 180m main budget"
assert "pull_request' && 55 || 180" not in android, "obsolete 55 minute Android reader cap can kill the emulator before route execution"
assert "pull_request' && 75 || 180" not in android, "Brain retest must keep the representative native-reader PR budget"
assert desktop.count(desktop_reader_timeout) == 1, "Desktop PR reader matrix must get the bounded 75 minute wrong-media witness budget"
assert "pull_request' && 55 || 240" not in desktop, "old Desktop cap can truncate the added macOS identity witness routes"

# Exhaustive/deep budgets remain available outside PRs through the right-hand
# branch of each event-aware expression; artifact persistence must remain fail-safe.
for workflow, deep_values in ((android, ("160", "180")), (desktop, ("240",))):
    for value in deep_values:
        assert f"|| {value} }}" in workflow, f"deep native budget {value} minutes was lost"
    assert "if: always()" in workflow, "native evidence artifacts/diagnosis must survive failures"

print("native PR timeout contract tests passed")

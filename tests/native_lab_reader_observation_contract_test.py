#!/usr/bin/env python3
"""Native Labs must observe official-client reader failures without repairing Nuvio repos."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tv = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text(encoding="utf-8")
mobile = (ROOT / "scripts/run_native_corpus_mobile_suite.sh").read_text(encoding="utf-8")
desktop = (ROOT / "scripts/run_native_corpus_desktop_suite.sh").read_text(encoding="utf-8")
mobile_codegen = (ROOT / "scripts/native_player_diagnostics_codegen.py").read_text(encoding="utf-8")
desktop_workflow = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

for text in (tv, mobile, desktop):
    assert "gate_native_declared_provider_matrix.py" in text
    assert "reader_outcome=observational" in text
    assert "READER_STATE=degraded" in text
    assert "matrix_status=$MATRIX_STATUS" in text
    assert "NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE" not in text
    assert "NIAKVIO_REQUIRE_READER_SUCCESS" not in text

assert "Intent(context, MainActivity::class.java)" in mobile_codegen
assert "generateSequence(error) { it.cause }" in mobile_codegen
assert "getLaunchIntentForPackage(context.packageName)" not in mobile_codegen.split("MOBILE_HELPERS =", 1)[1]

assert "external client playback failures are preserved, never repaired here" in desktop_workflow

for forbidden in (
    "run_adaptive_quick_repair.py",
    "run_adaptive_deep_repair.py",
    "materialize_provider_v3_all.py",
    "reapply_published_overrides.py",
):
    assert forbidden not in desktop_workflow

print("native Lab reader observation contract passed")

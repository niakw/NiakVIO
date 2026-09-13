#!/usr/bin/env python3
"""Native Labs must observe official-client reader failures without repairing Nuvio repos."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tv = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text(encoding="utf-8")
mobile = (ROOT / "scripts/run_native_corpus_mobile_suite.sh").read_text(encoding="utf-8")
desktop = (ROOT / "scripts/run_native_corpus_desktop_suite.sh").read_text(encoding="utf-8")
mobile_codegen = (ROOT / "scripts/native_player_diagnostics_codegen.py").read_text(encoding="utf-8")
mobile_finalizer = (ROOT / "scripts/finalize_native_android_reader_source.py").read_text(encoding="utf-8")
desktop_workflow = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

for text in (tv, mobile, desktop):
    assert "gate_native_declared_provider_matrix.py" in text
    assert "reader_outcome=observational" in text
    assert "READER_STATE=degraded" in text
    assert "matrix_status=$MATRIX_STATUS" in text
    assert "NIAKVIO_NATIVE_PLAYER_OUTCOME_GLOBAL_GATE" not in text
    assert "NIAKVIO_REQUIRE_READER_SUCCESS" not in text

assert 'Intent().setClassName(' in mobile_codegen
assert "MainActivity::class.java.name" in mobile_codegen
assert '"com.nuviodebug.com"' not in mobile_codegen
assert "Intent(context, MainActivity::class.java)" not in mobile_codegen
assert "generateSequence(error) { it.cause }" in mobile_codegen
assert "getLaunchIntentForPackage(context.packageName)" not in mobile_codegen.split("MOBILE_HELPERS =", 1)[1]

# Codegen may initially use instrumentation context as a neutral placeholder. The
# mandatory finalizer owns the authoritative target-component rewrite and must reject
# any finalized Mobile source that still points at the test APK package.
assert 'MOBILE_EXPLICIT_TARGET_PACKAGE = "MainActivity::class.java.packageName,"' in mobile_finalizer
assert "source = source.replace(MOBILE_EXPLICIT_CONTEXT_PACKAGE, MOBILE_EXPLICIT_TARGET_PACKAGE, 1)" in mobile_finalizer
assert "or MOBILE_EXPLICIT_CONTEXT_PACKAGE in source" in mobile_finalizer

# Desktop reader/player failures are observational evidence: each official-client
# attempt may fail without repairing Nuvio, while the exhaustive provider matrix
# remains a separate blocking coverage contract.
assert "Reader/player outcomes are evidence. External client failures remain visible." in desktop_workflow
assert 'bash "$GITHUB_WORKSPACE/niakvio/scripts/run_native_corpus_desktop_suite.sh" || true' in desktop_workflow
assert "gate_native_player_reached.cjs" in desktop_workflow
assert "gate_native_declared_provider_matrix.py" in desktop_workflow
assert 'NIAKVIO_BRAIN_NONBLOCKING: "1"' in desktop_workflow

for forbidden in (
    "run_adaptive_quick_repair.py",
    "run_adaptive_deep_repair.py",
    "materialize_provider_v3_all.py",
    "reapply_published_overrides.py",
):
    assert forbidden not in desktop_workflow

print("native Lab reader observation contract passed")

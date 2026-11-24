#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
probe=(ROOT/".github/workflows/brain-catalogue-source-probe.yml").read_text(encoding="utf-8")
feedback=(ROOT/".github/workflows/brain-android-tv-emulator-feedback.yml").read_text(encoding="utf-8")
assert "native_run_id:" in probe
assert "build_brain_catalogue_source_probe_request.py" in probe
assert "--native-run-id" in probe
assert "persist_brain_catalogue_source_probe.py" in probe
assert "brain-catalogue-source-probe-history.json" in probe
assert "FIELD_BRAIN_SOURCE_FORCE_DISPATCH" in probe
assert "-f architecture_force=true" in probe and '-f target_provider="$provider"' in probe
assert "contents: write" in probe and "actions: write" in probe
assert "Dispatch exact-current catalogue source probe" in feedback
assert "brain-catalogue-source-probe.yml" in feedback
assert '-f native_run_id="$NATIVE_RUN_ID"' in feedback
assert "nativeExtractionZeroObserved" in feedback
assert "nativeSourceScriptShapePatterns" in feedback
assert "source probe" in feedback.casefold()
print("official TV -> exact source probe -> sanitized history -> FORCE closed-loop workflow contract passed")

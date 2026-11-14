#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_unrelated_active_provider_bytes.py"
spec = importlib.util.spec_from_file_location("active_byte_guard", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory(prefix="bulk-active-byte-guard-") as tmp:
    baseline = Path(tmp) / "baseline.json"
    request = ROOT / ".github/provider-onboarding/batch.json"
    payload = mod.capture(request, baseline)
    assert payload["publicationAuthority"] is False
    targets = set(payload["requestTargets"])
    assert targets
    protected = payload["protected"]
    assert protected
    assert all(row["provider"] not in targets for row in protected)
    assert all(len(row["sha256"]) == 64 for row in protected)
    mod.verify(baseline)

workflow = (ROOT / ".github/workflows/provider-bulk-onboarding.yml").read_text(encoding="utf-8")
assert "verify_unrelated_active_provider_bytes.py" in workflow
assert "--capture" in workflow and "--verify" in workflow
assert "provider_v3_minimizer_published_test.py" not in workflow, (
    "bulk onboarding must not demand a fleet-wide minimizer rewrite of proof-bound active bytes"
)
assert "provider_pending_minimizer_test.py" in workflow
print("bulk onboarding active exact-byte stability contract passed")

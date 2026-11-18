#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/external_audit/classify_findings.py"
spec = importlib.util.spec_from_file_location("external_audit_classifier", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert mod.norm_path(".github/workflows/native-mobile-android-reader.yml") == ".github/workflows/native-mobile-android-reader.yml"
assert mod.norm_path("./.github/workflows/native-mobile-android-reader.yml") == ".github/workflows/native-mobile-android-reader.yml"
assert mod.scope(".github/workflows/native-mobile-android-reader.yml") == "maintained"
assert mod.scope("providers/demo--nuvio--1234.js") == "generated"
assert mod.scope("provider-disabled/demo--nuvio--1234.js") == "generated"
assert mod.scope("provider-old/demo.js") == "historical"
assert mod.scope("scripts/provider_patches/demo.py") == "maintained"

print("external audit scope policy passed: dot-github preserved disabled-provider-bundles=generated")

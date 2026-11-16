#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_provider_onboarding_neutral_drift.py"
spec = importlib.util.spec_from_file_location("onboarding_drift", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

for path in (
    "MEMORY.md",
    "README.md",
    "README.fr.md",
    "PROVIDER_CENSUS_STATUS.md",
    "docs/ARCHITECTURE-NOTE.md",
    ".github/triggers/provider-v3-reconstruct-all.json",
):
    assert module.is_neutral_path(path), path

for path in (
    "manifest.json",
    "vf/manifest.json",
    "provider_catalog.json",
    "provider-overrides.json",
    "provider-v3-materialization.json",
    "PROVENANCE.json",
    "providers/demo.js",
    "provider-bases/demo.js",
    "scripts/provider_base_store.py",
    "scripts/add_provider.py",
    "engine_v2/src/repair-brain.mjs",
    ".github/workflows/add-provider.yml",
    "tests/add_provider_workflow_test.py",
    "automation/provider-v3-static-knowledge.json",
    "assets/providers/emojis.json",
):
    assert not module.is_neutral_path(path), path

neutral, blocking = module.classify_paths([
    "MEMORY.md",
    ".github/triggers/provider-projection-reconcile.json",
    "scripts/provider_base_store.py",
    "manifest.json",
])
assert neutral == [
    ".github/triggers/provider-projection-reconcile.json",
    "MEMORY.md",
]
assert blocking == ["manifest.json", "scripts/provider_base_store.py"]

single = (ROOT / ".github/workflows/add-provider.yml").read_text(encoding="utf-8")
bulk = (ROOT / ".github/workflows/provider-bulk-onboarding.yml").read_text(encoding="utf-8")
for workflow in (single, bulk):
    assert "check_provider_onboarding_neutral_drift.py" in workflow
    assert '--base "$BASE_SHA"' in workflow

assert '--head HEAD' in single
assert '--head origin/main' in single
assert '--head HEAD' in bulk

print("provider onboarding publication drift contract passed")

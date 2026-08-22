#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/normalize_core_media_policy.py"

spec = importlib.util.spec_from_file_location("core_media_policy", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cfg = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
normalized, changed = module.normalize(cfg)
source_changes = module.normalize_source_files(apply=False)

# Once main has been normalized this must remain a pure assertion, not a repair.
assert changed == [], changed
assert source_changes == [], source_changes
module.assert_policy(normalized)

purstream = normalized["provider_patches"]["purstream"]
assert purstream.get("patch_scripts") == [], purstream.get("patch_scripts")
assert purstream.get("patch_script_options") == {}, purstream.get("patch_script_options")

# Retired provider-specific implementations must not creep back into main.
for retired in (
    "scripts/provider_patches/purstream_tv_identity_v3.py",
    "scripts/provider_patches/purstream_tv_identity_impl_v3.py",
    "scripts/provider_patches/purstream_exact_tv_v2.py",
    "scripts/provider_patches/purstream_bridge.py",
    "scripts/migrate_tv_hardening_5_20_39.py",
):
    assert not (ROOT / retired).exists(), retired

print("Core media policy test passed: Purstream-specific repair hooks=0")

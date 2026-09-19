#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from scripts.normalize_runtime_repository_dependencies import (
    LEGACY_PATCH,
    assert_contract,
    normalize,
)

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
normalized, changed = normalize(json.loads(json.dumps(config)))
assert changed == [], f"clean-v3 provider DATA unexpectedly needs repository normalization: {changed}"
assert_contract(normalized)
assert not (ROOT / LEGACY_PATCH).exists()

for provider_id, row in normalized["provider_patches"].items():
    if not isinstance(row, dict):
        continue
    assert LEGACY_PATCH not in [str(v) for v in row.get("patch_scripts") or []], provider_id
    options = row.get("patch_script_options") or {}
    assert not isinstance(options, dict) or LEGACY_PATCH not in options, provider_id

print("runtime repository dependency clean-v3 tests passed: legacy materializer absent, provider DATA owns persisted routes")

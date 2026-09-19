#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_response_value_correlation_v20_5_1.py"

spec = importlib.util.spec_from_file_location("v2051", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V20.5.1 migration")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.patch_worker()
module.patch_proof()
module.patch_recovery()
module.patch_materializer()
module.patch_base()
module.validate_worker()
module.validate_proof()
module.validate_recovery()
module.validate_materializer()
module.validate_base()

base = module.BASE.read_text(encoding="utf-8")
assert module.MARKER in base
for needle in module.LEGACY_NEEDLES:
    assert needle in base, needle
assert module.STRICT_NEEDLE in base
assert "const valueSteps = (plan.steps || []).slice(0, 8);" in base
assert '"step_deferred"' in base
assert "..._spv205HttpValues(payload.value, payload.base, [])" in base

print("provider response-value correlation V20.5.1 compatibility tests passed")

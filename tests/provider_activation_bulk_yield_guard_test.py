#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "enforce_provider_activation_contract.py"
spec = importlib.util.spec_from_file_location("activation_contract", MODULE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert mod.DEFAULT_MINIMUM_BULK_YIELD == 0.75
assert mod.MIN_BULK_PROVIDER_COUNT == 8

# The production guard must prevent a low-yield bulk result from becoming a mass
# disable event. 13/44 is architecture failure, not evidence that 31 providers
# should suddenly be treated as genuinely broken. The authoritative certification
# denominator is the complete 46-row Provider JS manifest, never a targeted subset
# and never only the currently-enabled 44 rows.
ratio = 13 / 46
assert ratio < mod.DEFAULT_MINIMUM_BULK_YIELD
assert 33 / 46 > (1 - mod.DEFAULT_MINIMUM_BULK_YIELD)

# A 3/4 initial yield is the minimum accepted bootstrap architecture target.
assert 225 / 300 >= mod.DEFAULT_MINIMUM_BULK_YIELD
assert 224 / 300 < mod.DEFAULT_MINIMUM_BULK_YIELD

print("provider activation bulk-yield guard contract passed")

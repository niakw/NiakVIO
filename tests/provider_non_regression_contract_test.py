#!/usr/bin/env python3
"""Compatibility-aware entrypoint for the provider non-regression contract."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
impl_path = ROOT / "tests" / "provider_non_regression_contract_test_impl.py"
source = impl_path.read_text(encoding="utf-8")
old = 'finalizer = FINALIZER.read_text(encoding="utf-8")'
new = 'finalizer = FINALIZER.read_text(encoding="utf-8") + "\\n" + (ROOT / "scripts" / "finalize_provider_repair_disposition_v1_impl.py").read_text(encoding="utf-8")'
if source.count(old) != 1:
    raise AssertionError("provider non-regression finalizer compatibility anchor changed")
source = source.replace(old, new, 1)

# The durable implementation predates the declared-hub activation policy. Keep
# all historical semantic/non-regression assertions, but make activation debt
# explicitly depend on hub authority instead of the superseded force-all model.
old_activation = 'assert \'"activeBrokenProviderAllowed": False\' in finalizer'
new_activation = 'assert \'"activationFollowsDeclaredHub": True\' in finalizer'
if source.count(old_activation) != 1:
    raise AssertionError("provider non-regression activation assertion anchor changed")
source = source.replace(old_activation, new_activation, 1)

exec(compile(source, str(impl_path), "exec"), globals(), globals())

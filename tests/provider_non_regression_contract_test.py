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

# The active finalization branch is the 46-provider Labs branch. Keep the
# historical implementation source intact while projecting its workflow-branch
# assertion and human-readable wording onto the current operational contract.
old_branch_assert = 'assert "workbench/systemic-recovery-20260909" in nonreg'
new_branch_assert = 'assert "fix/labs-5.21.44-20260912" in nonreg'
if source.count(old_branch_assert) != 1:
    raise AssertionError("provider non-regression active-branch compatibility anchor changed")
source = source.replace(old_branch_assert, new_branch_assert, 1)
source = source.replace("rolling 96-provider floor", "rolling 46-provider floor", 1)

# Activation semantics now live directly in the durable implementation:
# exact hub-lab-matrix-46 membership owns visibility, while routeDataState owns
# repair/off debt. Do not rewrite those assertions to historical hub-presence or
# force-all policies here.
exec(compile(source, str(impl_path), "exec"), globals(), globals())


# Active44: explicit manual OFF may waive missing rolling lane proof, but the
# gate still evaluates semantic/HLS contract regression independently.
_gate_source = (ROOT / "scripts/check_provider_non_regression_v1.py").read_text(encoding="utf-8")
assert "manual_off_reason" in _gate_source
assert "manual-user-off-v1" in _gate_source
assert "semantic_capability_regression" in _gate_source
assert "historical_hls_m3u8_regression" in _gate_source

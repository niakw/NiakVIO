#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "scripts" / "build_provider_history_matrix_v3.py"
GATE = ROOT / "scripts" / "check_provider_non_regression_v1.py"
HISTORY_WF = ROOT / ".github" / "workflows" / "provider-history-matrix.yml"
NONREG_WF = ROOT / ".github" / "workflows" / "provider-non-regression.yml"
OWNERSHIP = ROOT / "tests" / "provider_v3_workflow_ownership_test.py"

for path in (V3, GATE, HISTORY_WF, NONREG_WF, OWNERSHIP):
    assert path.exists(), f"missing anti-regression contract file: {path.relative_to(ROOT)}"

v3 = V3.read_text(encoding="utf-8")
gate = GATE.read_text(encoding="utf-8")
history = HISTORY_WF.read_text(encoding="utf-8")
nonreg = NONREG_WF.read_text(encoding="utf-8")
ownership = OWNERSHIP.read_text(encoding="utf-8")

# Four exact checkpoints. A newer/current result must never fill an older hole.
for token in ('"5.21.0"', '"5.21.16"', '"5.21.36"'):
    assert token in v3, f"V3 historical ledger lost checkpoint {token}"
assert '"crossVersionFallbackAllowed": False' in v3
assert '"historicalGreenMayBecomeUnknownSilently": False' in v3
assert "historical_lanes = verified_lanes(row.get(\"historical52136\") or {})" in v3

# Publication gate extends the floor release after release: exact 5.21.36 proof
# plus the accepted baseline quick-yield from the PR/base commit.
assert 'git_json(base_ref, "provider-v3-quick-yield.json")' in gate
assert "required_lanes = historical_specific | rolling" in gate
assert "historical_positive_without_candidate_verified_lane" in gate
assert "semantic_capability_regression" in gate
assert "historical_hls_m3u8_regression" in gate
assert "--candidate-gate" in gate
assert "--all" in gate

# Shared Core/runtime/workflow changes are portfolio changes and must prove all 96.
for token in (
    '"core/"',
    '"lego/"',
    '"runtime/"',
    '"scripts/build_provider_"',
    '"scripts/materialize_provider_"',
    '".github/workflows/"',
):
    assert token in gate, f"global non-regression scope lost shared path {token}"
assert "if shared:" in gate and "return ids, changed, True" in gate

# V3 is the authoritative historical builder. V2 can remain an internal input,
# but the workflow may not publish V2 directly as its final authority.
assert "build_provider_history_matrix_v3.py" in history
assert "python scripts/build_provider_history_matrix_v3.py" in history
assert "python scripts/build_provider_history_matrix_v2.py\n" not in history

# A dedicated required proof workflow must run both ledger and live candidate gate.
for token in (
    "python scripts/build_provider_history_matrix_v3.py",
    "python scripts/check_provider_non_regression_v1.py",
    "python scripts/audit_provider_quick_yield.py",
    "--candidate-gate",
    "provider-v3-quick-yield.json",
    "provider-non-regression-gate.json",
):
    assert token in nonreg, f"provider non-regression workflow missing {token}"
assert "workbench/systemic-recovery-20260909" in nonreg
assert "pull_request:" in nonreg

# The canonical architecture ownership test must itself guard this workflow so a
# later cleanup cannot silently delete the gate.
assert "provider-non-regression.yml" in ownership
assert "check_provider_non_regression_v1.py" in ownership

print("provider non-regression contract passed: exact 4-state ledger + rolling candidate floor + 96 shared-core scope")

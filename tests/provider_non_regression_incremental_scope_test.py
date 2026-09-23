#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-non-regression.yml").read_text(encoding="utf-8")

assert "- name: Classify current provider-impact scope" in wf
assert "scripts/select_provider_materialization_scope.py" in wf
assert 'id: impact' in wf
assert 'mode="+str(d.get("mode") or "all")' in wf

for name in (
    "Materialize exact current provider candidate bytes",
    "Select rolling accepted baseline",
    "Seed candidate fixture memory from accepted baseline",
    "Run real rematerialized current-provider candidate census",
    "Enforce rolling non-regression floor",
):
    start=wf.index(f"- name: {name}")
    fragment=wf[start:start+260]
    assert "if: steps.impact.outputs.mode != 'none'" in fragment, (name,fragment)

assert "- name: Report control-plane-only non-regression no-op" in wf
assert "if: steps.impact.outputs.mode == 'none'" in wf
assert "FIELD_PROVIDER_NON_REGRESSION_NOOP provider_impact=none live_census_skipped=true" in wf

# Static contracts remain unconditional: control-plane changes still validate
# architecture/syntax without paying a live 42-provider network census.
static=wf.index("- name: Static anti-regression contracts")
impact=wf.index("- name: Classify current provider-impact scope")
materialize=wf.index("- name: Materialize exact current provider candidate bytes")
assert impact < static < materialize

print("Provider non-regression incremental scope contract passed")

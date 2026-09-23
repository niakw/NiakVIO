#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
workflow=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")

start=workflow.index("- name: Prove one canonical Learn Force repair implementation")
end=workflow.index("- name: Prepare integrated Repair WAF/network qualification",start)
block=workflow[start:end]

required=[
    "scripts/select_provider_materialization_scope.py",
    '--base HEAD^',
    '--head HEAD',
    'provider-preflight-scope.json',
    'if [ "$preflight_mode" = "none" ]',
    'FIELD_PROVIDER_PREFLIGHT_MATERIALIZATION mode=none skipped=true',
    'scripts/materialize_provider_v3_all.py',
    'FIELD_PROVIDER_PREFLIGHT_MATERIALIZATION mode=$preflight_mode skipped=false',
]
for needle in required:
    assert needle in block, needle

scope=block.index("scripts/select_provider_materialization_scope.py")
branch=block.index('if [ "$preflight_mode" = "none" ]')
full=block.index("scripts/materialize_provider_v3_all.py")
discovery=block.index("python tests/provider_discovery_v3_composition_test.py")
assert scope < branch < full < discovery
assert block.count("scripts/materialize_provider_v3_all.py") == 1

print("Brain preflight incremental materialization scope contract passed")

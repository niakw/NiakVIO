#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
workflow=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")

v5=workflow.index("python tests/brain_repair_experience_transfer_test.py")
materialize=workflow.index("python scripts/materialize_provider_v3_all.py")
discovery=workflow.index("python tests/provider_discovery_v3_composition_test.py")
assert v5 < materialize < discovery, (v5,materialize,discovery)
assert workflow.count("python tests/brain_repair_experience_transfer_test.py")==1

print("Brain preflight fail-fast ordering contract passed")

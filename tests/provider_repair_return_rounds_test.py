#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "run_provider_repair_pipeline_v6.py").read_text(encoding="utf-8")

for required in (
    'brain_rounds_per_batch = 1 if args.mode == "repair" else 3',
    '"--max-rounds-per-batch", str(brain_rounds_per_batch)',
    '"FIELD_PROVIDER_REPAIR_BRAIN_ROUNDS "',
):
    assert required in source, required

# Automatic Learning -> canonical Repair should execute the freshly learned
# hypothesis once. Explicit Force keeps the deeper three-round exploration.
assert 'args.mode == "repair"' in source
assert 'else 3' in source

print("provider canonical Repair return round contract passed")

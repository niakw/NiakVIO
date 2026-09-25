#!/usr/bin/env python3
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
source = (SCRIPTS / "run_provider_repair_pipeline_v6.py").read_text(encoding="utf-8")
spec = importlib.util.spec_from_file_location("provider_repair_pipeline_v6", SCRIPTS / "run_provider_repair_pipeline_v6.py")
assert spec and spec.loader
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)

for required in (
    'brain_rounds_per_batch = 1',
    '"--max-rounds-per-batch", str(brain_rounds_per_batch)',
    'brain_waves = 1 if args.mode == "repair" else 3',
    '"--waves", str(brain_waves)',
    'targeted_only=args.mode in {"repair", "force"}',
    '"FIELD_PROVIDER_REPAIR_BRAIN_ROUNDS "',
):
    assert required in source, required

# Automatic Learning -> canonical Repair should execute the freshly learned
# hypothesis once. Explicit Force keeps the deeper three-round exploration.
assert 'args.mode == "repair"' in source
assert 'else 3' in source

all_scope = {"mode": "all", "providers": [], "reasons": ["global:scripts/provider_base_store.py"]}
selected = pipeline.effective_repair_materialization_scope(
    all_scope,
    ["alpha", "beta"],
    targeted_only=True,
)
assert selected["mode"] == "providers", selected
assert selected["providers"] == ["alpha", "beta"], selected
assert selected["narrowed"] is True, selected

provider_scope = {"mode": "providers", "providers": ["alpha", "gamma"], "reasons": []}
selected = pipeline.effective_repair_materialization_scope(
    provider_scope,
    ["alpha", "beta"],
    targeted_only=True,
)
assert selected["providers"] == ["alpha"], selected

force_scope = pipeline.effective_repair_materialization_scope(
    all_scope,
    ["alpha"],
    targeted_only=True,
)
assert force_scope["mode"] == "providers", force_scope
assert force_scope["providers"] == ["alpha"], force_scope

print("provider canonical Repair return round/materialization contract passed")

#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"activate_bulk_offline_proven_providers.py"
spec=importlib.util.spec_from_file_location("bulk_offline_activation",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

request={"targetActive":{"global":60,"france":60}}
assert mod.activation_targets(request)=={"global":60,"france":60}

for bad in (
    {"targetActive":{"global":61,"france":60}},
    {"targetActive":{"global":60,"france":0}},
    {"targetActive":{"global":"x","france":60}},
):
    try:
        mod.activation_targets(bad)
    except RuntimeError:
        pass
    else:
        raise AssertionError(f"invalid target accepted: {bad}")

global_only={"projections":{"general":True,"vf":False}}
global_shared={"projections":{"general":True,"vf":True}}
france_only={"projections":{"general":False,"vf":True}}

assert mod.projection_impact("global",global_only)=={"global":1,"france":0}
assert mod.projection_impact("global",global_shared)=={"global":1,"france":1}
assert mod.projection_impact("france",france_only)=={"global":0,"france":1}

targets={"global":60,"france":60}
assert mod.capacity_block_reason({"global":59,"france":59},targets,{"global":1,"france":1}) is None
assert mod.capacity_block_reason({"global":59,"france":60},targets,{"global":1,"france":1})=="projection_target_capacity_reached:france"
assert mod.capacity_block_reason({"global":60,"france":59},targets,{"global":1,"france":0})=="projection_target_capacity_reached:global"

manifest={"scrapers":[
    {"id":"a","enabled":True},
    {"id":"b","enabled":False},
    {"id":"c"},
]}
assert mod.active_count(manifest)==2

# Concurrent Brain reactivation case: France already reached the request target.
# A shared Global candidate must be held rather than making the entire staged
# transaction overshoot and roll back after mutation.
current={"global":59,"france":60}
impact=mod.projection_impact("global",global_shared)
assert mod.capacity_block_reason(current,targets,impact)=="projection_target_capacity_reached:france"

# France-only candidate still fits when one France slot remains.
current={"global":60,"france":59}
impact=mod.projection_impact("france",france_only)
assert mod.capacity_block_reason(current,targets,impact) is None

print("bulk offline activation capacity contract passed: current projections are bounded before mutation")

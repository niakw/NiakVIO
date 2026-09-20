#!/usr/bin/env python3
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts/audit_provider_quick_yield.py"
spec=importlib.util.spec_from_file_location("audit_provider_quick_yield",path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

providers={f"provider-{i}" for i in range(100)}
parts=[mod._shard_filter(set(providers),4,i) for i in range(4)]
assert set().union(*parts)==providers
for i in range(4):
    for j in range(i+1,4):
        assert parts[i].isdisjoint(parts[j])
for p in providers:
    idx=mod._provider_shard(p,4)
    assert p in parts[idx]
print("Provider census deterministic sharding passed")

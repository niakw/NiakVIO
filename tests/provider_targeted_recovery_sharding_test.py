#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]

spec=importlib.util.spec_from_file_location("targeted",ROOT/"scripts/run_provider_targeted_recovery.py")
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

providers=[f"provider-{i}" for i in range(200)]
for count in (2,4,8,16):
    buckets=[0]*count
    for provider in providers:
        idx=mod.shard_for(provider,count)
        assert 0<=idx<count
        assert idx==mod.shard_for(provider,count)
        buckets[idx]+=1
    assert sum(buckets)==len(providers)
    assert max(buckets)-min(buckets)<30,(count,buckets)

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    shards=[]
    for idx,payload in enumerate([
        {
            "schemaVersion":3,"sourceCensusRunId":"55","shardCount":2,"shardIndex":0,
            "skippedEnvironmentProviders":["waf-a"],
            "providers":{"a":{"verifiedLanes":["movie"],"contradictions":0}},
            "groupResults":[{"groupId":"transport|html","repairScope":"transport","providers":["a"],"verifiedProviders":["a"],"playableProviders":["a"],"contradictionProviders":[]}],
        },
        {
            "schemaVersion":3,"sourceCensusRunId":"55","shardCount":2,"shardIndex":1,
            "skippedEnvironmentProviders":["waf-a"],
            "providers":{"b":{"verifiedLanes":[],"contradictions":1}},
            "groupResults":[{"groupId":"transport|html","repairScope":"transport","providers":["b"],"verifiedProviders":[],"playableProviders":[],"contradictionProviders":["b"]}],
        },
    ]):
        p=td/f"shard-{idx}.json"
        p.write_text(json.dumps(payload),encoding="utf-8")
        shards.append(p)
    out=td/"merged.json"
    subprocess.run([
        "python",str(ROOT/"scripts/merge_provider_targeted_recovery_shards.py"),
        *(str(p) for p in shards),"--output",str(out),"--run-id","99","--sha","deadbeef"
    ],check=True)
    merged=json.loads(out.read_text(encoding="utf-8"))

assert merged["shardsMerged"]==2
assert merged["selectedProviders"]==["a","b"]
assert merged["verifiedProviders"]==["a"]
assert merged["contradictionProviders"]==["b"]
assert merged["skippedEnvironmentProviders"]==["waf-a"]
assert merged["groupResults"][0]["providers"]==["a","b"]
print("Provider targeted recovery sharding passed")

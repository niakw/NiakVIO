#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/merge_provider_census_shards.py"

def row(pid,lane,playable=0,verified=0):
    return {"provider_id":pid,"semantic_type":lane,"status":"OK" if playable else "no_streams","debug_stage":"provider_returned_streams" if playable else "provider_network_zero_result","raw":playable,"playable":playable,"verified":verified,"contradictions":0,"sample_count":1}

base={"schema_version":6,"environment":"test","fixture_selection_policy":"test","max_samples_per_lane":4}
a={**base,"shard_count":2,"shard_index":0,"selected_providers":["a","c"],"provider_count":2,"rows":[row("a","movie",1,1),row("c","anime")]}
b={**base,"shard_count":2,"shard_index":1,"selected_providers":["b"],"provider_count":1,"rows":[row("b","tv",1,0)]}
with tempfile.TemporaryDirectory() as td:
    td=Path(td); ap=td/"a.json"; bp=td/"b.json"; out=td/"merged.json"
    ap.write_text(json.dumps(a),encoding="utf-8"); bp.write_text(json.dumps(b),encoding="utf-8")
    subprocess.run(["python",str(script),str(ap),str(bp),"--output",str(out)],check=True)
    value=json.loads(out.read_text(encoding="utf-8"))
assert value["provider_count"]==3
assert value["task_count"]==3
assert value["playable_providers"]==["a","b"]
assert value["verified_providers"]==["a"]
assert value["selected_providers"]==["a","b","c"]
assert len(value["shards"])==2
print("Provider census shard merge passed")

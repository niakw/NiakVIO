#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("targeted_waf_merge",ROOT/"scripts/merge_targeted_waf_refresh.py")
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

base={
 "schemaVersion":1,
 "providerFilter":[],
 "rows":[
  {"provider":"keep","lane":"movie","outcome":"browser_content_reached"},
  {"provider":"target","lane":"movie","outcome":"browser_timeout"},
 ],
 "residentialProviderReplay":{
  "available":True,
  "rows":[
   {"provider":"keep","lane":"movie","raw":1,"playable":1,"verified":1,"contradictions":0},
   {"provider":"target","lane":"movie","raw":0,"playable":0,"verified":0,"contradictions":0},
  ],
 }
}
refresh={
 "schemaVersion":1,
 "providerFilter":["target"],
 "rows":[{"provider":"target","lane":"movie","outcome":"browser_content_reached"}],
 "residentialProviderReplay":{
  "available":True,
  "rows":[{"provider":"target","lane":"movie","raw":2,"playable":1,"verified":1,"contradictions":0}],
 }
}
out=mod.merge(base,refresh,{"target"})
by={(r["provider"],r["lane"]):r for r in out["rows"]}
assert by[("keep","movie")]["outcome"]=="browser_content_reached"
assert by[("target","movie")]["outcome"]=="browser_content_reached"
assert out["lastRefreshProviderFilter"]==["target"]
assert out["providerFilter"]==[]
replay=out["residentialProviderReplay"]
rby={(r["provider"],r["lane"]):r for r in replay["rows"]}
assert rby[("keep","movie")]["verified"]==1
assert rby[("target","movie")]["raw"]==2
assert replay["providers"]==["keep","target"]
assert replay["playableProviders"]==["keep","target"]
assert replay["verifiedProviders"]==["keep","target"]
print("targeted WAF ledger merge contract passed")

#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/build_provider_repair_batch_plan.py"

status={
  "runId":123,
  "triggerSha":"abc",
  "providers":[
    {"provider":"a","status":"CHAIN REACHED","brainCheckRequired":True,"declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_zero_result","evidenceDepth":["movie=chain_reached"]},
    {"provider":"b","status":"CHAIN REACHED","brainCheckRequired":True,"declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_zero_result","evidenceDepth":["movie=chain_reached"]},
    {"provider":"c","status":"PROVIDER WAF/ANTIBOT","brainCheckRequired":True,"declaredLanes":["anime"],"currentVerifiedLanes":[],"dominantIssue":"provider_waf_challenge","evidenceDepth":["anime=none"]},
    {"provider":"green","status":"FULL OK","brainCheckRequired":False,"declaredLanes":["movie"],"currentVerifiedLanes":["movie"],"dominantIssue":"","evidenceDepth":[]},
  ]
}
overrides={
  "provider_patches":{
    "a":{"source_runtime_family":"catalogue-html-embed"},
    "b":{"source_runtime_family":"catalogue-html-embed"},
    "c":{"source_runtime_family":"dle-html"},
  },
  "provider_capabilities":{
    "a":{"strategy":"html_scraper"},
    "b":{"strategy":"html_scraper"},
    "c":{"strategy":"html_scraper"},
  }
}
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    sp=td/"status.json"; op=td/"overrides.json"; out=td/"plan.json"
    sp.write_text(json.dumps(status),encoding="utf-8")
    op.write_text(json.dumps(overrides),encoding="utf-8")
    subprocess.run(["python",str(script),"--status",str(sp),"--overrides",str(op),"--output",str(out)],check=True)
    plan=json.loads(out.read_text(encoding="utf-8"))

assert plan["unresolvedProviderCount"]==3
assert plan["groupCount"]==2
groups={row["repairScope"]:row for row in plan["groups"]}
assert groups["terminal-extraction"]["providers"]==["a","b"]
assert groups["terminal-extraction"]["providerLocalFallback"]=="only-after-shared-profile-failure"
assert groups["environment"]["providers"]==["c"]
print("Provider repair batch plan grouping passed")

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
    {"provider":"c","status":"HARNESS/ENV BLOCKED","brainCheckRequired":True,"declaredLanes":["anime"],"currentVerifiedLanes":[],"dominantIssue":"provider_waf_challenge","evidenceDepth":["anime=none"],"harnessTransportClass":"residential-exit-all-challenged"},
    {"provider":"d","status":"HARNESS MISMATCH","brainCheckRequired":True,"declaredLanes":["anime"],"currentVerifiedLanes":[],"dominantIssue":"provider_waf_challenge","evidenceDepth":["anime=lookup_only"],"harnessTransportClass":"browser-profile-only"},
    {"provider":"e","status":"PROVIDER NETWORK BLOCKED","brainCheckRequired":True,"declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_http_error","evidenceDepth":["movie=lookup_only"]},
    {"provider":"f","status":"PROVIDER NETWORK BLOCKED","brainCheckRequired":True,"declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_exception","evidenceDepth":["movie=none"]},
    {"provider":"green","status":"FULL OK","brainCheckRequired":False,"declaredLanes":["movie"],"currentVerifiedLanes":["movie"],"dominantIssue":"","evidenceDepth":[]},
  ]
}
overrides={
  "provider_patches":{
    "a":{"source_runtime_family":"catalogue-html-embed"},
    "b":{"source_runtime_family":"catalogue-html-embed"},
    "c":{"source_runtime_family":"dle-html"},
    "d":{"source_runtime_family":"dle-html"},
    "e":{"source_runtime_family":"site-html"},
    "f":{"source_runtime_family":"alternate-html"},
  },
  "provider_capabilities":{
    "a":{"strategy":"html_scraper"},
    "b":{"strategy":"html_scraper"},
    "c":{"strategy":"html_scraper"},
    "d":{"strategy":"html_scraper"},
    "e":{"strategy":"html_scraper"},
    "f":{"strategy":"html_scraper"},
  }
}
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    sp=td/"status.json"; op=td/"overrides.json"; out=td/"plan.json"
    sp.write_text(json.dumps(status),encoding="utf-8")
    op.write_text(json.dumps(overrides),encoding="utf-8")
    subprocess.run(["python",str(script),"--status",str(sp),"--overrides",str(op),"--output",str(out)],check=True)
    plan=json.loads(out.read_text(encoding="utf-8"))

assert plan["unresolvedProviderCount"]==6
assert plan["groupCount"]==4
groups={row["repairScope"]:row for row in plan["groups"] if row["repairScope"]!="harness-compatibility"}
harness={row["transportSignature"]:row for row in plan["groups"] if row["repairScope"]=="harness-compatibility"}
assert groups["terminal-extraction"]["providers"]==["a","b"]
assert groups["terminal-extraction"]["providerLocalFallback"]=="only-after-shared-profile-failure"
assert harness["residential-exit-all-challenged"]["providers"]==["c"]
assert harness["browser-profile-only"]["providers"]==["d"]
assert harness["residential-exit-all-challenged"]["harnessTransportClasses"]==["residential-exit-all-challenged"]
assert harness["browser-profile-only"]["harnessTransportClasses"]==["browser-profile-only"]
assert groups["transport"]["providers"]==["e","f"]
assert groups["transport"]["evidenceDepths"]==["lookup","none"]
assert groups["transport"]["dominantIssues"]==["network_exception","network_http_error"]
print("Provider repair batch plan grouping passed")

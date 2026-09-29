#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/refine_provider_repair_batches.py"

plan={
  "sourceRunId":"10",
  "groups":[
    {"groupId":"route|html|lookup|zero","repairScope":"route-to-terminal","capabilityStrategy":"html_scraper","transportSignature":"browser-profile-only","providers":["a","b","c","d","e"]}
  ]
}
verdict={
  "runId":11,
  "providers":{
    "a":{"debugStages":{"movie":"provider_network_zero_result"},"network":{"movie":[{"host":"site.example","path":"/search","method":"GET","status":200}]}},
    "b":{"debugStages":{"movie":"provider_network_zero_result"},"network":{"movie":[{"host":"site.example","path":"/search","method":"GET","status":200}]}},
    "c":{"debugStages":{"movie":"provider_network_zero_result"},"network":{"movie":[{"host":"api.example","path":"/map/157336","method":"GET","status":200}]}},
    "d":{"debugStages":{"movie":"provider_waf_challenge"},"network":{"movie":[{"host":"blocked.example","path":"/search","method":"GET","status":403}]}},
    "e":{"debugStages":{"movie":"provider_waf_challenge"},"network":{"movie":[{"host":"blocked.example","path":"/search","method":"GET","status":403}]}}
  }
}
status={"targetedTransportBlockedQueue":["d"]}
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    pp=td/"plan.json"; vp=td/"verdict.json"; sp=td/"status.json"; out=td/"out.json"
    pp.write_text(json.dumps(plan),encoding="utf-8")
    vp.write_text(json.dumps(verdict),encoding="utf-8")
    sp.write_text(json.dumps(status),encoding="utf-8")
    subprocess.run([sys.executable,str(script),"--plan",str(pp),"--verdict",str(vp),"--status",str(sp),"--output",str(out)],check=True)
    value=json.loads(out.read_text(encoding="utf-8"))
assert value["sourceRunId"]=="10"
assert value["groupCount"]==4
groups=sorted(value["groups"],key=lambda x:-x["providerCount"])
assert groups[0]["providers"]==["a","b"]
assert groups[0]["splitReason"]=="observed-signature-divergence"
assert groups[0]["transportSignature"]=="browser-profile-only"
assert groups[1]["providers"] in (["c"],["d"])
by_provider={tuple(group["providers"]):group for group in value["groups"]}
assert by_provider[("c",)]["repairScope"]=="route-to-terminal"
assert by_provider[("d",)]["repairScope"]=="harness-compatibility"
assert by_provider[("d",)]["transportSignature"]=="targeted-provider-waf-challenge"
assert by_provider[("e",)]["repairScope"]=="route-to-terminal"
assert by_provider[("e",)]["transportSignature"]=="browser-profile-only"
print("Provider repair batch refinement passed")

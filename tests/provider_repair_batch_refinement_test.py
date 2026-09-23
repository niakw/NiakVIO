#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/refine_provider_repair_batches.py"

plan={
  "sourceRunId":"10",
  "groups":[
    {"groupId":"route|html|lookup|zero","repairScope":"route-to-terminal","capabilityStrategy":"html_scraper","transportSignature":"browser-profile-only","providers":["a","b","c"]}
  ]
}
verdict={
  "runId":11,
  "providers":{
    "a":{"debugStages":{"movie":"provider_network_zero_result"},"network":{"movie":[{"host":"site.example","path":"/search","method":"GET","status":200}]}},
    "b":{"debugStages":{"movie":"provider_network_zero_result"},"network":{"movie":[{"host":"site.example","path":"/search","method":"GET","status":200}]}},
    "c":{"debugStages":{"movie":"provider_network_zero_result"},"network":{"movie":[{"host":"api.example","path":"/map/157336","method":"GET","status":200}]}}
  }
}
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    pp=td/"plan.json"; vp=td/"verdict.json"; out=td/"out.json"
    pp.write_text(json.dumps(plan),encoding="utf-8")
    vp.write_text(json.dumps(verdict),encoding="utf-8")
    subprocess.run(["python",str(script),"--plan",str(pp),"--verdict",str(vp),"--output",str(out)],check=True)
    value=json.loads(out.read_text(encoding="utf-8"))
assert value["sourceRunId"]=="10"
assert value["groupCount"]==2
groups=sorted(value["groups"],key=lambda x:-x["providerCount"])
assert groups[0]["providers"]==["a","b"]
assert groups[0]["splitReason"]=="observed-signature-divergence"
assert groups[0]["transportSignature"]=="browser-profile-only"
assert groups[1]["providers"]==["c"]
print("Provider repair batch refinement passed")

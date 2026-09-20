#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/run_provider_repair_batch.py"

plan={
  "sourceRunId":"42",
  "groups":[
    {"groupId":"terminal|html|chain|zero","repairScope":"terminal-extraction","providers":["a","b"]},
    {"groupId":"environment|any|none|waf","repairScope":"environment","providers":["c"]},
    {"groupId":"route|html|lookup|zero","repairScope":"route-to-terminal","providers":["b","d"]},
  ]
}
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    pp=td/"plan.json"; out=td/"out.json"
    pp.write_text(json.dumps(plan),encoding="utf-8")
    subprocess.run([
        "python",str(script),"--plan",str(pp),
        "--repair-scope","terminal-extraction,route-to-terminal",
        "--output",str(out),"--dry-run"
    ],check=True)
    value=json.loads(out.read_text(encoding="utf-8"))
assert value["providerCount"]==3
assert value["providers"]==["a","b","d"]
assert len(value["selectedGroupIds"])==2
print("Provider repair batch runner selection passed")

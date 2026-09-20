#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/stage_provider_batch.py"

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    req=td/"batch.json"; out=td/"summary.json"
    req.write_text(json.dumps({"providers":[
        {
            "id":"bulk-scale-contract-provider-zz999",
            "name":"Bulk Scale Contract Provider",
            "types":["movie","tv"],
            "languages":["en"],
            "strategy":"mixed_embed_resolver",
            "direct":"https://example.invalid"
        }
    ]}),encoding="utf-8")
    subprocess.run([
        "python",str(script),"--request",str(req),"--output",str(out),"--dry-run"
    ],cwd=ROOT,check=True)
    value=json.loads(out.read_text(encoding="utf-8"))

assert value["providerCount"]==1
assert value["newProviderCount"]==1
assert value["mode"]=="dry-run"
assert value["networkDiscoveryExecuted"] is False
assert value["nativeLabExecuted"] is False
assert value["activationAttempted"] is False
assert value["strategies"]=={"mixed_embed_resolver":1}
assert value["declaredTypeCounts"]=={"movie":1,"tv":1}
print("Bulk provider onboarding dry-run contract passed")

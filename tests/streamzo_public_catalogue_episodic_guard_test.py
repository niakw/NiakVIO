#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/streamzo_public_catalogue_v2.py"

spec = importlib.util.spec_from_file_location("streamzo_public_catalogue_v2", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = "module.exports={getStreams:async()=>[]};\n"
patched = module.apply(source, {"base_url": "https://streamzo.fr", "provider_name": "StreamZo"})

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_text(patched, encoding="utf-8")
    runner.write_text(
        "global.__calls=0;\n"
        "global.fetch=async function(){global.__calls++;throw new Error('episodic fallback must not reach film recovery');};\n"
        "const p=require(" + json.dumps(str(provider)) + ");\n"
        "Promise.resolve(p.getStreams('280049','anime',1,1)).then(v=>{"
        "console.log(JSON.stringify({rows:Array.isArray(v)?v.length:-1,calls:global.__calls}));"
        "}).catch(e=>{console.error(e);process.exit(1)});\n",
        encoding="utf-8",
    )
    result = subprocess.run(["node", str(runner)], text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip())
    assert payload == {"rows": 0, "calls": 0}, payload

assert 'q.mediaType==="tv"||q.mediaType==="anime"' in patched
assert 'Number(q.season)>0&&Number(q.episode)>0' in patched
print("streamzo episodic fallback guard tests passed")

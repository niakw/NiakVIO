#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/vostfree_dle_uqload_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["vostfree"]

assert "NIAKVIO_VOSTFREE_DLE_UQLOAD_RUNTIME_V1" in src
assert 'var semantic=s((obj&&obj.semanticType)||ctx.semanticType||"").toLowerCase();' in src
assert 'if(semantic==="anime"||(type==="tv"&&!semantic))type="anime";' in src
assert 'if(type!=="anime")return null;' in src
assert 'c.site+"/index.php?do=search"' in src
assert 'action_select_season' not in src
assert 'provider:"vostfree",resolve:resolve' in src
assert r'video\.sibnet\.ru' in src
assert r'https?:\/\/video\.sibnet\.ru\/' in src
assert r'https?:\\/\\/video\\.sibnet\\.ru' not in src
assert 'function sibnetEmbed' in src
assert 'function sibnetMedia' in src
assert 'Vostfree | Sibnet' in src
assert "api_recipe" not in ov
assert ov["search_request_plan"][0]["route"]=="/index.php"
assert ov["search_request_plan"][0]["requestSpec"]["method"]=="POST"
assert ov["search_request_plan"][0]["requestSpec"]["body"]["story"]=="{query}"

print("Vostfree anime TV transport contract passed")


# Parse the exact generated JavaScript so Python/raw-string escaping regressions
# cannot pass a text-only contract again.
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("niakvio_vostfree_runtime_test",ROOT/"scripts/provider_patches/vostfree_dle_uqload_runtime_v1.py")
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
wrapper=mod.WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps({
    "site":"https://ipv4.vostfree.ws",
    "ua":"NiakVIO-Test",
},separators=(",",":")))
with tempfile.TemporaryDirectory() as td:
    probe=Path(td)/"vostfree-runtime.cjs"
    probe.write_text(wrapper,encoding="utf-8")
    subprocess.run(["node","--check",str(probe)],cwd=ROOT,check=True,capture_output=True,text=True)

print("Vostfree generated JavaScript syntax contract passed")

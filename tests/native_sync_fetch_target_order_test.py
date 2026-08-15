#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/native_sync_fetch_target_order_v1.py"
UPGRADE = ROOT / "scripts/apply_runtime_capability_upgrade_v4.py"

spec = importlib.util.spec_from_file_location("native_sync_fetch_target_order_v1", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Providers without the target-media resolver must remain byte-identical.
plain = "module.exports={getStreams:async()=>[]};\n"
assert module.apply(plain) == plain

scaffold = r'''
/* NUVIO_TV_TARGET_MEDIA_V4 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function hostname(u){try{return new URL(u).hostname.toLowerCase()}catch(_){return ""}}
function rejected(){return false}
async function resource(u,base,ref){return await g.fetch(u,{headers:base,referrer:ref})}
function proof(r){return r&&r.kind?r.kind:null}
function genericUrls(){return[]}
function normalizeRow(row){return row&&row.url?row:null}
function unique(rows){var out=[],seen={};rows.forEach(function(row){if(!row||!row.url||seen[row.url])return;seen[row.url]=1;out.push(row)});return out}
function compactRow(row,media){return{url:media.url,kind:media.kind,name:row.name||"x"}}
async function invoke(old,self,args){return await old.apply(self,args)}
'''
source = scaffold + module.OLD_RESOLVE + "\n" + module.OLD_TV_ROWS + r'''
module.exports={run:async function(){return tvRows(async function(){return [
 {name:"external-dead",url:"https://uqload.is/embed-dead.html",headers:{Referer:"https://streamzo.fr/interstellar"}},
 {name:"same-origin-empty",url:"https://streamzo.fr/embed/vidnest.fun/23254",headers:{Referer:"https://streamzo.fr/interstellar"}},
 {name:"same-origin-good",url:"https://streamzo.fr/embed/uqload.is/23254?src=https://uqload.is/embed-good.html",headers:{Referer:"https://streamzo.fr/interstellar"}}
]},null,arguments)}};
})(typeof globalThis!=="undefined"?globalThis:this,{maxDepth:5,maxCandidates:22,providerName:"StreamZo"});
'''

patched = module.apply(source)
assert patched != source
assert patched.count(module.MARKER) == 1
assert module.OLD_RESOLVE not in patched
assert module.OLD_TV_ROWS not in patched
assert module.NEW_RESOLVE in patched
assert module.NEW_TV_ROWS in patched
assert "function serialNativeTargetRuntime()" in patched
assert "function targetRank(u,ref)" in patched
assert "function orderedNativeRows(values)" in patched
assert module.apply(patched) == patched

# Reproduce the native-TV failure mode: an external player that must never be
# touched sits before two StreamZo first-party wrappers. The first same-origin
# wrapper has no media; the second proves HLS. TV must stop there, before the
# external fallback can consume the native bridge timeout.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_text(patched, encoding="utf-8")
    runner.write_text(
        "global.navigator={userAgent:'NuvioTV Android TV'};\n"
        "global.__NUVIO_TV_RUNTIME__=true;\n"
        "global.__native_fetch=function(){};\n"
        "global.__calls=[];\n"
        "global.fetch=async function(url){\n"
        "  url=String(url);global.__calls.push(url);\n"
        "  if(url.includes('uqload.is/embed-dead'))throw new Error('dead external fallback must not be reached');\n"
        "  if(url.includes('/embed/uqload.is/'))return {url:url,kind:'hls',type:'application/vnd.apple.mpegurl',headers:{}};\n"
        "  return {url:url,kind:null,type:'text/html',text:'',headers:{}};\n"
        "};\n"
        f"const p=require({json.dumps(str(provider))});\n"
        "p.run().then(rows=>console.log(JSON.stringify({calls:global.__calls,rows:rows}))).catch(e=>{console.error(e);process.exit(1)});\n",
        encoding="utf-8",
    )
    result = subprocess.run(["node", str(runner)], text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    value = json.loads(result.stdout.strip())
    assert value["calls"] == [
        "https://streamzo.fr/embed/vidnest.fun/23254",
        "https://streamzo.fr/embed/uqload.is/23254?src=https://uqload.is/embed-good.html",
    ], value
    assert len(value["rows"]) == 1, value
    assert value["rows"][0]["kind"] == "hls", value
    assert "/embed/uqload.is/" in value["rows"][0]["url"], value

# The repository-wide runtime upgrade must keep this traversal transform directly
# before the final safety wrapper for every HLS-capable provider.
upgrade = UPGRADE.read_text(encoding="utf-8")
assert 'TARGET_ORDER_PATCH = "scripts/provider_patches/native_sync_fetch_target_order_v1.py"' in upgrade
assert "scripts.append(TARGET_ORDER_PATCH)\n        scripts.append(RUNTIME_PATCH)" in upgrade
assert '"target_order_patch": TARGET_ORDER_PATCH' in upgrade

print("native synchronous target ordering tests passed")

#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))

subprocess.run([sys.executable, "scripts/upgrade_mugiwara_episode_failclosed_v2.py"], cwd=ROOT, check=True)
subprocess.run([sys.executable, "scripts/upgrade_manual_tv_live_regressions_v34.py"], cwd=ROOT, check=True)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


presentation = load(ROOT / "scripts/provider_patches/global_stream_presentation_v1.py", "presentation_v34")
sanitizer = load(ROOT / "scripts/provider_patches/stream_output_sanitizer_v8.py", "sanitizer_v8")

base = r'''
"use strict";
async function getStreams() {
  return [
    {name:"Example 1080P Hindi",title:"Example 1080P Hindi",quality:"720p",language:"VO",url:"https://good.example/video.mp4"},
    {name:"Example dead",title:"Example dead",quality:"480p",language:"VO",url:"https://dead.example/video.mp4"}
  ];
}
module.exports={getStreams};
'''

patched = presentation.apply(base, context={"provider_id": "moviebox"})
options = {
    "probe_all_urls": True,
    "probe_direct_media": True,
    "max_probes": 8,
    "probe_timeout_ms": 1200,
    "min_vod_duration_seconds": 60,
}
once = sanitizer.apply(patched, options=options, context={"provider_id": "moviebox"})
twice = sanitizer.apply(once, options=options, context={"provider_id": "moviebox"})
assert once == twice, "V8 is not byte-idempotent on identical reapplication"

runner = r'''
function headers(type){return{get:(key)=>String(key).toLowerCase()==="content-type"?type:""}}
global.fetch=async(url)=>{
  const u=String(url);
  if(u.includes("dead.example")) throw new Error("network dead");
  if(u.includes("good.example")){
    const bytes=new Uint8Array([0,0,0,24,102,116,121,112,105,115,111,109]);
    return{ok:true,status:200,url:u,headers:headers("video/mp4"),arrayBuffer:async()=>bytes.buffer};
  }
  throw new Error("unexpected fetch "+u);
};
const provider=require(process.argv[2]);
(async()=>{
  const rows=await provider.getStreams("157336","movie");
  if(rows.length!==1)throw new Error("strict V8 did not drop dead row: "+JSON.stringify(rows));
  const row=rows[0];
  if(row.quality!=="1080p")throw new Error("strongest quality evidence lost: "+JSON.stringify(row));
  if(row.language!=="Hindi")throw new Error("detailed language evidence lost: "+JSON.stringify(row));
  if(!/1080p/i.test(String(row.title||"")))throw new Error("normalized title missing recovered quality: "+JSON.stringify(row));
  console.log("MANUAL_TV_V34_RUNTIME_OK rows=1 quality="+row.quality+" language="+row.language);
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "provider.js"
    test = tmp_path / "test.js"
    provider.write_text(once, encoding="utf-8")
    test.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True, timeout=20)

provider_base = (ROOT / "scripts/provider_base_store.py").read_text(encoding="utf-8")
compositor = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
mugiwara = (ROOT / "scripts/provider_patches/mugiwarastream_packed_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_PROVIDER_ROUTE_MEDIA_COMPAT_V34" in provider_base
assert "_spv34RouteMediaCompatible(route, mediaType)" in provider_base
assert "stream_output_sanitizer_v8.py" in compositor
assert "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8" in compositor
assert "NIAKVIO_MUGIWARA_EPISODE_FAIL_CLOSED_V2" in mugiwara
assert 'if(q.type!=="movie")return[]' in mugiwara
print("manual TV live regressions V34/V8 contract passed")

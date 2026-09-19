#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_node(source: str, runner: str, timeout: int = 20) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        provider = root / "provider.js"
        test_js = root / "test.js"
        provider.write_text(source, encoding="utf-8")
        test_js.write_text(runner, encoding="utf-8")
        result = subprocess.run(
            ["node", str(test_js), str(provider)],
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        if result.returncode:
            raise AssertionError(result.stdout + "\n" + result.stderr)
        return result.stdout


media_source = (
    ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
).read_text(encoding="utf-8")
assert 'cfg.get("provider_timeout_ms", 25_000)' in media_source
assert 'cfg.get("tv_provider_timeout_ms", 25_000)' in media_source
assert "tmdb-data-contract-launch-gate-v33-25s-isolated-failfast" in media_source
assert '"fetchSliceMs"' in media_source
assert '"maxHardFailures"' in media_source

sanitizer = load(
    ROOT / "scripts/provider_patches/stream_output_sanitizer_v6.py",
    "manual_tv_sanitizer",
)
presentation = load(
    ROOT / "scripts/provider_patches/global_stream_presentation_v1.py",
    "manual_tv_presentation",
)
media = load(
    ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py",
    "manual_tv_media",
)

# Provider says 480p; verified HLS master says 1080p => Core exposes 1080p.
base = (
    'module.exports={getStreams:async()=>[{name:"Papadustream",title:"Papadustream",'
    'quality:"480p",url:"https://cdn.example/master.m3u8"}]};\n'
)
patched = sanitizer.apply(
    base,
    options={
        "probe_all_urls": True,
        "probe_direct_media": True,
        "max_probes": 8,
        "probe_timeout_ms": 1500,
        "min_vod_duration_seconds": 60,
    },
    context={"provider_id": "papadustream"},
)
quality_runner = r'''
const playlist="#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080\nhttps://cdn.example/1080.m3u8\n";
global.fetch=async u=>({
  ok:true,status:200,url:String(u),
  headers:{get:k=>String(k).toLowerCase()==="content-type"?"application/vnd.apple.mpegurl":""},
  arrayBuffer:async()=>new TextEncoder().encode(playlist).buffer
});
const p=require(process.argv[2]);
(async()=>{
  const rows=await p.getStreams();
  if(rows.length!==1||rows[0].quality!=="1080p")throw new Error(JSON.stringify(rows));
  console.log("QUALITY_OVERRIDE_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
assert "QUALITY_OVERRIDE_OK" in run_node(patched, quality_runner)

# Strict all-URL sanitizer: an HTTP 403 row must never reach Nuvio.
base_403 = (
    'module.exports={getStreams:async()=>[{name:"VidRock",title:"VidRock",'
    'quality:"720p",url:"https://cdn.example/forbidden.m3u8"}]};\n'
)
patched_403 = sanitizer.apply(
    base_403,
    options={
        "probe_all_urls": True,
        "probe_direct_media": True,
        "max_probes": 8,
        "probe_timeout_ms": 1000,
        "min_vod_duration_seconds": 60,
    },
    context={"provider_id": "vidrock"},
)
forbidden_runner = r'''
global.fetch=async u=>({
  ok:false,status:403,url:String(u),headers:{get:()=>"text/html"},
  arrayBuffer:async()=>new Uint8Array([60,104,116,109,108,62]).buffer
});
const p=require(process.argv[2]);
(async()=>{
  const rows=await p.getStreams();
  if(rows.length!==0)throw new Error("403 leaked "+JSON.stringify(rows));
  console.log("HTTP403_FAIL_CLOSED_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
assert "HTTP403_FAIL_CLOSED_OK" in run_node(patched_403, forbidden_runner)

# Uniform title + safe detailed language/dialect retention.
pbase = (
    'module.exports={getStreams:async()=>[{name:"Castle",title:"random",quality:"1080p",'
    'language:"hi",url:"https://cdn.example/file.mp4"}]};\n'
)
presented = presentation.apply(pbase, context={"provider_id": "castle"})
presentation_runner = r'''
const p=require(process.argv[2]);
(async()=>{
  const rows=await p.getStreams("not-a-tmdb-id","movie");
  const r=rows[0];
  if(r.language!=="Hindi")throw new Error("language "+JSON.stringify(r));
  if(!/1080p/.test(r.title)||!/Hindi/.test(r.title))throw new Error("title "+r.title);
  console.log("LANGUAGE_DETAIL_OK "+r.title);
})().catch(e=>{console.error(e);process.exit(1)});
'''
assert "LANGUAGE_DETAIL_OK" in run_node(presented, presentation_runner)

# Real navigation shape: A and B ignore AbortSignal forever, C owns the result.
mbase = r'''
"use strict";
async function getStreams(id){
  await fetch("https://provider.example/"+id+"/one");
  return [{url:"https://media.example/"+id+".mp4",title:"row-"+id}];
}
module.exports={getStreams};
'''
managed = media.apply(
    mbase,
    options={
        "semantic_types": ["movie"],
        "provider_timeout_ms": 25_000,
        "tv_provider_timeout_ms": 25_000,
        "fetch_slice_ms": 7_000,
        "max_hard_failures": 3,
        "supersede_settle_ms": 700,
    },
)
navigation_runner = r'''
const calls=[];
global.navigator={userAgent:"Nuvio TV Android"};
global.fetch=(url)=>{
  const u=String(url);calls.push(u);
  if(u.includes("/1/")||u.includes("/2/"))return new Promise(()=>{});
  return Promise.resolve({ok:true,status:200,url:u,headers:{get:()=>"video/mp4"},text:async()=>"ok",json:async()=>({})});
};
const p=require(process.argv[2]);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const a=p.getStreams("1","movie");await sleep(20);
  const b=p.getStreams("2","movie");await sleep(20);
  const started=Date.now();
  const c=p.getStreams("3","movie");
  const all=await Promise.race([
    Promise.all([a,b,c]),
    sleep(1800).then(()=>{throw new Error("navigation accumulation")})
  ]);
  if(Date.now()-started>=1500)throw new Error("supersession too slow");
  if(all[0].length||all[1].length)throw new Error("stale rows leaked "+JSON.stringify(all));
  if(!all[2].length||!String(all[2][0].url).includes("/3.mp4"))throw new Error("latest row missing "+JSON.stringify(all));
  if(calls.some(x=>x.includes("/1/two")||x.includes("/2/two")))throw new Error("stale fallback network leaked "+JSON.stringify(calls));
  console.log("NAVIGATION_ABC_OK "+JSON.stringify(calls));
})().catch(e=>{console.error(e);process.exit(1)});
'''
assert "NAVIGATION_ABC_OK" in run_node(managed, navigation_runner, timeout=8)

print("manual TV regression contract passed")

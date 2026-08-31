#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HLS_PATCH = ROOT / "scripts" / "provider_patches" / "hls_master_audio_preserver_v1.py"
SAFETY_PATCH = ROOT / "scripts" / "provider_patches" / "runtime_capability_media_safety_v4.py"

def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

hls_module = load_module(HLS_PATCH, "hls_master_audio_preserver")
safety_module = load_module(SAFETY_PATCH, "runtime_capability_media_safety")

BASE = "module.exports={getStreams:async()=>[{name:'x',url:'https://media.example/master.m3u8',type:'hls'}]};\n"


def patched(provider_id: str, source: str = BASE) -> str:
    safety = safety_module.apply(source, context={"provider_id": provider_id})
    return hls_module.apply(safety, context={"provider_id": provider_id})


future = patched("future-provider")
assert future.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1
assert '"implementationRevision":"field-safety-v7-stream-scoped-p2p-vod-duration"' in future
assert '"implementationRevision":"scoped-playback-context-v4"' not in future
assert '"durationIdentity":true' in future
assert '"strictPlayback":false' in future

netmirror = patched("netmirror")
assert '"durationIdentity":true' in netmirror
assert '"strictPlayback":false' in netmirror

# Provider identity never changes global safety defaults. Core may pass a
# declarative strict_playback capability option for a provider strategy.
moviebox = patched("moviebox")
assert '"durationIdentity":true' in moviebox
assert '"strictPlayback":false' in moviebox
moviebox_strict = safety_module.apply(
    BASE,
    options={"strict_playback": True, "duration_identity": True},
    context={"provider_id": "moviebox"},
)
moviebox_strict = hls_module.apply(
    moviebox_strict,
    options={"strict_playback": True, "duration_identity": True},
    context={"provider_id": "moviebox"},
)
assert '"durationIdentity":true' in moviebox_strict
assert '"strictPlayback":true' in moviebox_strict


def run_node(source: str, fetch_impl: str, expression: str) -> object:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(source, encoding="utf-8")
        runner.write_text(
            "global.TMDB_API_KEY=String(1);\n"
            "global.fetch=" + fetch_impl + ";\n"
            "const p=require(" + json.dumps(str(provider)) + ");\n"
            + expression
            + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["node", str(runner)], text=True, capture_output=True, check=False
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip())


# NetMirror field regression: the provider can label a foreign programme with
# the requested TMDB title. A clearly incompatible HLS duration must therefore
# be rejected at runtime before the player sees it.
wrong_duration_fetch = r"""async function(url){
  url=String(url);
  if(url.includes('api.themoviedb.org'))return {ok:true,status:200,json:async()=>({runtime:90}),headers:{get:()=> 'application/json'}};
  if(url.includes('media.example'))return {ok:true,status:200,url:url,text:async()=> '#EXTM3U\n#EXTINF:3940,\na.ts\n#EXTINF:3940,\nb.ts\n#EXTINF:3940,\nc.ts\n#EXT-X-ENDLIST\n',headers:{get:()=> 'application/vnd.apple.mpegurl'}};
  throw new Error('unexpected '+url);
}"""
value = run_node(
    netmirror,
    wrong_duration_fetch,
    "p.getStreams('123','movie',null,null).then(v=>console.log(JSON.stringify(v))).catch(e=>{console.error(e);process.exit(1)})",
)
assert value == [], value

# A compatible HLS duration remains available.
valid_duration_fetch = r"""async function(url){
  url=String(url);
  if(url.includes('api.themoviedb.org'))return {ok:true,status:200,json:async()=>({runtime:90}),headers:{get:()=> 'application/json'}};
  if(url.includes('media.example'))return {ok:true,status:200,url:url,text:async()=> '#EXTM3U\n#EXTINF:2700,\na.ts\n#EXTINF:2700,\nb.ts\n#EXT-X-ENDLIST\n',headers:{get:()=> 'application/vnd.apple.mpegurl'}};
  throw new Error('unexpected '+url);
}"""
value = run_node(
    netmirror,
    valid_duration_fetch,
    "p.getStreams('123','movie',null,null).then(v=>console.log(JSON.stringify(v))).catch(e=>{console.error(e);process.exit(1)})",
)
assert len(value) == 1, value

# MovieBox field regression: returned rows that answer 403 must not create a
# clickable stream that spins forever. Its runtime guard fails closed.
moviebox_direct_source = "module.exports={getStreams:async()=>[{name:'moviebox',url:'https://media.example/video.mp4',type:'mp4'}]};\n"
moviebox_direct = safety_module.apply(
    moviebox_direct_source,
    options={"strict_playback": True, "duration_identity": True},
    context={"provider_id": "moviebox"},
)
moviebox_direct = hls_module.apply(
    moviebox_direct,
    options={"strict_playback": True, "duration_identity": True},
    context={"provider_id": "moviebox"},
)
forbidden_fetch = r"""async function(url){
  return {ok:false,status:403,url:String(url),text:async()=>'',headers:{get:()=> 'text/plain'}};
}"""
value = run_node(
    moviebox_direct,
    forbidden_fetch,
    "p.getStreams('123','movie',null,null).then(v=>console.log(JSON.stringify(v))).catch(e=>{console.error(e);process.exit(1)})",
)
assert value == [], value

print("runtime media safety guard tests passed")

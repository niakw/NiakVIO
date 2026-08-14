#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "hls_master_audio_preserver_v1.py"

spec = importlib.util.spec_from_file_location("runtime_media_safety_patch", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = "module.exports={getStreams:async()=>[{name:'x',url:'https://media.example/master.m3u8',type:'hls'}]};\n"


def patched(provider_id: str, source: str = BASE) -> str:
    return module.apply(source, context={"provider_id": provider_id})


future = patched("future-provider")
assert "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1" in future
assert '"implementationRevision":"field-safety-v3-native-aware"' in future
assert '"durationIdentity":false' in future
assert '"strictPlayback":false' in future
assert 'if(typeof g.__native_fetch==="function")return true' not in future
assert "if(nativeRuntime)return {keep:true" in future

netmirror = patched("netmirror")
assert '"durationIdentity":true' in netmirror
moviebox = patched("moviebox")
assert '"strictPlayback":true' in moviebox


def run_node(source: str, fetch_impl: str, expression: str, prelude: str = "") -> object:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(source, encoding="utf-8")
        runner.write_text(
            prelude
            + "\nglobal.fetch=" + fetch_impl + ";\n"
            + "const p=require(" + json.dumps(str(provider)) + ");\n"
            + expression
            + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(runner)], text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip())


wrong_duration_fetch = r"""async function(url){
  url=String(url);
  if(url.includes('api.themoviedb.org'))return {ok:true,status:200,json:async()=>({runtime:90}),headers:{get:()=> 'application/json'}};
  if(url.includes('media.example'))return {ok:true,status:200,url:url,text:async()=> '#EXTM3U\n#EXTINF:3940,\na.ts\n#EXTINF:3940,\nb.ts\n#EXTINF:3940,\nc.ts\n',headers:{get:()=> 'application/vnd.apple.mpegurl'}};
  throw new Error('unexpected '+url);
}"""
value = run_node(
    netmirror,
    wrong_duration_fetch,
    "p.getStreams('123','movie',null,null).then(v=>console.log(JSON.stringify(v))).catch(e=>{console.error(e);process.exit(1)})",
)
assert value == [], value

valid_duration_fetch = r"""async function(url){
  url=String(url);
  if(url.includes('api.themoviedb.org'))return {ok:true,status:200,json:async()=>({runtime:90}),headers:{get:()=> 'application/json'}};
  if(url.includes('media.example'))return {ok:true,status:200,url:url,text:async()=> '#EXTM3U\n#EXTINF:2700,\na.ts\n#EXTINF:2700,\nb.ts\n',headers:{get:()=> 'application/vnd.apple.mpegurl'}};
  throw new Error('unexpected '+url);
}"""
value = run_node(
    netmirror,
    valid_duration_fetch,
    "p.getStreams('123','movie',null,null).then(v=>console.log(JSON.stringify(v))).catch(e=>{console.error(e);process.exit(1)})",
)
assert len(value) == 1, value

moviebox_direct = patched(
    "moviebox",
    "module.exports={getStreams:async()=>[{name:'moviebox',url:'https://media.example/video.mp4',type:'mp4'}]};\n",
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

# NuvioMobile/NuvioDesktop expose __native_fetch too. In those runtimes the
# host HTTP call is synchronous from QuickJS and a JS AbortSignal cannot bound
# it. The global safety layer must therefore NOT issue another HLS fetch.
native_stream = patched("streamzo")
value = run_node(
    native_stream,
    "async function(){global.__fetchCalls++;throw new Error('safety layer must not fetch on native clients')}",
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    prelude="global.__fetchCalls=0;global.__native_fetch=function(){throw new Error('native bridge should not be touched by post-result guard')};",
)
assert value == {"rows": 1, "calls": 0}, value

# Obvious web/embed pages remain fail-closed even on native clients, without a
# network request. This covers the field MovieBox YouTube-embed failure mode.
embed = patched(
    "future-provider",
    "module.exports={getStreams:async()=>[{name:'bad',url:'https://moviebox.yachts//www.youtube.com/embed/abc'}]};\n",
)
value = run_node(
    embed,
    "async function(){global.__fetchCalls++;throw new Error('must reject statically')}",
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    prelude="global.__fetchCalls=0;global.__native_fetch=function(){};",
)
assert value == {"rows": 0, "calls": 0}, value

print("runtime media safety guard tests passed")

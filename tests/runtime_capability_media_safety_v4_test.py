#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/runtime_capability_media_safety_v4.py"

# The native budget layers, synchronous-target traversal and final runtime
# capability guard form one engine stack. Keep their focused regression tests
# mandatory anywhere the v4 regression test is run (including permanent npm CI).
for companion in (
    "tests/native_catalogue_recovery_budget_test.py",
    "tests/native_hls_integrity_budget_test.py",
    "tests/native_sync_fetch_target_order_test.py",
):
    result = subprocess.run(
        [sys.executable, str(ROOT / companion)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

spec = importlib.util.spec_from_file_location("runtime_capability_media_safety_v4", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = "module.exports={getStreams:async()=>[{name:'x',url:'https://media.example/master.m3u8',type:'hls'}]};\n"


def patched(provider_id: str, source: str = BASE) -> str:
    return module.apply(source, context={"provider_id": provider_id})


def run_node(source: str, fetch_impl: str, expression: str, prelude: str = "") -> object:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(source, encoding="utf-8")
        runner.write_text(
            prelude + "\nglobal.fetch=" + fetch_impl + ";\n" +
            "const p=require(" + json.dumps(str(provider)) + ");\n" + expression + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(runner)], text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip())


streamzo = patched("streamzo")
assert streamzo.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1
assert '"implementationRevision":"field-safety-v6-core-repair-types"' in streamzo
policy = module._collision_policy()
assert policy["259544"]["expectedYear"] == 2025
assert 1996 in policy["259544"]["ambiguousReleaseYears"]
assert policy["760873"]["expectedYear"] == 2021

# Any old published wrapper is replaced, never stacked.
legacy = streamzo.replace('"implementationRevision":"field-safety-v6-core-repair-types"', '"implementationRevision":"field-safety-v2"')
upgraded = patched("streamzo", legacy)
assert upgraded.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1
assert '"implementationRevision":"field-safety-v6-core-repair-types"' in upgraded
assert '"implementationRevision":"field-safety-v2"' not in upgraded
assert patched("streamzo", upgraded) == upgraded

# Every official Nuvio native QuickJS host exposes __native_fetch. Because that
# bridge is synchronous in Desktop, Mobile and TV, the safety layer must not add
# a post-result media probe on any of those clients.
for user_agent in ("NuvioDesktop macOS", "NuvioMobile Android", "NuvioTV Android TV"):
    value = run_node(
        streamzo,
        "async function(){global.__fetchCalls++;throw new Error('must not probe from native safety layer')}",
        "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
        "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:" + json.dumps(user_agent) + "};",
    )
    assert value == {"rows": 1, "calls": 0}, (user_agent, value)

# Native TV still rejects obvious embeds statically without touching fetch.
tv_bad = patched("streamzo", "module.exports={getStreams:async()=>[{url:'https://host.test/embed/player'}]};\n")
value = run_node(
    tv_bad,
    "async function(){global.__fetchCalls++;throw new Error('must reject statically')}",
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 0, "calls": 0}, value

# 5.20.70 regression: known same-title remakes/collisions are now fail-closed in
# native runtimes. Wrong 1996 Nube must not appear for TMDB 259544 (2025 remake),
# and a row with no positive release discriminator is hidden rather than guessed.
for name in ("Hell Teacher Nube 1996 S01E01", "Hianime"):
    src = "module.exports={getStreams:async()=>[{name:" + json.dumps(name) + ",url:'https://media.example/nube.m3u8',type:'hls'}]};\n"
    value = run_node(
        patched("hianime", src),
        "async function(){global.__fetchCalls++;throw new Error('must not probe from native safety layer')}",
        "p.getStreams('259544','tv',1,1).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
        "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
    )
    assert value == {"rows": 0, "calls": 0}, (name, value)

# Positive release evidence remains usable without an extra native fetch.
correct_nube = patched(
    "hianime",
    "module.exports={getStreams:async()=>[{name:'The 99-Legged Bug S01E01',url:'https://media.example/nube-2025.m3u8',type:'hls'}]};\n",
)
value = run_node(
    correct_nube,
    "async function(){global.__fetchCalls++;throw new Error('must not probe from native safety layer')}",
    "p.getStreams('259544','tv',1,1).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 1, "calls": 0}, value

# Explicit episode contradictions are rejected globally, not only for the three
# curated collision fixtures.
wrong_episode = patched(
    "anikototv",
    "module.exports={getStreams:async()=>[{name:'Jujutsu Kaisen S01E02',url:'https://media.example/jjk.m3u8',type:'hls'}]};\n",
)
value = run_node(
    wrong_episode,
    "async function(){global.__fetchCalls++;throw new Error('must not probe from native safety layer')}",
    "p.getStreams('95479','tv',1,1).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 0, "calls": 0}, value

# Static identity must inspect every row, not just the bounded remote-probe head.
many_wrong = patched(
    "hianime",
    "module.exports={getStreams:async()=>Array.from({length:20},(_,i)=>({name:'Hell Teacher Nube 1996 S01E01 '+i,url:'https://media.example/'+i+'.m3u8',type:'hls'}))};\n",
)
value = run_node(
    many_wrong,
    "async function(){global.__fetchCalls++;throw new Error('must not probe from native safety layer')}",
    "p.getStreams('259544','tv',1,1).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 0, "calls": 0}, value

# Non-native/web-like runtime keeps bounded remote validation.
forbidden = r"""async function(url){global.__fetchCalls++;return {ok:false,status:403,url:String(url),text:async()=>'',headers:{get:()=> 'text/plain'}}}"""
value = run_node(
    patched("moviebox", "module.exports={getStreams:async()=>[{url:'https://media.example/video.mp4',type:'mp4'}]};\n"),
    forbidden,
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.navigator={userAgent:'web-like-test'};",
)
assert value["rows"] == 0 and value["calls"] >= 1, value


# Media-type compatibility is a capability adapter: the upstream call may receive
# tv while the Core keeps the original anime request as the identity contract.
alias_source = r"""
module.exports={getStreams:async function(id,type,season,episode){
  global.__seenType=type;
  return [{name:'Hell Mode S01E01',url:'https://media.example/hellmode.m3u8',type:'hls'}];
}};
"""
alias_patched = module.apply(
    alias_source,
    options={"request_type_aliases": {"anime": "tv"}, "capability_strategy": "mixed_embed_resolver"},
    context={"provider_id": "streamzo"},
)
value = run_node(
    alias_patched,
    "async function(){throw new Error('native path must not add remote media probes')}",
    "p.getStreams('280049','anime',1,1).then(v=>console.log(JSON.stringify({rows:v.length,seenType:global.__seenType}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 1, "seenType": "tv"}, value
assert '"requestTypeAliases":{"anime":"tv"}' in alias_patched
assert '"durationIdentity":true' in alias_patched


# Duration identity is a global Core invariant, not a provider exception.
# In a runtime where bounded media probing is allowed, an episodic request
# expected around 24 minutes must reject a terminal HLS around 93 minutes.
duration_fetch = r"""async function(url){
  global.__fetchCalls++;
  url=String(url);
  if(url.includes('api.themoviedb.org')) {
    return {ok:true,status:200,url,headers:{get:()=> 'application/json'},json:async()=>({runtime:24}),text:async()=>JSON.stringify({runtime:24})};
  }
  if(url.includes('master.m3u8')) {
    return {ok:true,status:200,url,headers:{get:()=> 'application/vnd.apple.mpegurl'},text:async()=> '#EXTM3U\n#EXTINF:2790,\na.ts\n#EXTINF:2790,\nb.ts\n'};
  }
  return {ok:false,status:404,url,headers:{get:()=> 'text/plain'},text:async()=>''};
}"""
value = run_node(
    module.apply(BASE, context={"provider_id": "generic-provider"}),
    duration_fetch,
    "p.getStreams('280049','anime',1,1).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.navigator={userAgent:'web-like-test'};",
)
assert value["rows"] == 0 and value["calls"] >= 2, value

print("runtime capability media safety v4 tests passed")

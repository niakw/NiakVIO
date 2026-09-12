#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts/provider_patches/runtime_capability_media_safety_v4.py"

# Native HLS behavior remains a focused companion of final media safety.
# Target traversal/order is now Core-owned and no legacy source-shape ordering
# patch is replayed during Provider v3 reconstruction.
for companion in (
    "tests/native_hls_integrity_budget_test.py",
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
assert '"implementationRevision":"field-safety-v9-correlated-player-fallback"' in streamzo
assert "routeIdentity(" not in streamzo
assert "wrong_release_year" not in streamzo
assert "season_episode_identity_mismatch" not in streamzo
assert "collisionFixtures" not in streamzo
# Any old published wrapper is replaced, never stacked.
legacy = streamzo.replace('"implementationRevision":"field-safety-v9-correlated-player-fallback"', '"implementationRevision":"field-safety-v2"')
upgraded = patched("streamzo", legacy)
assert upgraded.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1
assert '"implementationRevision":"field-safety-v9-correlated-player-fallback"' in upgraded
assert '"implementationRevision":"field-safety-v2"' not in upgraded
assert patched("streamzo", upgraded) == upgraded

# Every official Nuvio native QuickJS host exposes __native_fetch. Because that
# bridge is synchronous in Desktop, Mobile and TV, the safety layer must not add
# a post-result media probe on any of those clients.
for user_agent in ("NuvioDesktop macOS", "NuvioMobile Android", "NuvioTV Android TV"):
    value = run_node(
        streamzo,
        "async function(){global.__fetchCalls++;throw new Error('must not probe from native safety layer')}",
        "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
        "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:" + json.dumps(user_agent) + "};",
    )
    assert value == {"rows": 1, "calls": 0}, (user_agent, value)

# Native TV still rejects obvious embeds statically without touching fetch.
tv_bad = patched("streamzo", "module.exports={getStreams:async()=>[{url:'https://host.test/embed/player'}]};\n")
value = run_node(
    tv_bad,
    "async function(){global.__fetchCalls++;throw new Error('must reject statically')}",
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 0, "calls": 0}, value

# Exact proof-correlated player fallbacks pass media safety so the terminal
# sanitizer can arbitrate them. Native runtimes must not add a media probe.
for player_url in (
    "https://smoothpre.com/embed/abc123",
    "https://video.sibnet.ru/shell.php?videoid=12345",
):
    marked = patched(
        "generic-provider",
        "module.exports={getStreams:async()=>[{url:" + json.dumps(player_url) + ",__nuvioCorrelatedPlayerFallbackV1:{url:" + json.dumps(player_url) + "}}]};\n",
    )
    value = run_node(
        marked,
        "async function(){global.__fetchCalls++;throw new Error('native path must not probe correlated player fallback')}",
        "p.getStreams('95479','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),url:(Array.isArray(v)&&v[0]&&v[0].url)||'',proof:(Array.isArray(v)&&v[0]&&!!v[0].__nuvioCorrelatedPlayerFallbackV1),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
        "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
    )
    assert value == {"rows": 1, "url": player_url, "proof": True, "calls": 0}, (player_url, value)

# Unmarked or mismatched embed proof remains rejected.
for proof_url in ("", "https://smoothpre.com/embed/other"):
    marker = "" if not proof_url else ",__nuvioCorrelatedPlayerFallbackV1:{url:" + json.dumps(proof_url) + "}"
    source = "module.exports={getStreams:async()=>[{url:'https://smoothpre.com/embed/abc123'" + marker + "}]};\n"
    value = run_node(
        patched("generic-provider", source),
        "async function(){global.__fetchCalls++;throw new Error('must reject statically')}",
        "p.getStreams('95479','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
        "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
    )
    assert value == {"rows": 0, "calls": 0}, (proof_url, value)

# Explicit video-page policy stays stronger than the correlated-player exception.
youtube = "https://www.youtube.com/embed/abc123"
source = "module.exports={getStreams:async()=>[{url:" + json.dumps(youtube) + ",__nuvioCorrelatedPlayerFallbackV1:{url:" + json.dumps(youtube) + "}}]};\n"
value = run_node(
    patched("generic-provider", source),
    "async function(){global.__fetchCalls++;throw new Error('must reject statically')}",
    "p.getStreams('95479','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 0, "calls": 0}, value

# A mixed provider keeps normal media rows while P2P rows are rejected individually.
mixed_p2p = patched(
    "streamzo",
    "module.exports={getStreams:async()=>[{url:'magnet:?xt=urn:btih:abc',type:'torrent',infoHash:'abc'},{url:'https://media.example/ok.m3u8',type:'hls'}]};\n",
)
value = run_node(
    mixed_p2p,
    "async function(){global.__fetchCalls++;throw new Error('native path must not probe')}",
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),url:(Array.isArray(v)&&v.length>0&&v[0]!=null&&v[0].url!=null?v[0].url:null),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 1, "url": "https://media.example/ok.m3u8", "calls": 0}, value

# Non-native/web-like runtime keeps bounded remote validation.
forbidden = r"""async function(url){global.__fetchCalls++;return {ok:false,status:403,url:String(url),text:async()=>'',headers:{get:()=> 'text/plain'}}}"""
value = run_node(
    patched("moviebox", "module.exports={getStreams:async()=>[{url:'https://media.example/video.mp4',type:'mp4'}]};\n"),
    forbidden,
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
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
    "p.getStreams('280049','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),seenType:global.__seenType}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 1, "seenType": "tv"}, value
assert '"requestTypeAliases":{"anime":"tv"}' in alias_patched
assert '"durationIdentity":true' in alias_patched


# Duration identity is stream-scoped and only authoritative for complete VOD HLS.
# A live/sliding playlist without ENDLIST is a window, not the work duration.
live_duration_fetch = r"""async function(url){
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
    live_duration_fetch,
    "p.getStreams('280049','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.TMDB_API_KEY=String(1);global.navigator={userAgent:'web-like-test'};",
)
assert value["rows"] == 1 and value["calls"] >= 2, value

# The same implausible duration is a contradiction when ENDLIST proves VOD completeness.
vod_duration_fetch = live_duration_fetch.replace(
    "#EXTINF:2790,\\nb.ts\\n'",
    "#EXTINF:2790,\\nb.ts\\n#EXT-X-ENDLIST\\n'",
)
value = run_node(
    module.apply(BASE, context={"provider_id": "generic-provider"}),
    vod_duration_fetch,
    "p.getStreams('280049','anime',1,1).then(v=>console.log(JSON.stringify({rows:(Array.isArray(v)?v.length:0),calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.TMDB_API_KEY=String(1);global.navigator={userAgent:'web-like-test'};",
)
assert value["rows"] == 0 and value["calls"] >= 2, value

print("runtime capability media safety v4 tests passed")

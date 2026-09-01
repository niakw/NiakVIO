#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "stream_output_sanitizer_v6.py"

spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v6_direct", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    source = r'''
module.exports={getStreams:async function(){return [
  {name:"opaque-mp4",url:"https://media.example/token-mp4",headers:{"X-Legacy":"kept"}},
  {name:"opaque-hls",url:"https://media.example/token-hls"},
  {name:"missing-header-hls",url:"https://media.example/token-hls-missing"},
  {name:"opaque-mkv",url:"https://media.example/token-mkv"},
  {name:"html-embed",url:"https://media.example/embed/abc"},
  {name:"json-resolver",url:"https://media.example/api-resolver"},
  {name:"forbidden-403",url:"https://media.example/forbidden.mp4"},
  {name:"html-error",url:"https://media.example/not-media"},
  {name:"dns-inconclusive",url:"https://media.example/dns.mp4"},
  {name:"server-503-inconclusive",url:"https://media.example/server-503.mp4"}
]}};
'''
    patched = module.apply(
        source,
        options={
            "probe_direct_media": True,
            "probe_all_urls": True,
            "max_probes": 10,
            "probe_timeout_ms": 2000,
            "min_vod_duration_seconds": 0,
        },
    )
    assert '"implementationVersion":9' in patched
    assert patched.count("/* START NIAKVIO_FIX:CORE.STREAM_SANITIZER.V6 */") == 1
    assert "NUVIO_STREAM_OUTPUT_HLS_HTML_REPAIR_V7" not in patched
    assert "NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6" not in patched

    runner = r'''
const vm=require('vm');
const source=process.argv[2];
function makeResponse(url,type,bytes,disposition){
  let offset=0;
  return {
    ok:true,status:200,url,
    headers:{get:(key)=>{
      key=String(key).toLowerCase();
      if(key==='content-type')return type||'';
      if(key==='content-disposition')return disposition||'';
      return null;
    }},
    body:{getReader:()=>({
      read:async()=>{
        if(offset>=bytes.length)return {done:true,value:undefined};
        const end=Math.min(offset+7,bytes.length);
        const value=new Uint8Array(bytes.slice(offset,end));
        offset=end;
        return {done:false,value};
      },
      cancel:async()=>{}
    })}
  };
}
const enc=(text)=>Array.from(Buffer.from(text,'utf8'));
const responses={
  'https://media.example/token-mp4':()=>makeResponse('https://cdn.example/final/opaque','video/mp4',[0,0,0,24,102,116,121,112,1,2,3,4]),
  'https://media.example/token-hls':()=>makeResponse('https://cdn.example/final/hls-opaque','text/plain',enc('#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n')),
  'https://media.example/token-hls-missing':()=>makeResponse('https://cdn.example/final/no-header','text/plain',enc('#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nsegment-a.ts\n#EXT-X-ENDLIST\n')),
  'https://media.example/token-mkv':()=>makeResponse('https://cdn.example/final/download','application/octet-stream',[0x1a,0x45,0xdf,0xa3,1,2,3,4],'attachment; filename="movie.mkv"'),
  'https://media.example/embed/abc':()=>makeResponse('https://media.example/embed/abc','text/html',enc('<html><body><video><source src="/nested/master.m3u8"></video></body></html>')),
  'https://media.example/nested/master.m3u8':()=>makeResponse('https://media.example/nested/master.m3u8','application/vnd.apple.mpegurl',enc('#EXTM3U\n#EXT-X-TARGETDURATION:5\n#EXTINF:5,\nseg.ts\n#EXT-X-ENDLIST\n')),
  'https://media.example/api-resolver':()=>makeResponse('https://media.example/api-resolver','application/json',enc('{"file":"https://cdn.example/resolved/movie.mp4"}')),
  'https://cdn.example/resolved/movie.mp4':()=>makeResponse('https://cdn.example/resolved/movie.mp4','video/mp4',[0,0,0,24,102,116,121,112,5,6,7,8]),
  'https://media.example/forbidden.mp4':()=>({ok:false,status:403,url:'https://media.example/forbidden.mp4',headers:{get:()=>''},body:{getReader:()=>({read:async()=>({done:true}),cancel:async()=>{}})}}),
  'https://media.example/not-media':()=>makeResponse('https://media.example/not-media','text/html',enc('<html><body>error</body></html>')),
  'https://media.example/dns.mp4':()=>{throw new Error('dns lookup failed')},
  'https://media.example/server-503.mp4':()=>({ok:false,status:503,url:'https://media.example/server-503.mp4',headers:{get:()=>''},body:{getReader:()=>({read:async()=>({done:true}),cancel:async()=>{}})}})
};
const calls=[];
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,encodeURIComponent,
  fetch:async(url,init)=>{calls.push({url:String(url),headers:init&&init.headers||{}});const factory=responses[String(url)];if(!factory)throw new Error('unexpected '+url);return factory();}
};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie'})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(error=>{console.error(error);process.exit(1)});
'''

    with tempfile.TemporaryDirectory() as directory:
        runner_path = Path(directory) / "sanitizer-direct-test.cjs"
        runner_path.write_text(runner, encoding="utf-8")
        process = subprocess.run(
            ["node", str(runner_path), patched],
            capture_output=True,
            text=True,
            timeout=20,
        )
    assert process.returncode == 0, process.stderr
    payload = json.loads(process.stdout.strip())
    rows = payload["rows"]
    calls = payload["calls"]
    assert len(rows) == 8, rows
    by_name = {row["name"]: row for row in rows}

    assert by_name["opaque-mp4"]["url"] == "https://cdn.example/final/opaque"
    assert by_name["opaque-mp4"]["isDirect"] is True
    assert by_name["opaque-mp4"]["behaviorHints"]["proxyHeaders"]["request"]["X-Legacy"] == "kept"

    assert by_name["opaque-hls"]["url"] == "https://cdn.example/final/hls-opaque"
    assert by_name["opaque-hls"]["isDirect"] is True

    repaired = by_name["missing-header-hls"]
    assert repaired["url"].startswith("data:application/vnd.apple.mpegurl;charset=utf-8,%23EXTM3U%0A"), repaired
    assert repaired["type"] == "hls"
    assert repaired["isDirect"] is True
    assert "https%3A%2F%2Fcdn.example%2Ffinal%2Fsegment-a.ts" in repaired["url"], repaired["url"]

    assert by_name["opaque-mkv"]["url"] == "https://cdn.example/final/download"
    assert by_name["opaque-mkv"]["isDirect"] is True

    embed = by_name["html-embed"]
    assert embed["url"] == "https://media.example/nested/master.m3u8", embed
    embed_headers = embed["behaviorHints"]["proxyHeaders"]["request"]
    assert embed_headers["Referer"] == "https://media.example/embed/abc"
    assert embed_headers["Origin"] == "https://media.example"
    nested_call = next(call for call in calls if call["url"] == "https://media.example/nested/master.m3u8")
    assert nested_call["headers"]["Referer"] == "https://media.example/embed/abc"
    assert nested_call["headers"]["Origin"] == "https://media.example"

    resolved = by_name["json-resolver"]
    assert resolved["url"] == "https://cdn.example/resolved/movie.mp4", resolved
    assert resolved["isDirect"] is True

    assert "forbidden-403" not in by_name
    assert "html-error" not in by_name
    assert by_name["dns-inconclusive"]["url"] == "https://media.example/dns.mp4"
    assert by_name["server-503-inconclusive"]["url"] == "https://media.example/server-503.mp4"

    # All invalid streams must collapse to an empty array; no dead row may leak.
    all_bad_source = r'''
module.exports={getStreams:async function(){return [
  {name:"bad403",url:"https://media.example/forbidden.mp4"},
  {name:"badhtml",url:"https://media.example/not-media"}
]}};
'''
    all_bad_patched = module.apply(
        all_bad_source,
        options={
            "probe_direct_media": True,
            "probe_all_urls": True,
            "max_probes": 8,
            "probe_timeout_ms": 2000,
            "min_vod_duration_seconds": 0,
        },
    )
    with tempfile.TemporaryDirectory() as directory:
        runner_path = Path(directory) / "sanitizer-all-bad-test.cjs"
        runner_path.write_text(runner, encoding="utf-8")
        process = subprocess.run(
            ["node", str(runner_path), all_bad_patched],
            capture_output=True,
            text=True,
            timeout=20,
        )
    assert process.returncode == 0, process.stderr
    all_bad_payload = json.loads(process.stdout.strip())
    assert all_bad_payload["rows"] == [], all_bad_payload["rows"]

    # Native runtime: probes are serialized. Once the provider-wide deadline is
    # consumed by the first synchronous-host-like request, no second network call
    # is started. A conclusive 403 is removed; the unprobed-after-deadline row is
    # kept as transport-uncertain rather than guessed dead.
    native_source = r'''
module.exports={getStreams:async function(){return [
  {name:"first-403",url:"https://native.example/first.mp4"},
  {name:"second-uncertain",url:"https://native.example/second.mp4"}
]}};
'''
    native_patched = module.apply(
        native_source,
        options={
            "probe_direct_media": True,
            "probe_all_urls": True,
            "max_probes": 2,
            "probe_timeout_ms": 2000,
            "min_vod_duration_seconds": 0,
        },
    )
    native_runner = r'''
const vm=require('vm');
const source=process.argv[2];
let calls=0,active=0,maxActive=0;
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,encodeURIComponent};
sandbox.globalThis=sandbox;
sandbox.__native_fetch=function(){};
sandbox.__nuvioProviderDeadlineMs=Date.now()+5;
sandbox.fetch=async function(url){
  calls++;active++;maxActive=Math.max(maxActive,active);
  await new Promise(resolve=>setTimeout(resolve,20));
  active--;
  const u=String(url);
  if(u.indexOf('/first.mp4')>=0)return {ok:false,status:403,url:u,headers:{get:()=>''},body:{getReader:()=>({read:async()=>({done:true}),cancel:async()=>{}})}};
  throw new Error('second native fetch must not start after provider deadline');
};
vm.runInNewContext(source,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie'}).then(rows=>{
  console.log(JSON.stringify({rows,calls,maxActive}));
}).catch(error=>{console.error(error);process.exit(1)});
'''
    with tempfile.TemporaryDirectory() as directory:
        runner_path = Path(directory) / "sanitizer-native-deadline-test.cjs"
        runner_path.write_text(native_runner, encoding="utf-8")
        process = subprocess.run(
            ["node", str(runner_path), native_patched],
            capture_output=True,
            text=True,
            timeout=20,
        )
    assert process.returncode == 0, process.stderr
    native_payload = json.loads(process.stdout.strip())
    assert native_payload["calls"] == 1, native_payload
    assert native_payload["maxActive"] == 1, native_payload
    assert [row["name"] for row in native_payload["rows"]] == ["second-uncertain"], native_payload

    print("stream output sanitizer direct normalization tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

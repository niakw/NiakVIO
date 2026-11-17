#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "stream_output_sanitizer_v11.py"

spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v11_multi", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run(patched: str) -> dict:
    runner = r'''
const vm=require('vm');
const source=process.argv[2];
function response(url){
  const bytes=[0,0,0,24,102,116,121,112,1,2,3,4,5,6,7,8];
  let used=false;
  return {
    ok:true,status:200,url,
    headers:{get:(key)=>String(key).toLowerCase()==='content-type'?'video/mp4':''},
    body:{getReader:()=>({
      read:async()=> used ? {done:true,value:undefined} : (used=true,{done:false,value:new Uint8Array(bytes)}),
      cancel:async()=>{}
    })}
  };
}
const calls=[];
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,encodeURIComponent,
  fetch:async(url,init)=>{calls.push({url:String(url),headers:init&&init.headers||{}});return response(String(url));}
};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:10000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie'})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(error=>{console.error(error);process.exit(1)});
'''
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "multi-variant.cjs"
        path.write_text(runner, encoding="utf-8")
        process = subprocess.run(
            ["node", str(path), patched],
            capture_output=True,
            text=True,
            timeout=25,
        )
    assert process.returncode == 0, process.stdout + process.stderr
    return json.loads(process.stdout.strip())


def main() -> int:
    rows = [
        {
            "name": f"reader-{index + 1}",
            "title": f"Reader {index + 1} {quality}",
            "quality": quality,
            "url": f"https://media.example/source-{index + 1}-{quality}.mp4",
            "headers": {"Referer": f"https://player.example/{index + 1}"},
        }
        for index, quality in enumerate(
            ["2160p", "1080p", "720p", "480p"] * 6
        )
    ]
    source = "module.exports={getStreams:async function(){return " + json.dumps(rows) + ";}};\n"
    patched = module.apply(
        source,
        options={
            "probe_direct_media": True,
            "probe_all_urls": True,
            "max_probes": 40,
            "probe_timeout_ms": 2000,
            "min_vod_duration_seconds": 0,
        },
    )
    payload = run(patched)
    assert len(payload["rows"]) == 24, payload["rows"]
    assert len(payload["calls"]) == 24, payload["calls"]
    assert {row.get("quality") for row in payload["rows"]} >= {"2160p", "1080p", "720p", "480p"}

    # Bare-URL dedupe is wrong for a playback identity whose required Referer
    # differs. Both variants must be validated independently and preserved.
    shared = [
        {
            "name": "reader-a",
            "url": "https://media.example/shared.mp4",
            "headers": {"Referer": "https://player-a.example/watch"},
        },
        {
            "name": "reader-b",
            "url": "https://media.example/shared.mp4",
            "headers": {"Referer": "https://player-b.example/watch"},
        },
    ]
    shared_source = "module.exports={getStreams:async function(){return " + json.dumps(shared) + ";}};\n"
    shared_patched = module.apply(
        shared_source,
        options={
            "probe_direct_media": True,
            "probe_all_urls": True,
            "max_probes": 40,
            "probe_timeout_ms": 2000,
            "min_vod_duration_seconds": 0,
        },
    )
    shared_payload = run(shared_patched)
    assert len(shared_payload["calls"]) == 2, shared_payload
    referers = {call["headers"].get("Referer") for call in shared_payload["calls"]}
    assert referers == {
        "https://player-a.example/watch",
        "https://player-b.example/watch",
    }, shared_payload
    assert len(shared_payload["rows"]) == 2, shared_payload

    # Plugin results do not carry rich audioTracks into Nuvio Mobile/Desktop.
    # Keep the richer HLS master so the player itself can discover every audio rendition.
    master_source = r"""
module.exports={getStreams:async function(){return [{
  name:"reader",url:"https://player.example/embed/abc",
  headers:{Referer:"https://provider.example/title"}
}]}};\n"""
    master_patched = module.apply(
        master_source,
        options={
            "probe_direct_media": True,
            "probe_all_urls": True,
            "max_probes": 40,
            "probe_timeout_ms": 2000,
            "min_vod_duration_seconds": 0,
        },
    )
    master_runner = r"""
const vm=require('vm');const source=process.argv[2];const enc=t=>new Uint8Array(Buffer.from(t,'utf8'));
function response(url,type,text){let used=false,b=enc(text);return {ok:true,status:200,url,headers:{get:k=>String(k).toLowerCase()==='content-type'?type:''},body:{getReader:()=>({read:async()=>used?{done:true}:{done:false,value:(used=true,b)},cancel:async()=>{}})}}}
const child='#EXTM3U\\n#EXT-X-TARGETDURATION:120\\n#EXTINF:120,\\nseg.ts\\n#EXT-X-ENDLIST\\n';
const master='#EXTM3U\\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",LANGUAGE="fr",NAME="Français",DEFAULT=YES,URI="fr.m3u8"\\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",LANGUAGE="en",NAME="English",AUTOSELECT=YES,URI="en.m3u8"\\n#EXT-X-STREAM-INF:BANDWIDTH=3000000,AUDIO="aud"\\nvideo.m3u8\\n';
const html='<video><source src="https://cdn.example/child.m3u8"><source src="https://cdn.example/master.m3u8"></video>';
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,encodeURIComponent,
 fetch:async(url)=>{let u=String(url);if(u.includes('/embed/'))return response(u,'text/html',html);if(u.endsWith('/child.m3u8'))return response(u,'application/vnd.apple.mpegurl',child);if(u.endsWith('/master.m3u8'))return response(u,'application/vnd.apple.mpegurl',master);throw new Error('unexpected '+u)}};
sandbox.globalThis=sandbox;vm.runInNewContext(source,sandbox,{timeout:10000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie'}).then(rows=>console.log(JSON.stringify(rows))).catch(e=>{console.error(e);process.exit(1)});
"""
    with tempfile.TemporaryDirectory() as directory:
        runner_path = Path(directory) / "multi-audio-master.cjs"
        runner_path.write_text(master_runner, encoding="utf-8")
        process = subprocess.run(
            ["node", str(runner_path), master_patched],
            capture_output=True,
            text=True,
            timeout=25,
        )
    assert process.returncode == 0, process.stdout + process.stderr
    master_rows = json.loads(process.stdout.strip())
    assert len(master_rows) == 1, master_rows
    assert master_rows[0]["url"] == "https://cdn.example/master.m3u8", master_rows
    assert master_rows[0]["playerHost"] == "player.example", master_rows
    assert master_rows[0]["terminalHost"] == "cdn.example", master_rows

    print("stream output sanitizer multi-variant test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

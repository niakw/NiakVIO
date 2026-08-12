#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "stream_output_sanitizer_v5.py"

spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v5_direct", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    source = r'''
module.exports={getStreams:async function(){return [
  {name:"opaque-mp4",url:"https://media.example/token-mp4"},
  {name:"opaque-hls",url:"https://media.example/token-hls"},
  {name:"opaque-mkv",url:"https://media.example/token-mkv"},
  {name:"html-error",url:"https://media.example/not-media"}
]}};
'''
    patched = module.apply(
        source,
        options={
            "probe_direct_media": True,
            "probe_all_urls": True,
            "max_probes": 4,
            "probe_timeout_ms": 2000,
            "min_vod_duration_seconds": 0,
        },
    )
    assert '"implementationVersion":6' in patched

    runner = r'''
const vm=require('vm');
const source=process.argv[2];
function makeResponse(url,type,bytes,disposition){
  let used=false;
  return {
    ok:true,status:200,url,
    headers:{get:(key)=>{
      key=String(key).toLowerCase();
      if(key==='content-type')return type||'';
      if(key==='content-disposition')return disposition||'';
      return null;
    }},
    body:{getReader:()=>({
      read:async()=>used?{done:true,value:undefined}:(used=true,{done:false,value:new Uint8Array(bytes)}),
      cancel:async()=>{}
    })}
  };
}
const enc=(text)=>Array.from(Buffer.from(text,'utf8'));
const responses={
  'https://media.example/token-mp4':()=>makeResponse('https://cdn.example/final/opaque','video/mp4',[0,0,0,24,102,116,121,112,1,2,3,4]),
  'https://media.example/token-hls':()=>makeResponse('https://cdn.example/final/hls-opaque','text/plain',enc('#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n')),
  'https://media.example/token-mkv':()=>makeResponse('https://cdn.example/final/download','application/octet-stream',[0x1a,0x45,0xdf,0xa3,1,2,3,4],'attachment; filename="movie.mkv"'),
  'https://media.example/not-media':()=>makeResponse('https://media.example/not-media','text/html',enc('<html><body>error</body></html>'))
};
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  fetch:async(url)=>{const factory=responses[String(url)];if(!factory)throw new Error('unexpected '+url);return factory();}
};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie'})
  .then(rows=>console.log(JSON.stringify(rows)))
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
    rows = json.loads(process.stdout.strip())
    assert len(rows) == 3, rows
    by_name = {row["name"]: row for row in rows}
    assert by_name["opaque-mp4"]["url"] == "https://cdn.example/final/opaque"
    assert by_name["opaque-mp4"]["isDirect"] is True
    assert by_name["opaque-hls"]["url"] == "https://cdn.example/final/hls-opaque"
    assert by_name["opaque-hls"]["isDirect"] is True
    assert by_name["opaque-mkv"]["url"] == "https://cdn.example/final/download"
    assert by_name["opaque-mkv"]["isDirect"] is True
    assert "html-error" not in by_name

    print("stream output sanitizer direct normalization tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

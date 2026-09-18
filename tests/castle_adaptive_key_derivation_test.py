#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

spec=importlib.util.spec_from_file_location("castle_runtime",ROOT/"scripts/provider_patches/castle_runtime_v1.py")
assert spec and spec.loader
castle=importlib.util.module_from_spec(spec);spec.loader.exec_module(castle)
source=castle.apply("module.exports={getStreams:async()=>[]};\n")

with tempfile.TemporaryDirectory(prefix="niakvio-castle-key-") as raw:
    root=Path(raw)
    provider=root/"provider.cjs"
    runner=root/"runner.cjs"
    provider.write_text(source,encoding="utf-8")
    runner.write_text(r'''
global.__nuvioProviderValueTraceHistoryV21=[];
global.__crypto_aes_decrypt_raw=function(_alg,key,_iv,cipher){
  const keyText=Buffer.from(key.buffer,key.byteOffset,key.byteLength).toString('utf8');
  if(keyText==='1234567890abcdef') return new Uint8Array(cipher.buffer.slice(cipher.byteOffset,cipher.byteOffset+cipher.byteLength));
  return new Uint8Array(Buffer.from('not-json','utf8'));
};
const enc=v=>Buffer.from(JSON.stringify(v),'utf8').toString('base64');
const encrypted=v=>({ok:true,status:200,text:async()=>enc(v),json:async()=>v,headers:{get:()=>null}});
global.fetch=async function(url,init){
  url=String(url);
  if(url.includes('/getSecurityKey/1')) return {ok:true,status:200,json:async()=>({code:200,msg:'OK',data:'1234567890abcdef'}),headers:{get:()=>null}};
  if(url.includes('/searchByKeyword')) return encrypted({data:{rows:[{id:'m1',title:'Interstellar',year:2014}]}});
  if(url.includes('/film-api/v1.9.9/movie?')) return encrypted({data:{episodes:[{id:'e1',number:1,tracks:[]}]}});
  if(url.includes('/movie/getVideo2?')) return encrypted({data:{videoUrl:'https://media.example/master.m3u8',videos:[],subtitles:[]}});
  throw new Error('unexpected '+url);
};
const p=require(__PROVIDER__);
p.getStreams({
 tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014,
 tmdbMetadata:{title:'Interstellar',release_date:'2014-11-05'}
}).then(rows=>{
 const trace=global.__nuvioProviderValueTraceHistoryV21||[];
 console.log(JSON.stringify({rows,trace}));
}).catch(e=>{console.error(e&&e.stack||e);process.exit(1)});
'''.replace("__PROVIDER__",json.dumps(str(provider))),encoding="utf-8")
    cp=subprocess.run(["node",str(runner)],text=True,capture_output=True,timeout=20,check=False)
    assert cp.returncode==0,cp.stdout+cp.stderr
    result=json.loads(cp.stdout.strip())
    assert result["rows"],result
    stages=[row.get("route","") for row in result["trace"] if row.get("stage")=="castle_decrypt"]
    assert any("mode=base64;json=0" in row for row in stages),stages
    assert any("mode=raw;json=1" in row for row in stages),stages

print("Castle adaptive raw/base64 key derivation test passed")

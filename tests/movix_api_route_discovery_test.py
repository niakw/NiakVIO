import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recovery', ROOT / 'scripts/provider_patches/vf_catalogue_recovery.py')
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)

source = 'module.exports={getStreams:async()=>{throw new Error("native route must be skipped")}};'
patched = recovery.apply(source, options={
    'strategy': 'api_discovery',
    'provider_name': 'Movix',
    'base_url': 'https://movix.fun',
    'api_url': 'https://api.movix.fun',
    'types': ['movie'],
    'recovery_first': True,
    'skip_native_when_unresolved': True,
    'obsolete_route_tokens': ['/api/fstream/', 'fstream'],
})

with tempfile.TemporaryDirectory() as tmp:
    target = Path(tmp) / 'movix.js'
    target.write_text(patched)
    harness = r'''
const target=process.argv[1], requested=[];
global.fetch=async function(input){
 const url=typeof input==='string'?input:String(input&&input.url||input); requested.push(url);
 if(url==='https://movix.fun') return {ok:true,status:200,text:async()=>'<script src="/assets/app.js"></script>',json:async()=>({})};
 if(url==='https://movix.fun/assets/app.js') return {ok:true,status:200,text:async()=> 'const endpoint="/api/catalog/movie/{id}"',json:async()=>({})};
 if(url==='https://api.movix.fun/api/catalog/movie/577922') return {ok:true,status:200,text:async()=>'',json:async()=>({players:{VF:[{url:'https://video.example/movie.m3u8'}]}})};
 return {ok:false,status:404,text:async()=>'',json:async()=>({})};
};
(async()=>{const p=require(target);const rows=await p.getStreams('577922','movie',null,null);process.stdout.write(JSON.stringify({requested,rows}));})().catch(e=>{console.error(e.stack||e);process.exit(1)});
'''
    result = subprocess.run(['node','-e',harness,str(target)],text=True,capture_output=True,check=True)
    payload=json.loads(result.stdout)
    assert 'https://api.movix.fun/api/catalog/movie/577922' in payload['requested']
    assert all('/api/fstream/' not in url for url in payload['requested'])
    assert payload['rows'] and payload['rows'][0]['url']=='https://video.example/movie.m3u8'

# No discovered route: return an empty result and never execute the unsafe native function.
with tempfile.TemporaryDirectory() as tmp:
    target = Path(tmp) / 'movix.js'; target.write_text(patched)
    harness = r'''
global.fetch=async()=>({ok:true,status:200,text:async()=>'<html></html>',json:async()=>({})});
(async()=>{const p=require(process.argv[1]);const rows=await p.getStreams('577922','movie',null,null);process.stdout.write(JSON.stringify(rows));})().catch(e=>{console.error(e.stack||e);process.exit(1)});
'''
    result=subprocess.run(['node','-e',harness,str(target)],text=True,capture_output=True,check=True)
    assert json.loads(result.stdout)==[]

print('movix API route discovery tests passed')

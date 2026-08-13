#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/global_catalogue_alias_recovery_v2.py"
spec = importlib.util.spec_from_file_location("global_alias_identity", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
options = {"base_url":"https://catalog.example","provider_name":"example","max_aliases":8,"max_candidates":8,"max_players":8,"timeout_ms":5000,"budget_ms":20000}
base = "module.exports={getStreams:async function(){return [{title:'House of the Dragon - S03 E01',url:'https://wrong.example/video.m3u8'}];}};"
patched = module.apply(base, options)
assert "nativeIdentityReject" in patched
assert "implementationRevision" in patched
# Same config must be idempotent, while an implementation-revision upgrade must
# have stripped the previous V2 block instead of stacking it.
assert module.apply(patched, options) == patched
assert patched.count("NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:") == 1
runner = r'''
const assert=require('assert');
function response(body,status=200,type='application/json',url=''){return {ok:status>=200&&status<400,status,url,headers:{get(n){return String(n).toLowerCase()==='content-type'?type:null}},async json(){return JSON.parse(body)},async text(){return body}}}
global.fetch=async function(url){url=String(url);
 if(url.includes('/movie/424242?')&&url.includes('language=fr-FR'))return response(JSON.stringify({id:424242,title:'Mon ninja et moi 3',original_title:'Ternet Ninja 3',release_date:'2025-08-21'}),200,'application/json',url);
 if(url.includes('/movie/424242?')&&url.includes('language=en-US'))return response(JSON.stringify({id:424242,title:'Checkered Ninja 3',original_title:'Ternet Ninja 3',release_date:'2025-08-21'}),200,'application/json',url);
 if(url.includes('/movie/424242/alternative_titles?'))return response(JSON.stringify({titles:[]}),200,'application/json',url);
 if(url.startsWith('https://catalog.example/?s=')||url.startsWith('https://catalog.example/search?'))return response('<a href="/ternet-ninja-3-2025">Ternet Ninja 3 (2025)</a>',200,'text/html',url);
 if(url==='https://catalog.example/ternet-ninja-3-2025')return response('<h1>Ternet Ninja 3 (2025)</h1><iframe src="https://player.example/e/correct"></iframe>',200,'text/html',url);
 return response('',404,'text/plain',url);
};
PATCHED
(async()=>{const rows=await module.exports.getStreams({id:'tmdb:424242',mediaType:'movie',title:'Mon ninja et moi 3',year:2025});assert.strictEqual(rows.length,1,JSON.stringify(rows));assert.strictEqual(rows[0].url,'https://player.example/e/correct');console.log('strict native identity guard runtime test passed')})().catch(e=>{console.error(e);process.exit(1)});
'''.replace('PATCHED', patched)
with tempfile.NamedTemporaryFile('w', suffix='.cjs', dir=ROOT, delete=False, encoding='utf-8') as handle:
    handle.write(runner); path=Path(handle.name)
try:
    proc=subprocess.run(['node',str(path)],cwd=ROOT,capture_output=True,text=True,timeout=30)
    if proc.returncode: raise AssertionError(proc.stdout+'\n'+proc.stderr)
finally:
    path.unlink(missing_ok=True)
print('strict native identity guard tests passed')

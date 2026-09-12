#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'scripts'/'provider_base_store.py'
text=BASE.read_text(encoding='utf-8')
marker='NIAKVIO_PROVIDER_EMBEDDED_STRUCTURED_EPISODE_V25_1'
assert marker in text
start=text.index('/* '+marker+' */')
end=text.index('function _spv214EpisodeNumber',start)
helper=text[start:end]
for forbidden in ('mugiwara','smoothpre','jujutsu','animeserver','voiranime','wooka'):
    assert forbidden not in helper.casefold(),forbidden

script=r'''
function _text(v){return String(v == null ? "" : v)}
''' + helper + r'''
const structured={wrapper:{seasons:[
  {id:"1",lang:{sub:[
    ["https://alpha.invalid/e1","https://alpha.invalid/e2"],
    ["https://beta.invalid/e1","https://beta.invalid/e2"]
  ]}},
  {id:"2",lang:{sub:[
    ["https://alpha.invalid/s2e1","https://alpha.invalid/s2e2"],
    ["https://beta.invalid/s2e1","https://beta.invalid/s2e2"]
  ]}}
]}};
const decoded='0:{"meta":true,"carrier":'+JSON.stringify(structured)+'}';
const html='<script>self.__next_f.push([1,'+JSON.stringify(decoded)+'])</script>';
const values=_spv251EmbeddedJsonValues(html);
if(!values.length) throw new Error('embedded values not decoded');
const scoped=_spv251SeasonEpisodeScopedValue(values[0],"anime",1,2,0);
const out=JSON.stringify(scoped);
if(!out.includes('alpha.invalid/e2')||!out.includes('beta.invalid/e2')) throw new Error('requested episode missing: '+out);
if(out.includes('alpha.invalid/e1')||out.includes('beta.invalid/e1')) throw new Error('wrong episode leaked: '+out);
if(out.includes('s2e')) throw new Error('wrong season leaked: '+out);
console.log('embedded structured episode v25.1 node contract passed');
'''
path=ROOT/'automation'/'tmp-v25-1-contract.js'
path.write_text(script,encoding='utf-8')
try:
    subprocess.run(['node',str(path)],cwd=ROOT,check=True)
finally:
    path.unlink(missing_ok=True)
print('provider embedded structured episode v25.1 tests passed')

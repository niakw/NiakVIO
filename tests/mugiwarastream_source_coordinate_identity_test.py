#!/usr/bin/env python3
from __future__ import annotations
import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts/provider_patches/mugiwarastream_packed_runtime_v1.py").read_text("utf-8")
tree = ast.parse(source)
wrapper = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "WRAPPER" for t in node.targets):
        wrapper = ast.literal_eval(node.value)
        break
assert isinstance(wrapper, str)
wrapper = wrapper.replace("CONFIG_PLACEHOLDER", json.dumps({
    "base": "https://mugiwara-no-streaming.com",
    "ua": "NiakVIO-Test",
}, separators=(",", ":")))
anchor = 'try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"mugiwarastream",resolve:resolve}}catch(_e){}'
assert wrapper.count(anchor) == 1
wrapper = wrapper.replace(
    anchor,
    'g.__niakvioMugiwaraSourceCoordinateTest={matchSeason:matchSeason,episodeSources:episodeSources,attachIdentity:attachIdentity,resolveRows:resolveRows,discoverPage:discoverPage};' + anchor,
)
script = """
const assert = require('node:assert/strict');
const {streamIdentity} = require('./scripts/nuvio_client_lab.cjs');
globalThis.__nuvioCoreGetTmdbDataV1 = async () => ({metadata:{name:'Jujutsu Kaisen'}});
globalThis._crawlDirectMedia = async () => [{url:'https://cdn.example/opaque/master.m3u8', quality:'1080p'}];
globalThis.fetch = async (url) => {
  const value=String(url);
  if(value.includes('/api/suggest/lookup?')) return {ok:true,url:value,text:async()=>JSON.stringify({
    exact:{slug:'jujutsu-kaisen',anime:'Jujutsu Kaisen'},
    results:[{slug:'jujutsu-kaisen',anime:'Jujutsu Kaisen'}],
  })};
  throw new Error('unexpected network '+value);
};
eval(%WRAPPER%);
(async()=>{
  const h=globalThis.__niakvioMugiwaraSourceCoordinateTest;
  assert.ok(h);
  const direct={id:'1',lang:{vostfr:[['https://vidmoly.me/a1','https://vidmoly.me/a2'],['https://vidmoly.me/b1','https://vidmoly.me/b2']]}};
  const selected=h.matchSeason([direct],1,2);
  assert.equal(selected.index,1);
  assert.equal(selected.sourceSeason,1);
  assert.equal(selected.sourceEpisode,2);
  const split=h.matchSeason([
    {id:'1-1',lang:{vostfr:[['https://vidmoly.me/a1','https://vidmoly.me/a2']]}},
    {id:'1-2',lang:{vostfr:[['https://vidmoly.me/a3','https://vidmoly.me/a4']]}},
  ],1,3);
  assert.equal(split.index,0);
  assert.equal(split.sourceSeason,1);
  assert.equal(split.sourceEpisode,3);
  const positional=h.matchSeason([{id:'alpha',lang:{vostfr:[['https://vidmoly.me/x1']]} }],1,1);
  assert.equal(positional.sourceSeason,null);
  assert.equal(positional.sourceEpisode,null);

  const page=await h.discoverPage({tmdbId:'95479',type:'anime',season:1,episode:1});
  assert.deepEqual(page,{url:'https://mugiwara-no-streaming.com/catalogue/jujutsu-kaisen/episodes/saison1',sourceTitle:'Jujutsu Kaisen'});

  const identity={sourceTitle:page.sourceTitle,mediaType:'anime',season:1,episode:1};
  const rows=h.episodeSources(direct,'vostfr',0,identity);
  assert.equal(rows.length,2);
  const resolved=await h.resolveRows([rows[0]]);
  assert.equal(resolved.length,1);
  assert.equal(resolved[0].niakvioIdentityAuthority,'provider-source-coordinate-v1');
  assert.equal(resolved[0].niakvioIdentitySourceTitle,'Jujutsu Kaisen');
  assert.equal(resolved[0].niakvioIdentitySeason,1);
  assert.equal(resolved[0].niakvioIdentityEpisode,1);
  assert.equal(resolved[0].niakvioPresentationOnly,true);

  const fixture={title:'Jujutsu Kaisen',mediaType:'anime',season:1,episode:1};
  assert.deepEqual(streamIdentity(resolved[0],fixture),{status:'match',reason:'provider_source_coordinate'});
  assert.equal(streamIdentity(resolved[0],{...fixture,episode:2}).status,'contradiction');

  const untrusted=h.attachIdentity({url:'https://cdn.example/master.m3u8'},{identity:{sourceTitle:'Jujutsu Kaisen',mediaType:'anime',season:null,episode:1}});
  assert.equal(untrusted.niakvioIdentityAuthority,undefined);
})().catch(error=>{console.error(error);process.exit(1)});
""".replace("%WRAPPER%", json.dumps(wrapper))
subprocess.run(["node", "-e", script], cwd=ROOT, check=True)
print("Mugiwara provider-source-coordinate terminal identity contract passed")

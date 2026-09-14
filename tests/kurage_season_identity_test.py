#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts" / "provider_patches" / "kurage_runtime_v1.py"
spec = importlib.util.spec_from_file_location("kurage_runtime_v1", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = '"use strict";\nmodule.exports={getStreams:async()=>[]};\n'
PATCHED = mod.apply(BASE)
# Managed-fix metadata is encoded in FIXDATA; assert executable season-aware
# bytes instead of searching plaintext metadata labels inside the generated JS.
assert "NIAKVIO_KURAGE_RUNTIME_V1" in PATCHED
assert "function advanceSeason" in PATCHED
assert "anilistId:Number(ani.id)" in PATCHED

NODE = r'''
const scenario=process.argv[3];
global.__nuvioCoreGetTmdbDataV1=async(req)=>({
  state:'ok',
  metadata:{id:280049,name:'Hell Mode',original_name:'Hell Mode',first_air_date:'2025-01-01'},
  episodeMetadata:{air_date:'2026-03-10'}
});
let trpcAnimeId=0,trpcEpisode=0,searchCalls=0,idCalls=0;
function seasonOne(withRelation){
  return {
    id:101,type:'ANIME',format:'TV',title:{english:'Hell Mode',romaji:'Hell Mode',native:null},
    startDate:{year:2025,month:1,day:1},episodes:12,
    relations:{edges:withRelation?[{relationType:'SEQUEL',node:{
      id:202,type:'ANIME',format:'TV',title:{english:'Hell Mode Season 2',romaji:'Hell Mode 2nd Season',native:null},
      startDate:{year:2026,month:1,day:1},episodes:12
    }}]:[]}
  };
}
function seasonTwo(){
  return {id:202,type:'ANIME',format:'TV',title:{english:'Hell Mode Season 2',romaji:'Hell Mode 2nd Season',native:null},startDate:{year:2026,month:1,day:1},episodes:12,relations:{edges:[]}};
}
global.fetch=async(url,opt={})=>{
  const text=String(url);
  if(text.includes('graphql.anilist.co')){
    const body=JSON.parse(String(opt.body||'{}'));
    if(body.variables&&body.variables.search){
      searchCalls++;
      const rows=scenario==='direct'?[seasonOne(false),seasonTwo()]:[seasonOne(true)];
      return {ok:true,status:200,json:async()=>({data:{Page:{media:rows}}})};
    }
    if(body.variables&&body.variables.id){
      idCalls++;
      return {ok:true,status:200,json:async()=>({data:{Media:seasonOne(true)}})};
    }
    throw new Error('unexpected AniList query');
  }
  if(text.includes('/api/trpc/')){
    const parsed=new URL(text);
    const input=JSON.parse(parsed.searchParams.get('input'));
    trpcAnimeId=Number(input['1'].json.animeId);
    trpcEpisode=Number(input['1'].json.episode);
    return {ok:true,status:200,json:async()=>[
      {result:{data:{json:{id:trpcAnimeId}}}},
      {result:{data:{json:{sources:[{url:'/api/proxy/hell-mode-s2e10.m3u8',quality:'1080p',language:'sub'}]}}}},
      {result:{data:{json:{sources:[]}}}}
    ]};
  }
  throw new Error('unexpected fetch '+text);
};
require(process.argv[2]);
(async()=>{
  const runtime=global.__niakvioProviderRuntimeResolverV1;
  if(!runtime||runtime.provider!=='kurage')throw new Error('Kurage runtime not registered');
  const out=await runtime.resolve([{tmdbId:'280049',canonicalMediaType:'anime',mediaType:'tv',season:2,episode:10}],{});
  if(!Array.isArray(out)||out.length<1)throw new Error('no Kurage rows');
  if(trpcAnimeId!==202)throw new Error('wrong AniList season identity '+trpcAnimeId);
  if(trpcEpisode!==10)throw new Error('wrong episode '+trpcEpisode);
  if(Number(out[0].anilistId)!==202||Number(out[0].season)!==2||Number(out[0].episode)!==10)throw new Error('output identity mismatch '+JSON.stringify(out[0]));
  if(searchCalls!==1)throw new Error('unexpected search count '+searchCalls);
  if(scenario==='direct'&&idCalls!==0)throw new Error('direct season match should not hydrate base');
  console.log('KURAGE_SEASON_IDENTITY_OK scenario='+scenario+' anilist='+trpcAnimeId+' episode='+trpcEpisode);
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "provider.cjs"
    runner = tmp_path / "runner.cjs"
    provider.write_text(PATCHED, encoding="utf-8")
    runner.write_text(NODE, encoding="utf-8")
    for scenario in ("direct", "sequel"):
        result = subprocess.run(
            ["node", str(runner), str(provider), scenario],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"KURAGE_SEASON_IDENTITY_OK scenario={scenario}" in result.stdout

print("kurage season-aware identity tests passed")

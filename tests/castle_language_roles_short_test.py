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


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


castle = load_module(ROOT / "scripts/provider_patches/castle_runtime_v1.py", "castle_runtime_v1")
presentation = load_module(
    ROOT / "scripts/provider_patches/global_stream_presentation_v1.py",
    "global_stream_presentation_v1_castle_test",
)


def run_node(source: str, runner_source: str) -> dict | list:
    with tempfile.TemporaryDirectory(prefix="niakvio-castle-language-") as raw:
        root = Path(raw)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(source, encoding="utf-8")
        runner.write_text(
            runner_source.replace("__PROVIDER__", json.dumps(str(provider))),
            encoding="utf-8",
        )
        completed = subprocess.run(
            ["node", str(runner)],
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=20,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        return json.loads(completed.stdout.strip())


# Castle already receives languageName/abbreviate from its API. The provider layer
# must expose that evidence structurally on every individual stream. The visible
# provider name stays language-free; the old API label is retained only as provenance.
castle_source = castle.apply("module.exports={getStreams:async()=>[]};\n")
castle_rows = run_node(
    castle_source,
    r"""
global.__crypto_aes_decrypt_raw=function(_alg,_key,_iv,cipher){return cipher};
const b64=function(value){return Buffer.from(JSON.stringify(value),'utf8').toString('base64')};
const encrypted=function(value){return {ok:true,status:200,text:async()=>b64(value),json:async()=>value};};
const tracks=[
  {existIndividualVideo:true,languageId:'1',languageName:'Hindi',abbreviate:'hi'},
  {existIndividualVideo:true,languageId:'2',languageName:'Tamil',abbreviate:'ta'},
  {existIndividualVideo:true,languageId:'3',languageName:'Telugu',abbreviate:'te'},
  {existIndividualVideo:true,languageId:'4',languageName:'Bengali',abbreviate:'bn'}
];
const byId={'1':'Hindi','2':'Tamil','3':'Telugu','4':'Bengali'};
global.fetch=async function(url,init){
  url=String(url);
  if(url.includes('/v0.1/system/getSecurityKey/1')){
    return {ok:true,status:200,json:async()=>({code:200,data:'QUFBQUFBQUFBQUFBQUFBQQ=='})};
  }
  if(url.includes('/movie/searchByKeyword')){
    return encrypted({data:{rows:[{id:'m1',title:'Test Film',year:2024}]}});
  }
  if(url.includes('/film-api/v1.9.9/movie?')){
    return encrypted({data:{episodes:[{id:'e1',number:1,tracks:tracks}]}});
  }
  if(url.includes('/movie/getVideo2?')){
    const body=JSON.parse(String(init&&init.body||'{}'));
    const language=byId[String(body.languageId||'')];
    if(!language)throw new Error('unexpected languageId '+String(body.languageId));
    return encrypted({data:{
      videoUrl:'https://media.example/'+language.toLowerCase()+'/master.m3u8',
      videos:[{url:'https://media.example/'+language.toLowerCase()+'/master.m3u8',resolutionDescription:'1080p'}],
      subtitles:[]
    }});
  }
  throw new Error('unexpected fetch '+url);
};
const p=require(__PROVIDER__);
p.getStreams({
  tmdbId:'1',mediaType:'movie',title:'Test Film',year:2024,
  tmdbMetadata:{title:'Test Film',release_date:'2024-01-01'}
}).then(rows=>console.log(JSON.stringify(rows))).catch(e=>{console.error(e&&e.stack||e);process.exit(1)});
""",
)
assert [row.get("language") for row in castle_rows] == ["Hindi", "Tamil", "Telugu", "Bengali"], castle_rows
assert all(row.get("quality") == "1080p" for row in castle_rows), castle_rows
assert all(row.get("name") == "Castle - 1080p" for row in castle_rows), castle_rows
assert [row.get("sourceLabel") for row in castle_rows] == [
    "Castle [Hindi]", "Castle [Tamil]", "Castle [Telugu]", "Castle [Bengali]"
], castle_rows


# Core V23 owns role inference. With Hindi proven as the TMDB original language,
# Hindi must be Original while Tamil becomes a Dub. Castle itself never guesses roles.
role_source = (
    "module.exports={getStreams:async()=>["
    "{name:'Castle',sourceLabel:'Castle [Hindi]',url:'https://media.example/hi.m3u8',quality:'1080p',language:'Hindi'},"
    "{name:'Castle',sourceLabel:'Castle [Tamil]',url:'https://media.example/ta.m3u8',quality:'1080p',language:'Tamil'}"
    "]};\n"
)
role_source = presentation.apply(role_source, context={"provider_id": "castle"})
projected = run_node(
    role_source,
    r"""
global.__nuvioCoreGetTmdbDataV1=async function(){
  return {state:'ok',tmdbId:'1',tmdbNamespace:'movie',metadata:{
    id:1,title:'Test Film',release_date:'2024-01-01',runtime:120,original_language:'hi'
  },episodeMetadata:null};
};
const p=require(__PROVIDER__);
p.getStreams({tmdbId:'1',mediaType:'movie',title:'Test Film',year:2024})
 .then(rows=>console.log(JSON.stringify(rows)))
 .catch(e=>{console.error(e&&e.stack||e);process.exit(1)});
""",
)
assert len(projected) == 2, projected
hindi, tamil = projected
assert hindi["title"] == "Castle - 1080p", hindi
assert tamil["title"] == "Castle - 1080p", tamil
assert hindi["languageTracks"][0]["label"] == "Hindi", hindi
assert hindi["languageTracks"][0]["role"] == "Original", hindi
assert tamil["languageTracks"][0]["label"] == "Tamil", tamil
assert tamil["languageTracks"][0]["role"] == "Dub", tamil
assert "Hindi · Original" in hindi["description"], hindi
assert "Tamil · Dub" in tamil["description"], tamil
assert "HI Original" in hindi["displayBadges"], hindi
assert "TA Dub" in tamil["displayBadges"], tamil

print("Castle structured language + V23 Original/Dub tests passed")

#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
PATCH=ROOT/"scripts/provider_patches/ticketed_encrypted_api_runtime_v1.py"
spec=importlib.util.spec_from_file_location("ticketed_encrypted_api_runtime_v1",PATCH)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

assert "WebAssembly" not in mod.WRAPPER
assert "TextEncoder" not in mod.WRAPPER
assert "TextDecoder" not in mod.WRAPPER
assert "NIAKVIO_TICKETED_ENCRYPTED_API_RUNTIME_V1" in mod.WRAPPER
assert mod.MANAGED_FIX_ID == "PROVIDER.GENERIC.TICKETED_ENCRYPTED.API.V1"
assert mod.GENERIC_REUSABLE is True

cfg={
 "providerId":"demo-ticketed","providerName":"Demo Ticketed",
 "apiBase":"https://api.demo.test","siteBase":"https://demo.test",
 "challengePath":"/altcha/challenge","challengeBodyField":"altcha",
 "ticketPath":"/streams/ticket","ticketMethod":"POST","ticketField":"ticket","ticketHeader":"X-Stream-Ticket",
 "moviePath":"/streams/movie/{id}","tvPath":"/streams/tv/{id}/{season}/{episode}",
 "subtitleMoviePath":"/subs/movie/{id}","subtitleTvPath":"/subs/tv/{id}/{season}/{episode}",
 "serverQueryKey":"s","decryptUrl":"https://decrypt.demo.test/dec","decryptBodyField":"data",
 "servers":[{"id":"dcloud","label":"DCloud"},{"id":"acme","label":"Acme"},{"id":"movie-only","label":"MovieOnly","movieOnly":True}],
 "maxPow":20,"maxStreams":8,"maxSubtitles":12,"userAgent":"NiakVIO-Test",
}
compiled=mod.WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,separators=(",",":")))
harness=r'''
"use strict";
globalThis.btoa=globalThis.btoa||function(v){return Buffer.from(String(v),"binary").toString("base64")};
const calls=[];let ticketNo=0;
function R(url,obj,status=200){return{ok:status>=200&&status<300,status,url,headers:{get(){return"application/json"}},async json(){return obj},async text(){return JSON.stringify(obj)}}}
globalThis.fetch=async function(url,opt){
 url=String(url);opt=opt||{};const headers=opt.headers||{};calls.push({url,headers,body:String(opt.body||""),method:String(opt.method||"GET")});
 if(url==="https://api.demo.test/subs/movie/19995")return R(url,[{url:"https://subs.example/fr.vtt",language:"fr",name:"French"}]);
 if(url==="https://api.demo.test/subs/tv/120089/1/1")return R(url,[{url:"https://subs.example/anime-fr.vtt",language:"fr"}]);
 if(url==="https://api.demo.test/altcha/challenge")return R(url,{algorithm:"SHA-256",challenge:"590c9f8430c7435807df8ba9a476e3f1295d46ef210f6efae2043a4c085a569e",maxnumber:0,salt:"test",signature:"sig"});
 if(url==="https://api.demo.test/streams/ticket"){const b=JSON.parse(String(opt.body||"{}")),d=JSON.parse(Buffer.from(String(b.altcha||""),"base64").toString("utf8"));if(d.number!==0||d.salt!=="test")throw new Error("ALTCHA mismatch");ticketNo++;return R(url,{ticket:"ticket-"+ticketNo})}
 if(url.startsWith("https://api.demo.test/streams/movie/19995")){if(!headers["X-Stream-Ticket"])throw new Error("movie ticket missing");const s=new URL(url).searchParams.get("s");return R(url,{n:"n-"+s,d:"movie-"+s})}
 if(url.startsWith("https://api.demo.test/streams/tv/120089/1/1")){if(!headers["X-Stream-Ticket"])throw new Error("tv ticket missing");const s=new URL(url).searchParams.get("s");return R(url,{n:"n-"+s,d:"anime-"+s})}
 if(url==="https://decrypt.demo.test/dec"){const b=JSON.parse(String(opt.body||"{}")),d=b.data&&b.data.d;
  if(d==="movie-dcloud")return R(url,{status:200,result:{url:"https://cdn.example/shared-master.m3u8",language:"English",quality:"1080p",headers:{"X-Media":"en"}}});
  if(d==="movie-acme")return R(url,{status:200,result:{url:"https://cdn.example/shared-master.m3u8",language:"French",quality:"1080p",headers:{"X-Media":"fr"}}});
  if(d==="movie-movie-only")return R(url,{status:200,result:{url:"https://cdn.example/movie-only.m3u8",language:"Turkish",quality:"720p"}});
  if(d==="anime-dcloud")return R(url,{status:200,result:{url:"https://cdn.example/anime-en.m3u8",language:"English",quality:"1080p"}});
  if(d==="anime-acme")return R(url,{status:200,result:{url:"https://cdn.example/anime-fr.m3u8",language:"French",quality:"1080p"}});
 }
 throw new Error("unexpected "+url)
};
'''+compiled+r'''
(async()=>{
 const h=globalThis.__niakvioProviderRuntimeResolverV1;if(!h||h.provider!=="demo-ticketed")throw new Error("hook missing");
 const movie=await h.resolve([{tmdbId:"19995",canonicalMediaType:"movie",mediaType:"movie"}]);
 if(movie.length!==3)throw new Error("movie streams "+JSON.stringify(movie));
 if(movie[0].url!==movie[1].url||movie[0].language===movie[1].language)throw new Error("language/header multiplicity collapsed");
 if(movie.some(x=>x.headers["X-Stream-Ticket"]))throw new Error("ticket leaked");
 if(!movie.every(x=>x.niakvioIdentityAuthority==="tmdb-direct-route-v1"&&x.niakvioIdentityTmdbId==="19995"&&x.niakvioIdentityMediaType==="movie"&&x.niakvioIdentitySeason===0&&x.niakvioIdentityEpisode===0&&x.niakvioPresentationOnly===true))throw new Error("movie identity provenance missing "+JSON.stringify(movie));
 if(!movie.every(x=>x.subtitles.length===1&&x.subtitles[0].language==="fr"))throw new Error("subtitles lost");
 const mark=calls.length,anime=await h.resolve([{tmdbId:"120089",canonicalMediaType:"anime",mediaType:"anime",season:1,episode:1}]);
 if(anime.length!==2)throw new Error("movieOnly leaked");
 if(!anime.every(x=>x.niakvioIdentityAuthority==="tmdb-direct-route-v1"&&x.niakvioIdentityTmdbId==="120089"&&x.niakvioIdentityMediaType==="anime"&&x.niakvioIdentitySeason===1&&x.niakvioIdentityEpisode===1&&x.niakvioPresentationOnly===true))throw new Error("anime identity provenance missing "+JSON.stringify(anime));
 const ac=calls.slice(mark).map(x=>x.url);if(!ac.some(u=>u.includes("/streams/tv/120089/1/1"))||ac.some(u=>u.includes("/streams/movie/120089")))throw new Error("anime route mismatch");
 const sc=calls.filter(x=>x.url.includes("/streams/movie/")||x.url.includes("/streams/tv/")),tickets=sc.map(x=>x.headers["X-Stream-Ticket"]);
 if(new Set(tickets).size!==tickets.length)throw new Error("ticket reused");
 console.log(JSON.stringify({movie,anime,tickets}));
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
'''
with tempfile.TemporaryDirectory(prefix="niakvio-ticketed-api-") as td:
 p=Path(td)/"probe.cjs";p.write_text(harness,encoding="utf-8")
 proc=subprocess.run(["node",str(p)],cwd=ROOT,capture_output=True,text=True,check=True)
result=json.loads(proc.stdout.strip().splitlines()[-1])
assert {row["language"] for row in result["movie"][:2]}=={"English","French"}
assert len(result["tickets"])==len(set(result["tickets"]))

batch=json.loads((ROOT/".github/provider-onboarding/batch.json").read_text(encoding="utf-8"))
meow=next(row for row in [*(batch.get("providers") or []),*(batch.get("deferredProviders") or [])] if row.get("id")=="meowtv")
blocks=meow.get("providerBlocks") or []
assert len(blocks)==1,blocks
assert blocks[0]["script"]=="scripts/provider_patches/ticketed_encrypted_api_runtime_v1.py"
opts=blocks[0]["options"]
assert opts["provider"]=="meowtv"
assert opts["apiBase"]=="https://api.meowtv.ru"
assert opts["challengePath"]=="/altcha/challenge"
assert opts["ticketHeader"]=="X-Stream-Ticket"
assert opts["decryptUrl"].endswith("/dec-meowtv")

add=(ROOT/"scripts/add_provider.py").read_text(encoding="utf-8")
assert "structured_provider_blocks(request)" in add
assert 'patch["provider_lego_scripts"]' in add
assert 'patch["provider_lego_options"]' in add
gate=(ROOT/".github/workflows/github-actions-gate.yml").read_text(encoding="utf-8")
fin=(ROOT/".github/workflows/release-finalize.yml").read_text(encoding="utf-8")
for w in (gate,fin):
 assert "tests/provider_ticketed_encrypted_api_runtime_test.py" in w
 assert "scripts/provider_patches/ticketed_encrypted_api_runtime_v1.py" in w
assert "scripts/add_provider.py" in gate and "scripts/add_provider.py" in fin
print("ticketed encrypted API Bloc contract passed")

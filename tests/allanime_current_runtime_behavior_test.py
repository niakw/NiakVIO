#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/allanime_site_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["allanime"]
opts=ov["provider_lego_options"]["scripts/provider_patches/allanime_site_runtime_v1.py"]
wrapper=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0].replace("CONFIG_PLACEHOLDER",json.dumps(opts,separators=(",",":")))

harness=r'''
const nc=require("node:crypto");
global.crypto=nc.webcrypto;
const te=new TextEncoder();
const mask=Uint8Array.from({length:32},(_,i)=>i+1);
const rawKey=Uint8Array.from({length:32},(_,i)=>160+i);
function hex(a){return Array.from(a).map(x=>x.toString(16).padStart(2,"0")).join("")}
function b64(a){return Buffer.from(a).toString("base64")}
const partB=Uint8Array.from({length:32},(_,i)=>rawKey[i]^mask[i]);
const calls=[];
function R(url,status,body,ct){return {ok:status>=200&&status<300,status,url,headers:{get(n){return String(n).toLowerCase()==="content-type"?(ct||"application/json"):""}},async text(){return typeof body==="string"?body:JSON.stringify(body)},async json(){return typeof body==="string"?JSON.parse(body):body}}}
global.fetch=async function(url,opt){
  url=String(url); opt=opt||{}; calls.push({url,method:String(opt.method||"GET").toUpperCase(),body:String(opt.body||"")});
  if(url==="https://api.mkissa.net/api" && String(opt.method||"GET").toUpperCase()==="POST") return R(url,200,{data:{shows:{edges:[{_id:"aa-current-1",name:"Death Note",englishName:"Death Note",availableEpisodes:{sub:37,dub:37}}]}}});
  if(url==="https://mkissa.to") return R(url,200,'<html><script>window.x={"epoch":321,"partB":"'+b64(partB)+'"};</script><script src="https://cdn.mkissa.net/all/mk/_app/immutable/entry/app.ABC123.js"></script></html>',"text/html");
  if(url==="https://cdn.mkissa.net/all/mk/_app/immutable/entry/app.ABC123.js") return R(url,200,'"../chunks/chunk.XYZ.js"',"application/javascript");
  if(url==="https://cdn.mkissa.net/all/mk/_app/immutable/chunks/chunk.XYZ.js") return R(url,200,'const mask="'+hex(mask)+'";',"application/javascript");
  if(url.startsWith("https://api.mkissa.net/api?")){
    const u=new URL(url),ext=JSON.parse(u.searchParams.get("extensions")||"{}");
    if(!ext.aaReq||String(ext.aaReq).length<20)throw new Error("aaReq missing");
    if(!ext.persistedQuery||ext.persistedQuery.sha256Hash!=="f4662f4b7510b26795dd53ef824a0bf1740fbbc5d1273fab18222ac831bca8d0")throw new Error("current hash missing");
    const iv=Uint8Array.from({length:12},(_,i)=>70+i);
    const key=await crypto.subtle.importKey("raw",rawKey,{name:"AES-GCM"},false,["encrypt"]);
    const payload=te.encode(JSON.stringify({episode:{sourceUrls:[{sourceName:"Yt-mp4",sourceUrl:"https://cdn.example/video.mp4"}]}}));
    const sealed=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv,tagLength:128},key,payload));
    const blob=new Uint8Array(1+12+sealed.length);blob[0]=1;blob.set(iv,1);blob.set(sealed,13);
    return R(url,200,{data:{tobeparsed:b64(blob)}});
  }
  if(url==="https://cdn.example/video.mp4") return R(url,206,"","video/mp4");
  return R(url,404,{});
};
''' + wrapper + r'''
(async()=>{
  const hook=globalThis.__niakvioProviderRuntimeResolverV1;
  if(!hook||hook.provider!=="allanime")throw new Error("AllAnime hook missing");
  const out=await hook.resolve([{tmdbId:"13916",semanticType:"anime",season:1,episode:1,tmdbMetadata:{name:"Death Note",original_name:"DEATH NOTE",seasons:[{season_number:1,episode_count:37}]}}],{});
  if(!Array.isArray(out)||out.length<1)throw new Error("no current AllAnime stream: "+JSON.stringify(out));
  if(out[0].url!=="https://cdn.example/video.mp4")throw new Error("wrong terminal "+JSON.stringify(out[0]));
  const flat=calls.map(x=>x.url).join("\n");
  for(const token of ["https://mkissa.to","/entry/app.ABC123.js","/chunks/chunk.XYZ.js","https://api.mkissa.net/api?","https://cdn.example/video.mp4"]) if(!flat.includes(token))throw new Error("missing "+token+"\n"+flat);
  console.log("ALLANIME_CURRENT_AAREQ_GCM_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",harness],check=True)
print("AllAnime current Mkissa aaReq/AES-GCM behavior passed")

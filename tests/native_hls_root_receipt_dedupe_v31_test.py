#!/usr/bin/env python3
"""Exact generic ProviderBase V30 -> V31 receipt/dedupe causal regression.

The scenario models an official player HTML announcing a signed HLS master:
crawler pushes the URL *before* following it; the successful HLS GET later
carries a bounded proof. V30 silently loses that proof in first-wins dedupe.
V31 retains it only for the same URL+headers, while preserving first-row
metadata; media child/segment and terminal decoding are not certified here.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from provider_base_store import build_clean_provider_seed
from provider_patches.native_hls_root_receipt_v1 import apply as apply_v30
from provider_patches.native_hls_root_receipt_dedupe_v31 import (
    MARKER, apply as apply_v31, validate,
)

base = build_clean_provider_seed("candidate-dedupe-oracle")
v30 = apply_v30(base)
v31 = apply_v31(base)
validate(v31)
assert MARKER not in base.decode() and MARKER not in v30.decode()
assert MARKER in v31.decode()
assert v31 != v30 != base
try:
    apply_v31(v31)
except ValueError:
    pass
else:
    raise AssertionError("V31 must never stack on an already mutated candidate")

def extract(data: bytes) -> dict[str, str]:
    source = data.decode("utf-8")
    return {
        "dedupe": source[
            source.index("function _streamPlaybackKey(stream) {"):
            source.index("function _recipeValue(row, fields)", source.index("function _streamPlaybackKey(stream) {"))
        ],
        "crawler": source[
            source.index("async function _crawlDirectMedia(seedUrls, referer, maxDepth) {"):
            source.index("function _candidateScore(url, meta)", source.index("async function _crawlDirectMedia(seedUrls, referer, maxDepth) {"))
        ],
    }

runner = r"""
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const files=JSON.parse(fs.readFileSync(0,'utf8'));
const player='https://player.test/e/episode1';
const master='https://hls.test/master.m3u8?signature=ephemeral';
const hls='#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",LANGUAGE="fr",URI="fr.m3u8"\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",LANGUAGE="en",URI="en.m3u8"\n#EXT-X-STREAM-INF:BANDWIDTH=4200000,AUDIO="aud"\nvideo.m3u8\n';
async function run(version,{html=false,oversized=false,rewrite=false}={}){
 let requests=[],read=0;
 const context={
  URL, Date, Set, Map, Promise, Object, Number, String,
  __native_fetch:()=>{},
  _spv187PrioritizedPlayerRoutes: x=>x,
  _crawlEligible:()=>true,
  _spv187QueueScore: u=>u===master?4:1,
  _crawlUrlScore:u=>u===master?10:1,
  _crawlCanonical:u=>u,
  _crawlFollowable:()=>true,
  _spv187PlayerRouteVariants:()=>[],
  _origin:u=>new URL(u).origin,
  _text:x=>String(x||''),
  _uniq:x=>[...new Set(x)],
  _directMedia:u=>/\.m3u8(?:[?#]|$)/.test(u),
  _streams:(urls,ref)=>urls.map(u=>({
    url:rewrite?'https://proxy.test/rewrite.m3u8':u,
    headers:{Referer:ref},quality:u===master?'1080p':''
  })),
  _jsonUrls:()=>[],
  _spv26JsonMediaRows:()=>[],
  _spv186UnpackPackedPlayer:x=>x,
  _spv26ExplicitMediaRows:()=>[],
  _spv241ExplicitPlayerPayloadUrls:()=>[],
  _extractUrls:s=>s==='player html'?[master]:[],
  _spv21DecodedObfuscatedHls:()=> '',
  _spv188PlayerForm:()=>null,
  _fetch:async u=>{
    requests.push(u);
    if(u===player)return {url:u,ok:true,headers:{get:k=>k==='content-type'?'text/html':''},text:async()=> 'player html'};
    if(u===master)return {url:u,ok:true,headers:{get:k=>k==='content-type'?'application/vnd.apple.mpegurl':k==='content-length'&&oversized?'131073':''},
      text:async()=>{read++;return html?'<html>forbidden</html>':hls}};
    throw Error('unexpected source');
  }
 };
 vm.createContext(context);
 const src=files[version];
 const crawler=vm.runInContext(src.dedupe+'\n'+src.crawler+'\n_crawlDirectMedia',context);
 const rows=await crawler([player], 'https://provider.test/show',2);
 return {rows,requests,read};
}
(async()=>{
 const before=await run('v30');
 assert.equal(before.requests.length,2);
 assert.equal(before.rows.length,1);
 assert.equal(before.rows[0].__nuvioCoreMediaProofV1,undefined,
   'V30 must reproduce first-unverified-row witness loss');
 const after=await run('v31');
 assert.equal(after.requests.length,2, 'V31 does not introduce any network fetch');
 assert.equal(after.rows.length,1);
 assert.equal(after.rows[0].url,master);
 assert.equal(after.rows[0].quality,'1080p');
 assert.equal(after.rows[0].headers.Referer,player);
 assert.equal(after.rows[0].__nuvioCoreMediaProofV1.body,hls);
 assert.equal(after.rows[0].__nuvioCoreMediaProofV1.url,master);
 const bad=await run('v31',{html:true});
 assert.equal(bad.rows[0].__nuvioCoreMediaProofV1,undefined);
 const huge=await run('v31',{oversized:true});
 assert.equal(huge.rows[0].__nuvioCoreMediaProofV1,undefined);
 const rewritten=await run('v31',{rewrite:true});
 assert.equal(rewritten.rows[0].__nuvioCoreMediaProofV1,undefined);
 const ctx={URL,Map,Set,Object,String,Number};
 vm.createContext(ctx);
 vm.runInContext(files.v31.dedupe,ctx);
 const same='https://hls.test/master.m3u8';
 const row=(ref,proof)=>({url:same,headers:{Referer:ref},quality:'720p', ...(proof?{__nuvioCoreMediaProofV1:{url:same,kind:'hls',body:hls}}:{})});
 const distinct=vm.runInContext('_dedupeStreamRows',ctx)([row('https://p1.test'),row('https://p2.test',true)]);
 assert.equal(distinct.length,2,'different playback headers must not collapse');
 assert.equal(distinct[0].__nuvioCoreMediaProofV1,undefined);
 const tampered=vm.runInContext('_dedupeStreamRows',ctx)([row('https://p1.test'),
   {...row('https://p1.test',true),__nuvioCoreMediaProofV1:{url:'https://other.test',kind:'hls',body:hls}}]);
 assert.equal(tampered.length,1);
 assert.equal(tampered[0].__nuvioCoreMediaProofV1,undefined);
 console.log('V31 generic dedupe fixture: V30 loses witness; V31 retains same-url/header receipt; unsafe variants rejected');
})().catch(e=>{console.error(e);process.exitCode=1});
"""
result = subprocess.run(
    ["node", "-e", runner], input=json.dumps({"v30": extract(v30), "v31": extract(v31)}),
    capture_output=True, text=True, timeout=20, check=False,
)
assert result.returncode == 0, result.stdout + "\n" + result.stderr
print(result.stdout.strip())

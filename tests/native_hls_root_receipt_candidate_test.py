#!/usr/bin/env python3
"""Execute V30 Core-owned HLS receipt on exact generated ProviderBase crawler JS.

Candidate-only oracle: no production provider bytes change, and a successful
master receipt is not terminal video/audio proof.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))
from provider_base_store import build_clean_provider_seed
from native_hls_root_receipt_v1 import MARKER, apply, validate

base = build_clean_provider_seed("receipt-contract")
assert MARKER not in base.decode("utf-8")
candidate = apply(base)
validate(candidate)
assert base != candidate
try:
    apply(candidate)
except ValueError:
    pass
else:
    raise AssertionError("V30 candidate must reject duplicate application")

source = candidate.decode("utf-8")
start = source.index("async function _crawlDirectMedia(seedUrls, referer, maxDepth) {")
end = source.index("function _candidateScore(url, meta)", start)
crawl = source[start:end]
assert crawl.count(MARKER) == 1
# Both existing downstream Core layers must consume/remove in-memory proof,
# independently of the candidate's attempted source capture.
hls = (ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py").read_text()
sanitizer = (ROOT / "scripts/provider_patches/stream_output_sanitizer.py").read_text()
assert "var proof=stream&&stream.__nuvioCoreMediaProofV1;" in hls
assert "function stripCoreHlsProofBody" in hls
assert "delete stream.__nuvioCoreMediaProofV1" in sanitizer
assert "function coreMediaProof(stream,url)" in sanitizer

runner = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const crawler = JSON.parse(fs.readFileSync(0,'utf8'));
const master = '#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio0",LANGUAGE="fr",URI="fr.m3u8"\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio0",LANGUAGE="en",URI="en.m3u8"\n#EXT-X-STREAM-INF:BANDWIDTH=4200000,AUDIO="audio0"\nvideo.m3u8\n';
function createFixture({native=true, contentType='application/vnd.apple.mpegurl', body=master, size='', rewrite=false, url='https://media.example/master.m3u8?sig=temporary'}={}) {
  const calls = [];
  let bodyReads = 0;
  const context = {
    URL,
    Date,
    Set,
    Promise,
    _spv187PrioritizedPlayerRoutes:x=>x,
    _crawlEligible:()=>true,
    _spv187QueueScore:()=>1,
    _crawlUrlScore:()=>1,
    _crawlCanonical:x=>x,
    _crawlFollowable:()=>false,
    _spv187PlayerRouteVariants:()=>[],
    _origin:u=>new URL(u).origin,
    _text:x=>String(x||''),
    _uniq:x=>[...new Set(x)],
    _directMedia:u=>/\\.m3u8(?:[?#]|$)/.test(u)||/\\.mp4(?:[?#]|$)/.test(u),
    _streams:urls=>urls.map(x=>({url:rewrite?'https://proxy.example/rewrite.m3u8':x,headers:{Referer:'https://player.example'}})),
    _jsonUrls:()=>[],
    _spv26JsonMediaRows:()=>[],
    _spv186UnpackPackedPlayer:x=>x,
    _spv26ExplicitMediaRows:()=>[],
    _spv241ExplicitPlayerPayloadUrls:()=>[],
    _extractUrls:()=>[],
    _spv21DecodedObfuscatedHls:()=> '',
    _spv188PlayerForm:()=>null,
    _dedupeStreamRows:rows=>[...new Map(rows.map(x=>[x.url,x])).values()],
    _fetch:async target=>{
      calls.push(target);
      if(calls.length>1)throw Error('http_403_on_duplicate_signed_root');
      return {url:target,ok:true,headers:{get:key=>key==='content-type'?contentType:key==='content-length'?size:''},
        text:async()=>{bodyReads++;return body}};
    },
  };
  if(native)context.__native_fetch=()=>{};
  vm.createContext(context);
  const crawl=vm.runInContext(crawler+';_crawlDirectMedia;',context);
  return {crawl, calls, get bodyReads(){return bodyReads}, url};
}
(async()=>{
 const a=createFixture();
 const rows=await a.crawl([a.url],'https://player.example',1);
 assert.equal(rows.length,1);
 assert.equal(a.calls.length,1,'one root fetch, never another signed GET');
 assert.equal(a.bodyReads,1);
 assert.equal(rows[0].url,a.url);
 const receipt=rows[0].__nuvioCoreMediaProofV1;
 assert.ok(receipt,'V30 must attach the successful in-memory HLS receipt');
 assert.equal(receipt.kind,'hls');
 assert.equal(receipt.url,a.url);
 assert.equal(receipt.body,master,'preserve the FR/EN master exactly');
 assert.deepEqual(rows[0].headers,{Referer:'https://player.example'});

 const desktop=createFixture({native:false});
 const desktopRows=await desktop.crawl([desktop.url],'https://player.example',1);
 assert.equal(desktopRows.length,1);
 assert.equal(desktop.bodyReads,0);
 assert.equal(desktopRows[0].__nuvioCoreMediaProofV1,undefined,
  'non-native path must be byte/behavior-compatible');

 const invalid=createFixture({body:'<html>403 challenge</html>'});
 const invalidRows=await invalid.crawl([invalid.url],'https://player.example',1);
 assert.equal(invalidRows[0].__nuvioCoreMediaProofV1,undefined,
  'HTML masquerading as an HLS resource is not proof');

 const large=createFixture({size:'131073'});
 const largeRows=await large.crawl([large.url],'https://player.example',1);
 assert.equal(large.bodyReads,0);
 assert.equal(largeRows[0].__nuvioCoreMediaProofV1,undefined,
  'oversized announced payload is never stored');

 const transformed=createFixture({rewrite:true});
 const transformedRows=await transformed.crawl([transformed.url],'https://player.example',1);
 assert.equal(transformedRows[0].__nuvioCoreMediaProofV1,undefined,
  'rewritten URL must not borrow a proof for another endpoint');

 const mp4=createFixture({url:'https://media.example/movie.mp4'});
 const mp4Rows=await mp4.crawl([mp4.url],'https://player.example',1);
 assert.equal(mp4Rows[0].__nuvioCoreMediaProofV1,undefined,
  'direct MP4 is not an HLS proof');

 console.log('V30 candidate: native master receipt=1; duplicate signed root GET=0; desktop, HTML, oversized, rewritten URL and MP4 guards=pass');
})().catch(e=>{console.error(e);process.exitCode=1});
"""
result = subprocess.run(
    ["node", "-e", runner], input=json.dumps(crawl), text=True,
    capture_output=True, timeout=12
)
assert result.returncode == 0, (result.stdout, result.stderr)
print(result.stdout.strip())

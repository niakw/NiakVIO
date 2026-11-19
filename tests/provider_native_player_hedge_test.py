#!/usr/bin/env python3
"""Shared ProviderBase hedged players: avoid a slow origin, keep strict boundaries."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts/provider_base_store.py").read_text(encoding="utf-8")
start = source.index("async function _crawlDirectMedia(seedUrls, referer, maxDepth) {")
end = source.index("function _candidateScore(url, meta)", start)
crawl = source[start:end]
assert "NIAKVIO_PROVIDER_NATIVE_PLAYER_HEDGE_V27" in crawl
assert "Promise.race([Promise.all(workers), firstDirect])" in crawl
assert "const workers = [crawlWorker(), crawlWorker()]" in crawl
assert "if (hedgeStopped) return;" in crawl

js = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const crawler = JSON.parse(process.env.CRAWL_CODE);
function make(native, slowHost, fastHost, blockingNativeBridge=false) {
  const requests = [];
  const starts = [];
  const f = {
    _spv187PrioritizedPlayerRoutes: x => x,
    _crawlEligible: () => true,
    _spv187QueueScore: x => x.includes('slow.example') ? 2 : 1,
    _crawlUrlScore: () => 0,
    _crawlCanonical: x => x,
    _crawlFollowable: () => false,
    _spv187PlayerRouteVariants: () => [],
    _origin: u => new URL(u).origin,
    _text: x => String(x || ''),
    _uniq: x => [...new Set(x)],
    _directMedia: u => /\.m3u8(?:[?#]|$)/.test(u),
    _streams: urls => urls.map(url => ({url, type:'hls'})),
    _jsonUrls: () => [],
    _spv26JsonMediaRows: () => [],
    _spv186UnpackPackedPlayer: x => x,
    _spv26ExplicitMediaRows: () => [],
    _spv241ExplicitPlayerPayloadUrls: () => [],
    _extractUrls: text => text.includes('fast-master') ? ['https://media.example/fast-master.m3u8'] : [],
    _spv21DecodedObfuscatedHls: () => '',
    _spv188PlayerForm: () => null,
    _dedupeStreamRows: rows => [...new Map(rows.map(x=>[x.url,x])).values()],
    _fetch: async u => {
      requests.push(u);
      starts.push({url:u,at:Date.now()});
      if (u.includes('slow.example')) {
        if (blockingNativeBridge) {
          // Official NuvioTV's async fetch() calls a synchronous
          // __native_fetch -> OkHttp Call.execute() before its first await.
          // The JS thread cannot schedule its second worker meanwhile.
          const until=Date.now()+150;
          while (Date.now()<until) {}
        } else {
          await new Promise(r=>setTimeout(r,150));
        }
        throw new Error('http_522');
      }
      await new Promise(r=>setTimeout(r,8));
      return {url:u,headers:{get:()=> 'text/html'},text:async()=> 'fast-master'};
    },
  };
  f.globalThis = native
    ? { __native_fetch:()=>{}, __nuvioProviderDeadlineMs:Date.now()+25000 }
    : {};
  vm.createContext(f);
  f.testCrawl=vm.runInContext(crawler+';_crawlDirectMedia;',f);
  return {f, requests, starts};
}
(async()=>{
 const slow='https://slow.example/embed/bad',fast='https://fast.example/e/good';
 const a=make(true,slow,fast),start=Date.now();
 const rows=await a.f.testCrawl([slow,fast],'https://example.org',2);
 const ms=Date.now()-start;
 assert.equal(rows.length,1,JSON.stringify(rows));
 assert.match(rows[0].url,/fast-master\.m3u8/);
 assert.ok(ms<100,'native fast origin must not wait for slow failed sibling: '+ms);
 assert.equal(a.requests.length,2,'hedge limited to two initially independent hosts');
 const b=make(false,slow,fast),startB=Date.now();
 const old=await b.f.testCrawl([slow,fast],'https://example.org',2);
 assert.equal(old.length,1);
 assert.ok(Date.now()-startB>=140,'non-native retains complete sequential scan');
 const c=make(true,slow,'https://slow.example/e/other'),startC=Date.now();
 const same=await c.f.testCrawl([slow,'https://slow.example/e/other'],'https://example.org',2);
 assert.equal(same.length,0);
 assert.ok(Date.now()-startC>=140,'same-host URLs never fast-hedge');
 const d=make(true,slow,fast,true),startD=Date.now();
 const bridged=await d.f.testCrawl([slow,fast],'https://example.org',2);
 const actualMs=Date.now()-startD;
 assert.equal(bridged.length,1,'sync transport can still return late direct media');
 assert.ok(actualMs>=140,'sync native bridge cannot turn Promise.all into HTTP parallelism: '+actualMs);
 assert.equal(d.requests.length,2,'no hidden duplicate requests under sync native bridge');
 assert.ok(d.starts[1].at-d.starts[0].at>=140,
    'the fast second host must not start before a blocking native 522 completes');
 console.log('provider native hedge contract passed: async-fixture-fast=true, sync-android-tv-parallel=false, bounded=2');
})().catch(e=>{console.error(e);process.exitCode=1});
"""
# Pass source through stdin to avoid env/code quoting for the dynamic function.
runner = """const fs = require('node:fs');process.env.CRAWL_CODE=fs.readFileSync(0,'utf8');""" + js
result = subprocess.run(["node","-e",runner], input=json.dumps(crawl), text=True,
                        capture_output=True, timeout=15)
assert result.returncode == 0, (result.stdout, result.stderr)
print(result.stdout.strip())

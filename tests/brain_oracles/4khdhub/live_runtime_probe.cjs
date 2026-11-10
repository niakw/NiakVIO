#!/usr/bin/env node
'use strict';
// Read-only probe of the exact sandbox provider runtime, with real upstream
// requests and bounded media-header inspection. No credentials or URLs logged.
const fs = require('node:fs');
const vm = require('node:vm');
const {performance} = require('node:perf_hooks');

const [sourcePath,fixtureRaw] = process.argv.slice(2);
if (!sourcePath || !fixtureRaw) throw new Error('usage: live_runtime_probe.cjs <provider.js> <fixture-json>');
const fixture = JSON.parse(fixtureRaw);
const meta = fixture.mediaType === 'tv'
  ? {name:fixture.title,original_name:fixture.title,first_air_date:String(fixture.year)+'-01-01'}
  : {title:fixture.title,original_title:fixture.title,release_date:String(fixture.year)+'-01-01'};

globalThis.__nuvioCoreGetTmdbDataV1 = async () => ({metadata:meta});
globalThis.__probeProviderModel = {
  officialSite: 'https://4khdhub.one',
  knownSite: 'https://4khdhub.one',
};
const rawFetch = globalThis.fetch;
const traffic = [];
const domain = (url) => {
  try {return new URL(String(url)).hostname.toLowerCase();}
  catch {return 'invalid';}
};
globalThis.fetch = async (url,init={}) => {
  const host = domain(url);
  const controller = new AbortController();
  const abort = setTimeout(() => controller.abort(),10000);
  const started = performance.now();
  try {
    const response = await rawFetch(url,{...init,signal:controller.signal});
    traffic.push({
      host:host.slice(0,80),
      status:response.status,
      contentType:(response.headers.get('content-type')||'').split(';')[0].slice(0,75),
      latencyMs:Math.round(performance.now()-started),
    });
    return response;
  } catch(error) {
    traffic.push({
      host:host.slice(0,80),
      status:null,
      failure:String(error?.name||'request_error').slice(0,45),
      latencyMs:Math.round(performance.now()-started),
    });
    throw error;
  } finally {clearTimeout(abort);}
};
async function inspect(candidate) {
  const url = String(candidate?.url||'');
  if (!/^https?:\/\//i.test(url)) return {status:null,contentType:null,bytes:0,kind:'invalid_url'};
  const controller = new AbortController();
  const abort = setTimeout(()=>controller.abort(),8500);
  try {
    const response = await rawFetch(url,{
      redirect:'follow',signal:controller.signal,
      headers:{...candidate.headers,Range:'bytes=0-16383',Accept:'*/*'},
    });
    let buffer = Buffer.alloc(0);
    if (response.body?.getReader) {
      const reader=response.body.getReader();
      while (buffer.length < 16384) {
        const next=await reader.read();
        if(next.done) break;
        buffer=Buffer.concat([buffer,Buffer.from(next.value).subarray(0,16384-buffer.length)]);
      }
      try{await reader.cancel()}catch{}
    }
    const contentType=(response.headers.get('content-type')||'').split(';')[0].toLowerCase();
    const ascii=buffer.subarray(0,140).toString('utf8').toLowerCase();
    const kind=(/m3u8|application\/vnd\.apple/i.test(contentType)||ascii.includes('#extm3u'))?'hls'
      : buffer.length>8&&buffer.subarray(4,8).toString()==='ftyp'?'mp4'
      : buffer.length>=4&&buffer[0]===0x1a&&buffer[1]===0x45?'matroska'
      : /html|<!doctype|<html|cloudflare|captcha/.test(contentType+' '+ascii)?'challenge_or_html':'unknown';
    return {host:domain(response.url),status:response.status,contentType,bytes:buffer.length,kind};
  } catch(error) {return {status:null,bytes:0,kind:'network_error',error:String(error?.name||'error').slice(0,45)}}
  finally {clearTimeout(abort)}
}

(async()=>{
  const source=fs.readFileSync(sourcePath,'utf8');
  vm.runInThisContext('var NIAKVIO_PROVIDER_MODEL = globalThis.__probeProviderModel;\n'+source,
    {filename:'sandbox-provider-runtime.cjs',timeout:12000});
  const resolver=globalThis.__niakvioProviderRuntimeResolverV1;
  if (!resolver || typeof resolver.resolve!=='function') throw new Error('provider_resolver_not_registered');
  const started=performance.now();
  let rows=[],runtimeError=null;
  try {
    const result=await resolver.resolve([String(fixture.tmdbId),fixture.mediaType,
      fixture.season??null,fixture.episode??null]);
    rows=Array.isArray(result)?result:[];
  } catch(error) {runtimeError=String(error?.name||'error').slice(0,65)}
  const media=await Promise.all(rows.slice(0,2).map(inspect));
  const healthyMedia=media.filter(r=>[200,206].includes(r.status)&&['hls','mp4','matroska'].includes(r.kind));
  const res={
    fixture:fixture.name,
    upstreamRealNetwork:true,tmdbMetadataSource:'known_fixture_not_network_tmdb',
    elapsedMs:Math.round(performance.now()-started),
    attemptedRequests:traffic.length,
    upstreamHosts:[...new Set(traffic.map(r=>r.host))].slice(0,10),
    statuses:traffic.reduce((a,r)=>(a[String(r.status??r.failure)]=(a[String(r.status??r.failure)]||0)+1,a),{}),
    rawMediaRows:rows.length,
    probedMedia:media,
    candidateBinaryHeaders:healthyMedia.length,
    streamDecoded:false,workEpisodeIdentityDecoded:false,
    runtimeError,
  };
  process.stdout.write(JSON.stringify(res)+'\n');
  // A success means probe ran and contacted the provider, NOT that media works.
  if(!traffic.length || runtimeError) process.exitCode=2;
})().catch(e=>{process.stderr.write(String(e?.stack||e)+'\n');process.exitCode=1;});

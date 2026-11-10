'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');

const ORIGIN = 'https://animevost.fr';
const cases = {
  '/api/animes/jjk': {
    seasons: [
      {season_number:1,episodes:[{episode_number:1,streams:[
        {video_url:'https://media.example/S01E01.m3u8',language:'VOSTFR'}]}]},
      {season_number:0,episodes:[{episode_number:1,streams:[
        {video_url:'https://media.example/S00E01.m3u8',quality:'1080p',language:'VOSTFR'}],
        subtitles:[
          {url:'https://subs.example/JJK.S00E01.fr.vtt',language:'fr',season_number:0,episode_number:1},
          {url:'https://subs.example/JJK.S03E01.fr.vtt',language:'fr',season_number:3,episode_number:1}
        ]}]}
    ]
  }
};
globalThis.__nuvioMediaContext = {tmdbMetadata:{
  name:'Jujutsu Kaisen',original_name:'Jujutsu Kaisen'
}};
const requests = [];
let alternateSearchOnly=false;
globalThis.fetch = async (url) => {
  url=String(url);
  requests.push(url.replace(/\?.*/, '?q=[redacted]'));
  let data;
  if (url.startsWith(ORIGIN+'/api/anime/search?')) {
    data={results:alternateSearchOnly?[]:[{title:'Jujutsu Kaisen',slug:'jjk'}]};
  } else if (url.startsWith(ORIGIN+'/api/animes/search?')) {
    data={animes:[{title:'Jujutsu Kaisen',slug:'jjk'}],results:[]};
  } else {
    const endpoint=new URL(url);
    data=cases[endpoint.pathname];
  }
  return {ok:Boolean(data),status:data?200:404,json:async()=>data,
    text:async()=>JSON.stringify(data||{})};
};

const historical = require(path.resolve(process.argv[2]));
const current = require(path.resolve(process.argv[3]));
const repaired = require(path.resolve(__dirname,'provider_repaired_oracle.cjs'));
async function evaluate(provider) {
  return {
    special:await provider.getStreams('95479','tv',0,1),
    missing:await provider.getStreams('95479','tv',1,99),
    normal:await provider.getStreams('95479','tv',1,1)
  };
}
(async()=>{
  const broken = await evaluate(historical);
  const production = await evaluate(current);
  const oracle = await evaluate(repaired);
  assert.equal(broken.special?.[0]?.url,'https://media.example/S01E01.m3u8',
    'Real shared runtime should reproduce original S00->S01 fallback');
  assert.equal(broken.missing?.[0]?.url,'https://media.example/S01E01.m3u8',
    'Real shared runtime should reproduce missing-episode fallback');
  assert.equal(production.special?.[0]?.url,'https://media.example/S00E01.m3u8',
    'Current family Lego must now match the strict repaired oracle for S00');
  assert.equal(production.special?.[0]?.seasonNumber,0);
  assert.equal(production.special?.[0]?.episodeNumber,1);
  assert.deepEqual(production.missing,[],
    'Current shared runtime must not substitute the first episode for missing E99');
  assert.equal(production.normal?.[0]?.url,'https://media.example/S01E01.m3u8');
  alternateSearchOnly=true;
  const secondaryRoute=await evaluate(current);
  assert.equal(secondaryRoute.special?.[0]?.url,'https://media.example/S00E01.m3u8',
    '200 empty primary search must fall through to provider-owned secondary search route');
  assert.equal(oracle.special?.[0]?.url,'https://media.example/S00E01.m3u8');
  assert.equal(oracle.special?.[0]?.seasonNumber,0);
  assert.equal(oracle.special?.[0]?.episodeNumber,1);
  assert.equal(oracle.missing.length,0,'No first-episode fallback in repaired oracle');
  assert.equal(oracle.normal?.[0]?.url,'https://media.example/S01E01.m3u8');
  assert.deepEqual(oracle.special[0].subtitles.map(x=>x.url),
    ['https://subs.example/JJK.S00E01.fr.vtt'],
    'Detached subtitles from the wrong episode must never be attached');
  assert.ok(requests.length>0);
  console.log('BRAIN_PROVIDER_ORACLE_REPLAY provider=animevost-fr '+
    'baseline_wrong_s00=true baseline_wrong_missing_episode=true '+
    'oracle_correct_s00=true oracle_no_episode_fallback=true '+
    'shared_runtime_correct_s00=true shared_runtime_no_episode_fallback=true '+
    'secondary_search_empty_primary_recovered=true '+
    'subtitle_cross_episode_rejected=true '+
    'network_fixture_only=true decoded_media_validated=false');
})().catch(error=>{console.error(error.stack||error);process.exitCode=1});

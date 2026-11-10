#!/usr/bin/env node
// Read-only source-shape capture. Never stores media URLs, subtitles or page
// bodies; logs only response type and structural keys for a single known title.
const origin='https://animevost.fr';
const query='Jujutsu Kaisen';
const routes=[
  '/api/anime/search?q='+encodeURIComponent(query),
  '/api/animes/search?q='+encodeURIComponent(query)
];
const report={provider:'animevost-fr',lane:'anime',fixture:'Jujutsu Kaisen S01E01',
  observationOnly:true,playableProof:false,search:[],detail:null};
function rows(x){
  if(Array.isArray(x)) return x;
  if(!x||typeof x!=='object') return [];
  for(const k of ['results','data','items','animes']) {
    if(Array.isArray(x[k]))return x[k];
    if(Array.isArray(x[k]?.results))return x[k].results;
  }
  return [];
}
function shape(x){
  if(Array.isArray(x))return {kind:'array',length:x.length};
  if(!x||typeof x!=='object')return {kind:typeof x};
  const r=rows(x);
  return {kind:'object',keys:Object.keys(x).sort().slice(0,30),
    candidateCount:r.length,firstCandidateKeys:r[0]&&typeof r[0]==='object'
      ?Object.keys(r[0]).sort().slice(0,35):[],
    firstHasSlug:Boolean(r[0]?.slug),
    firstHasTitle:Boolean(r[0]?.title||r[0]?.name)};
}
async function get(route){
  try{
    const response=await fetch(origin+route,{
      signal:AbortSignal.timeout(12000),
      headers:{Accept:'application/json,text/plain,*/*','Accept-Language':'fr-FR,fr;q=0.9'},
      redirect:'follow'
    });
    const text=(await response.text()).slice(0,96_000);
    let parsed=null;
    try{parsed=JSON.parse(text)}catch{}
    return {status:response.status,finalHost:new URL(response.url).hostname,
      contentType:(response.headers.get('content-type')||'').split(';')[0],
      bytesObserved:text.length,parsed,shape:shape(parsed),htmlResponse:parsed===null&&/<html|<!doctype/i.test(text)};
  }catch(error){return {status:null,error:String(error?.code||error?.name||'network_error'),shape:{kind:'unavailable'}}}
}
let slug='';
for(const route of routes){
  const r=await get(route);
  report.search.push({route:route.split('?')[0],status:r.status,
    finalHost:r.finalHost||null,contentType:r.contentType||null,
    bytesObserved:r.bytesObserved||0,htmlResponse:Boolean(r.htmlResponse),
    shape:r.shape,error:r.error||null});
  const row=rows(r.parsed).find(item=>
    String(item?.title||item?.name||'').toLowerCase().includes('jujutsu')
    && /^[a-zA-Z0-9_-]{1,100}$/.test(String(item?.slug||'')));
  if(row)slug=String(row.slug);
}
if(slug){
  const detail=await get('/api/animes/'+encodeURIComponent(slug));
  const body=detail.parsed||{};
  const seasons=rows(body.seasons);
  report.detail={
    route:'/api/animes/{slug}',status:detail.status,contentType:detail.contentType||null,
    shape:detail.shape,seasonCount:seasons.length,
    firstSeasonKeys:seasons[0]&&typeof seasons[0]==='object'?Object.keys(seasons[0]).sort().slice(0,20):[],
    firstSeasonEpisodesCount:rows(seasons[0]?.episodes).length,
    firstEpisodeKeys:rows(seasons[0]?.episodes)[0]?Object.keys(rows(seasons[0]?.episodes)[0]).sort().slice(0,25):[],
    firstEpisodeStreamCount:rows(rows(seasons[0]?.episodes)[0]?.streams).length,
    error:detail.error||null
  };
}
console.log('FIELD_BRAIN_ORACLE_LIVE_PROVIDER_SHAPE '+JSON.stringify(report));

#!/usr/bin/env python3
"""Shared clean-room DLE anime runtime Lego.

Evidence-backed transport contract used by French-Manga and VoirAnime-Homes:
TMDB title -> POST /engine/ajax/search.php -> local news id ->
GET /engine/ajax/manga_episodes_api.php?id=... -> exact episode player URLs ->
NiakVIO's existing bounded direct-media crawler.

This is intentionally a fallback runtime: the provider's existing getStreams runs
first, and this resolver is used only when Core dispatch asks it to recover a
non-movie episodic request.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.DLE.ANIME.RUNTIME.V1"
MARKER = "NIAKVIO_DLE_ANIME_RUNTIME_V1"
SECURITY_MARKER = "NIAKVIO_HTML_FILTER_SCANNER_V1"

WRAPPER = r'''
/* NIAKVIO_DLE_ANIME_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function arr(v){return Array.isArray(v)?v:[]}
  function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
  function stripTags(v){var src=String(v==null?"":v),out="",inTag=false;for(var i=0;i<src.length;i++){var ch=src.charAt(i);if(ch==="<"){inTag=true;out+=" ";continue}if(ch===">"){inTag=false;continue}if(!inTag)out+=ch}return s(out).replace(/&(?:nbsp|amp|quot|#0*39);/gi," ").replace(/\s+/g," ").trim()}
  function absolute(v,base){try{return new URL(s(v).replace(/&amp;/gi,"&").replace(/\\\//g,"/"),base).toString()}catch(_e){return""}}
  function score(a,b){a=norm(a);b=norm(b);if(!a||!b)return 0;if(a===b)return 120;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 85;var aw=a.split(/\s+/),bw=b.split(/\s+/),n=0;for(var i=0;i<bw.length;i++)if(bw[i].length>2&&aw.indexOf(bw[i])>=0)n+=14;return n}
  function uniq(v){var o=[],seen=Object.create(null);for(var i=0;i<v.length;i++){var x=s(v[i]),k=norm(x);if(!x||!k||seen[k])continue;seen[k]=1;o.push(x)}return o}
  function request(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var canonical=s((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||ctx.canonicalMediaType||ctx.semanticType||args[1]||"tv").toLowerCase();
    if(canonical==="series"||canonical==="anime")canonical="tv";
    if(canonical==="movie")return null;
    var id=s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
    if(!/^\d+$/.test(id))return [];
    var season=Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode=Number((obj&&obj.episode)!=null?obj.episode:args[3])||1;
    var m=(obj&&obj.tmdbMetadata)||ctx.tmdbMetadata||{},titles=uniq([obj&&obj.title,obj&&obj.name,m.name,m.title,m.original_name,m.original_title,ctx.title]);
    return {tmdbId:id,type:"tv",season:season,episode:episode,titles:titles};
  }
  async function metadata(q){
    try{
      var fn=g&&g.__nuvioCoreGetTmdbDataV1;
      if(typeof fn==="function"){
        var z=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"}),m=z&&z.metadata||{};
        q.titles=uniq(q.titles.concat([m.name,m.title,m.original_name,m.original_title]));
        var alt=m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length&&q.titles.length<8;i++)q.titles=uniq(q.titles.concat([alt[i]&&(alt[i].title||alt[i].name)]));
      }
    }catch(_e){}
    return q;
  }
  function headers(referer,accept){var h={"User-Agent":c.userAgent,"Accept":accept||"*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","X-Requested-With":"XMLHttpRequest"};if(referer)h.Referer=referer;try{h.Origin=new URL(c.base).origin}catch(_e){}return h}
  async function responseText(url,init){try{var r=await g.fetch(url,Object.assign({redirect:"follow"},init||{}));if(!r||!r.ok)return null;return {text:await r.text(),url:r.url||url,status:r.status}}catch(_e){return null}}
  async function responseJson(url,init){var r=await responseText(url,init);if(!r)return null;try{return {data:JSON.parse(r.text),url:r.url,status:r.status}}catch(_e){return null}}
  function candidateWindows(html){
    var out=[],seen=Object.create(null),re=/<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]{0,1200}?)<\/a>/gi,m;
    while((m=re.exec(html||""))!==null&&out.length<80){
      var from=Math.max(0,m.index-900),to=Math.min((html||"").length,re.lastIndex+900),chunk=(html||"").slice(from,to),href=absolute(m[1],c.base),label=stripTags(m[2]);
      var idm=chunk.match(/(?:newsid|data-news-id|data-id)["'=:\s]+(\d{1,12})/i)||href.match(/[?&](?:newsid|id)=(\d{1,12})/i);
      var titlem=chunk.match(/class=["'][^"']*(?:short-title|search-item-title|title)[^"']*["'][^>]*>([\s\S]{0,400}?)<\//i),title=titlem?stripTags(titlem[1]):label;
      var key=(idm?idm[1]:"")+"|"+href;if((idm||href)&&!seen[key]){seen[key]=1;out.push({id:idm?idm[1]:"",url:href,title:title||label})}
    }
    var cfg=/(?:data-news-id|data-id)=["'](\d+)["'][\s\S]{0,500}?(?:data-title|title)=["']([^"']+)["']/gi;
    while((m=cfg.exec(html||""))!==null&&out.length<100){var k=m[1]+"|"+norm(m[2]);if(!seen[k]){seen[k]=1;out.push({id:m[1],url:"",title:stripTags(m[2])})}}
    return out
  }
  function seasonSignal(row,season){
    var text=s((row&&row.title)||"")+" "+s((row&&row.url)||""),m=text.match(/(?:^|[^a-z0-9])s(?:aison|eason)?[ ._\/-]*0*(\d{1,2})(?:[^0-9]|$)/i)||text.match(/(?:^|[^a-z0-9])0*(\d{1,2})(?:e|eme|ème)[ ._\/-]*saison(?:[^a-z0-9]|$)/i);
    if(!m)return 0;return Number(m[1])===Number(season)?1:-1
  }
  function bestCandidate(rows,title,season){var best=null,bestScore=0;for(var i=0;i<rows.length;i++){var r=rows[i],ss=seasonSignal(r,season);if(ss<0)continue;var sc=score(r.title,title)+(ss>0?45:(Number(season)>1?-12:0));if(sc>bestScore){best=r;bestScore=sc;if(best)best._seasonVerified=ss>0}}return bestScore>=42?best:null}
  async function searchOne(query,title,season){
    var body="query="+encodeURIComponent(query)+"&page=1",res=await responseText(c.base+"/engine/ajax/search.php",{method:"POST",headers:Object.assign(headers(c.base+"/","text/html,*/*"),{"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"}),body:body});
    if(!res||!res.text)return null;var rows=candidateWindows(res.text),best=bestCandidate(rows,title,season);if(!best)return null;
    if(!best.id&&best.url){var detail=await responseText(best.url,{headers:headers(c.base+"/","text/html,*/*")});if(detail){var idm=detail.text.match(/(?:newsid|data-news-id|data-id)["'=:\s]+(\d{1,12})/i)||detail.text.match(/[?&]newsid=(\d{1,12})/i);if(idm)best.id=idm[1]}}
    return best&&best.id?best:null;
  }
  function explicitSeasonBranch(data,season){
    if(!data||typeof data!=="object")return null;var target=Number(season)||1,containers=["seasons","saisons"];
    for(var ci=0;ci<containers.length;ci++){var box=data[containers[ci]];if(box&&typeof box==="object"&&box[String(target)]!=null)return box[String(target)]}
    for(var k in data){if(!Object.prototype.hasOwnProperty.call(data,k))continue;var low=s(k).toLowerCase().replace(/[_ .]+/g,"-"),m=low.match(/^(?:season|saison)-?0*(\d{1,2})$/)||low.match(/^s0*(\d{1,2})$/);if(m&&Number(m[1])===target)return data[k]}
    return null
  }
  function episodeFrom(value,episode,language,seasonVerified,depth){
    if(depth>5||!value||typeof value!=="object")return null;var keys=[String(episode),"episode-"+episode,"ep-"+episode,"e"+episode];
    for(var i=0;i<keys.length;i++)if(value[keys[i]]!=null)return {language:language||"VOSTFR",value:value[keys[i]],seasonVerified:!!seasonVerified};
    for(var k in value){if(!Object.prototype.hasOwnProperty.call(value,k))continue;var low=s(k).toLowerCase();if(low===String(episode)||low==="episode-"+episode||low==="ep-"+episode||low==="e"+episode)return {language:language||"VOSTFR",value:value[k],seasonVerified:!!seasonVerified}}
    return null
  }
  function episodeNodes(data,season,episode){
    if(!data||typeof data!=="object")return[];var langs=["vf","vostfr","VOSTFR","VF"],out=[],seen=Object.create(null);
    function add(hit){if(!hit)return;var key=s(hit.language)+"|";try{key+=JSON.stringify(hit.value)}catch(_e){key+=String(out.length)}if(seen[key])return;seen[key]=1;out.push(hit)}
    for(var li=0;li<langs.length;li++){var lang=langs[li],branch=data[lang];if(!branch||typeof branch!=="object")continue;var scoped=explicitSeasonBranch(branch,season),hit=scoped&&episodeFrom(scoped,episode,String(lang).toLowerCase()==="vf"?"VF":"VOSTFR",true,0);add(hit)}
    var rootScoped=explicitSeasonBranch(data,season);if(rootScoped){for(var lj=0;lj<langs.length;lj++){var sl=langs[lj],sb=rootScoped[sl];if(sb&&typeof sb==="object")add(episodeFrom(sb,episode,String(sl).toLowerCase()==="vf"?"VF":"VOSTFR",true,0))}add(episodeFrom(rootScoped,episode,"VOSTFR",true,0))}
    if(out.length)return out;
    for(var l=0;l<langs.length;l++){var lg=langs[l],generic=data[lg];if(!generic||typeof generic!=="object")continue;add(episodeFrom(generic,episode,String(lg).toLowerCase()==="vf"?"VF":"VOSTFR",false,0))}
    add(episodeFrom(data,episode,"VOSTFR",false,0));return out
  }
  function collectUrls(value,base,out,depth){
    if(depth>5||value==null||out.length>=20)return;
    if(typeof value==="string"){var text=value.replace(/\\\//g,"/");var direct=text.match(/https?:\/\/[^"'<>\s]+/gi)||[];for(var i=0;i<direct.length&&out.length<20;i++){var u=absolute(direct[i],base);if(u&&out.indexOf(u)<0)out.push(u)};var frame=/<iframe[^>]+src=["']([^"']+)["']/gi,m;while((m=frame.exec(text))!==null&&out.length<20){var f=absolute(m[1],base);if(f&&out.indexOf(f)<0)out.push(f)};return}
    if(Array.isArray(value)){for(var a=0;a<value.length;a++)collectUrls(value[a],base,out,depth+1);return}
    if(typeof value==="object")for(var k in value)if(Object.prototype.hasOwnProperty.call(value,k))collectUrls(value[k],base,out,depth+1)
  }
  async function resolveDle(q){
    q=await metadata(q);if(!q.titles.length)return [];
    var hit=null;for(var i=0;i<q.titles.length&&i<6&&!hit;i++){var title=q.titles[i],queries=Number(q.season)>1?[title+" saison "+q.season,title+" season "+q.season,title]:[title];for(var qi=0;qi<queries.length&&!hit;qi++)hit=await searchOne(queries[qi],title,q.season)}if(!hit||!hit.id)return [];
    var ep=await responseJson(c.base+"/engine/ajax/manga_episodes_api.php?id="+encodeURIComponent(hit.id),{headers:headers(hit.url||c.base+"/","application/json,text/plain,*/*")});if(!ep||!ep.data)return [];
    var nodes=episodeNodes(ep.data,q.season,q.episode);if(!nodes.length)return [];
    var buckets=[];for(var ni=0;ni<nodes.length;ni++){var node=nodes[ni];if(Number(q.season)>1&&!node.seasonVerified&&!hit._seasonVerified)continue;var players=[];collectUrls(node.value,hit.url||c.base+"/",players,0);if(!players.length)continue;var rows=[];if(typeof _crawlDirectMedia==="function")try{rows=await _crawlDirectMedia(players,hit.url||c.base+"/",3)}catch(_e){rows=[]}if(!Array.isArray(rows)||!rows.length){for(var p=0;p<players.length&&p<c.maxStreams;p++)rows.push({url:players[p],headers:{Referer:hit.url||c.base+"/"}})}var bucket=[];for(var z=0;z<rows.length&&bucket.length<c.maxStreams;z++){var raw=rows[z];if(!raw||!/^https?:\/\//i.test(s(raw.url)))continue;var r=Object.assign({},raw);r.provider=c.provider;r.name=r.name||c.name;r.title=r.title||c.name+" | "+node.language;r.language=node.language||r.language||"";bucket.push(r)}if(bucket.length)buckets.push(bucket)}
    var out=[],seen=Object.create(null),pos=0,advanced=true;while(out.length<c.maxStreams&&advanced){advanced=false;for(var bi=0;bi<buckets.length&&out.length<c.maxStreams;bi++){var bucket=buckets[bi];if(pos>=bucket.length)continue;advanced=true;var r=bucket[pos],key=s(r.url)+"|"+s(r.language);if(seen[key])continue;seen[key]=1;out.push(r)}pos++}return out
  }
  async function resolve(args,_ctx){var q=request(args);if(q===null)return null;if(!q||!q.tmdbId)return [];return await resolveDle(q)}
  try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:c.provider,resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "").rstrip("/"),
        "provider": str(cfg.get("provider") or "dle-anime"),
        "name": str(cfg.get("name") or cfg.get("provider") or "DLE Anime"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
        "maxStreams": max(1, min(int(cfg.get("max_streams") or 6), 12)),
    }
    if not payload["base"].startswith("https://"):
        raise ValueError("DLE anime runtime requires an https base")
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "scope": "episodic-anime-fallback-provider-resolver",
            "searchContract": "POST /engine/ajax/search.php query+page",
            "episodesContract": "GET /engine/ajax/manga_episodes_api.php?id=<local-news-id>",
            "mediaResolution": "existing-bounded-direct-media-crawler",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "signedMediaPersisted": False,
            "legacyExecutableSeed": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")

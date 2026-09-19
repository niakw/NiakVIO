#!/usr/bin/env python3
"""NiakVIO-owned YFlix TMDB DB -> encrypted AJAX -> terminal media runtime.

The clean-room chain follows the current public EncDecEndpoints contract:
TMDB -> enc-dec flix DB -> yflix episode/server ids -> encrypted AJAX ->
dec-movies-flix -> terminal host (including RapidShare dec-rapid).

No upstream provider JavaScript is embedded or executed.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.YFLIX.RUNTIME.V1"
MARKER = "NIAKVIO_YFLIX_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_YFLIX_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}var type=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||x.semanticType||x.canonicalMediaType||a[1]||"movie").toLowerCase();if(type==="series")type="tv";if(type!=="movie"&&type!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;var season=Number((o&&(o.season||o.seasonNumber))||x.season||a[2]||(type==="tv"?1:1))||1,episode=Number((o&&(o.episode||o.episodeNumber))||x.episode||a[3]||1)||1;return{type:type,id:id,season:season,episode:episode}}
function headers(ref,extra){var h={"User-Agent":c.userAgent,"Accept":"application/json,text/html,*/*","Accept-Language":"en-US,en;q=0.9","X-Requested-With":"XMLHttpRequest"};if(ref)h.Referer=ref;return Object.assign(h,extra||{})}
async function jsonReq(url,opt){try{var r=await g.fetch(url,opt||{headers:headers("")});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function post(url,body,ref){return await jsonReq(url,{method:"POST",headers:headers(ref,{"Content-Type":"application/json"}),body:JSON.stringify(body||{})})}
function value(v){for(var i=0;i<5;i++){if(v==null)return null;if(typeof v==="string"){try{v=JSON.parse(v);continue}catch(_e){return v}}if(Array.isArray(v))return v;if(typeof v!=="object")return v;if(Object.prototype.hasOwnProperty.call(v,"result")){v=v.result;continue}if(Object.prototype.hasOwnProperty.call(v,"data")&&Object.keys(v).length<=3){v=v.data;continue}return v}return v}
function firstRow(v){v=value(v);if(Array.isArray(v))return v.length?value(v[0]):null;if(v&&typeof v==="object"){if(Array.isArray(v.results))return v.results.length?value(v.results[0]):null;if(Array.isArray(v.items))return v.items.length?value(v.items[0]):null}return v&&typeof v==="object"?v:null}
async function db(q){return firstRow(await jsonReq(c.db+"/find?tmdb_id="+encodeURIComponent(q.id),{headers:headers("")}))}
function n(v){var x=Number(v);return Number.isFinite(x)?x:0}
function episodeFromDb(row,q){var eps=row&&row.episodes;if(!eps)return"";var sn=String(q.season),en=String(q.episode),hit=eps&&eps[sn]&&eps[sn][en];if(hit&&typeof hit==="object")return s(hit.eid||hit.id||hit.episode_id);if(Array.isArray(eps)){for(var i=0;i<eps.length;i++){var e=eps[i]||{};if((!e.season||n(e.season)===q.season)&&n(e.episode||e.number||e.ep)===q.episode){var id=s(e.eid||e.id||e.episode_id);if(id)return id}}}return""}
function contentId(row){var info=row&&row.info||{};return s(info.flix_id||info.flixId||row&&row.flix_id||row&&row.flixId||row&&row.id)}
async function enc(v){var j=await jsonReq(c.api+"/enc-movies-flix?text="+encodeURIComponent(s(v)),{headers:headers("")});return s(j&&(j.result||j.data||j))}
async function parseHtml(raw){raw=s(raw);if(!raw)return null;var j=await post(c.api+"/parse-html",{text:raw},"");return value(j)}
function walk(v,fn,path,depth){if(depth>10||v==null)return;if(Array.isArray(v)){for(var i=0;i<v.length;i++)walk(v[i],fn,path.concat(String(i)),depth+1);return}if(typeof v!=="object")return;fn(v,path);for(var k in v)walk(v[k],fn,path.concat(k),depth+1)}
function episodeCandidates(v,q){var exact=[],all=[];walk(v,function(o,path){var id=s(o.eid||o.episode_id||o.episodeId);if(!id)return;var label=path.join(" ")+" "+s(o.title||o.name||o.label),sn=n(o.season||o.season_number),ep=n(o.episode||o.number||o.ep);all.push(id);if((!sn||sn===q.season)&&((ep&&ep===q.episode)||new RegExp("(?:episode|ep)[^0-9]{0,3}"+q.episode+"\\b","i").test(label)))exact.push(id)},[],0);return exact.length?exact:all}
function lids(v){var out=[],seen={};walk(v,function(o){var id=s(o.lid||o.link_id||o.linkId);if(id&&!seen[id]){seen[id]=1;out.push(id)}},[],0);return out}
async function ajaxParsed(base,path){try{var r=await jsonReq(base+path,{headers:headers(base.replace(/\/ajax\/?$/,"")+"/")});var raw=r&&(r.result||r.data||r.html);return await parseHtml(raw)}catch(_e){return null}}
async function freshEid(base,row,q){var cid=contentId(row);if(!cid)return"";var token=await enc(cid);if(!token)return"";var parsed=await ajaxParsed(base,"/episodes/list?id="+encodeURIComponent(cid)+"&_="+encodeURIComponent(token)),ids=episodeCandidates(parsed,q);return ids[0]||""}
async function decoded(base,lid){var token=await enc(lid);if(!token)return null;var r=await jsonReq(base+"/links/view?id="+encodeURIComponent(lid)+"&_="+encodeURIComponent(token),{headers:headers(base.replace(/\/ajax\/?$/,"")+"/")}),cipher=s(r&&(r.result||r.data));if(!cipher)return null;return value(await post(c.api+"/dec-movies-flix",{text:cipher},""))}
function mediaRows(v){var out=[],seen={};walk(v,function(o){var keys=["url","file","src","source","stream","playbackUrl","playback_url"];for(var i=0;i<keys.length;i++){var u=s(o[keys[i]]);if(/^https?:\/\//i.test(u)&&!seen[u]){seen[u]=1;out.push({url:u,quality:s(o.quality||o.resolution||"Auto"),language:s(o.language||o.lang||"")})}}},[],0);return out}
function rapid(u){return /https?:\/\/(?:[^/]+\.)?(?:rapidshare\.cc|rapidairmax\.site)\//i.test(u)}
async function rapidRows(url){try{var media=url.replace(/\/e2?\//,"/media/"),r=await jsonReq(media,{headers:headers(url)}),cipher=s(r&&(r.result||r.data));if(!cipher)return[];var dec=value(await post(c.api+"/dec-rapid",{text:cipher,agent:c.userAgent},url));return mediaRows(dec)}catch(_e){return[]}}
async function crawlRows(url,ref){var rows=[];try{if(typeof _crawlDirectMedia==="function")rows=await _crawlDirectMedia([url],ref,2)}catch(_e){rows=[]}var out=[];for(var i=0;i<(rows||[]).length;i++){var r=rows[i],u=s(r&&r.url);if(/^https?:\/\//i.test(u))out.push({url:u,quality:s(r.quality||"Auto"),language:s(r.language||"")})}return out}
async function terminal(v,base){var candidates=mediaRows(v),out=[],seen={};for(var i=0;i<candidates.length&&out.length<c.maxStreams;i++){var row=candidates[i],u=row.url,rows=/\.(?:m3u8|mp4|webm)(?:[?#]|$)/i.test(u)?[row]:(rapid(u)?await rapidRows(u):await crawlRows(u,base));for(var j=0;j<rows.length&&out.length<c.maxStreams;j++){var x=rows[j],xurl=s(x.url);if(!/^https?:\/\//i.test(xurl)||seen[xurl])continue;seen[xurl]=1;out.push({name:"YFlix",title:"YFlix"+(x.quality&&x.quality!=="Auto"?" - "+x.quality:""),url:xurl,quality:x.quality||"Auto",language:x.language||"",provider:"yflix",isDirect:/\.(?:m3u8|mp4|webm)(?:[?#]|$)/i.test(xurl),headers:headers(base.replace(/\/ajax\/?$/,"")+"/")})}}return out}
async function resolveBase(base,row,q){var eid=episodeFromDb(row,q);if(!eid)eid=await freshEid(base,row,q);if(!eid)return[];var token=await enc(eid);if(!token)return[];var serverTree=await ajaxParsed(base,"/links/list?eid="+encodeURIComponent(eid)+"&_="+encodeURIComponent(token)),ids=lids(serverTree);for(var i=0;i<ids.length&&i<8;i++){var dec=await decoded(base,ids[i]);if(!dec)continue;var out=await terminal(dec,base);if(out.length)return out}return[]}
async function resolve(a){var q=req(a);if(!q)return null;var row=await db(q);if(!row)return[];for(var i=0;i<c.ajaxBases.length;i++){var out=await resolveBase(s(c.ajaxBases[i]).replace(/\/$/,""),row,q);if(out.length)return out}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"yflix",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "db": "https://enc-dec.app/db/flix",
        "api": "https://enc-dec.app/api",
        "ajaxBases": ["https://yflix.to/ajax", "https://1moviesz.to/ajax", "https://1movies.bz/ajax", "https://solarmovie.fi/ajax"],
        "maxStreams": 8,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["db"] = str(cfg.get("db") or "").rstrip("/")
    cfg["api"] = str(cfg.get("api") or "").rstrip("/")
    cfg["ajaxBases"] = [str(v).rstrip("/") for v in cfg.get("ajaxBases") or [] if str(v).strip()]
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "yflix-db-encrypted-ajax-v1",
            "identity": "tmdb-db-flix",
            "semanticLanes": ["movie", "tv"],
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")

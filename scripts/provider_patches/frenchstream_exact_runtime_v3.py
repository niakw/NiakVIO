#!/usr/bin/env python3
"""Frenchstream exact bounded movie + episodic transport runtime.

Movie identity is ``f-{tmdbId}`` -> ``film_api.php``. TV/anime transport uses
``s-{tmdbId}`` -> seasons -> episode JSON; anime remains semantically anime in
Core and is only aliased to TV inside the provider transport. When an anime has
no direct ``s-{tmdbId}`` tag, the runtime uses Core TMDB metadata to perform the
site's own DLE title search, derives the site's actual ``s-*`` tag, then reuses
the same bounded episodic transport. Movie resolution prioritizes currently
proven Vidzy terminals before FSVID/Uqload; episodic resolution keeps
FSVID/Uqload before Vidzy. Packed JavaScript and the current FSVID/Vidzy
base64+reverse+XOR transport are decoded structurally without eval. A stream is
returned only after a 2xx HLS response beginning with #EXTM3U. The known
Vidzy/FSVID troll HLS is always rejected. Core owns final output policy.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.FRENCHSTREAM.EXACT.RUNTIME.V3"

WRAPPER = r'''
/* NIAKVIO_FRENCHSTREAM_EXACT_RUNTIME_V3 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function S(v){return String(v==null?"":v).trim()}
function A(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g.__nuvioMediaContext||{}}catch(_e){}var explicit=S((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||a[1]||"").toLowerCase(),contextual=S(x.semanticType||x.canonicalMediaType||x.mediaType||x.type||"").toLowerCase();if(explicit==="series")explicit="tv";if(contextual==="series")contextual="tv";var semantic=explicit==="movie"?"movie":(explicit==="anime"||contextual==="anime"?"anime":(explicit||contextual));if(semantic!=="movie"&&semantic!=="tv"&&semantic!=="anime")return null;var transport=semantic==="anime"?"tv":semantic;return{type:transport,semanticType:semantic,tmdbId:S((o&&(o.tmdbId||o.id))||f||x.tmdbId),season:Number((o&&o.season)||a[2]||x.season)||1,episode:Number((o&&o.episode)||a[3]||x.episode)||1}}
function H(ref,accept){return{"User-Agent":c.ua,"Accept":accept||"*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7","Referer":ref||c.bases[0]+"/"}}
async function T(url,ref,accept){try{var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:H(ref,accept)});if(!r||!r.ok)return null;return{text:await r.text(),url:r.url||url}}catch(_e){return null}}
async function POST(url,body,ref,accept){try{var h=H(ref,accept);h["Content-Type"]="application/x-www-form-urlencoded";var r=await g.fetch(url,{method:"POST",redirect:"follow",headers:h,body:body});if(!r||!r.ok)return null;return{text:await r.text(),url:r.url||url}}catch(_e){return null}}
function O(url){var m=/^(https?:\/\/[^/]+)/i.exec(S(url));return m?m[1]+"/":""}
function K(n,r){var z="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";return n<r?z.charAt(n):K(Math.floor(n/r),r)+z.charAt(n%r)}
function Q(src,pos){while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;var q=src.charAt(pos);if(q!=="'"&&q!=='"')return null;var out="",i=pos+1;for(;i<src.length;i++){var ch=src.charAt(i);if(ch===q)return{v:out,p:i+1};if(ch==="\\"&&i+1<src.length){i++;var e=src.charAt(i);out+=e==="n"?"\n":e==="r"?"\r":e==="t"?"\t":e}else out+=ch}return null}
function U(src,off){var mark="eval(function(p,a,c,k,e,d)",st=src.indexOf(mark,off||0);if(st<0)return null;var call=src.indexOf("}(",st);if(call<0)return null;var p=Q(src,call+2);if(!p)return null;var pos=p.p;while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;if(src.charAt(pos)!==",")return null;var m=/^\s*(\d+)\s*,\s*(\d+)\s*,/.exec(src.slice(pos+1));if(!m)return null;var radix=Number(m[1]),count=Number(m[2]);if(radix<2||radix>62||count>10000)return null;pos=pos+1+m[0].length;var w=Q(src,pos);if(!w)return null;var vals=w.v.split("|"),d={};for(var n=count-1;n>=0;n--){var k=K(n,radix);d[k]=(n<vals.length&&vals[n])?vals[n]:k}return{decoded:p.v.replace(/\b\w+\b/g,function(x){return Object.prototype.hasOwnProperty.call(d,x)?d[x]:x}),next:call+2}}
function E(src){var full=S(src),pos=0;for(var i=0;i<8;i++){var row=U(full,pos);if(!row)break;full+="\n"+row.decoded;pos=row.next}return full}
function M(src){var full=E(src).replace(/\\\//g,"/").replace(/&amp;/g,"&").replace(/&quot;/g,'"');var out=[],seen={},re=/https?:\/\/[^\s"'<>\\]+(?:\.m3u8|\/hls2\/|\/master\.m3u8)[^\s"'<>\\]*/gi,m;while((m=re.exec(full))!==null){var u=m[0].replace(/[),\];}]+$/g,"");if(/\/troll\/master\.m3u8/i.test(u)||seen[u])continue;seen[u]=1;out.push(u)}return out}
function D64(v){var s=S(v).replace(/-/g,"+").replace(/_/g,"/").replace(/[^A-Za-z0-9+/=]/g,"");while(s.length%4)s+="=";var tab="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",out="";for(var i=0;i<s.length;i+=4){var a=tab.indexOf(s.charAt(i)),b=tab.indexOf(s.charAt(i+1)),cc=s.charAt(i+2)==="="?-1:tab.indexOf(s.charAt(i+2)),d=s.charAt(i+3)==="="?-1:tab.indexOf(s.charAt(i+3));if(a<0||b<0)continue;out+=String.fromCharCode((a<<2)|(b>>4));if(cc>=0)out+=String.fromCharCode(((b&15)<<4)|(cc>>2));if(d>=0)out+=String.fromCharCode(((cc&3)<<6)|d)}return out}
function X(src,hostname){var html=E(src),video="",m=/\}\)\(["']([A-Za-z0-9+/=_-]{50,})["']\)/.exec(html);if(m&&html.indexOf("reverse().join")>=0){var bin=D64(m[1]);if(bin){var hh=0;for(var j=0;j<hostname.length;j++)hh=(hh+hostname.charCodeAt(j))&255;var a=bin.split("").reverse().join(""),r="";for(var i=0;i<a.length;i++){var kk=(0x3d+i*89+hh)&255;r+=String.fromCharCode(a.charCodeAt(i)^kk)}if(/^https?:/i.test(r)&&/\.m3u8/i.test(r)&&!/\/troll\//i.test(r))video=r}}
if(!video){var re=/(?:var|let|const)\s*k=\[([0-9,\s]+)\],b=atob\(s\)[\s\S]*?return\s+\w+\}\)\(["']([A-Za-z0-9+/=_-]+)["']\)/g,z;while((z=re.exec(html))!==null){var nums=z[1].split(","),key=[];for(var q=0;q<nums.length;q++){var n=parseInt(nums[q],10);if(!isNaN(n))key.push(n)}if(!key.length)continue;var b=D64(z[2]),dec="";for(var k=0;k<b.length;k++)dec+=String.fromCharCode(b.charCodeAt(k)^key[k%key.length]);if(/^https?:/i.test(dec)&&/\.m3u8/i.test(dec)&&!/\/troll\//i.test(dec)){video=dec;break}}}return video}
function L(v){var x=S(v).toLowerCase();if(x==="vf"||x==="vff"||x==="vfq"||x==="default")return"VF";if(x==="vostfr")return"VOSTFR";if(x==="vo")return"VO";return x?x.toUpperCase():"VF"}
async function V(u,player,lang,host){if(!u||/\/troll\/master\.m3u8/i.test(u))return null;try{var r=await g.fetch(u,{method:"GET",redirect:"follow",headers:H(player,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*")});if(!r||!r.ok)return null;var b=await r.text();if(!/^#EXTM3U/m.test(b))return null;return{name:"Frenchstream | "+S(host).toUpperCase(),title:"Frenchstream | "+S(host).toUpperCase(),url:u,quality:"HD",language:L(lang),headers:H(player,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),provider:"frenchstream",isDirect:true}}catch(_e){return null}}
async function P(row,ref){var isFV=row.host==="vidzy"||row.host==="premium",self=O(row.url),p=await T(row.url,isFV&&self?self:ref,"text/html,*/*");if(!p)return null;if(isFV){var hm=/^https?:\/\/([^/]+)/i.exec(p.url||row.url),direct=X(p.text,hm?hm[1]:"");if(direct){var playRef=row.host==="vidzy"?"https://vidzy.live/":"https://fsvid.lol/",fv=await V(direct,playRef,row.lang,row.host);if(fv)return fv}}var xs=M(p.text);for(var i=0;i<xs.length&&i<5;i++){var ok=await V(xs[i],p.url,row.lang,row.host);if(ok)return ok}return null}
async function R(rows,ref){var out=[],seen={};for(var i=0;i<rows.length&&i<8;i++){var st=await P(rows[i],ref);if(st&&!seen[st.url]){seen[st.url]=1;out.push(st)}if(out.length>=4)break}return out}
function N(html){var out=[],seen={},pats=[/openModal\(["']?(\d+)/gi,/data-id=["']?(\d+)/gi,/[?&]newsid=(\d+)/gi,/href=["'][^"']*\/(\d+)-[^"']+["']/gi],m;for(var p=0;p<pats.length;p++){pats[p].lastIndex=0;while((m=pats[p].exec(html))!==null)if(!seen[m[1]]){seen[m[1]]=1;out.push(m[1])}}return out.slice(0,8)}
function movieRows(d){var out=[],players=d&&d.players,hosts=["vidzy","premium","uqload"],langs=["default","vostfr","vff","vfq","vo"],seen={};if(!players)return out;for(var h=0;h<hosts.length;h++){var name=hosts[h],v=players[name];if(!v)continue;if(typeof v==="string"){if(/^https?:\/\//i.test(v))out.push({url:v,lang:"default",host:name});continue}for(var l=0;l<langs.length;l++){var u=S(v[langs[l]]);if(/^https?:\/\//i.test(u)&&!seen[u]){seen[u]=1;out.push({url:u,lang:langs[l],host:name})}}}return out}
function seasonId(rows,n){if(!Array.isArray(rows)||!rows.length)return"";for(var i=0;i<rows.length;i++){var m=/saison\s*(\d+)/i.exec(S(rows[i]&&rows[i].title));if(m&&Number(m[1])===n)return S(rows[i].id)}return S(rows[Math.max(0,Math.min(rows.length-1,n-1))]&&rows[Math.max(0,Math.min(rows.length-1,n-1))].id)}
function tvRows(d,ep){var out=[],langs=["vf","vostfr","vo"],hosts=["premium","uqload","vidzy"],seen={};for(var l=0;l<langs.length;l++){var per=d&&d[langs[l]],players=per&&(per[String(ep)]||per[ep]);if(!players)continue;for(var h=0;h<hosts.length;h++){var u=S(players[hosts[h]]);if(/^https?:\/\//i.test(u)&&!seen[u]){seen[u]=1;out.push({url:u,lang:langs[l],host:hosts[h]})}}}return out}
async function MOV(base,q){var tag="f-"+q.tmdbId,sr=await T(base+"/index.php?do=xfsearch&xfname=tagz&xf="+encodeURIComponent(tag),base+"/","text/html,*/*");if(!sr)return[];var ids=N(sr.text);for(var i=0;i<ids.length;i++){var api=await T(base+"/engine/ajax/film_api.php?id="+encodeURIComponent(ids[i]),sr.url,"application/json,text/plain,*/*");if(!api)continue;var d=null;try{d=JSON.parse(api.text)}catch(_e){}if(!d||S(d.meta&&d.meta.tagz)!==tag)continue;var streams=await R(movieRows(d),api.url);if(streams.length)return streams}return[]}
async function TVTAG(base,q,tag){var sr=await T(base+"/engine/ajax/get_seasons.php?serie_tag="+encodeURIComponent(tag)+"&news_id=0",base+"/","application/json,text/plain,*/*");if(!sr)return[];var seasons=[];try{seasons=JSON.parse(sr.text)}catch(_e){}var sid=seasonId(seasons,q.season);if(!sid)return[];var ep=await T(base+"/data/eps_"+encodeURIComponent(sid)+".txt?v="+Math.floor(Date.now()/30000),base+"/index.php?newsid="+encodeURIComponent(sid),"application/json,text/plain,*/*");if(!ep)return[];var d=null;try{d=JSON.parse(ep.text)}catch(_e2){}return d?await R(tvRows(d,q.episode),ep.url):[]}
async function TV(base,q){return await TVTAG(base,q,"s-"+q.tmdbId)}
function uniq(v){var o=[],seen={};for(var i=0;i<v.length;i++){var x=S(v[i]);if(x&&!seen[x]){seen[x]=1;o.push(x)}}return o}
async function META(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:String(q.tmdbId),mediaType:"tv",tmdbNamespace:"tv"});if(z&&z.metadata)return z.metadata}}catch(_e){}return null}
function TITLES(meta){if(!meta||typeof meta!=="object")return[];var out=[meta.name,meta.original_name,meta.title,meta.original_title];var ats=meta.alternative_titles&&meta.alternative_titles.results;if(Array.isArray(ats))for(var i=0;i<ats.length&&i<12;i++)out.push(ats[i]&&ats[i].title);return uniq(out).slice(0,8)}
function SERIES_TAG(html){var pats=[/(?:data-tagz|sd-tagz|tagz)\s*=\s*["'][^"']*\b(s-\d+)\b[^"']*["']/i,/(?:data-tagz|sd-tagz|tagz)[^>]{0,200}?\b(s-\d+)\b/i,/\b(s-\d+)\b/i];for(var i=0;i<pats.length;i++){var m=pats[i].exec(html||"");if(m)return S(m[1])}return""}
async function ANIME_SEARCH(base,q){var meta=await META(q),titles=TITLES(meta);for(var ti=0;ti<titles.length;ti++){var body="do=search&subaction=search&story="+encodeURIComponent(titles[ti]),sr=await POST(base+"/index.php",body,base+"/","text/html,*/*");if(!sr)continue;var directTag=SERIES_TAG(sr.text);if(directTag){var direct=await TVTAG(base,q,directTag);if(direct.length)return direct}var ids=N(sr.text);for(var i=0;i<ids.length&&i<6;i++){var detail=await T(base+"/index.php?newsid="+encodeURIComponent(ids[i]),sr.url,"text/html,*/*");if(!detail)continue;var tag=SERIES_TAG(detail.text);if(!tag)continue;var rows=await TVTAG(base,q,tag);if(rows.length)return rows}}return[]}
async function resolve(a){var q=A(a);if(!q||!q.tmdbId)return q===null?null:[];for(var i=0;i<c.bases.length;i++){var base=c.bases[i].replace(/\/$/,""),x=q.type==="movie"?await MOV(base,q):await TV(base,q);if(x.length)return x;if(q.semanticType==="anime"){x=await ANIME_SEARCH(base,q);if(x.length)return x}}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"frenchstream",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    bases=cfg.get("bases") if isinstance(cfg.get("bases"),list) else ["https://french-stream.one"]
    payload={"bases":[str(v).rstrip("/") for v in bases if str(v).strip()],"ua":str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")}
    return replace_managed_fix(text,MANAGED_FIX_ID,WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":"))),data={"semanticLanes":["movie","tv","anime"],"animeTransportAlias":"tv","animeFallback":"core-tmdb-title -> DLE search -> site s-* tag -> episodic chain","argumentAuthority":"explicit movie remains authoritative; semantic anime survives tv transport via Core context","movieIdentity":"f-{tmdbId}","tvIdentity":"s-{tmdbId}","moviePlayerPriority":["vidzy","premium","uqload"],"tvPlayerPriority":["premium","uqload","vidzy"],"packedDecodeNoEval":True,"fsvidVidzyXorNoEval":True,"terminal":"2xx + EXTM3U","fixtureHardcodes":False,"runtimeResolverRegistration":True})

if __name__ == "__main__":
    raise SystemExit("patch module only")
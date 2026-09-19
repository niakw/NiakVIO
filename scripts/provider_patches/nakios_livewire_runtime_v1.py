#!/usr/bin/env python3
"""Nakios current Livewire search -> work snapshot -> verified Vidzy HLS runtime.

The provider homepage owns the current Livewire search snapshot and CSRF token.
Movie work pages serialize player URLs in their wire:snapshot payloads; V1 uses
only Vidzy because that branch has current terminal HLS proof. No fixture slugs,
player tokens, signed HLS URLs or session values are persisted.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.NAKIOS.LIVEWIRE.RUNTIME.V1"
MARKER = "NIAKVIO_NAKIOS_LIVEWIRE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_NAKIOS_LIVEWIRE_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function slug(v){return s(v).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
  function entity(v){return s(v).replace(/&quot;/g,'"').replace(/&#039;|&#39;/g,"'").replace(/&amp;/g,"&").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/\\\//g,"/")}
  function request(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var canonical=s((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType))||ctx.canonicalMediaType||ctx.mediaType||"").toLowerCase();
    if(canonical!=="movie")return null;
    var meta=(obj&&obj.tmdbMetadata)||ctx.tmdbMetadata||{};
    var title=s((obj&&(obj.title||obj.name))||meta.title||meta.name||meta.original_title||ctx.title||"");if(!title)return null;
    return {title:title,year:Number((obj&&obj.year)||meta.release_year||meta.year||ctx.year)||0};
  }
  function headers(referer,accept){return {"User-Agent":c.userAgent,"Accept":accept||"*/*","Referer":referer||c.site+"/"}}
  function cookies(resp){
    try{if(resp&&resp.headers&&typeof resp.headers.getSetCookie==="function"){var xs=resp.headers.getSetCookie();if(xs&&xs.length)return xs.map(function(x){return s(x).split(";",1)[0]}).join("; ")}}catch(_e){}
    try{var raw=resp&&resp.headers&&resp.headers.get&&resp.headers.get("set-cookie");if(raw)return raw.split(/,(?=[^;,]+=)/).map(function(x){return s(x).split(";",1)[0]}).join("; ")}catch(_e2){}
    return "";
  }
  async function home(){
    try{var r=await g.fetch(c.site+"/",{redirect:"follow",headers:headers(c.site+"/","text/html,*/*")});if(!r||!r.ok)return null;return {text:await r.text(),url:r.url||c.site+"/",cookie:cookies(r)}}catch(_e){return null}
  }
  function csrf(text){var m=/<meta\b[^>]*name=["']csrf-token["'][^>]*content=["']([^"']+)/i.exec(text||"");if(!m)m=/<meta\b[^>]*content=["']([^"']+)["'][^>]*name=["']csrf-token["']/i.exec(text||"");return entity(m&&m[1]||"")}
  function snapshots(text){var out=[],re=/wire:snapshot=(?:"([^"]+)"|'([^']+)')/gi,m;while((m=re.exec(text||""))!==null){var raw=entity(m[1]||m[2]||"");try{out.push({raw:raw,obj:JSON.parse(raw)})}catch(_e){}}return out}
  function searchSnapshot(text){var xs=snapshots(text);for(var i=0;i<xs.length;i++){var memo=xs[i].obj&&xs[i].obj.memo||{};if(s(memo.name)==="search-component")return xs[i].raw}return ""}
  function paths(text){
    var decoded=entity(text),out=[],seen={},re=/(?:href=)?["']?(\/(?:movie)\/[A-Za-z0-9._~%+-]+)["'\\<\s]/gi,m;
    while((m=re.exec(decoded))!==null){var p=m[1];if(!seen[p]){seen[p]=1;out.push(p)}}return out;
  }
  function scorePath(p,q){var ps=slug(p),ts=slug(q.title),score=0,toks=ts.split("-").filter(function(x){return x.length>=3&&x!=="the"&&x!=="film"&&x!=="movie"});for(var i=0;i<toks.length;i++)if(ps.indexOf(toks[i])>=0)score+=10;if(ps.indexOf(ts)>=0)score+=60;return score}
  async function search(q,h){
    var snap=searchSnapshot(h.text),token=csrf(h.text);if(!snap||!token)return null;
    var body=JSON.stringify({_token:token,components:[{snapshot:snap,updates:{q:q.title},calls:[]}]});
    var hs=headers(h.url,"application/json,*/*");hs["Content-Type"]="application/json";hs["X-Livewire"]="true";hs["Origin"]=c.site;if(h.cookie)hs["Cookie"]=h.cookie;
    try{var r=await g.fetch(c.site+"/livewire/update",{method:"POST",redirect:"follow",headers:hs,body:body});if(!r||!r.ok)return null;var raw=await r.text(),data;try{data=JSON.parse(raw)}catch(_e){return null}var html="";if(data&&Array.isArray(data.components)){for(var i=0;i<data.components.length;i++){var fx=data.components[i]&&data.components[i].effects||{};if(typeof fx.html==="string")html+="\n"+fx.html}}var ps=paths(html);if(!ps.length)return null;ps.sort(function(a,b){return scorePath(b,q)-scorePath(a,q)});return {path:ps[0],cookie:h.cookie,searchHtml:html}}catch(_e2){return null}
  }
  async function getText(url,referer,cookie){try{var hs=headers(referer,"text/html,*/*");if(cookie)hs["Cookie"]=cookie;var r=await g.fetch(url,{redirect:"follow",headers:hs});if(!r||!r.ok)return null;return {text:await r.text(),url:r.url||url}}catch(_e){return null}}
  function embeds(text){
    var decoded=entity(text),out=[],seen={},re=/https?:\/\/[^\s"'&<>\\]+/gi,m;while((m=re.exec(decoded))!==null){var u=m[0].replace(/[),\];}]+$/g,"");if(!/vidzy\.(?:live|org|cc)\//i.test(u))continue;if(!seen[u]){seen[u]=1;out.push(u)}}return out;
  }
  function hls(text){var decoded=entity(text),out=[],seen={},re=/https?:\/\/[^\s"'<>\\]+\.m3u8[^\s"'<>\\]*/gi,m;while((m=re.exec(decoded))!==null){var u=m[0];if(!seen[u]){seen[u]=1;out.push(u)}}return out}
  async function vidzy(embed,detail){var page=await getText(embed,detail,"");if(!page)return null;var xs=hls(page.text);for(var i=0;i<xs.length&&i<4;i++){try{var r=await g.fetch(xs[i],{redirect:"follow",headers:headers(page.url,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*")});if(r&&r.ok){var txt=await r.text();if(/^#EXTM3U/m.test(txt))return {url:xs[i],referer:page.url,manifest:txt}}}catch(_e){}}return null}
  function quality(text){var best=0,re=/RESOLUTION=\d+x(\d+)/gi,m;while((m=re.exec(text||""))!==null){var n=parseInt(m[1],10)||0;if(n>best)best=n}return best?best+"p":"HD"}
  async function resolve(args){
    var q=request(args);if(!q)return [];
    var h=await home();if(!h)return [];
    var hit=await search(q,h);if(!hit||!hit.path)return [];
    var detail=c.site+hit.path,page=await getText(detail,h.url,hit.cookie);if(!page)return [];
    var players=embeds(page.text),out=[],seen={};for(var i=0;i<players.length&&i<c.maxPlayers;i++){var media=await vidzy(players[i],page.url);if(!media||seen[media.url])continue;seen[media.url]=1;out.push({name:"Nakios | Vidzy",title:"Nakios | Vidzy",url:media.url,quality:quality(media.manifest),language:"VO",headers:headers(media.referer,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),provider:"nakios",isDirect:true});if(out.length>=c.maxStreams)break}return out;
  }
  function install(container,key){if(!container||typeof container[key]!=="function"||container[key].__niakvioNakiosLivewireV1)return false;var wrapped=async function(){return await resolve(arguments)};wrapped.__niakvioNakiosLivewireV1=true;container[key]=wrapped;return true}
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e2){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "site": str(cfg.get("site") or "https://nakios.live"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151 Safari/537.36"),
        "maxPlayers": int(cfg.get("max_players") or 4),
        "maxStreams": int(cfg.get("max_streams") or 3),
    }
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "identity": "catalog-title-livewire",
            "search": "home-csrf-search-component-snapshot",
            "workPlayers": "wire-snapshot-vidzy",
            "terminalProof": "hls-extm3u",
            "movieOnlyV1": True,
            "ephemeralValuesPersisted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")

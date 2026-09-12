#!/usr/bin/env python3
"""Vostfree current DLE search -> exact episode -> Uqload packed HLS runtime."""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VOSTFREE.DLE.UQLOAD.RUNTIME.V1"
MARKER = "NIAKVIO_VOSTFREE_DLE_UQLOAD_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VOSTFREE_DLE_UQLOAD_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function ent(v){return s(v).replace(/&quot;/g,'"').replace(/&#039;|&#39;/g,"'").replace(/&amp;/g,"&").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/\\\//g,"/")}
  function slug(v){return s(v).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
  function hdr(ref,accept){return {"User-Agent":c.ua,"Accept":accept||"*/*","Referer":ref||c.site+"/"}}
  function argsOf(a){
    var first=a[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g.__nuvioMediaContext||{}}catch(_e){}
    var type=s((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||a[1]||ctx.canonicalMediaType||ctx.mediaType||"").toLowerCase();
    if(type!=="anime")return null;
    var meta=(obj&&obj.tmdbMetadata)||ctx.tmdbMetadata||ctx.fixtureMetadata||{};
    return {tmdbId:s((obj&&(obj.tmdbId||obj.id))||first),title:s((obj&&(obj.title||obj.name))||meta.title||meta.name||meta.original_name||ctx.title||""),season:Number((obj&&obj.season)||a[2]||ctx.season)||1,episode:Number((obj&&obj.episode)||a[3]||ctx.episode)||1};
  }
  async function meta(q){
    if(q.title)return q;
    try{if(typeof _tmdb==="function"){var m=await _tmdb(q.tmdbId,"tv");if(m){q.title=s(m.title||(m.aliases&&m.aliases[0])||"")}}}catch(_e){}
    try{var ctx=g.__nuvioMediaContext||{},tm=ctx.tmdbMetadata||{};if(!q.title)q.title=s(tm.name||tm.title||tm.original_name||tm.original_title||"")}catch(_e2){}
    return q;
  }
  async function fetchText(url,opt){try{var r=await g.fetch(url,opt||{redirect:"follow",headers:hdr(c.site+"/","text/html,*/*")});if(!r||!r.ok)return null;return {text:await r.text(),url:r.url||url,status:r.status}}catch(_e){return null}}
  function score(u,title,season){var x=slug(u),t=slug(title),score=0,toks=t.split("-").filter(function(v){return v.length>=3&&v!=="the"&&v!=="les"&&v!=="des"});for(var i=0;i<toks.length;i++)if(x.indexOf(toks[i])>=0)score+=8;if(x.indexOf(t)>=0)score+=50;if(season>1&&(x.indexOf("saison-"+season)>=0||x.indexOf("season-"+season)>=0||x.indexOf("s"+season)>=0))score+=16;return score}
  async function search(q){
    var body="do=search&subaction=search&search_start=0&full_search=0&result_from=1&story="+encodeURIComponent(q.title);
    var hs=hdr(c.site+"/","text/html,*/*");hs["Content-Type"]="application/x-www-form-urlencoded";
    var r=await fetchText(c.site+"/index.php?do=search",{method:"POST",redirect:"follow",headers:hs,body:body});if(!r)return null;
    var out=[],seen={},re=/(?:href=)?["'](https?:\/\/[^"']+\.html|\/[^"']+\.html)["']/gi,m;while((m=re.exec(r.text))!==null){var u=m[1];if(u.charAt(0)==="/")u=c.site+u;if(u.indexOf(c.site)!==0||seen[u])continue;seen[u]=1;out.push(u)}
    out.sort(function(a,b){return score(b,q.title,q.season)-score(a,q.title,q.season)});return out.length?out[0]:null;
  }
  function content(text,id){
    var re=new RegExp("<div\\s+id=[\"']content_player_"+id+"[\"'][^>]*>([\\s\\S]*?)<\\/div>","i"),m=re.exec(text||"");
    return s((m&&m[1]||"").replace(/<[^>]+>/g," "));
  }
  function uqToken(text,episode){
    var startRe=new RegExp("<div\\s+id=[\"']buttons_"+episode+"[\"'][^>]*>","i"),sm=startRe.exec(text||"");if(!sm)return "";
    var start=sm.index,end=text.length,nextRe=new RegExp("<div\\s+id=[\"']buttons_"+(episode+1)+"[\"'][^>]*>","i"),next=nextRe.exec(text.slice(start+sm[0].length));
    if(next)end=start+sm[0].length+next.index;
    var block=text.slice(start,end),re=/<div\s+id=["']player_(\d+)["'][^>]*class=["']([^"']*uqload[^"']*)["'][^>]*>/ig,m;
    while((m=re.exec(block))!==null){var token=content(text,Number(m[1]));if(token)return token}return "";
  }
  async function uqPrefix(detail){
    var js=await fetchText(c.site+"/templates/Animix/js/anime.js",{redirect:"follow",headers:hdr(detail,"*/*")});if(!js)return "";
    var m=/(https:\/\/uqload\.[A-Za-z0-9.-]+\/embed-)/i.exec(js.text);return m?m[1]:"";
  }
  function key(n,radix){var chars="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";if(n<radix)return chars.charAt(n);return key(Math.floor(n/radix),radix)+chars.charAt(n%radix)}
  function jsstr(src,pos){
    while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;
    var q=src.charAt(pos);if(q!=="'"&&q!=='"')return null;
    var out="",i=pos+1;
    for(;i<src.length;i++){
      var ch=src.charAt(i);if(ch===q)return {v:out,p:i+1};
      if(ch==="\\"&&i+1<src.length){i++;var e=src.charAt(i);out+=e==="n"?"\n":e==="r"?"\r":e==="t"?"\t":e}else out+=ch;
    }
    return null;
  }
  function unpack(src){
    var mark="eval(function(p,a,c,k,e,d)",st=src.indexOf(mark);if(st<0)return src;
    var call=src.indexOf("}(",st);if(call<0)return src;
    var p=jsstr(src,call+2);if(!p)return src;
    var pos=p.p;while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;if(src.charAt(pos)!==",")return src;
    var mm=/^\s*(\d+)\s*,\s*(\d+)\s*,/.exec(src.slice(pos+1));if(!mm)return src;
    var radix=Number(mm[1]),count=Number(mm[2]);pos=pos+1+mm[0].length;
    var w=jsstr(src,pos);if(!w)return src;
    var vals=w.v.split("|"),dict={};for(var n=count-1;n>=0;n--){var k=key(n,radix);dict[k]=(n<vals.length&&vals[n])?vals[n]:k}
    return p.v.replace(/\b\w+\b/g,function(x){return Object.prototype.hasOwnProperty.call(dict,x)?dict[x]:x});
  }
  function media(text){var expanded=ent(text),last="";for(var i=0;i<3&&expanded!==last;i++){last=expanded;var u=unpack(expanded);if(u!==expanded)expanded+="\n"+u;else break}var out=[],seen={},re=/https?:\/\/[^\s"'<>\\]+\.m3u8[^\s"'<>\\]*/gi,m;while((m=re.exec(expanded))!==null){var u=m[0].replace(/[),\];}]+$/g,"");if(!seen[u]){seen[u]=1;out.push(u)}}return out}
  async function resolve(a){
    var q=argsOf(a);if(!q)return null;q=await meta(q);if(!q.title)return [];
    var detail=await search(q);if(!detail)return [];
    var page=await fetchText(detail,{redirect:"follow",headers:hdr(c.site+"/","text/html,*/*")});if(!page)return [];
    var token=uqToken(page.text,q.episode);if(!token)return [];
    var prefix=await uqPrefix(page.url);if(!prefix)return [];
    var embed=prefix+token+".html",epage=await fetchText(embed,{redirect:"follow",headers:hdr(page.url,"text/html,*/*")});if(!epage)return [];
    var xs=media(epage.text);for(var i=0;i<xs.length&&i<3;i++){try{var r=await g.fetch(xs[i],{redirect:"follow",headers:hdr(epage.url,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*")});if(r&&r.ok){var body=await r.text();if(/^#EXTM3U/m.test(body)){var lang=/vostfr/i.test(page.text+page.url)?"VOSTFR":/\bvf\b/i.test(page.text+page.url)?"VF":"VO";return [{name:"Vostfree | Uqload",title:"Vostfree | Uqload",url:xs[i],quality:"HD",language:lang,headers:hdr(epage.url,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),provider:"vostfree",isDirect:true}]}}}catch(_e){}}
    return [];
  }
  try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"vostfree",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    payload={"site":str(cfg.get("site") or "https://ipv4.vostfree.ws"),"ua":str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36")}
    wrapper=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,wrapper,data={"site":payload["site"],"search":"dle-post","episode":"buttons_N -> uqload player/content token","playerContract":"anime.js uqload embed prefix","terminal":"packed Uqload HLS + EXTM3U","semanticLane":"anime","fixtureHardcodes":False,"runtimeResolverRegistration":True})

if __name__ == "__main__":
    raise SystemExit("patch module only")

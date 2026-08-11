#!/usr/bin/env python3
from __future__ import annotations


def apply(text: str, **_kwargs) -> str:
    marker = "NUVIO_FRENCHSTREAM_RAW_TV_V1"
    if marker in text:
        return text
    wrapper = r'''
/* NUVIO_FRENCHSTREAM_RAW_TV_V1 */
(function(g){
  var BASE="https://fs16.lol";
  function clean(v){return String(v==null?"":v).trim()}
  function argsOf(args){var first=args[0],out={};if(first&&typeof first==="object"&&!Array.isArray(first))out=Object.assign({},first);else{out.tmdbId=String(first||"");out.mediaType=String(args[1]||"movie");out.season=args[2];out.episode=args[3]}out.tmdbId=String(out.tmdbId||out.id||"");out.mediaType=String(out.mediaType||out.type||"movie").toLowerCase();return out}
  async function request(url,json){try{var r=await g.fetch(url,{headers:{"User-Agent":"Mozilla/5.0","Accept":json?"application/json,text/plain,*/*":"text/html,*/*","Referer":BASE+"/"},redirect:"follow"});if(!r||!r.ok)return null;return json?await r.json():await r.text()}catch(_e){return null}}
  function seasonNumber(title){var m=clean(title).match(/saison\s*(\d+)/i);return m?Number(m[1]):0}
  function row(url,lang,host){return {name:"Frenchstream",title:"["+String(lang||"VF").toUpperCase()+"] "+String(host||"PLAYER").toUpperCase(),url:url,headers:{Referer:BASE+"/"},isDirect:false,language:String(lang||"vf").toLowerCase()}}
  async function rawTv(req){
    if(req.mediaType!=="tv"||!req.tmdbId)return [];
    var seasons=await request(BASE+"/engine/ajax/get_seasons.php?serie_tag=s-"+encodeURIComponent(req.tmdbId)+"&news_id=0",true);if(!Array.isArray(seasons)||!seasons.length)return [];
    var sn=Number(req.season)||1,target=null;for(var i=0;i<seasons.length;i++){if(seasonNumber(seasons[i]&&seasons[i].title)===sn){target=seasons[i];break}}if(!target)target=seasons[0];var sid=clean(target&&target.id);if(!sid)return [];
    var eps=await request(BASE+"/data/eps_"+encodeURIComponent(sid)+".txt?v="+Math.floor(Date.now()/30000),true);if(!eps||typeof eps!=="object")return [];
    var ep=String(Number(req.episode)||1),out=[],seen={};for(var li=0;li<["vf","vostfr","vo"].length;li++){var lang=["vf","vostfr","vo"][li],bucket=eps[lang],players=bucket&&(bucket[ep]||bucket[Number(ep)]);if(!players||typeof players!=="object")continue;for(var host in players){var u=clean(players[host]);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;out.push(row(u,lang,host))}}
    return out.slice(0,24)
  }
  function install(container,key){if(!container||typeof container[key]!=="function"||container[key].__nuvioFrenchstreamRawTv)return false;var original=container[key];var wrapped=async function(){var req=argsOf(arguments);if(req.mediaType==="tv"){var raw=await rawTv(req);if(raw.length)return raw}return original.apply(this,arguments)};wrapped.__nuvioFrenchstreamRawTv=true;wrapped.__nuvioOriginal=original;container[key]=wrapped;return true}
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''
    return text.rstrip() + "\n" + wrapper

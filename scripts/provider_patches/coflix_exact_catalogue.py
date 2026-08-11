#!/usr/bin/env python3
from __future__ import annotations


def apply(text: str, **_kwargs) -> str:
    marker = "NUVIO_COFLIX_EXACT_CATALOGUE_V1"
    if marker in text:
        return text
    wrapper = r'''
/* NUVIO_COFLIX_EXACT_CATALOGUE_V1 */
(function(g){
  var BASE="https://coflix.esq",TMDB="8265bd1679663a7ea12ac168da84d2e8";
  function clean(v){return String(v==null?"":v).replace(/&amp;/gi,"&").trim()}
  function norm(v){try{return clean(v).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return clean(v).toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}}
  function slug(v){return norm(v).replace(/\s+/g,"-")}
  function abs(v,b){try{return new URL(clean(v),b).href}catch(_e){return ""}}
  function argsOf(args){var first=args[0],out={};if(first&&typeof first==="object"&&!Array.isArray(first))out=Object.assign({},first);else{out.tmdbId=String(first||"");out.mediaType=String(args[1]||"movie");out.season=args[2];out.episode=args[3]}out.tmdbId=String(out.tmdbId||out.id||"");out.mediaType=String(out.mediaType||out.type||"movie").toLowerCase();return out}
  async function request(url,json){try{var r=await g.fetch(url,{headers:{"User-Agent":"Mozilla/5.0","Accept":json?"application/json,text/plain,*/*":"text/html,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.5","Referer":BASE+"/"},redirect:"follow"});if(!r||!r.ok)return null;return json?await r.json():await r.text()}catch(_e){return null}}
  async function meta(req){var kind=req.mediaType==="tv"?"tv":"movie",data=await request("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(req.tmdbId)+"?api_key="+TMDB+"&language=fr-FR",true);if(!data)return null;var title=clean(data.title||data.name),original=clean(data.original_title||data.original_name),date=clean(data.release_date||data.first_air_date),year=Number(date.slice(0,4))||0;return title?{title:title,original:original,year:year}:null}
  function identityOk(html,meta){var low=norm(String(html||"").replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," ").replace(/<[^>]+>/g," ")),want=norm(meta.title),orig=norm(meta.original);if(!want&&!orig)return false;var matched=(want&&low.indexOf(want)>=0)||(orig&&low.indexOf(orig)>=0);if(!matched)return false;if(meta.year){var years=String(html||"").match(/\b(?:19|20)\d{2}\b/g)||[];if(years.length&&years.indexOf(String(meta.year))<0)return false}return true}
  function playerRows(html,pageUrl,title){var out=[],seen={},patterns=[/<iframe\b[^>]*(?:src|data-src)=["']([^"']+)["']/gi,/<(?:a|button)\b[^>]*(?:data-src|data-url|data-embed|data-player)=["']([^"']+)["']/gi,/["'](https?:\\?\/\\?\/[^"'<>\s]+(?:lecteurvideo\.com\/embed\.php|\/embed[^"'<>\s]*|\/e\/[^"'<>\s]*))["']/gi];for(var p=0;p<patterns.length;p++){var re=patterns[p],m;while((m=re.exec(String(html||"")))!==null){var u=abs(String(m[1]).replace(/\\\//g,"/"),pageUrl);if(!/^https?:\/\//i.test(u)||seen[u]||/\.(?:css|js|png|jpe?g|gif|svg|ico)(?:[?#]|$)/i.test(u))continue;seen[u]=1;out.push({name:"Coflix",title:"[VF] Coflix - "+title,url:u,headers:{Referer:pageUrl},isDirect:false,language:"fr"});if(out.length>=16)return out}}return out}
  function anchors(html,base){var out=[],re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(String(html||"")))!==null){var u=abs(m[1],base),label=clean(m[2].replace(/<[^>]+>/g," ")).replace(/\s+/g," ");if(!u||!label||/\/wp-(?:content|admin|json|includes)\//i.test(u))continue;out.push({url:u,label:label})}return out}
  function score(row,meta){var t=norm(row.label),q=norm(meta.title),o=norm(meta.original),h=norm(row.url),s=0;if(t===q||o&&t===o)s=130;else if(q&&t.indexOf(q)>=0)s=96;else if(o&&t.indexOf(o)>=0)s=92;else{var words=q.split(" ").filter(function(w){return w.length>2}),hits=words.filter(function(w){return t.indexOf(w)>=0||h.indexOf(w)>=0}).length;if(words.length&&hits===words.length)s=84}if(meta.year){var years=(row.label+" "+row.url).match(/\b(?:19|20)\d{2}\b/g)||[];if(years.length&&years.indexOf(String(meta.year))<0)s-=100}return s}
  async function recover(req){var m=await meta(req);if(!m)return [];
    if(req.mediaType==="movie"){
      var slugs=[slug(m.title),slug(m.original)].filter(Boolean),tried={};for(var i=0;i<slugs.length;i++){for(var y=0;y<2;y++){var s=slugs[i]+(y&&m.year?"-"+m.year:""),u=BASE+"/film/"+s+"/";if(tried[u])continue;tried[u]=1;var page=await request(u,false);if(page&&identityOk(page,m)){var rows=playerRows(page,u,m.title);if(rows.length)return rows}}}
    }
    var searchUrl=BASE+"/?s="+encodeURIComponent(m.title),search=await request(searchUrl,false);if(!search)return [];var candidates=anchors(search,searchUrl).map(function(r){return {row:r,score:score(r,m)}}).filter(function(x){return x.score>=84}).sort(function(a,b){return b.score-a.score}).slice(0,5);for(var c=0;c<candidates.length;c++){var pageUrl=candidates[c].row.url,page=await request(pageUrl,false);if(!page||!identityOk(page,m))continue;var rows=playerRows(page,pageUrl,m.title);if(rows.length)return rows}return []
  }
  function install(container,key){if(!container||typeof container[key]!=="function"||container[key].__nuvioCoflixExact)return false;var original=container[key];var wrapped=async function(){var req=argsOf(arguments),rows=await recover(req);if(rows.length)return rows;return original.apply(this,arguments)};wrapped.__nuvioCoflixExact=true;wrapped.__nuvioOriginal=original;container[key]=wrapped;return true}
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''
    return text.rstrip() + "\n" + wrapper

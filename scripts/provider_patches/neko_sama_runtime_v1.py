#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix
import anime_catalogue_runtime_common as common

MANAGED_FIX_ID = "PROVIDER.NEKO-SAMA.RUNTIME.V1"
MARKER = "NIAKVIO_NEKO_SAMA_RUNTIME_V2"
CONTRACT_MARKER = "NIAKVIO_NEKO_SEARCH_SEASON_EPLISTER_V2"

NEKO_BLOCK = r'''  /* NIAKVIO_NEKO_SEARCH_SEASON_EPLISTER_V2 */
  function nekoEpisodes(html){
    var out=[],seen={},src=s(html),start=src.indexOf("eplister");if(start<0)return out;
    var end=src.indexOf("</ul>",start),block=end>=0?src.slice(start,end):src.slice(start,start+100000);
    var re=/<a[^>]+href=["']([^"']*episode-(\d+)(?:-saison-(\d+))?[^"'?]*)["'][^>]*>[\s\S]{0,500}?<(?:div|span)[^>]*class=["'][^"']*epl-num[^"']*["'][^>]*>\s*([^<]{0,30})<\/(?:div|span)>/gi,m;
    while((m=re.exec(block))!==null&&out.length<500){var u=abs(m[1],c.base),num=parseInt(s(m[4]),10)||parseInt(m[2],10),sn=m[3]?parseInt(m[3],10):null;if(!u||!num||seen[num])continue;seen[num]=1;out.push({url:u,num:num,season:sn,label:"Épisode "+num})}
    return out
  }
  function nekoRootSlug(url){var sl=s(url).replace(/.*\/anime\//,"").replace(/\/$/,"").toLowerCase();return sl.replace(/-(?:saison|saga)-\d+$/,"")}
  function nekoSiblingPages(html,sourceUrl,wantedSeason){
    var out=[],seen={},root=nekoRootSlug(sourceUrl),re=/href=["']([^"']*\/anime\/([a-z0-9-]+?)\/?)['"]/gi,m;
    while((m=re.exec(html||""))!==null&&out.length<40){var u=abs(m[1],c.base),sl=s(m[2]).toLowerCase();if(!u||seen[u]||sl===root||!(sl.indexOf(root+"-")===0))continue;seen[u]=1;var sm=sl.match(/-(?:saison|saga)-(\d+)/),sn=sm?parseInt(sm[1],10):null,rank=0;if(wantedSeason&&sn===wantedSeason)rank+=40;else if(wantedSeason&&sn)rank-=Math.min(20,Math.abs(sn-wantedSeason)*2);else if(sn==null)rank-=10;if(/(^|-)(oav|special|film|films|movie|recap|fan-letter)(-|$)/.test(sl))rank-=25;out.push({url:u,season:sn,score:rank})}
    out.sort(function(a,b){return b.score-a.score});return out
  }
  async function nekoFollowHub(url,html,wantedSeason,targetEp){
    var pages=nekoSiblingPages(html,url,wantedSeason),fallback=null;
    for(var i=0;i<pages.length&&i<5;i++){var h=await text(pages[i].url,"text/html,*/*"),eps=nekoEpisodes(h);if(!eps.length)continue;if(targetEp&&eps.some(function(e){return e.num===targetEp}))return {url:pages[i].url,episodes:eps};if(!fallback)fallback={url:pages[i].url,episodes:eps}}
    return fallback
  }
  function nekoCandidateScore(url,title,wantedSeason){
    var sl=s(url).replace(/.*\/anime\//,"").replace(/\/$/,"").toLowerCase(),sm=sl.match(/-(?:saison|saga)-(\d+)/),sn=sm?parseInt(sm[1],10):null,clean=sl.replace(/-(?:saison|saga)-\d+$/,"").replace(/-/g," "),v=score(clean,title);
    if(wantedSeason&&sn===wantedSeason)v+=40;else if(wantedSeason&&sn)v-=Math.min(60,Math.abs(sn-wantedSeason)*20);else if(sn==null)v-=5;if(/(^|-)(oav|special|film|films|movie|recap|fan-letter)(-|$)/.test(sl))v-=25;return v
  }
  async function nekoSearch(query){
    var h=await text(c.base+"/?s="+encodeURIComponent(query),"text/html,*/*");if(h.length<500)return [];
    var out=[],seen={},re=/href=["']([^"']*\/anime\/[^"']+)["']/gi,m;while((m=re.exec(h))!==null&&out.length<40){var u=abs(m[1],c.base);if(!u||seen[u])continue;seen[u]=1;out.push(u)}return out
  }
  async function nekoFindSeries(meta){
    for(var ai=0;ai<meta.aliases.length&&ai<5;ai++){
      var title=meta.aliases[ai],words=norm(title).split(/\s+/).filter(Boolean),queries=[title];if(words.length>2)queries.push(words.slice(0,2).join(" "));if(words.length>3)queries.push(words.slice(0,3).join(" "));
      var links=[];for(var qi=0;qi<queries.length&&!links.length;qi++)links=await nekoSearch(queries[qi]);
      links.sort(function(a,b){return nekoCandidateScore(b,title,meta.season)-nekoCandidateScore(a,title,meta.season)});
      for(var i=0;i<links.length&&i<7;i++){var u=links[i],h=await text(u,"text/html,*/*");if(h.length<1000)continue;var eps=nekoEpisodes(h);if(!eps.length){var hub=await nekoFollowHub(u,h,meta.season,meta.episode);if(hub)return hub;continue}if(eps.some(function(e){return e.num===meta.episode}))return {url:u,episodes:eps}}
      var direct=c.base+"/anime/"+slug(title)+"/",dh=await text(direct,"text/html,*/*");if(dh.length>1000){var deps=nekoEpisodes(dh);if(deps.some(function(e){return e.num===meta.episode}))return {url:direct,episodes:deps};var found=await nekoFollowHub(direct,dh,meta.season,meta.episode);if(found)return found}
    }
    return null
  }
  function nekoButtons(html){
    var out=[],groupRe=/<div[^>]*class=["'][^"']*server-group[^"']*["'][^>]*>([\s\S]*?)(?=<div[^>]*class=["'][^"']*server-group|<div[^>]*class=["'][^"']*server-divider|<!--\s*VF SERVERS|$)/gi,gm;
    while((gm=groupRe.exec(html||""))!==null&&out.length<20){var block=gm[1],lm=block.match(/<label[^>]*>([\s\S]*?)<\/label>/i),label=lm?s(lm[1].replace(/<[^>]+>/g," ")).toUpperCase():"",language=/^VF\b|FRENCH/.test(label)?"VF":/SUB|VOSTFR/.test(label)?"VOSTFR":"VOSTFR",re=/loadMi\(\{\s*value\s*:\s*['"]([A-Za-z0-9+/=]{20,})['"]\s*\}\)/g,m;
      while((m=re.exec(block))!==null&&out.length<20){try{var decoded=atob(m[1]),sm=decoded.match(/src=["']([^"']+)["']/i),u=sm?abs(sm[1].replace(/&#0*38;/g,"&"),c.base):"";if(u)out.push({url:u,language:language})}catch(_e){}}}
    return out
  }
  async function neko(meta){
    var series=await nekoFindSeries(meta);if(!series||!series.episodes||!series.episodes.length)return [];
    var ep=null;for(var i=0;i<series.episodes.length;i++)if(series.episodes[i].num===meta.episode){ep=series.episodes[i];break}if(!ep)return [];
    var eh=await text(ep.url,"text/html,*/*"),buttons=nekoButtons(eh),ordered=buttons.filter(function(b){return b.language==="VF"}).concat(buttons.filter(function(b){return b.language==="VOSTFR"})),out=[],have={};
    for(var j=0;j<ordered.length&&out.length<2;j++){var btn=ordered[j],language=btn.language;if(have[language])continue;var u=btn.url;if(u.indexOf("animes-sama.su")>=0){var ph=await text(u,"text/html,*/*"),im=ph.match(/class=["'][^"']*player-iframe[^"']*["'][\s\S]{0,400}?src=["']([^"']+)["']/i)||ph.match(/<iframe[^>]*src=["']([^"']+)["']/i);if(!im)continue;u=abs(im[1].replace(/&#0*38;/g,"&"),btn.url)}if(!u)continue;out.push(stream(u,c.name+" ["+language+"] "+(ep.label||("Épisode "+meta.episode)),language,"HD",null,{"Referer":ep.url}));have[language]=1}
    return out
  }'''


def _neko_wrapper() -> str:
    start = common.WRAPPER.find("  function nekoEpisodes(html){")
    end = common.WRAPPER.find("\n\n  function fullEpisodes(html){", start)
    if start < 0 or end < 0:
        raise ValueError("shared anime runtime Neko block anchors missing")
    return common.WRAPPER[:start] + NEKO_BLOCK + common.WRAPPER[end:]


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "mode": "neko_wp",
        "base": "https://animes-sama.su",
        "provider": "neko-sama",
        "name": "Neko-Sama",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/3",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "https://animes-sama.su").rstrip("/")
    payload = dict(cfg)
    wrapper = _neko_wrapper().replace("MARKER_PLACEHOLDER", MARKER).replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "identity": "core-tmdb-aliases-anime-only",
            "movieAliasAllowed": False,
            "animeTvTransportAliasAllowed": True,
            "legacyExecutableSeed": False,
            "runtimeRevision": CONTRACT_MARKER,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")

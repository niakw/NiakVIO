#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "non_display_recovery_runtime_v1.py"

_UNSAFE = (
    'function strip(v){return s(v).replace(/<scr' + 'ipt[\\s\\S]*?<\\/script>/gi," ")'
    '.replace(/<sty' + 'le[\\s\\S]*?<\\/style>/gi," ")'
    '.replace(/<[' + '^>]+>/g," ")'
    '.replace(/&[^;]+;/g," ").replace(/\\s+/g," ").trim()}'
)
_SAFE = (
    'function strip(v){var src=String(v==null?"":v),lower=src.toLowerCase(),out="",i=0,inTag=false;'
    'while(i<src.length){var ch=src.charAt(i);if(!inTag&&ch==="<"){'
    'if(lower.slice(i,i+7)==="<script"){var sc=lower.indexOf("</script",i+7);if(sc<0)break;'
    'var se=src.indexOf(">",sc+8);i=se<0?src.length:se+1;out+=" ";continue}'
    'if(lower.slice(i,i+6)==="<style"){var tc=lower.indexOf("</style",i+6);if(tc<0)break;'
    'var te=src.indexOf(">",tc+7);i=te<0?src.length:te+1;out+=" ";continue}'
    'inTag=true;out+=" ";i++;continue}if(inTag){if(ch===">")inTag=false;i++;continue}'
    'out+=ch;i++}return s(out).replace(/&[^;]+;/g," ").replace(/\\s+/g," ").trim()}'
)

_PLAYER_MARKER = 'NIAKVIO_ANIMESAMACO_PLAYER_DISCOVERY_V2'
_PLAYER_HELPER = r'''/* NIAKVIO_ANIMESAMACO_PLAYER_DISCOVERY_V2 */
function animeSamaPlayers(html,base){var out=[],seen={};function push(u){u=abs(u,base);if(u&&!seen[u]){seen[u]=1;out.push(u)}}var raw=s(html).replace(/\\\//g,"/"),m,re=/(?:videoUrls|filmUrls)\s*=\s*\{([^}]{0,1600})\}/gi;while((m=re.exec(raw))!==null){var pr=/(?:["']?(?:vf|vostfr|vo|v1|v2)["']?)\s*:\s*["'](https?:\/\/[^"'\s]+)["']/gi,p;while((p=pr.exec(m[1]))!==null)push(p[1])}var ir=/<iframe[^>]+src=["']([^"']+)["']/gi,i;while((i=ir.exec(raw))!==null)push(i[1]);return out}
'''
_PLAYER_INSERT_ANCHOR = '\n\nasync function animeSamaCo(q){'
_OLD_ROUTE = r'''var shells=hrefs(eh.text,/["'](https?:\/\/video\.sibnet\.ru\/shell\.php\?videoid=\d+[^"']*)["']/gi,eh.url);var rows=await crawl(shells,eh.url,"AnimeSamaCo","VOSTFR");'''
_NEW_ROUTE = r'''var shells=hrefs(eh.text,/["'](https?:\/\/video\.sibnet\.ru\/shell\.php\?videoid=\d+[^"']*)["']/gi,eh.url);var players=animeSamaPlayers(eh.text,eh.url);var rows=await crawl(uniq(shells.concat(players)),eh.url,"AnimeSamaCo","VOSTFR");'''

_SEARCH_MARKER = 'NIAKVIO_ANIMESAMACO_KEYWORD_FALLBACK_V3'
_SEARCH_HELPER = r'''/* NIAKVIO_ANIMESAMACO_KEYWORD_FALLBACK_V3 */
function animeSamaFallbackQueries(titles){var out=[],seen={};for(var i=0;i<titles.length&&out.length<6;i++){var clean=s(titles[i]).replace(/[\s:._-]+(?:season|saison)\s*\d+.*$/i,"").trim(),words=clean.split(/\s+/).filter(function(w){return w.length>=4});if(words.length>=2){var last=words[words.length-1],first=words[0];if(!seen[norm(last)]){seen[norm(last)]=1;out.push(last)}if(out.length<6&&!seen[norm(first)]){seen[norm(first)]=1;out.push(first)}}}return out}
'''
_SEARCH_INSERT_ANCHOR = 'async function animeSamaCo(q){'
_OLD_SEARCH = r'''async function animeSamaCo(q){q=await metadata(q);if(!q.titles.length)return[];var candidates=[],seen={};for(var ti=0;ti<q.titles.length&&ti<6;ti++){var t=q.titles[ti],r=await resp(c.base+"/template-php/defaut/fetch.php",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},body:"query="+encodeURIComponent(t),referer:c.base+"/"});if(!r)continue;var re=/<a[^>]+href=["']([^"']*\/anime\/[^"'#?]+\.html)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(r.text))!==null){var u=abs(m[1],c.base),label=strip(m[2]),sc=score(label||u,t);if(u&&!seen[u]&&sc>=35){seen[u]=1;candidates.push({url:u,score:sc,title:t})}}if(candidates.length>=4)break}'''
_NEW_SEARCH = r'''async function animeSamaCo(q){q=await metadata(q);if(!q.titles.length)return[];var candidates=[],seen={},queries=uniq(q.titles.concat(animeSamaFallbackQueries(q.titles)));for(var ti=0;ti<queries.length&&ti<10;ti++){var t=queries[ti],r=await resp(c.base+"/template-php/defaut/fetch.php",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},body:"query="+encodeURIComponent(t),referer:c.base+"/"});if(!r)continue;var re=/<a[^>]+href=["']([^"']*\/anime\/[^"'#?]+\.html)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(r.text))!==null){var u=abs(m[1],c.base),label=strip(m[2]),sc=0;for(var si=0;si<q.titles.length;si++)sc=Math.max(sc,score(label||u,q.titles[si]));if(sc<35)sc=score(label||u,t);if(u&&!seen[u]&&sc>=35){seen[u]=1;candidates.push({url:u,score:sc,title:t})}}if(candidates.length>=4)break}'''


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    changed = []

    if _SAFE not in text:
        count = text.count(_UNSAFE)
        if count != 1:
            raise SystemExit(f"expected one unsafe non-display strip anchor, got {count}")
        text = text.replace(_UNSAFE, _SAFE, 1)
        changed.append("html_scanner")
    if _UNSAFE in text or _SAFE not in text:
        raise SystemExit("non-display HTML security replacement failed closed")

    if _PLAYER_MARKER not in text:
        count = text.count(_PLAYER_INSERT_ANCHOR)
        if count != 1:
            raise SystemExit(f"expected one AnimeSamaCo helper insertion anchor, got {count}")
        text = text.replace(_PLAYER_INSERT_ANCHOR, '\n\n' + _PLAYER_HELPER + 'async function animeSamaCo(q){', 1)
        changed.append("animesamaco_player_helper")

    if _NEW_ROUTE not in text:
        count = text.count(_OLD_ROUTE)
        if count != 1:
            raise SystemExit(f"expected one AnimeSamaCo Sibnet-only route anchor, got {count}")
        text = text.replace(_OLD_ROUTE, _NEW_ROUTE, 1)
        changed.append("animesamaco_player_route")

    if _SEARCH_MARKER not in text:
        count = text.count(_SEARCH_INSERT_ANCHOR)
        if count != 1:
            raise SystemExit(f"expected one AnimeSamaCo search helper insertion anchor, got {count}")
        text = text.replace(_SEARCH_INSERT_ANCHOR, _SEARCH_HELPER + _SEARCH_INSERT_ANCHOR, 1)
        changed.append("animesamaco_keyword_helper")

    if _NEW_SEARCH not in text:
        count = text.count(_OLD_SEARCH)
        if count != 1:
            raise SystemExit(f"expected one AnimeSamaCo exact-title search anchor, got {count}")
        text = text.replace(_OLD_SEARCH, _NEW_SEARCH, 1)
        changed.append("animesamaco_keyword_search")

    if _PLAYER_MARKER not in text or _NEW_ROUTE not in text:
        raise SystemExit("AnimeSamaCo player discovery V2 replacement failed closed")
    if _SEARCH_MARKER not in text or _NEW_SEARCH not in text:
        raise SystemExit("AnimeSamaCo keyword fallback V3 replacement failed closed")

    TARGET.write_text(text, encoding="utf-8")
    if changed:
        print("NON_DISPLAY_RECOVERY_UPGRADED " + ",".join(changed))
    else:
        print("NON_DISPLAY_RECOVERY_ALREADY_CURRENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

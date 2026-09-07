#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = ROOT / "scripts" / "provider_patches" / "global_stream_identity_v1.py"
ANIME_PATH = ROOT / "scripts" / "provider_patches" / "anime_sama_runtime_v1.py"

IDENTITY_OLD = '''  if(movie&&year&&expectedYear&&year!==expectedYear)return-1;\n  var score=0,primary=expected[0]||"";\n  if(title&&expected.indexOf(title)>=0)score+=200;\n  else if(title&&primary&&(title.indexOf(primary)>=0||primary.indexOf(title)>=0))score+=90;\n  if(title&&primary){primary.split(" ").filter(function(v){return v.length>=3}).forEach(function(token){if(title.indexOf(token)>=0)score+=10})}\n  if(movie&&year&&expectedYear&&year===expectedYear)score+=40;\n  if(actualMedia&&expectedMedia&&actualMedia===expectedMedia)score+=60;\n  if(providerId)score+=15;\n  return score;\n'''
IDENTITY_NEW = '''  if(movie&&year&&expectedYear&&year!==expectedYear)return-1;\n  // NIAKVIO_CATALOGUE_TITLE_FAIL_CLOSED_V30\n  // Type/year/provider id are corroborating evidence only. They can never turn\n  // an unrelated catalogue row into a match. This prevents a successful HTTP\n  // search from selecting an arbitrary provider item when the requested title\n  // is absent.\n  if(!title||!expected.length)return-1;\n  var score=0,primary=expected[0]||"",identityMatched=false;\n  if(expected.indexOf(title)>=0){score+=200;identityMatched=true}\n  else if(primary&&(title.indexOf(primary)>=0||primary.indexOf(title)>=0)){score+=90;identityMatched=true}\n  if(!identityMatched)return-1;\n  if(title&&primary){primary.split(" ").filter(function(v){return v.length>=3}).forEach(function(token){if(title.indexOf(token)>=0)score+=10})}\n  if(movie&&year&&expectedYear&&year===expectedYear)score+=40;\n  if(actualMedia&&expectedMedia&&actualMedia===expectedMedia)score+=60;\n  if(providerId)score+=15;\n  return score;\n'''

ANIME_OLD = '''async function searchSlugs(base,title){var url=base+"/template-php/defaut/fetch.php",body="query="+encodeURIComponent(title),html=await text(url,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","Referer":base+"/"},body:body});if(!html)return[];var out=[],re=/href=["'][^"']*\\/catalogue\\/([^/"'#?]+)\\/?[^"']*["']/gi,m;while((m=re.exec(html))!==null){var s=txt(m[1]);if(s&&!out.includes(s))out.push(s);if(out.length>=2)break}return out}\n'''
ANIME_NEW = '''function searchSlugIdentityOk(expected,candidate){/* NIAKVIO_ANIME_SAMA_SEARCH_IDENTITY_V30 */var human=txt(candidate).replace(/-/g," ");try{var policy=g&&g.__nuvioIdentityPolicyV1;if(policy&&typeof policy.catalogueScore==="function")return Number(policy.catalogueScore({title:human,expectedTitles:[expected],strictIdentity:true}))>0}catch(_e){}var a=slug(expected),b=slug(candidate);return !!(a&&b&&(a===b||a.indexOf(b)>=0||b.indexOf(a)>=0))}\nasync function searchSlugs(base,title){var url=base+"/template-php/defaut/fetch.php",body="query="+encodeURIComponent(title),html=await text(url,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","Referer":base+"/"},body:body});if(!html)return[];var out=[],re=/href=["'][^"']*\\/catalogue\\/([^/"'#?]+)\\/?[^"']*["']/gi,m;while((m=re.exec(html))!==null){var s=txt(m[1]);if(s&&searchSlugIdentityOk(title,s)&&!out.includes(s))out.push(s);if(out.length>=2)break}return out}\n'''

changed = []
identity = IDENTITY_PATH.read_text(encoding="utf-8")
if "NIAKVIO_CATALOGUE_TITLE_FAIL_CLOSED_V30" not in identity:
    if identity.count(IDENTITY_OLD) != 1:
        raise AssertionError(f"catalogue score anchor drifted count={identity.count(IDENTITY_OLD)}")
    IDENTITY_PATH.write_text(identity.replace(IDENTITY_OLD, IDENTITY_NEW, 1), encoding="utf-8")
    changed.append("core_catalogue_score")

anime = ANIME_PATH.read_text(encoding="utf-8")
if "NIAKVIO_ANIME_SAMA_SEARCH_IDENTITY_V30" not in anime:
    if anime.count(ANIME_OLD) != 1:
        raise AssertionError(f"anime-sama search anchor drifted count={anime.count(ANIME_OLD)}")
    ANIME_PATH.write_text(anime.replace(ANIME_OLD, ANIME_NEW, 1), encoding="utf-8")
    changed.append("anime_sama_search")

print("CATALOGUE_IDENTITY_FAILCLOSED_V30 changed=" + (",".join(changed) if changed else "none") + " already_current=" + str(not changed).lower())

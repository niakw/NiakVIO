#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANIME_PATH = ROOT / "scripts" / "provider_patches" / "anime_sama_runtime_v1.py"

ANIME_OLD = '''async function searchSlugs(base,title){var url=base+"/template-php/defaut/fetch.php",body="query="+encodeURIComponent(title),html=await text(url,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","Referer":base+"/"},body:body});if(!html)return[];var out=[],re=/href=["'][^"']*\\/catalogue\\/([^/"'#?]+)\\/?[^"']*["']/gi,m;while((m=re.exec(html))!==null){var s=txt(m[1]);if(s&&!out.includes(s))out.push(s);if(out.length>=2)break}return out}\n'''
ANIME_NEW = '''function searchSlugIdentityOk(expected,candidate){/* NIAKVIO_ANIME_SAMA_SEARCH_IDENTITY_V30 */var a=slug(expected),b=slug(candidate);return !!(a&&b&&(a===b||a.indexOf(b)>=0||b.indexOf(a)>=0))}\nasync function searchSlugs(base,title){var url=base+"/template-php/defaut/fetch.php",body="query="+encodeURIComponent(title),html=await text(url,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","Referer":base+"/"},body:body});if(!html)return[];var out=[],re=/href=["'][^"']*\\/catalogue\\/([^/"'#?]+)\\/?[^"']*["']/gi,m;while((m=re.exec(html))!==null){var s=txt(m[1]);if(s&&searchSlugIdentityOk(title,s)&&!out.includes(s))out.push(s);if(out.length>=2)break}return out}\n'''

anime = ANIME_PATH.read_text(encoding="utf-8")
if "NIAKVIO_ANIME_SAMA_SEARCH_IDENTITY_V30" in anime:
    print("CATALOGUE_IDENTITY_FAILCLOSED_V30 changed=none already_current=true")
    raise SystemExit(0)
if anime.count(ANIME_OLD) != 1:
    raise AssertionError(f"anime-sama search anchor drifted count={anime.count(ANIME_OLD)}")
ANIME_PATH.write_text(anime.replace(ANIME_OLD, ANIME_NEW, 1), encoding="utf-8")
print("CATALOGUE_IDENTITY_FAILCLOSED_V30 changed=anime_sama_search already_current=false")

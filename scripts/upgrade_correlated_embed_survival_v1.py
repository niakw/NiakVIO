#!/usr/bin/env python3
"""Wire current embed resolvers into the existing correlated-player fallback contract.

This is intentionally narrow: only provider rows that explicitly carry the existing
__nuvioCorrelatedPlayerFallbackV1 proof may survive media enrichment when bounded
resolution cannot prove direct media. The terminal sanitizer/runtime safety remain
responsible for accepting only known player-like routes and clearing the private proof.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one hook, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


changed = []

media = ROOT / "scripts/provider_patches/global_media_enrichment_v1.py"
if replace_once(
    media,
    '"implementationRevision": "scoped-playback-context-v9-browser-default-ua",',
    '"implementationRevision": "scoped-playback-context-v10-correlated-player-survival",',
):
    changed.append(str(media.relative_to(ROOT)))

old_anchor = 'function refererOf(row,u){var h=baseHeaders(row),k=keyOf(h,"Referer");return s(k?h[k]:(row&&(row.referer||row.referrer||row.playerUrl||row.embedUrl||row.pageUrl))||u)}\n'
new_anchor = old_anchor + r'''function correlatedPlayerFallback(row,u){
  if(!row||typeof row!=="object"||!/^https?:\/\//i.test(s(u)))return false;
  var proof=row.__nuvioCorrelatedPlayerFallbackV1;
  if(!proof||typeof proof!=="object"||s(proof.url)!==s(u))return false;
  try{
    var parsed=new URL(s(u)),path=s(parsed.pathname).toLowerCase();
    if(/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return true;
    if(/\/(?:shell|video|stream)(?:\.php|[/?#.-]|$)/i.test(path))return true;
  }catch(_e){}
  return false;
}
'''
if replace_once(media, old_anchor, new_anchor):
    if str(media.relative_to(ROOT)) not in changed:
        changed.append(str(media.relative_to(ROOT)))

old_enrich = 'if(i<c.maxRows){var ref=refererOf(row,u),jar=[],found=await resolve(u,row,ref,0,{},jar);for(var j=0;j<found.length;j++)add(clone(row,found[j]));if(found.length)continue}/* Unresolved player/download pages are not playable streams. */}return out}'
new_enrich = 'if(i<c.maxRows){var ref=refererOf(row,u),jar=[],found=await resolve(u,row,ref,0,{},jar);for(var j=0;j<found.length;j++)add(clone(row,found[j]));if(found.length)continue;if(c.preserveOriginal&&correlatedPlayerFallback(row,u)){add(row);continue}}/* Unresolved uncorrelated player/download pages are not playable streams. */}return out}'
if replace_once(media, old_enrich, new_enrich):
    if str(media.relative_to(ROOT)) not in changed:
        changed.append(str(media.relative_to(ROOT)))

provider_hooks = [
    (
        ROOT / "scripts/provider_patches/allwish_current_runtime_v1.py",
        'streams.push({name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName+(streams.length?" #"+(streams.length+1):""),url:u,headers:{Referer:watch,Origin:BASE}});',
        'streams.push({name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName+(streams.length?" #"+(streams.length+1):""),url:u,headers:{Referer:watch,Origin:BASE},__nuvioCorrelatedPlayerFallbackV1:{url:u}});',
    ),
    (
        ROOT / "scripts/provider_patches/flemmix_current_runtime_v1.py",
        'return {name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName+(index?" #"+(index+1):""),url:u,headers:{Referer:ref,Origin:BASE}}',
        'return {name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName+(index?" #"+(index+1):""),url:u,headers:{Referer:ref,Origin:BASE},__nuvioCorrelatedPlayerFallbackV1:{url:u}}',
    ),
    (
        ROOT / "scripts/provider_patches/allanime_current_runtime_v1.py",
        'return {name:name,title:name+(index?" #"+(index+1):""),url:u,headers:{Referer:finalEp}}',
        'return {name:name,title:name+(index?" #"+(index+1):""),url:u,headers:{Referer:finalEp},__nuvioCorrelatedPlayerFallbackV1:{url:u}}',
    ),
    (
        ROOT / "scripts/provider_patches/moviebox_current_embed_v2.py",
        'return [{name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName,url:src,headers:{Referer:REFERER}}];',
        'return [{name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName,url:src,headers:{Referer:REFERER},__nuvioCorrelatedPlayerFallbackV1:{url:src}}];',
    ),
    (
        ROOT / "scripts/provider_patches/wookafr_showvideo_base64_v1.py",
        'return {name:name,title:name+(index?" #"+(index+1):""),url:row.url,headers:row.referer?{Referer:row.referer}:undefined};',
        'return {name:name,title:name+(index?" #"+(index+1):""),url:row.url,headers:row.referer?{Referer:row.referer}:undefined,__nuvioCorrelatedPlayerFallbackV1:{url:row.url}};',
    ),
]

for path, old, new in provider_hooks:
    if replace_once(path, old, new):
        changed.append(str(path.relative_to(ROOT)))

print("CORRELATED_EMBED_SURVIVAL_V1_OK changed=" + (",".join(changed) if changed else "none"))

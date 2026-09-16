#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "scripts/provider_patches/mugiwarastream_packed_runtime_v1.py"
t = p.read_text(encoding="utf-8")

old_tmdb = '''  async function tmdbTitle(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn!=="function"||!q.tmdbId)return"";var z=await fn({tmdbId:String(q.tmdbId),mediaType:"movie",tmdbNamespace:"movie"}),m=z&&z.metadata;if(!m)return"";return s(m.title||m.name||m.original_title||m.original_name)}catch(_e){return""}}\n'''
new_tmdb = '''  async function tmdbTitle(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn!=="function"||!q.tmdbId)return"";var kind=q.type==="movie"?"movie":"tv",z=await fn({tmdbId:String(q.tmdbId),mediaType:kind,tmdbNamespace:kind}),m=z&&z.metadata;if(!m)return"";return s(m.title||m.name||m.original_title||m.original_name)}catch(_e){return""}}\n  /* NIAKVIO_MUGIWARA_SAME_ORIGIN_LOOKUP_V2 */\n  function lookupHeaders(){var h=headers(c.base+"/","application/json, text/plain, */*");h["Sec-Fetch-Site"]="same-origin";h["Sec-Fetch-Mode"]="cors";h["Sec-Fetch-Dest"]="empty";return h}\n  async function discoverPage(q){var title=await tmdbTitle(q);if(!title)return"";try{var u=c.base+"/api/suggest/lookup?q="+encodeURIComponent(title),r=await g.fetch(u,{method:"GET",redirect:"follow",headers:lookupHeaders()});if(!r||!r.ok)return"";var payload=JSON.parse(await r.text()),rows=Array.isArray(payload&&payload.results)?payload.results:[],chosen=payload&&payload.exact&&payload.exact.slug?payload.exact:null,target=norm(title);for(var i=0;i<rows.length;i++){var row=rows[i]||{};if(norm(row.anime)===target||norm(row.matched)===target){chosen=row;break}}if(!chosen&&rows.length)chosen=rows[0];var slug=s(chosen&&chosen.slug);return slug?c.base+"/catalogue/"+encodeURIComponent(slug):""}catch(_e){return""}}\n'''
if old_tmdb in t:
    t = t.replace(old_tmdb, new_tmdb, 1)
elif "NIAKVIO_MUGIWARA_SAME_ORIGIN_LOOKUP_V2" not in t:
    raise SystemExit("tmdbTitle anchor drifted")

old_resolve = '''/* NIAKVIO_MUGIWARA_SPECIALIZED_FALLBACK_PRIORITY_V1 */if(pageUrl){var specialized=await fallback(pageUrl,q);if(Array.isArray(specialized)&&specialized.length)return specialized;/* NIAKVIO_MUGIWARA_EPISODE_FAIL_CLOSED_V2 */if(q.type!=="movie")return[]}if(Array.isArray(nativeResult)&&nativeResult.length)return nativeResult;return[]}\n'''
new_resolve = '''/* NIAKVIO_MUGIWARA_SPECIALIZED_FALLBACK_PRIORITY_V1 */if(!pageUrl)pageUrl=await discoverPage(q);if(pageUrl){var specialized=await fallback(pageUrl,q);if(Array.isArray(specialized)&&specialized.length)return specialized;/* NIAKVIO_MUGIWARA_EPISODE_FAIL_CLOSED_V2 */if(q.type!=="movie")return[]}if(Array.isArray(nativeResult)&&nativeResult.length)return nativeResult;return[]}\n'''
if old_resolve in t:
    t = t.replace(old_resolve, new_resolve, 1)
elif new_resolve not in t:
    raise SystemExit("resolve fallback anchor drifted")

p.write_text(t, encoding="utf-8")
print("Mugiwara discovery V2 staged")

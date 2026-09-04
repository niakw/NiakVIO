#!/usr/bin/env python3
"""Centralize TMDB access in Core without embedding credentials.

Provider bundles and presentation layers consume one Core capability:
``globalThis.__nuvioCoreGetTmdbDataV1(request)``. The request contains only
TMDB identity/transport coordinates; the function owns cache and authentication
through a host runtime credential or Nuvio native bridge and returns metadata
only. No credential is serialized or returned to provider code.

This migration is intentionally idempotent and fails if an unexpected legacy
shape remains, so reconstruction cannot silently re-introduce embedded secrets
or independent TMDB clients.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
PROVIDER_BASE = ROOT / "scripts" / "provider_base_store.py"
PRESENTATION = ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py"


def replace_optional(text: str, old: str, new: str) -> tuple[str, bool]:
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def patch_core() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    changed = False

    old_doc = """TMDB API metadata is authoritative when available. The build may embed an\nobfuscated runtime-only TMDB v3 API key generated from the repository secret;\nthe plaintext key is never committed and is never passed into provider business\nlogic. Object-style requests can also carry trusted TMDB metadata directly.\n"""
    new_doc = """TMDB API metadata is authoritative when available. Core owns one dynamic\nmetadata capability backed by request context/cache, a credential explicitly\nsupplied by the host runtime/CI, or the trusted native fetch bridge. Provider\nbundles never embed, receive, recover or decrypt a TMDB credential.\n"""
    text, did = replace_optional(text, old_doc, new_doc)
    changed |= did

    text, did = replace_optional(
        text,
        'RUNTIME_KEY_PATH = ROOT / "runtime" / "tmdb-runtime-key.json"\n\n\n',
        '',
    )
    changed |= did

    start = text.find("def _runtime_key_payload() -> dict[str, Any]:\n")
    if start >= 0:
        end = text.find("\n\ndef _strip_existing", start)
        if end < 0:
            raise AssertionError("embedded TMDB payload helper end anchor drifted")
        text = text[:start] + text[end + 2 :]
        changed = True

    text, did = replace_optional(text, '        **_runtime_key_payload(),\n', '')
    changed |= did

    js_start = text.find('function embeddedKey(){\n')
    if js_start >= 0:
        js_end = text.find('function localKey(){\n', js_start)
        if js_end < 0:
            raise AssertionError("embeddedKey/localKey source anchor drifted")
        text = text[:js_start] + text[js_end:]
        changed = True

    old_local = '''function localKey(){\n  var key="";\n  try{key=normalizeKey(g&&g.TMDB_API_KEY);if(key)return key}catch(_){}\n  try{if(typeof TMDB_API_KEY!=="undefined"){key=normalizeKey(TMDB_API_KEY);if(key)return key}}catch(_){}\n  try{return normalizeKey(embeddedKey())}catch(_){return""}\n}\n'''
    new_local = '''function localKey(){\n  var key="";\n  try{key=normalizeKey(g&&g.TMDB_API_KEY);if(key)return key}catch(_){}\n  try{if(typeof TMDB_API_KEY!=="undefined"){key=normalizeKey(TMDB_API_KEY);if(key)return key}}catch(_){}\n  return"";\n}\n'''
    text, did = replace_optional(text, old_local, new_local)
    changed |= did

    old_timeout = 'function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}\n'
    new_timeout = old_timeout + 'function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_){return false}}\n'
    if 'function nativeFetchBridge(){' not in text:
        text, did = replace_optional(text, old_timeout, new_timeout)
        if not did:
            raise AssertionError("native TMDB bridge insertion anchor drifted")
        changed = True

    old_api = '''async function apiJson(url){\n  var key=localKey(),token=localToken();\n  if(!g||typeof g.fetch!=="function"||(!key&&!token))return{state:"unavailable",value:null};\n  try{\n'''
    new_api = '''async function apiJson(url){\n  var key=localKey(),token=localToken(),nativeBridge=nativeFetchBridge();\n  if(!g||typeof g.fetch!=="function"||(!key&&!token&&!nativeBridge))return{state:"unavailable",value:null};\n  try{\n'''
    if new_api not in text:
        text, did = replace_optional(text, old_api, new_api)
        if not did:
            raise AssertionError("TMDB apiJson runtime/native bridge anchor drifted")
        changed = True

    old_probe = '    var probe=await apiJson("https://api.themoviedb.org/3/"+namespace+"/"+encodeURIComponent(id)+"?append_to_response=keywords,alternative_titles,external_ids&language=fr-FR");\n'
    new_probe = '''    var append=namespace==="movie"?"keywords,alternative_titles,external_ids,release_dates":"keywords,alternative_titles,external_ids,content_ratings";\n    var probe=await apiJson("https://api.themoviedb.org/3/"+namespace+"/"+encodeURIComponent(id)+"?append_to_response="+encodeURIComponent(append)+"&language=fr-FR");\n'''
    if new_probe not in text:
        text, did = replace_optional(text, old_probe, new_probe)
        if not did:
            raise AssertionError("TMDB metadata append projection anchor drifted")
        changed = True

    capability = '''async function coreGetTmdbData(request){\n  var q=request&&typeof request==="object"&&!Array.isArray(request)?request:{};\n  var id=s(q.tmdbId||q.tmdb_id||q.id).replace(/^tmdb:/i,"");\n  if(!/^\\d+$/.test(id))return{state:"not_found",tmdbId:"",tmdbNamespace:"",metadata:null,episodeMetadata:null};\n  var explicit=s(q.tmdbNamespace||q.namespace).toLowerCase();\n  var candidates=explicit==="movie"||explicit==="tv"?[explicit]:namespaceCandidates(q.mediaType||q.type,q.season,q.episode);\n  var unavailable=false;\n  for(var i=0;i<candidates.length;i++){\n    var namespace=candidates[i]==="movie"?"movie":"tv";\n    var probe=await tmdb(namespace,id);\n    if(!probe||probe.state==="unavailable"){unavailable=true;continue}\n    if(probe.state!=="ok"||!probe.metadata)continue;\n    var episodeMetadata=null;\n    var season=Number(q.season||0)||0,episode=Number(q.episode||0)||0;\n    if(namespace==="tv"&&season>0&&episode>0){\n      var episodeKey="episode:tv:"+id+":"+season+":"+episode+":fr-FR";\n      if(Object.prototype.hasOwnProperty.call(mediaCache,episodeKey)){\n        var cachedEpisode=await mediaCache[episodeKey];\n        episodeMetadata=cachedEpisode&&cachedEpisode.metadata?cachedEpisode.metadata:cachedEpisode&&cachedEpisode.value?cachedEpisode.value:cachedEpisode||null;\n      }else{\n        var pendingEpisode=(async function(){\n          var row=await apiJson("https://api.themoviedb.org/3/tv/"+encodeURIComponent(id)+"/season/"+encodeURIComponent(season)+"/episode/"+encodeURIComponent(episode)+"?language=fr-FR");\n          if(!row||row.state!=="ok")return{state:row&&row.state||"unavailable",metadata:null};\n          return{state:"ok",metadata:row.value};\n        })();\n        mediaCache[episodeKey]=pendingEpisode;\n        var episodeResult=await pendingEpisode;\n        if(episodeResult&&episodeResult.state==="unavailable")delete mediaCache[episodeKey];else mediaCache[episodeKey]=episodeResult;\n        episodeMetadata=episodeResult&&episodeResult.metadata||null;\n      }\n    }\n    return{state:"ok",tmdbId:id,tmdbNamespace:namespace,metadata:probe.metadata,episodeMetadata:episodeMetadata};\n  }\n  return{state:unavailable?"unavailable":"not_found",tmdbId:id,tmdbNamespace:"",metadata:null,episodeMetadata:null};\n}\ntry{if(g)g.__nuvioCoreGetTmdbDataV1=coreGetTmdbData}catch(_){}\n'''
    if 'g.__nuvioCoreGetTmdbDataV1=coreGetTmdbData' not in text:
        anchor = '  if(value&&value.state==="unavailable")delete mediaCache[cacheKey];else mediaCache[cacheKey]=value;\n  return value;\n}\nfunction fallbackType(input,semantic){\n'
        replacement = '  if(value&&value.state==="unavailable")delete mediaCache[cacheKey];else mediaCache[cacheKey]=value;\n  return value;\n}\n' + capability + 'function fallbackType(input,semantic){\n'
        text, did = replace_optional(text, anchor, replacement)
        if not did:
            raise AssertionError("Core TMDB capability insertion anchor drifted")
        changed = True

    forbidden = (
        "RUNTIME_KEY_PATH",
        "_runtime_key_payload",
        "tmdbKeyCipher",
        "tmdbKeySalt",
        "function embeddedKey",
        "normalizeKey(embeddedKey())",
        "NiakVIO/TMDB/v1",
    )
    leftovers = [needle for needle in forbidden if needle in text]
    if leftovers:
        raise AssertionError(f"embedded TMDB key mechanism still present: {leftovers}")

    required = (
        'function nativeFetchBridge(){',
        '(!key&&!token&&!nativeBridge)',
        'release_dates',
        'content_ratings',
        'g.__nuvioCoreGetTmdbDataV1=coreGetTmdbData',
        'episode:tv:',
        'https://api.themoviedb.org/3/',
        '__nuvioTmdbMetadataCacheV1',
    )
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise AssertionError(f"Core TMDB metadata capability missing: {missing}")

    if changed:
        TARGET.write_text(text, encoding="utf-8")
    return changed


def patch_provider_base() -> bool:
    text = PROVIDER_BASE.read_text(encoding="utf-8")
    if '__nuvioCoreGetTmdbDataV1' in text:
        return False
    anchor = '''  try {\n    const cache = typeof globalThis !== "undefined" ? globalThis.__nuvioTmdbMetadataCacheV1 : null;\n    const cached = cache && cache[identity];\n    if (cached && typeof cached.then !== "function") {\n      const row = cached.metadata && typeof cached.metadata === "object" ? cached.metadata : cached;\n      const projected = project(row);\n      if (projected) return projected;\n    }\n  } catch (_) {}\n  return null;\n}\n'''
    replacement = '''  try {\n    const cache = typeof globalThis !== "undefined" ? globalThis.__nuvioTmdbMetadataCacheV1 : null;\n    const cached = cache && cache[identity];\n    if (cached) {\n      const settled = typeof cached.then === "function" ? await cached : cached;\n      const row = settled && settled.metadata && typeof settled.metadata === "object" ? settled.metadata : settled;\n      const projected = project(row);\n      if (projected) return projected;\n    }\n  } catch (_) {}\n  try {\n    const getTmdbData = typeof globalThis !== "undefined" ? globalThis.__nuvioCoreGetTmdbDataV1 : null;\n    if (typeof getTmdbData === "function") {\n      const result = await getTmdbData({ tmdbId: String(tmdbId), mediaType: type, tmdbNamespace: type });\n      const row = result && result.metadata && typeof result.metadata === "object" ? result.metadata : null;\n      const projected = project(row);\n      if (projected) return projected;\n    }\n  } catch (_) {}\n  return null;\n}\n'''
    if anchor not in text:
        raise AssertionError("ProviderBase _tmdb cache tail anchor drifted")
    text = text.replace(anchor, replacement, 1)
    PROVIDER_BASE.write_text(text, encoding="utf-8")
    return True


def patch_presentation() -> bool:
    text = PRESENTATION.read_text(encoding="utf-8")
    changed = False
    text, did = replace_optional(text, '        "tmdbRuntimeKeyRequired": True,\n', '        "tmdbCoreCapabilityRequired": True,\n')
    changed |= did

    start = text.find('function nativeFetchBridge(){')
    end = text.find('function mediaLine(meta,q){', start) if start >= 0 else -1
    if start >= 0:
        if end < 0:
            raise AssertionError("presentation TMDB helper end anchor drifted")
        helper = '''async function cacheValue(key){try{var cache=g&&g.__nuvioTmdbMetadataCacheV1;if(cache&&Object.prototype.hasOwnProperty.call(cache,key))return await cache[key]}catch(_e){}return null}\nfunction certification(d,kind){var rows=kind==="movie"?(d&&d.release_dates&&d.release_dates.results):(d&&d.content_ratings&&d.content_ratings.results);if(!Array.isArray(rows))return"";var row=rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="FR"})||rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="US"})||rows[0];if(!row)return"";if(kind==="movie"){var releases=Array.isArray(row.release_dates)?row.release_dates:[];for(var i=0;i<releases.length;i++){var v=s(releases[i]&&releases[i].certification);if(v)return v}return""}return s(row.rating)}\nasync function coreTmdb(q){if(!/^\\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie",result=null,d=null,ep=null;try{var getter=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof getter==="function")result=await getter({tmdbId:q.tmdbId,mediaType:kind,tmdbNamespace:kind,season:q.season,episode:q.episode})}catch(_e){}if(result&&result.state==="ok"){d=result.metadata||null;ep=result.episodeMetadata||null}if(!d){var cached=await cacheValue(kind+":"+s(q.tmdbId));d=cached&&cached.metadata?cached.metadata:cached&&cached.value?cached.value:cached||null}if(!d)return null;if(!ep&&kind==="tv"&&q.season>0&&q.episode>0){var cachedEpisode=await cacheValue("episode:tv:"+s(q.tmdbId)+":"+q.season+":"+q.episode+":fr-FR");ep=cachedEpisode&&cachedEpisode.metadata?cachedEpisode.metadata:cachedEpisode&&cachedEpisode.value?cachedEpisode.value:cachedEpisode||null}var date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(ep&&Number(ep.runtime||0)>0)runtime=Number(ep.runtime||0);else if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);return{title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind)}}\n'''
        text = text[:start] + helper + text[end:]
        changed = True

    old_install = 'var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var meta=null;try{meta=await tmdb(q)}catch(_e){}return rebuild(v,x,x.list.map(function(r){return present(r,meta,q)}))};'
    new_install = 'var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var meta=null;try{meta=await coreTmdb(q)}catch(_e){}return rebuild(v,x,x.list.map(function(r){return present(r,meta,q)}))};'
    if new_install not in text:
        text, did = replace_optional(text, old_install, new_install)
        if not did:
            raise AssertionError("presentation TMDB install anchor drifted")
        changed = True

    forbidden = ("runtimeTmdbKey", "runtimeTmdbAllowed", "tmdbJson(", "tmdbRuntimeKeyRequired")
    leftovers = [needle for needle in forbidden if needle in text]
    if leftovers:
        raise AssertionError(f"presentation still owns TMDB credentials/client: {leftovers}")
    required = ("__nuvioCoreGetTmdbDataV1", "coreTmdb(q)", "badgeIds", "description")
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise AssertionError(f"presentation Core TMDB integration missing: {missing}")

    if changed:
        PRESENTATION.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    core_changed = patch_core()
    provider_changed = patch_provider_base()
    presentation_changed = patch_presentation()
    print(
        "TMDB_CORE_CAPABILITY_V1_OK "
        f"core_changed={str(core_changed).lower()} "
        f"provider_changed={str(provider_changed).lower()} "
        f"presentation_changed={str(presentation_changed).lower()} "
        "credential_exposed=false dynamic=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

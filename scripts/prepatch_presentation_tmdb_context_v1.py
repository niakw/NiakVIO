#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts/provider_patches/global_stream_presentation_v1.py'
MARKER = 'NUVIO_PRESENTATION_REUSE_MEDIA_CONTEXT_TMDB_V1'

text = TARGET.read_text(encoding='utf-8')
if MARKER not in text:
    old = '''async function coreTmdb(q){if(!/^\\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie",result=null,d=null,ep=null;try{var getter=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof getter==="function")result=await getter({tmdbId:q.tmdbId,mediaType:kind,tmdbNamespace:kind,season:q.season,episode:q.episode})}catch(_e){}if(result&&result.state==="ok"){d=result.metadata||null;ep=result.episodeMetadata||null}if(!d){var cached=await cacheValue(kind+":"+s(q.tmdbId));d=cached&&cached.metadata?cached.metadata:cached&&cached.value?cached.value:cached||null}if(!d)return null;if(!ep&&kind==="tv"&&q.season>0&&q.episode>0){var cachedEpisode=await cacheValue("episode:tv:"+s(q.tmdbId)+":"+q.season+":"+q.episode+":fr-FR");ep=cachedEpisode&&cachedEpisode.metadata?cachedEpisode.metadata:cachedEpisode&&cachedEpisode.value?cachedEpisode.value:cachedEpisode||null}var date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(ep&&Number(ep.runtime||0)>0)runtime=Number(ep.runtime||0);else if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);return{title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind)}}'''
    new = '''/* NUVIO_PRESENTATION_REUSE_MEDIA_CONTEXT_TMDB_V1 */\nfunction contextTmdb(q,kind){try{var ctx=g&&g.__nuvioMediaContext;if(!ctx||typeof ctx!=="object"||!ctx.tmdbMetadata)return null;if(s(ctx.tmdbId)!==s(q.tmdbId))return null;var ns=s(ctx.tmdbNamespace).toLowerCase();if(ns&&ns!==kind)return null;return ctx.tmdbMetadata}catch(_e){return null}}\nasync function coreTmdb(q){if(!/^\\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie",result=null,d=contextTmdb(q,kind),ep=null,needsEpisode=kind==="tv"&&q.season>0&&q.episode>0;if(!d||needsEpisode){try{var getter=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof getter==="function")result=await getter({tmdbId:q.tmdbId,mediaType:kind,tmdbNamespace:kind,season:q.season,episode:q.episode})}catch(_e){}if(result&&result.state==="ok"){if(!d)d=result.metadata||null;ep=result.episodeMetadata||null}}if(!d){var cached=await cacheValue(kind+":"+s(q.tmdbId));d=cached&&cached.metadata?cached.metadata:cached&&cached.value?cached.value:cached||null}if(!d)return null;if(!ep&&needsEpisode){var cachedEpisode=await cacheValue("episode:tv:"+s(q.tmdbId)+":"+q.season+":"+q.episode+":fr-FR");ep=cachedEpisode&&cachedEpisode.metadata?cachedEpisode.metadata:cachedEpisode&&cachedEpisode.value?cachedEpisode.value:cachedEpisode||null}var date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(ep&&Number(ep.runtime||0)>0)runtime=Number(ep.runtime||0);else if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);return{title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind)}}'''
    count = text.count(old)
    if count != 1:
        raise AssertionError(f'presentation coreTmdb anchor expected once, got {count}')
    TARGET.write_text(text.replace(old, new, 1), encoding='utf-8')

value = TARGET.read_text(encoding='utf-8')
for needle in (MARKER, 'function contextTmdb(q,kind)', 'd=contextTmdb(q,kind)', 'if(!d||needsEpisode)'):
    if needle not in value:
        raise AssertionError(needle)
print('PRESENTATION_TMDB_CONTEXT_REUSE_V1_OK')

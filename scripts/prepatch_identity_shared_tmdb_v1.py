#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts/provider_patches/global_stream_identity_v1.py'
MARKER = 'NUVIO_IDENTITY_SHARED_TMDB_CAPABILITY_V1'

text = TARGET.read_text(encoding='utf-8')
if MARKER not in text:
    old = r'''async function tmdb(q){var titles=uniq([q.title]),episodeTitles=[],year=q.year,imdb=q.imdbId,key=runtimeTmdbKey();if(!/^\d+$/.test(q.tmdbId||""))return{titles:titles,episodeTitles:episodeTitles,year:year,imdbId:imdb};var k=kind(q),base="https://api.themoviedb.org/3/"+k+"/"+encodeURIComponent(q.tmdbId),d=await cachedTmdb(q);if(!d&&key)d=await jsonFetch(base+"?api_key="+encodeURIComponent(key)+"&language=fr-FR&append_to_response=external_ids");if(d){var date=s(d.release_date||d.first_air_date);titles=uniq(titles.concat([d.title,d.name,d.original_title,d.original_name]));year=year||Number((date.match(/(?:19|20)\d{2}/)||[])[0]||0)||0;imdb=imdb||s(d.external_ids&&d.external_ids.imdb_id).toLowerCase()}return{titles:titles,episodeTitles:episodeTitles,year:year,imdbId:imdb}}'''
    new = r'''/* NUVIO_IDENTITY_SHARED_TMDB_CAPABILITY_V1 */
async function tmdb(q){var titles=uniq([q.title]),episodeTitles=[],year=q.year,imdb=q.imdbId,key=runtimeTmdbKey();if(!/^\d+$/.test(q.tmdbId||""))return{titles:titles,episodeTitles:episodeTitles,year:year,imdbId:imdb};var k=kind(q),base="https://api.themoviedb.org/3/"+k+"/"+encodeURIComponent(q.tmdbId),d=await cachedTmdb(q),shared=false;if(!d){try{var getter=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof getter==="function"){shared=true;var result=await getter({tmdbId:q.tmdbId,mediaType:k,tmdbNamespace:k,season:q.season,episode:q.episode});if(result&&result.state==="ok"&&result.metadata)d=result.metadata}}catch(_e){}}if(!d&&!shared&&key)d=await jsonFetch(base+"?api_key="+encodeURIComponent(key)+"&language=fr-FR&append_to_response=external_ids");if(d){var date=s(d.release_date||d.first_air_date);titles=uniq(titles.concat([d.title,d.name,d.original_title,d.original_name]));year=year||Number((date.match(/(?:19|20)\d{2}/)||[])[0]||0)||0;imdb=imdb||s(d.external_ids&&d.external_ids.imdb_id).toLowerCase()}return{titles:titles,episodeTitles:episodeTitles,year:year,imdbId:imdb}}'''
    count = text.count(old)
    if count != 1:
        raise AssertionError(f'identity tmdb anchor expected once, got {count}')
    text = text.replace(old, new, 1)
    text = text.replace('"implementationRevision": "cross-client-shared-catalogue-policy-movie-year-only-v9",', '"implementationRevision": "cross-client-shared-tmdb-owner-movie-year-only-v10",', 1)
    TARGET.write_text(text, encoding='utf-8')

value = TARGET.read_text(encoding='utf-8')
for needle in (
    MARKER,
    'g.__nuvioCoreGetTmdbDataV1',
    'shared=true',
    'if(!d&&!shared&&key)',
    'cross-client-shared-tmdb-owner-movie-year-only-v10',
):
    if needle not in value:
        raise AssertionError(needle)
print('IDENTITY_SHARED_TMDB_CAPABILITY_V1_OK')

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation/provider-v3-static-knowledge.json"

def uniq(values):
    out=[]
    for v in values or []:
        x=str(v or '').strip()
        if x and x not in out: out.append(x)
    return out

ov=json.loads(OVERRIDES.read_text(encoding='utf-8'))
patches=ov.setdefault('provider_patches',{})
caps=ov.setdefault('provider_capabilities',{})

# Coflix: the current first-party WordPress player exposes a GET-query REST
# resolver that accepts raw TMDB identity. Runtime-signed play URLs are never
# persisted; only the stable endpoint contract belongs in DATA.
cp=patches.setdefault('coflix',{})
cp['official_site']='https://coflix.group'
cp['official_api']='https://coflix.group/wp-json/coflix/v1/resolve'
cp['capability']='api_stream_resolver'
cp['identity_input']={'mode':'tmdb_direct','requires_tmdb_before_run':True,'required_fields':['tmdbId','mediaType']}
cp['provider_lego_scripts']=uniq(list(cp.get('provider_lego_scripts') or [])+['scripts/provider_patches/coflix_rest_runtime_v1.py'])
cp['candidate_learned_routes']=uniq(list(cp.get('candidate_learned_routes') or [])+['/wp-json/coflix/v1/resolve?tmdb={id}&type={type}&season={season}&episode={episode}'])
notes=cp.get('notes');notes=[notes] if isinstance(notes,str) else list(notes or [])
for note in (
    'NIAKVIO_COFLIX_REST_RUNTIME_V1: current player contract is GET /wp-json/coflix/v1/resolve with raw TMDB + movie/tv transport and season/episode for TV.',
    'Coflix signed play URLs are ephemeral runtime output and must never be persisted in provider DATA.',
):
    if note not in notes: notes.append(note)
cp['notes']=notes
cc=caps.setdefault('coflix',{})
cc['strategy']='api_stream_resolver';cc['validation']='provider_native';cc['requires_direct_media']=True
cc['observed_origins']=uniq(['https://coflix.group','https://coflix.group/wp-json/coflix/v1/resolve']+list(cc.get('observed_origins') or []))

# VoirAnime: current search result identity is the numeric prefix in
# /<id>-<slug>.html; the episode API is stable structured JSON with VF/VOSTFR.
vp=patches.setdefault('voiranime',{})
vp['official_site']='https://voiranime.homes'
vp['capability']='mixed_embed_resolver'
vp['identity_input']={'mode':'catalog_search','requires_tmdb_before_run':True,'required_fields':['title','mediaType']}
vp['provider_lego_scripts']=uniq(list(vp.get('provider_lego_scripts') or [])+['scripts/provider_patches/voiranime_homes_runtime_v1.py'])
vp['candidate_learned_routes']=uniq(list(vp.get('candidate_learned_routes') or [])+['/engine/ajax/search.php','/{id}-{slug}.html','/engine/ajax/manga_episodes_api.php?id={id}'])
notes=vp.get('notes');notes=[notes] if isinstance(notes,str) else list(notes or [])
for note in (
    'NIAKVIO_VOIRANIME_HOMES_RUNTIME_V1: current search id is the numeric prefix of /<id>-<slug>.html, not a newsid token in search HTML.',
    'Episode API returns vf/vostfr episode maps; player and signed HLS URLs are runtime-only and are never persisted.',
):
    if note not in notes: notes.append(note)
vp['notes']=notes
vc=caps.setdefault('voiranime',{})
vc['strategy']='mixed_embed_resolver';vc['validation']='provider_native'
vc['observed_origins']=uniq(['https://voiranime.homes','https://vidzy.live','https://vidzy.org','https://luluvdo.com']+list(vc.get('observed_origins') or []))

OVERRIDES.write_text(json.dumps(ov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

k=json.loads(KNOWLEDGE.read_text(encoding='utf-8'))
providers=k.setdefault('providers',{})
for pid,site,strategy,api,routes in (
    ('coflix','https://coflix.group','api_stream_resolver','https://coflix.group/wp-json/coflix/v1/resolve',['/wp-json/coflix/v1/resolve?tmdb={id}&type={type}&season={season}&episode={episode}']),
    ('voiranime','https://voiranime.homes','mixed_embed_resolver',None,['/engine/ajax/search.php','/{id}-{slug}.html','/engine/ajax/manga_episodes_api.php?id={id}']),
):
    row=providers.setdefault(pid,{})
    model=row.setdefault('model',{})
    model['knownSite']=site;model['officialSite']=site;model['strategy']=strategy
    if api is not None: model['officialApi']=api
    elif model.get('officialApi') and 'voiranime' in str(model.get('officialApi')).lower(): model['officialApi']=None
    origins=[x for x in list(model.get('origins') or []) if not (pid=='coflix' and str(x).startswith('http://coflix.'))]
    model['origins']=uniq([site]+origins)
    model['routes']=uniq(list(model.get('routes') or [])+routes)
    if pid=='coflix':
        model['identityInput']={'mode':'tmdb_direct','requiresTmdbBeforeRun':True,'requiredFields':['tmdbId','mediaType']}
    else:
        model['identityInput']={'mode':'catalog_search','requiresTmdbBeforeRun':True,'requiredFields':['title','mediaType']}
KNOWLEDGE.write_text(json.dumps(k,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('VOIRANIME_COFLIX_RUNTIME_DATA_STAGED coflix=https_rest_tmdb voiranime=href_id_episode_json activation_unchanged=1')

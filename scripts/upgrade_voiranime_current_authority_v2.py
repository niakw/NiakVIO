#!/usr/bin/env python3
"""Persist the A/B-proven current VoirAnime execution authority."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OVERRIDES=ROOT/'provider-overrides.json'
KNOWLEDGE=ROOT/'automation/provider-v3-static-knowledge.json'
OLD_LEGO='scripts/provider_patches/voiranime_homes_runtime_v1.py'
SITE='https://voir-anime.to'
ROUTES=['https://voir-anime.to/anime/{slug}/']

def uniq(values):
    out=[]
    for value in values or []:
        s=str(value or '').strip()
        if s and s not in out: out.append(s)
    return out

def main()->int:
    cfg=json.loads(OVERRIDES.read_text(encoding='utf-8'))
    row=cfg['provider_patches']['voiranime']
    caps=cfg.setdefault('provider_capabilities',{}).setdefault('voiranime',{})
    before=json.dumps(cfg,sort_keys=True,ensure_ascii=False)
    row['official_site']=SITE
    row['proof_search_bases']=[SITE]
    row['learned_routes']=ROUTES
    row['candidate_learned_routes']=uniq(list(row.get('candidate_learned_routes') or [])+ROUTES)
    for key in ('search_request_plan','provider_value_plan','api_recipe'):
        row.pop(key,None)
    row['provider_lego_scripts']=[x for x in uniq(row.get('provider_lego_scripts') or []) if x!=OLD_LEGO]
    opts=row.get('provider_lego_options')
    if isinstance(opts,dict): opts.pop(OLD_LEGO,None)
    for key in ('domain_substitutions','runtime_domain_replacements','replacements'):
        mapping=row.get(key)
        if isinstance(mapping,dict):
            for old in list(mapping):
                if 'voiranime' in str(old).lower() or 'voir-anime' in str(old).lower(): mapping[old]='voir-anime.to'
    caps['strategy']='mixed_embed_resolver'; caps['validation']='provider_native'
    caps['observed_origins']=uniq([SITE]+list(caps.get('observed_origins') or []))
    changed=json.dumps(cfg,sort_keys=True,ensure_ascii=False)!=before
    if changed: OVERRIDES.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    k=json.loads(KNOWLEDGE.read_text(encoding='utf-8'))
    model=k.setdefault('providers',{}).setdefault('voiranime',{}).setdefault('model',{})
    model['knownSite']=SITE; model['officialSite']=SITE; model['strategy']='mixed_embed_resolver'
    model['origins']=uniq([SITE]+list(model.get('origins') or [])); model['routes']=ROUTES
    model.pop('apiRecipe',None)
    model['identityInput']={'mode':'catalog_search','requiresTmdbBeforeRun':True,'requiredFields':['title','mediaType']}
    KNOWLEDGE.write_text(json.dumps(k,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    check=json.loads(OVERRIDES.read_text(encoding='utf-8'))['provider_patches']['voiranime']
    assert check['official_site']==SITE and check['learned_routes']==ROUTES
    assert 'api_recipe' not in check and OLD_LEGO not in check.get('provider_lego_scripts',[])
    print(f'VOIRANIME_CURRENT_AUTHORITY_V2_OK changed={str(changed).lower()} site={SITE} stale_recipe=0 stale_homes_lego=0')
    return 0
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import materialize_provider_v3_all as m

cap={'strategy':'html_scraper'}

# A proof-v5 patch-owned external plan must prevent stale static apiRecipe promotion.
external=[{
    'base':'https://live.example',
    'route':'/series/{imdbId}',
    'requestSpec':{'method':'GET'},
    'proofModelVersion':5,
    'sourceRole':'external-identity-detail',
}]
patch={
    'route_proof_version':5,
    'external_identity_plan':external,
    'proof_detail_bases':['https://live.example'],
}
static={'model':{
    'routeProofVersion':5,
    'apiRecipe':{'proofModelVersion':5,'base':'https://stale-helper.example','directRoute':'/lookup/{tmdbId}'},
    'externalIdentityPlan':[],
    'proofDetailBases':[],
}}
model=m.provider_model('synthetic',patch,cap,static)
assert model['apiRecipe'] is None, model['apiRecipe']
assert model['externalIdentityPlan']==external, model['externalIdentityPlan']
assert model['proofDetailBases']==['https://live.example'], model['proofDetailBases']

# A patch-owned proven recipe must survive byte-for-byte instead of being replaced by static knowledge.
recipe={
    'proofModelVersion':5,
    'recipeKind':'typed-resolver-api',
    'movieRoute':'https://resolver.example/api?tmdb={tmdbId}&type=movie',
    'episodeRoute':'https://resolver.example/api?tmdb={tmdbId}&type=tv&season={season}&episode={episode}',
    'allowGenericFallback':False,
}
patch={'route_proof_version':5,'api_recipe':recipe}
static={'model':{
    'routeProofVersion':5,
    'apiRecipe':{'proofModelVersion':5,'base':'https://resolver.example','movieRoute':recipe['movieRoute'],'episodeRoute':recipe['episodeRoute']},
}}
model=m.provider_model('synthetic',patch,cap,static)
assert model['apiRecipe']==recipe, model['apiRecipe']

# Static proof remains a fallback only when patch DATA has no executable proof-v5 authority.
patch={'route_proof_version':0}
static_recipe={'proofModelVersion':5,'base':'https://fallback.example','directRoute':'/v1/{tmdbId}'}
static={'model':{'routeProofVersion':5,'apiRecipe':static_recipe}}
model=m.provider_model('synthetic',patch,cap,static)
assert model['apiRecipe']==static_recipe, model['apiRecipe']

one=(ROOT/'scripts'/'materialize_provider_v3_one.py').read_text(encoding='utf-8')
assert '# MATERIALIZER_EXECUTION_AUTHORITY_MONOTONIC_V25' in one
assert 'patch["api_recipe"] = canonical_recipe' not in one
print('materializer authority monotonic v25 tests passed')

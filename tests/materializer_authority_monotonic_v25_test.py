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

# A proof-v5 identity/helper recipe is not provider execution authority by itself.
# It may remain available as a fallback recipe, but must not suppress current
# provider-owned static catalogue routes.
helper={
    'proofModelVersion':5,
    'base':'https://arm.haglund.dev',
    'directRoute':'/api/v2/themoviedb?id={tmdbId}',
    'allowGenericFallback':False,
}
patch={'route_proof_version':5,'api_recipe':helper}
static={'model':{
    'routeProofVersion':5,
    'routes':['/?s={query}','/{slug}-streaming.html'],
    'apiRecipe':helper,
}}
model=m.provider_model('synthetic',patch,cap,static)
assert model['apiRecipe']==helper, model['apiRecipe']
assert '/?s={query}' in model['routes'], model['routes']
assert '/{slug}-streaming.html' in model['routes'], model['routes']
assert m._recipe_is_provider_execution_authority(helper) is False

provider_recipe={
    'proofModelVersion':5,
    'base':'https://provider.example',
    'directRoute':'/api/streams?id={tmdbId}',
}
assert m._recipe_is_provider_execution_authority(provider_recipe) is True

# A fresh patch route must not erase independent structured static plans.
patch={
    'route_proof_version':5,
    'learned_routes':['/search?keyword={query}'],
}
static_search=[{
    'route':'/search?keyword={query}',
    'requestSpec':{'method':'GET'},
    'proofModelVersion':5,
}]
static_values=[{
    'sourceRole':'search-result-id',
    'proofModelVersion':5,
    'requestSpec':{'method':'GET'},
}]
static_external=[{
    'base':'https://detail.example',
    'route':'/series/{imdbId}',
    'proofModelVersion':5,
}]
static={'model':{
    'routeProofVersion':5,
    'searchRequestPlan':static_search,
    'providerValuePlan':static_values,
    'externalIdentityPlan':static_external,
    'proofSearchBases':['https://search.example'],
    'proofDetailBases':['https://detail.example'],
}}
model=m.provider_model('synthetic',patch,cap,static)
assert model['routes']==['/search?keyword={query}'], model['routes']
assert model['searchRequestPlan']==static_search, model['searchRequestPlan']
assert model['providerValuePlan']==static_values, model['providerValuePlan']
assert model['externalIdentityPlan']==static_external, model['externalIdentityPlan']
assert model['proofSearchBases']==['https://search.example'], model['proofSearchBases']
assert model['proofDetailBases']==['https://detail.example'], model['proofDetailBases']

one=(ROOT/'scripts'/'materialize_provider_v3_one.py').read_text(encoding='utf-8')
assert '# MATERIALIZER_EXECUTION_AUTHORITY_MONOTONIC_V25' in one
assert 'patch["api_recipe"] = canonical_recipe' not in one
print('materializer authority monotonic v25 tests passed')

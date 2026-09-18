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

# Proof-v5 patch routes must never erase an independently proven static route,
# even when both are classified in the same coarse family.
patch={
    'route_proof_version':5,
    'learned_routes':['/?tmdbId={tmdbId}&type=tv&season={season}&episode={episode}'],
}
static={'model':{
    'routeProofVersion':5,
    'routes':['/{slug}/','/{slug}-episode-{episode}/'],
}}
model=m.provider_model('synthetic',patch,cap,static)
assert '/?tmdbId={tmdbId}&type=tv&season={season}&episode={episode}' in model['routes'], model['routes']
assert '/{slug}/' in model['routes'], model['routes']
assert '/{slug}-episode-{episode}/' in model['routes'], model['routes']

# Proof in another family must not erase a valid static API recipe.
static_recipe={
    'proofModelVersion':5,
    'base':'https://provider-api.example',
    'directRoute':'/movie/{tmdbId}',
}
patch={'route_proof_version':5,'learned_routes':['/?s={title}']}
static={'model':{'routeProofVersion':5,'apiRecipe':static_recipe}}
model=m.provider_model('synthetic',patch,cap,static)
assert model['apiRecipe']==static_recipe, model['apiRecipe']

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

# Route authority is monotone per family: a fresh search route replaces stale
# search routes, but must preserve independent detail/player/API route knowledge.
patch={
    'route_proof_version':5,
    'learned_routes':['/search?keyword={query}'],
}
static={'model':{
    'routeProofVersion':5,
    'routes':[
        '/?s={query}',
        '/watch/{slug}',
        '/player?id={id}',
        '/api/source?id={id}',
    ],
}}
model=m.provider_model('synthetic',patch,cap,static)
assert model['routes'][0]=='/search?keyword={query}', model['routes']
assert '/?s={query}' not in model['routes'], model['routes']
assert '/watch/{slug}' in model['routes'], model['routes']
assert '/player?id={id}' in model['routes'], model['routes']
assert '/api/source?id={id}' in model['routes'], model['routes']

# Reusable proof-v5 search routeData must become an executable generic search plan.
patch={'route_proof_version':0}
static={'model':{
    'routeProofVersion':5,
    'routeData':[
        {
            'role':'search',
            'origin':'https://catalog.example',
            'route':'/api/search?q={query}',
            'method':'GET',
            'semanticType':'movie',
            'requestSpecReusable':True,
            'requestSpec':{'method':'GET','headers':{'accept':'application/json'}},
            'proofModelVersion':5,
        },
        {
            'role':'search',
            'origin':'https://catalog.example',
            'route':'/api/search?q={query}',
            'method':'GET',
            'semanticType':'tv',
            'requestSpecReusable':True,
            'requestSpec':{'method':'GET','headers':{'accept':'application/json'}},
            'proofModelVersion':5,
        },
        {
            'role':'search',
            'origin':'https://catalog.example',
            'route':'/api/search?q=fixture-specific',
            'method':'GET',
            'semanticType':'movie',
            'requestSpecReusable':True,
            'proofModelVersion':5,
        },
    ],
}}
model=m.provider_model('synthetic',patch,cap,static)
assert len(model['searchRequestPlan'])==1, model['searchRequestPlan']
assert model['searchRequestPlan'][0]['base']=='https://catalog.example'
assert model['searchRequestPlan'][0]['route']=='/api/search?q={query}'
assert set(model['searchRequestPlan'][0]['semanticTypes'])=={'movie','tv'}
assert model['proofSearchBases']==['https://catalog.example']

# Live-recognized generalized search requests are also reusable execution knowledge.
patch={'route_proof_version':0}
static={'model':{'routeProofVersion':5},'knowledge':{'recognizedContract':{
    'requests':[{
        'role':'search',
        'route':'/?s={query}',
        'method':'GET',
        'semanticType':'movie',
        'executedEvidence':True,
        'httpUsed':True,
        'validationState':'live-validated',
        'derivation':{
            'origin':'https://live-catalog.example',
            'reusable':True,
            'fixtureSpecificValues':[],
            'dynamicQueryResidue':[],
        },
    }],
}}}
model=m.provider_model('synthetic',patch,cap,static)
assert len(model['searchRequestPlan'])==1, model['searchRequestPlan']
assert model['searchRequestPlan'][0]['base']=='https://live-catalog.example'
assert model['searchRequestPlan'][0]['route']=='/?s={query}'
assert model['proofSearchBases']==['https://live-catalog.example']

one=(ROOT/'scripts'/'materialize_provider_v3_one.py').read_text(encoding='utf-8')
assert '# MATERIALIZER_EXECUTION_AUTHORITY_MONOTONIC_V25' in one
assert 'patch["api_recipe"] = canonical_recipe' not in one
print('materializer authority monotonic v25 tests passed')

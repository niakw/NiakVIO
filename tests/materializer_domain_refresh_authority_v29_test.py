#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import materialize_provider_v3_one as one

# Domain Refresh/provider-overrides is publication authority. A stale static model
# may seed missing fields, but must never roll a current terminal backward.
overrides={'provider_patches':{'allanime':{
    'official_site':'https://ww2.aniwatch.fit',
    'official_hub':'https://allanime.sa.com/',
    'official_api':'https://api.current.example',
    'domain_substitutions':{'aniwatchtv.watch':'ww2.aniwatch.fit'},
    'api_recipe':{
        'proofModelVersion':5,
        'base':'https://api.current.example',
        'referer':'https://ww2.aniwatch.fit/',
        'directRoute':'/stream/{tmdbId}',
    },
}}}
static={'providers':{'allanime':{'model':{
    'officialSite':'https://aniwatchtv.watch',
    'knownSite':'https://aniwatchtv.watch',
    'officialHub':'https://stale-hub.example/',
    'officialApi':'https://api.stale.example',
    'fixedApi':'https://api.stale.example',
    'apiRecipe':{
        'proofModelVersion':5,
        'base':'https://api.stale.example',
        'referer':'https://aniwatchtv.watch/',
        'directRoute':'/stream/{tmdbId}',
    },
}}}}
changed=one.reconcile_provider_authority(overrides,static,'allanime')
row=overrides['provider_patches']['allanime']
assert row['official_site']=='https://ww2.aniwatch.fit', row
assert row['official_hub']=='https://allanime.sa.com/', row
assert row['official_api']=='https://api.current.example', row
assert row['api_recipe']['base']=='https://api.current.example', row
assert row['api_recipe']['referer']=='https://ww2.aniwatch.fit/', row
assert row['domain_substitutions']=={'aniwatchtv.watch':'ww2.aniwatch.fit'}, row
assert changed==[], changed

# Missing authority may still be seeded from structured static knowledge.
overrides2={'provider_patches':{'demo':{}}}
static2={'providers':{'demo':{'model':{
    'officialSite':'https://demo.example',
    'officialHub':'https://hub.example/',
    'officialApi':'https://api.demo.example',
}}}}
changed2=one.reconcile_provider_authority(overrides2,static2,'demo')
row2=overrides2['provider_patches']['demo']
assert row2['official_site']=='https://demo.example'
assert row2['official_hub']=='https://hub.example/'
assert row2['official_api']=='https://api.demo.example'
assert changed2==['demo']

print('materializer Domain Refresh authority v29 tests passed')

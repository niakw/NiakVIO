#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from promote_candidates import choose_variant_with_baseline_protection

registry=json.loads((ROOT/'provider-lkg.json').read_text())
manifest={row['id']:row for row in json.loads((ROOT/'manifest.json').read_text())['scrapers']}
assert registry['providers']
for provider_id, record in registry['providers'].items():
    path=ROOT/record['filename']
    assert path.is_file(), (provider_id,path)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'], provider_id
    assert provider_id in manifest
    assert manifest[provider_id]['filename']==record['filename'], provider_id

rank=lambda v: (int(v['health'].get('score',0)), -int(v.get('source_priority',999)))
baseline={
 'key':'published:anime-sama','baseline':True,'lkg':True,'source_priority':103,
 'metadata':{'supportedTypes':['anime']},
 'health':{'status':'no_streams','score':10,'evidence':{'streams_playable':0,'healthy_fixtures':0,'healthy_fixture_categories':[]}},
}
reachable={
 'key':'gowaru:anime-sama','baseline':False,'source_priority':0,
 'metadata':{'supportedTypes':['anime']},
 'health':{'status':'reachable','score':75,'evidence':{'streams_playable':0,'healthy_fixtures':0,'healthy_fixture_categories':[]}},
}
assert choose_variant_with_baseline_protection([reachable,baseline],rank,{'verified_categories':['anime']}) is baseline
healthy={
 'key':'gowaru:anime-sama-new','baseline':False,'source_priority':0,
 'metadata':{'supportedTypes':['anime']},
 'health':{'status':'healthy','score':90,'evidence':{'streams_playable':1,'healthy_fixtures':1,'healthy_fixture_categories':['anime']}},
}
assert choose_variant_with_baseline_protection([reachable,baseline,healthy],rank,{'verified_categories':['anime']}) is healthy
partial={
 'key':'upstream:mixed','baseline':False,'source_priority':0,
 'metadata':{'supportedTypes':['movie','tv']},
 'health':{'status':'healthy','score':95,'evidence':{'streams_playable':1,'healthy_fixtures':1,'healthy_fixture_categories':['movie']}},
}
mixed=dict(baseline); mixed['metadata']={'supportedTypes':['movie','tv']}
assert choose_variant_with_baseline_protection([mixed,partial],rank,{'verified_categories':['movie','tv']}) is mixed
print('LKG regression selection tests passed')

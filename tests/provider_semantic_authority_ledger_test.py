#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ledger=json.loads((ROOT/'automation/provider-semantic-authority-ledger-v1.json').read_text(encoding='utf-8'))
overrides=json.loads((ROOT/'provider-overrides.json').read_text(encoding='utf-8'))
providers=overrides['provider_patches']

for provider,rule in ledger['providers'].items():
    row=providers.get(provider)
    assert isinstance(row,dict), f'{provider}: missing provider override row'
    learned=set(row.get('learned_routes') or [])
    candidates=set(row.get('candidate_learned_routes') or [])
    for route in rule.get('requiredRoutes') or []:
        assert route in learned, f'{provider}: required learned route lost: {route}'
        assert route in candidates, f'{provider}: required candidate route lost: {route}'
    ref=rule.get('requiredRecipeReferer')
    if ref:
        recipe=row.get('api_recipe') or {}
        candidate=row.get('candidate_api_recipe') or {}
        assert recipe.get('referer')==ref, f'{provider}: api recipe referer lost'
        if candidate:
            assert candidate.get('referer')==ref, f'{provider}: candidate recipe referer lost'
    req=rule.get('requiredApiRecipe') or {}
    if req:
        recipe=row.get('api_recipe') or {}
        for key,value in req.items():
            assert recipe.get(key)==value, f'{provider}: api recipe {key} drift: {recipe.get(key)!r} != {value!r}'
    scripts=set(row.get('provider_lego_scripts') or [])
    for script in rule.get('requiredLegoScripts') or []:
        assert script in scripts, f'{provider}: required Lego lost: {script}'

print('provider semantic authority ledger contract passed')

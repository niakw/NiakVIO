#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from provider_patch_blocks import decode_managed_data

MANIFEST=ROOT/'manifest.json'
OVERRIDES=ROOT/'provider-overrides.json'


def cid(v: object)->str:
    return str(v or '').strip().casefold().replace('_','-')


def load(p:Path)->dict:
    v=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(v,dict): raise ValueError(p)
    return v


def proof5_rows(value: object, limit:int)->list[dict]:
    if not isinstance(value,list): return []
    return [copy.deepcopy(r) for r in value if isinstance(r,dict) and int(r.get('proofModelVersion') or 0)>=5][:limit]


def restore(provider_id:str)->bool:
    provider_id=cid(provider_id)
    manifest=load(MANIFEST)
    overrides=load(OVERRIDES)
    row=next((r for r in manifest.get('scrapers') or [] if isinstance(r,dict) and cid(r.get('id'))==provider_id),None)
    if not isinstance(row,dict): raise ValueError(f'{provider_id}: manifest row missing')
    path=ROOT/str(row.get('filename') or '')
    if not path.is_file(): raise ValueError(f'{provider_id}: published bundle missing: {path}')
    text=path.read_text(encoding='utf-8')
    fix_id=f'PROVIDER.{provider_id.upper()}.CONFIG.V1'
    data=decode_managed_data(text,fix_id)
    version=int(data.get('routeProofVersion') or 0)
    if version<5: raise ValueError(f'{provider_id}: published CONFIG is not proof-v5')
    patches=overrides.get('provider_patches')
    if not isinstance(patches,dict) or not isinstance(patches.get(provider_id),dict):
        raise ValueError(f'{provider_id}: provider patch missing')
    patch=patches[provider_id]
    before=json.dumps(patch,sort_keys=True,separators=(',',':'))
    patch['route_proof_version']=max(int(patch.get('route_proof_version') or 0),version)

    routes=[str(v).strip() for v in data.get('routes') or [] if str(v).strip() and str(v).strip()!='/']
    if routes: patch['learned_routes']=routes

    recipe=data.get('apiRecipe')
    if isinstance(recipe,dict) and int(recipe.get('proofModelVersion') or 0)>=5:
        patch['api_recipe']=copy.deepcopy(recipe)
    elif data.get('apiRecipe') is None:
        # Explicitly preserve the published no-recipe state so stale static helper
        # knowledge cannot be promoted over a stronger structured plan.
        patch.pop('api_recipe',None)

    list_map=(
        ('proofSearchBases','proof_search_bases',6),
        ('proofDetailBases','proof_detail_bases',6),
        ('proofProtectedHosts','proof_protected_hosts',24),
    )
    for source,target,limit in list_map:
        if source not in data: continue
        vals=[str(v).strip() for v in data.get(source) or [] if str(v).strip()][:limit]
        if vals: patch[target]=vals
        else: patch.pop(target,None)

    plan_map=(
        ('searchRequestPlan','search_request_plan',6),
        ('providerValuePlan','provider_value_plan',12),
        ('externalIdentityPlan','external_identity_plan',4),
    )
    for source,target,limit in plan_map:
        if source not in data: continue
        vals=proof5_rows(data.get(source),limit)
        if vals: patch[target]=vals
        else: patch.pop(target,None)

    after=json.dumps(patch,sort_keys=True,separators=(',',':'))
    changed=before!=after
    if changed:
        OVERRIDES.write_text(json.dumps(overrides,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PUBLISHED_EXECUTION_AUTHORITY_V25 provider=%s changed=%s routes=%d recipe=%d search=%d provider_value=%d external=%d'%(
        provider_id,str(changed).lower(),len(routes),int(isinstance(recipe,dict)),len(proof5_rows(data.get('searchRequestPlan'),6)),len(proof5_rows(data.get('providerValuePlan'),12)),len(proof5_rows(data.get('externalIdentityPlan'),4))))
    return changed


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('provider',nargs='+');args=ap.parse_args()
    changed=[]
    for raw in args.provider:
        if restore(raw): changed.append(cid(raw))
    print('PUBLISHED_EXECUTION_AUTHORITY_V25_DONE changed='+(','.join(changed) if changed else 'none'))
    return 0

if __name__=='__main__': raise SystemExit(main())

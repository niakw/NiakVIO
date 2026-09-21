#!/usr/bin/env python3
from __future__ import annotations
import copy,json,re
from typing import Any
from urllib.parse import urlsplit
SAFE_TYPES={'movie','tv','anime'}; SAFE_METHODS={'GET','POST'}
SAFE_HEADER_NAMES={'accept','accept-language','content-type','origin','referer','user-agent'}
SUPPORTED_BINDINGS={'id','slug'}; BINDING=re.compile(r'\{binding:([A-Za-z0-9_.-]+)\}',re.I); PROOF_MODEL_VERSION=6

def cid(v): return str(v or '').strip().casefold()
def safe_origin(v):
    t=str(v or '').strip().rstrip('/')
    try:p=urlsplit(t)
    except ValueError:return ''
    if p.scheme not in {'http','https'} or not p.hostname or p.username or p.password or p.query or p.fragment:return ''
    return f'{p.scheme}://{p.netloc}'
def safe_route(v):
    r=str(v or '').strip()
    if not r or len(r)>800 or '${' in r or r.count('{')!=r.count('}') or not r.startswith(('/','http://','https://')):return ''
    if any(m.group(1).casefold() not in SUPPORTED_BINDINGS for m in BINDING.finditer(r)):return ''
    return r

def request_spec(recipe:dict[str,Any],user_agent:str,origin:str)->dict[str,Any]:
    method=str(recipe.get('method') or 'GET').upper()
    if method not in SAFE_METHODS: raise ValueError(f'unsupported method {method}')
    names={str(x or '').strip().casefold() for x in recipe.get('headerNames') or [] if str(x or '').strip()}
    if not names.issubset(SAFE_HEADER_NAMES): raise ValueError('unsupported headers')
    body_kind=str(recipe.get('bodyKind') or 'none').casefold(); response=str(recipe.get('response') or '').casefold(); h={}
    if 'accept' in names:h['Accept']='application/json,text/plain,*/*' if response=='json' else 'text/html,application/xhtml+xml,application/json,*/*'
    if 'accept-language' in names:h['Accept-Language']='fr-FR,fr;q=0.9,en;q=0.5'
    if 'user-agent' in names:
        if not user_agent or len(user_agent)>240: raise ValueError('unsafe/missing user agent')
        h['User-Agent']=user_agent
    if 'referer' in names:h['Referer']=origin+'/'
    if 'origin' in names:h['Origin']=origin
    if 'content-type' in names:
        if body_kind=='json':h['Content-Type']='application/json'
        elif body_kind=='form':h['Content-Type']='application/x-www-form-urlencoded'
        elif body_kind not in {'none',''}:raise ValueError('unsupported body kind')
    spec={'method':method,'headers':h}; body=recipe.get('body') if isinstance(recipe.get('body'),dict) else {}
    if method=='POST':
        if body_kind not in {'json','form'} or not body:raise ValueError('POST requires structured body')
        spec['bodyKind']=body_kind;spec['body']=copy.deepcopy(body)
    elif body:raise ValueError('GET cannot carry body')
    return spec

def compile_program(program:dict[str,Any],provider:str)->dict[str,Any]:
    if program.get('profile')!='adaptive_runtime_recovery' or int(program.get('revision') or 0)<5:raise ValueError('unsupported accepted program')
    o=program.get('options') if isinstance(program.get('options'),dict) else {}; ua=str(o.get('user_agent') or '').strip()
    types=list(dict.fromkeys(str(x).strip().casefold() for x in o.get('types') or [] if str(x).strip().casefold() in SAFE_TYPES))
    if not types:raise ValueError('missing types')
    recipes=[copy.deepcopy(x) for x in o.get('request_recipes') or [] if isinstance(x,dict) and x.get('executable') is True]
    if not recipes:raise ValueError('no executable recipes')
    norm=[]
    for i,r in enumerate(recipes):
        origin=safe_origin(r.get('origin') or o.get('base_url'));route=safe_route(r.get('route'))
        if not origin or not route:raise ValueError(f'bad recipe {i}')
        semantic=str(r.get('semanticType') or '').strip().casefold();lanes=[semantic] if semantic in SAFE_TYPES else types
        bindings=[str(x).strip().casefold() for x in r.get('requiredBindings') or [] if str(x).strip()]
        if any(x not in SUPPORTED_BINDINGS for x in bindings):raise ValueError('unsupported binding')
        rb=[m.group(1).casefold() for m in BINDING.finditer(route)]
        if sorted(set(rb))!=sorted(set(bindings)) and (rb or bindings):raise ValueError('binding not route representable')
        norm.append({'origin':origin,'route':route,'role':str(r.get('role') or 'other').casefold(),'semanticTypes':lanes,'bindings':bindings,'requestSpec':request_spec(r,ua,origin)})
    indep=[x for x in norm if not x['bindings']];dep=[x for x in norm if x['bindings']];search=[]
    for x in indep:
        ser=json.dumps({'route':x['route'],'requestSpec':x['requestSpec']})
        if x['role']=='search' and any(t in ser for t in ('{query}','{tmdbId}','{imdbId}')):search.append(x)
    if not search:raise ValueError('no accepted search seed')
    srp=[{'base':x['origin'],'route':x['route'],'requestSpec':x['requestSpec'],'proofModelVersion':6,'sourceRole':'brain-accepted-runtime','semanticTypes':x['semanticTypes']} for x in search[:6]]
    pvp=[]
    for s in search:
        steps=[]
        for x in dep:
            if not set(x['semanticTypes']) & set(s['semanticTypes']):continue
            route=x['route']
            for b in x['bindings']:route=re.sub(r'\{binding:'+re.escape(b)+r'\}','{'+b+'}',route,flags=re.I)
            if not re.search(r'\{(?:id|slug)\}',route,re.I):raise ValueError('dependent recipe not representable')
            steps.append({'base':x['origin'],'route':route,'requestSpec':x['requestSpec'],'role':x['role'] if x['role'] in {'detail','episode','player','api','source'} else 'detail'})
        if steps:pvp.append({'searchBase':s['origin'],'searchRoute':s['route'],'searchRequestSpec':s['requestSpec'],'steps':steps[:8],'semanticTypes':s['semanticTypes'],'proofModelVersion':6,'sourceRole':'brain-accepted-provider-value-correlation'})
    if dep and not pvp:raise ValueError('lost dependent dataflow')
    return {'schemaVersion':1,'provider':cid(provider),'source':'strict-brain-accepted-runtime-program','acceptedProgramRevision':int(program.get('revision') or 0),'types':types,'origins':list(dict.fromkeys(x['origin'] for x in norm))[:24],'searchRequestPlan':srp,'providerValuePlan':pvp[:12]}

def find_accepted_program(report:dict[str,Any],provider:str)->dict[str,Any]:
    wanted=cid(provider);hits={}
    rows=[]
    rows.extend(report.get('acceptedRepairs') or [])
    for wave in report.get('waves') or []:
        if not isinstance(wave,dict):continue
        for batch in wave.get('batches') or []:
            if isinstance(batch,dict):rows.extend(batch.get('accepted') or [])
    for row in rows:
        if not isinstance(row,dict) or cid(row.get('provider'))!=wanted:continue
        p=row.get('acceptedProgram')
        if isinstance(p,dict) and p:
            hits[json.dumps(p,sort_keys=True,separators=(',',':'))]=copy.deepcopy(p)
    if len(hits)!=1:raise ValueError(f'{wanted}: expected exactly one unique acceptedProgram, found {len(hits)}')
    return next(iter(hits.values()))

def _merge_rows(primary:list[Any],existing:list[Any],limit:int)->list[Any]:
    out=[];seen=set()
    for row in [*primary,*existing]:
        if not isinstance(row,dict):continue
        key=json.dumps(row,sort_keys=True,separators=(',',':'))
        if key in seen:continue
        seen.add(key);out.append(copy.deepcopy(row))
        if len(out)>=limit:break
    return out

def apply_compiled(overrides:dict[str,Any],compiled:dict[str,Any])->dict[str,Any]:
    out=copy.deepcopy(overrides);provider=cid(compiled.get('provider'));patches=out.setdefault('provider_patches',{})
    if not isinstance(patches,dict):raise ValueError('provider_patches must be object')
    patch=patches.setdefault(provider,{})
    if not isinstance(patch,dict):raise ValueError(f'provider_patches.{provider} must be object')
    patch['search_request_plan']=_merge_rows(
        compiled.get('searchRequestPlan') or [],
        patch.get('search_request_plan') or [],
        6,
    )
    compiled_values=compiled.get('providerValuePlan') or []
    existing_values=patch.get('provider_value_plan') or []
    if compiled_values or existing_values:
        patch['provider_value_plan']=_merge_rows(compiled_values,existing_values,12)
    else:
        patch.pop('provider_value_plan',None)
    patch['brain_accepted_program']={'schema_version':1,'profile_revision':int(compiled.get('acceptedProgramRevision') or 0),'source':'strict-brain-accepted-runtime-program'}
    return out

def main()->int:
    import argparse
    from pathlib import Path
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,required=True);ap.add_argument('--provider',required=True);ap.add_argument('--overrides',type=Path,required=True);ap.add_argument('--proposal',type=Path,required=True);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    report=json.loads(args.report.read_text());overrides=json.loads(args.overrides.read_text());program=find_accepted_program(report,args.provider);compiled=compile_program(program,args.provider);proposed=apply_compiled(overrides,compiled)
    payload={'schemaVersion':1,'provider':cid(args.provider),'compiled':compiled,'proposedOverrides':proposed};args.proposal.parent.mkdir(parents=True,exist_ok=True);args.proposal.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    if args.apply:args.overrides.write_text(json.dumps(proposed,ensure_ascii=False,indent=2)+'\n')
    print(f"FIELD_BRAIN_ACCEPTED_PROGRAM_V3 provider={cid(args.provider)} search_plans={len(compiled['searchRequestPlan'])} value_plans={len(compiled['providerValuePlan'])} apply={str(args.apply).lower()}")
    return 0

if __name__=='__main__':raise SystemExit(main())

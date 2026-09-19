#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
PATH=ROOT/'scripts'/'recover_provider_routes_from_upstreams.py'
spec=importlib.util.spec_from_file_location('recovery_v231_test',PATH)
assert spec is not None and spec.loader is not None
recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)

OLD_SEARCH=[{'base':'https://old.example','route':'/search/{query}','requestSpec':{'method':'GET'},'proofModelVersion':5,'sourceRole':'catalog-search','semanticTypes':['movie']}]
OLD_PROVIDER=[{'searchBase':'https://old.example','searchRoute':'/search/{query}','searchRequestSpec':{'method':'GET'},'steps':[{'base':'https://old.example','route':'/detail/{id}','requestSpec':{'method':'GET'},'role':'detail'}],'semanticTypes':['movie'],'proofModelVersion':5,'sourceRole':'provider-value-correlation'}]
OLD_EXTERNAL=[{'base':'https://old.example','route':'/series/{imdbId}','requestSpec':{'method':'GET'},'proofModelVersion':5,'sourceRole':'external-identity-detail'}]

def write(path:Path,value:dict)->None:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def read(path:Path)->dict:return json.loads(path.read_text())

def run_case(patch:dict,model:dict,recovered:dict)->tuple[dict,dict]:
    with tempfile.TemporaryDirectory(prefix='niakvio-v231-') as tmp:
        root=Path(tmp); overrides=root/'provider-overrides.json'; knowledge=root/'knowledge.json'
        write(overrides,{'provider_patches':{'proof-test':copy.deepcopy(patch)}})
        write(knowledge,{'providers':{'proof-test':{'model':copy.deepcopy(model)}}})
        old_o,old_k=recovery.OVERRIDES,recovery.KNOWLEDGE
        try:
            recovery.OVERRIDES=overrides;recovery.KNOWLEDGE=knowledge
            recovery.apply_recovery({'schemaVersion':5,'providerCount':1,'providers':[dict({'providerId':'proof-test'},**recovered)]})
        finally:
            recovery.OVERRIDES, recovery.KNOWLEDGE=old_o,old_k
        return read(overrides)['provider_patches']['proof-test'],read(knowledge)['providers']['proof-test']['model']

# 1) A zero probe cannot delete any proof-v5 structured authority, even without apiRecipe.
patch={'route_proof_version':5,'search_request_plan':copy.deepcopy(OLD_SEARCH),'provider_value_plan':copy.deepcopy(OLD_PROVIDER),'external_identity_plan':copy.deepcopy(OLD_EXTERNAL),'proof_search_bases':['https://old.example'],'proof_detail_bases':['https://old.example']}
model={'routeProofVersion':5,'searchRequestPlan':copy.deepcopy(OLD_SEARCH),'providerValuePlan':copy.deepcopy(OLD_PROVIDER),'externalIdentityPlan':copy.deepcopy(OLD_EXTERNAL),'proofSearchBases':['https://old.example'],'proofDetailBases':['https://old.example']}
p,m=run_case(patch,model,{'status':'no-proven-route','source':{'repo':'upstream','sha':'zero'},'routes':[],'executionRoutes':[],'routeData':[],'tasks':[]})
assert p.get('search_request_plan')==OLD_SEARCH,p.get('search_request_plan')
assert p.get('provider_value_plan')==OLD_PROVIDER,p.get('provider_value_plan')
assert p.get('external_identity_plan')==OLD_EXTERNAL,p.get('external_identity_plan')
assert p.get('route_proof',{}).get('executionAuthorityPreserved') is True,p.get('route_proof')

# 2) Version-zero/static-looking rows are not executable proof and remain fail-closed.
patch={'route_proof_version':0,'search_request_plan':copy.deepcopy(OLD_SEARCH)}
model={'routeProofVersion':0,'searchRequestPlan':copy.deepcopy(OLD_SEARCH)}
p,m=run_case(patch,model,{'status':'no-proven-route','source':{'repo':'upstream','sha':'zero'},'routes':[],'executionRoutes':[],'routeData':[],'tasks':[]})
assert 'search_request_plan' not in p,p.get('search_request_plan')
assert 'searchRequestPlan' not in m,m.get('searchRequestPlan')

# 3) Fresh positive proof supersedes the old search plan.
route_data=[{'role':'search','origin':'https://new.example','route':'/find/{query}','requestSpec':{'method':'GET','headers':{'accept':'text/html'}},'requestSpecReusable':True,'status':200,'taskStreamCount':1,'taskRawStreamCount':1,'semanticType':'movie','fixture':'interstellar','requestIndex':1}]
patch={'route_proof_version':5,'search_request_plan':copy.deepcopy(OLD_SEARCH)}
model={'routeProofVersion':5,'searchRequestPlan':copy.deepcopy(OLD_SEARCH)}
p,m=run_case(patch,model,{'status':'proven','source':{'repo':'upstream','sha':'positive'},'routes':['/find/{query}'],'executionRoutes':['/find/{query}'],'routeData':route_data,'tasks':[]})
new=p.get('search_request_plan') or []
assert new and new[0].get('base')=='https://new.example',new
assert new!=OLD_SEARCH,new

print('route recovery monotonic structured v23.1 tests passed')

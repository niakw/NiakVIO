#!/usr/bin/env python3
"""The V2 resolver primitive is provider-agnostic and fail-closed."""
from __future__ import annotations
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"scripts/adaptive_runtime/runtime_repair.py"
spec=importlib.util.spec_from_file_location("source_resolver_runtime",SRC)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

source=r'''function txt(v){return String(v||"")}
async function text(url,opt){return ""}
function arrays(js){var out=[],re=/var\s+([a-z0-9_$]+)\s*=\s*\[([\s\S]*?)\s*\];/gim,m;while((m=re.exec(txt(js)))!==null){var vals=[],q=/["']([^"']+)["']/g,x;while((x=q.exec(m[2]))!==null){if(/^https?:\/\//i.test(x[1]))vals.push(x[1])}if(vals.length)out.push(vals)}return out}
async function direct(player,referer){return[]}
async function episodeJs(origin,body,groups,idx){for(var i=0;i<groups.length;i++){var player=groups[i][idx];if(!player)continue;var rows=await direct(player,origin+"/");}}
'''
patched,records=mod._apply_inline_token_resolver_contract(
    source.encode(),"same-origin-api-lien-j-l-v1"
)
text=patched.decode()
assert records and patched!=source.encode()
assert "||/^lien:/i.test(x[1])" in text
assert "epsJeton" in text and "/api/lien.php?j=" in text and "obj&&obj.u" in text
assert "NIAKVIO_SOURCE_RESOLVER_CONTRACT same-origin-api-lien-j-l-v1" in text
assert "anime-sama" not in text.casefold()
# Applying twice is a no-op and an unrelated source is never mutated.
again,again_records=mod._apply_inline_token_resolver_contract(
    patched,"same-origin-api-lien-j-l-v1"
)
assert again==patched and again_records==[]
plain,plain_records=mod._apply_inline_token_resolver_contract(
    b"async function unrelated(){return 1}","same-origin-api-lien-j-l-v1"
)
assert plain==b"async function unrelated(){return 1}" and plain_records==[]
try:
    mod._apply_inline_token_resolver_contract(source.encode(),"other")
except ValueError:
    pass
else:
    raise AssertionError("unknown resolver contract accepted")
with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as handle:
    handle.write(text)
    js=handle.name
check=subprocess.run(["node","--check",js],capture_output=True,text=True,check=False)
Path(js).unlink(missing_ok=True)
assert check.returncode==0,check.stderr

# Cross the real control-plane boundary: Learning planner selection -> adaptive
# matching -> exact provider-byte mutation. Separate planner/unit tests are not
# enough because the production failures occurred between these components.
planner=ROOT/"engine_v2/scripts/plan-repairs.mjs"
policy={"production":{
    "negativeExperimentMemory":{"rotateExperimentAfterFailures":1,"maxVariantsPerSignature":5,"finalVariantGeneration":2,"maxLearningGenerationsPerSignature":5},
    "maxHypotheses":3,"maxMutationsPerProvider":2,"maxRepeatedSignature":2,
    "maxGeneratedBytesPerProvider":180000,"maxElapsedMsPerProvider":45000,
},"skillMaturity":{}}
planner_candidate={
    "canonical_id":"resolver-representative",
    "censusPrior":{"status":"CHAIN REACHED","dominantIssue":"provider_network_zero_result","evidenceDepth":["anime=chain_reached"]},
    "metadata":{"supportedTypes":["anime"]},
}
planner_result={
    "status":"no_streams",
    "evidence":{"streams_playable":0,"streams_returned":0},
    "tests":[{
        "fixture":{"mediaType":"anime","category":"anime","title":"Synthetic"},
        "failure_class":"content_lookup_completed_no_streams",
        "status":"no_streams","network_observations":[],
        "streams_playable":0,"stream_count":0,
    }],
}
payload={
    "mode":"learning","explorationChain":True,"forcePreferredStrategy":"",
    "learningPreferredStrategy":"catalogue_inline_token_resolver_v2",
    "learningPreferredFailureClass":"chain_terminal_gap",
    "policy":policy,"learnedSkills":{},"negativeMemory":[],
    "items":[{"key":"published:resolver-representative","candidate":planner_candidate,"result":planner_result,"state":{}}],
}
planned=subprocess.run(
    ["node",str(planner)],cwd=ROOT,input=json.dumps(payload),
    capture_output=True,text=True,check=True,timeout=20,
)
plan=next(iter(json.loads(planned.stdout)["plans"].values()))
assert plan["learningPreferredSelected"] is True,plan
assert plan["postExhaustionStrategyProfile"]=="catalogue_inline_token_resolver_v2",plan
assert plan["allowedProfiles"]==["catalogue_inline_token_resolver_v2"],plan

with tempfile.TemporaryDirectory() as tmp:
    stage=Path(tmp)
    provider_path=stage/"providers"/"resolver-representative.js"
    provider_path.parent.mkdir(parents=True,exist_ok=True)
    provider_path.write_text(source,encoding="utf-8")
    candidate={
        "key":"published:resolver-representative",
        "canonical_id":"resolver-representative",
        "source":"synthetic",
        "local_path":"providers/resolver-representative.js",
        "bytes":len(source.encode()),
        "metadata":{
            "supportedTypes":["anime"],
            "baseUrl":"https://resolver-representative.example",
        },
        "brain_repair_plan":plan,
    }
    result={
        "key":"published:resolver-representative",
        "status":"no_streams",
        "evidence":{"streams_playable":0,"streams_returned":0},
        "tests":planner_result["tests"],
    }
    profiles=mod.matching_profiles(candidate,result,source,{})
    executable=[name for name in profiles if name in set(plan["allowedProfiles"])]
    assert executable==["catalogue_inline_token_resolver_v2"],(profiles,plan)
    repaired,error=mod.create_repair_candidate(
        stage,candidate,"catalogue_inline_token_resolver_v2",1
    )
    assert error is None and repaired is not None,error
    assert repaired["runtime_repair"]["profile"]=="catalogue_inline_token_resolver_v2",repaired
    assert repaired["runtime_repair"]["strategy"]=="catalogue_inline_token_resolver_v2",repaired
    final_bytes=(stage/repaired["local_path"]).read_bytes()
    assert final_bytes!=source.encode()
    final_text=final_bytes.decode()
    assert "NIAKVIO_SOURCE_RESOLVER_CONTRACT same-origin-api-lien-j-l-v1" in final_text
    assert "||/^lien:/i.test(x[1])" in final_text

# Downstream request-contract profiles must compose the resolver primitive
# instead of replacing it. This is the causal-chain regression that previously
# produced changed bytes with a zero parent->candidate network delta.
composed_candidate = {
    "canonical_id": "resolver-representative",
    "metadata": {
        "name": "Resolver Representative",
        "supportedTypes": ["anime"],
        "baseUrl": "https://resolver-representative.example",
    },
    "brain_repair_plan": {
        "failureClass": "media_extraction_gap",
        "experimentVariant": 4,
        "experimentGeneration": 5,
        "postExhaustionStrategyProfile": "document_request_contract_mining_v2",
        "allowedProfiles": ["document_request_contract_mining_v2"],
        "learningPreferredRequested": "document_request_contract_mining_v2",
        "learningPreferredSelected": True,
    },
}
composed_bytes, composed_records = mod._apply_adaptive(
    source.encode(),
    composed_candidate,
    profile_name="document_request_contract_mining_v2",
)
composed_text = composed_bytes.decode()
assert composed_bytes != source.encode()
assert "NIAKVIO_SOURCE_RESOLVER_CONTRACT same-origin-api-lien-j-l-v1" in composed_text
assert "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5" in composed_text
assert "NUVIO_ADAPTIVE_RUNTIME_CORE_V7" not in composed_text
assert '"scriptedRequestMining":true' in composed_text
assert '"newStrategyId":"document_request_contract_mining_v2"' in composed_text
profiles = [str(row.get("profile") or "") for row in composed_records]
assert profiles == [
    "inline_token_resolver_contract",
    "document_request_contract_mining_v2",
], composed_records
with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as handle:
    handle.write(composed_text)
    composed_js=handle.name
check=subprocess.run(["node","--check",composed_js],capture_output=True,text=True,check=False)
Path(composed_js).unlink(missing_ok=True)
assert check.returncode==0,check.stderr

print("Brain source resolver runtime V2: primitive + planner-to-mutation integration passed")

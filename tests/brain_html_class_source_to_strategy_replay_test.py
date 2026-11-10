#!/usr/bin/env python3
"""Current-byte HTML failure -> Brain planner -> bounded Lego selection.

This uses the actual provider-owned renderer and the real JS Brain planner,
not a provider-specific mutation. Source diagnosis is only a hypothesis;
offline 0->1 test and terminal playback gates remain separate.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import brain_repair_runtime as brain

def load(name, path):
    spec=importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

provider=load("brain_structural_source_oracle", ROOT/"scripts/provider_patches/4khdhub_runtime_v1.py")
source=provider.WRAPPER.replace(
    "CONFIG_PLACEHOLDER",
    json.dumps({"base":"https://provider.example","maxStreams":8,"ua":"test"}))
candidate={"key":"published:source-oracle","canonical_id":"source-oracle",
           "local_path":"providers/isolated-real-html-runtime.js",
           "metadata":{"supportedTypes":["movie","tv"]}}
failure={"status":"no_streams","evidence":{"streams_playable":0,"streams_returned":0},
         "tests":[{"status":"no_streams","failure_class":"content_lookup_completed_no_streams",
                   "fixture":{"mediaType":"movie","category":"movie"},
                   "streams_playable":0,"stream_count":0,
                   "network_observations":[{"status":200,"ok":True,"stage":"search"}]}]}
policy={"production":{"negativeExperimentMemory":{
        "rotateExperimentAfterFailures":1,"maxVariantsPerSignature":5},
        "maxHypotheses":3,"maxMutationsPerProvider":2,
        "maxRepeatedSignature":2,"maxGeneratedBytesPerProvider":180000,
        "maxElapsedMsPerProvider":45000},"skillMaturity":{}}
def node_plan(signal, memory=None, force=""):
    item={"key":"published:source-oracle",
          "candidate":{"canonical_id":"source-oracle",
                       "metadata":{"supportedTypes":["movie","tv"]},
                       "censusPrior":{"status":"ROUTE PROVEN",
                                      "dominantIssue":"provider_network_zero_result"},
                       **({"structuralRepairEvidence":signal} if signal else {})},
          "result":failure,"state":{}}
    payload={"mode":"repair","policy":policy,"learnedSkills":[],
             "negativeMemory":memory or [],"llmGuidance":[],
             "historicalSolutions":[],"forcePreferredStrategy":force,
             "items":[item]}
    p=subprocess.run(["node",str(ROOT/"engine_v2/scripts/plan-repairs.mjs")],
                     input=json.dumps(payload),capture_output=True,text=True,
                     cwd=ROOT,timeout=25)
    assert p.returncode==0,p.stderr
    d=json.loads(p.stdout)
    assert d["plannerErrors"]==0,d
    return d["plans"]["published:source-oracle"]

with tempfile.TemporaryDirectory(prefix="brain-html-structure-") as tmp:
    stage=Path(tmp)
    file=stage/candidate["local_path"]
    file.parent.mkdir(parents=True)
    file.write_text(source,encoding="utf-8")
    signal=brain._current_source_structural_repair_evidence(stage,candidate,failure)
    assert signal["profile"]=="html_class_token_exact_v1",signal
    assert signal["sourceSha256"]==hashlib.sha256(source.encode()).hexdigest()
    assert signal["diagnosticOnly"] and not signal["proofAuthority"]
    base=node_plan({})
    selected=node_plan(signal)
    assert selected["failureClass"] in {"route_proven_gap","search_gap"},selected
    assert selected["action"]=="probe-targeted-repair",selected
    assert selected["sourceStructuralProfileSelected"] is True,selected
    assert selected["allowedProfiles"][0]=="html_class_token_exact_v1",selected
    assert base["sourceStructuralProfileSelected"] is False,base
    assert "html_class_token_exact_v1" not in base["allowedProfiles"],base
    # The same known-source defect is recognized without any provider ID.
    alt={**candidate,"canonical_id":"second-provider","key":"published:second-provider"}
    assert brain._current_source_structural_repair_evidence(stage,alt,failure)["profile"]==signal["profile"]
    # A replayed actual failure of the same implementation blocks the
    # profile instead of bypassing negative memory with a new SHA.
    memory=[{"providerId":"source-oracle","profile":"html_class_token_exact_v1",
             "failureClass":selected["failureClass"],
             "executionObserved":True,"failures":1,
             "consecutiveFailures":1,"successes":0,
             "strategyImplementationFingerprint":selected["sourceStructuralProfileFingerprint"]}]
    failed=node_plan(signal,memory=memory)
    assert failed["sourceStructuralProfileSelected"] is False,failed
    # A well-known binding cannot be spoofed by arbitrary unchecked text.
    spoof=node_plan({**signal,"source":"historical-fixture"})
    assert spoof["sourceStructuralProfileSelected"] is False,spoof
    # Brain plan owner enforces exactly the selected bounded profile.
    brain.reset_runtime_state()
    brain.PLANS["published:source-oracle"]=selected
    wrapped=brain.wrap_matching_profiles(
        lambda *_args,**_kwargs:["adaptive_runtime_recovery","html_class_token_exact_v1"])
    chosen=wrapped(candidate,failure,source,config={})
    assert chosen[0]=="html_class_token_exact_v1",chosen
    # A deferred or held plan never gains mutation power from structural hints.
    brain.PLANS["published:source-oracle"]={**selected,"action":"deferred_retry"}
    assert wrapped(candidate,failure,source,config={})==[]
    assert brain._current_source_structural_repair_evidence(
        stage,candidate,{"status":"blocked"})=={}
    assert brain._current_source_structural_repair_evidence(
        stage,{**candidate,"local_path":"../.env"},failure)=={}
print("FIELD_BRAIN_HTML_CLASS_SOURCE_SELECTION real_published_family_source=true "
      "source_sha_bound=true parser_profile_selected=true "
      "negative_experiment_honored=true no_provider_id_exception=true "
      "no_direct_provider_mutation=true terminal_playback_unproven=true")

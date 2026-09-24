#!/usr/bin/env python3
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SCRIPT=ROOT/"scripts/import_external_brain_llm_guidance.py"
spec=importlib.util.spec_from_file_location("external_guidance",SCRIPT);assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
experiment={"routePolicy":"owned_plus_peer","recipePolicy":"current_plus_provider_peer","roleOrder":["player","source","api"],"terminalOnly":True,"aliasSearch":False,"responseSalvage":True,"documentRequestMining":False,"sessionBootstrap":True,"maxDepth":5,"maxPages":20,"maxEmbeds":28,"maxRecipePasses":4}
from brain_llm_experiment import fingerprint
fp=fingerprint(experiment)
row={"providerId":"Movie_Box","failureClass":"media-extraction-gap","targetLayer":"provider","strategy":"proven-request-program-and-terminal-extraction","profile":"player_media_extractor_v1","confidence":.96,"priorOnly":True,"experiment":experiment,"experimentFingerprint":fp}
base={"schemaVersion":2,"sourceNiakvioSha":"a"*40,"brainLlmSha":"b"*40,"publicationAuthority":False,"directMutationAuthority":False,"proofAuthority":False,"rawMutationContentRetained":False,"privateContentRetained":False,"minConfidence":.8,"providerCount":1,"rows":[row]}
safe=mod.sanitize(base,current_sha="c"*40,guidance_commit="d"*40)
assert safe["schemaVersion"]==2,safe
assert safe["sourceSha"]=="c"*40 and safe["sourceExternalNiakvioSha"]=="a"*40
assert safe["rows"][0]["providerId"]=="movie-box" and safe["rows"][0]["failureClass"]=="media_extraction_gap"
assert safe["rows"][0]["experiment"]==experiment
assert safe["rows"][0]["experimentFingerprint"]==fp
# v1 remains readable during migration but has no executable spec.
legacy={**base,"schemaVersion":1,"rows":[{k:v for k,v in row.items() if k not in {"experiment","experimentFingerprint"}}]}
legacy_safe=mod.sanitize(legacy,current_sha="c"*40)
assert legacy_safe["schemaVersion"]==2
assert "experiment" not in legacy_safe["rows"][0]
ok,blocked=mod.neutral_source_drift([".github/workflows/provider-recognition-repair-v6.yml",".github/triggers/provider-recognition-repair-v6.json","tests/x.py","scripts/import_external_brain_llm_guidance.py","scripts/brain_repair_runtime.py","scripts/run_provider_brain_repair.py","scripts/select_provider_materialization_scope.py","scripts/run_provider_repair_pipeline_v6.py","engine_v2/scripts/plan-repairs.mjs","automation/brain-repair-memory.json","automation/brain-positive-program-memory.json","automation/provider-brain-repair-123.json","automation/provider-targeted-regression-recovery-latest.json","automation/provider-repair-batch-refined-latest.json","MEMORY.md"]);assert ok and not blocked
ok,blocked=mod.neutral_source_drift(["provider-overrides.json","providers/demo.js"]);assert not ok and blocked==["provider-overrides.json","providers/demo.js"]
for bad in [
 {**base,"privateContentRetained":True},
 {**base,"rows":[{**row,"profile":"search_contract_inference_v1"}]},
 {**base,"rows":[{**row,"experimentFingerprint":"f"*64}]},
 {**base,"rawPrivateTranscript":"forbidden"},
]:
 try:mod.sanitize(bad,current_sha="c"*40)
 except ValueError:pass
 else:raise AssertionError("unsafe guidance accepted")
print("external Brain LLM v1/v2 guidance import contract passed")

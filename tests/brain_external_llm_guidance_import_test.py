#!/usr/bin/env python3
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SCRIPT=ROOT/"scripts/import_external_brain_llm_guidance.py"
spec=importlib.util.spec_from_file_location("external_guidance",SCRIPT);assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
base={"schemaVersion":1,"sourceNiakvioSha":"a"*40,"brainLlmSha":"b"*40,"publicationAuthority":False,"directMutationAuthority":False,"proofAuthority":False,"rawMutationContentRetained":False,"privateContentRetained":False,"minConfidence":.8,"providerCount":1,"rows":[{"providerId":"Movie_Box","failureClass":"media-extraction-gap","targetLayer":"provider","strategy":"proven-request-program-and-terminal-extraction","profile":"player_media_extractor_v1","confidence":.96,"priorOnly":True}]}
safe=mod.sanitize(base,current_sha="c"*40,guidance_commit="d"*40)
assert safe["sourceSha"]=="c"*40 and safe["sourceExternalNiakvioSha"]=="a"*40
assert safe["rows"][0]["providerId"]=="movie-box" and safe["rows"][0]["failureClass"]=="media_extraction_gap"
ok,blocked=mod.neutral_source_drift([".github/workflows/provider-recognition-repair-v6.yml",".github/triggers/provider-recognition-repair-v6.json","tests/x.py","scripts/import_external_brain_llm_guidance.py","scripts/select_provider_materialization_scope.py","scripts/run_provider_repair_pipeline_v6.py","MEMORY.md"]);assert ok and not blocked
ok,blocked=mod.neutral_source_drift(["provider-overrides.json","providers/demo.js"]);assert not ok and blocked==["provider-overrides.json","providers/demo.js"]
for bad in [
 {**base,"privateContentRetained":True},
 {**base,"rows":[{**base["rows"][0],"profile":"search_contract_inference_v1"}]},
 {**base,"rawPrivateTranscript":"forbidden"},
]:
 try:mod.sanitize(bad,current_sha="c"*40)
 except ValueError:pass
 else:raise AssertionError("unsafe guidance accepted")
print("external private-informed Brain LLM guidance import contract passed")

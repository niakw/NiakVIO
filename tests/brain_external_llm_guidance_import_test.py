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

memory={"experimentMemory":{"entries":[
 {"providerId":"movie-box","profile":"player_media_extractor_v1","llmAdvisorExperimentFingerprint":fp,"consecutiveFailures":1,"failures":1,"successes":0},
]}}
filtered,dropped=mod.filter_failed_guidance(mod.sanitize(base,current_sha="c"*40),memory)
assert dropped==1,(filtered,dropped)
assert filtered["providerCount"]==0 and filtered["rows"]==[],filtered
not_failed,dropped=mod.filter_failed_guidance(mod.sanitize(base,current_sha="c"*40),{"experimentMemory":{"entries":[
 {"providerId":"movie-box","profile":"player_media_extractor_v1","llmAdvisorExperimentFingerprint":"e"*64,"consecutiveFailures":1}
]}})
assert dropped==0 and not_failed["providerCount"]==1,not_failed
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

# Provider-local drift invalidates only the changed provider rows, not the
# entire sanitized advisor prior. Global/all drift remains fail-closed.
row2={**row,"providerId":"YFlix","failureClass":"search-gap","strategy":"search-detail-player-terminal-traversal","profile":"proven_route_terminal_traversal_v1"}
base2={**base,"providerCount":2,"rows":[row,row2]}
safe2=mod.sanitize(base2,current_sha="c"*40,guidance_commit="d"*40)
importer_source=SCRIPT.read_text(encoding="utf-8")
assert '"--committed-only"' in importer_source, "external guidance drift must ignore sandbox working-tree mutations"

orig_scope=mod.provider_materialization_scope
try:
 mod.provider_materialization_scope=lambda root,source,current:{"mode":"providers","providers":["movie-box"],"changedPaths":["providers/movie-box.js"],"reasons":["providers:providers/movie-box.js:movie-box"]}
 neutral,drifted=mod.source_drift(ROOT,"a"*40,"c"*40)
 assert neutral==[] and drifted=={"movie-box"}
 kept=[r for r in safe2["rows"] if mod.canon(r.get("providerId")) not in drifted]
 assert [r["providerId"] for r in kept]==["yflix"]
 mod.provider_materialization_scope=lambda root,source,current:{"mode":"all","providers":[],"changedPaths":["manifest.json","scripts/provider_patches/animesalt_runtime_v1.py","scripts/provider_patches/global_stream_presentation_v1.py","assets/README.md"],"reasons":["providers:manifest.json:animesalt","patch:scripts/provider_patches/animesalt_runtime_v1.py:animesalt","unowned-patch:scripts/provider_patches/global_stream_presentation_v1.py"]}
 neutral,drifted=mod.source_drift(ROOT,"a"*40,"c"*40)
 assert neutral==[] and drifted=={"animesalt"},(neutral,drifted)
 mod.provider_materialization_scope=lambda root,source,current:{"mode":"all","providers":[],"changedPaths":["scripts/provider_base_store.py"],"reasons":["global:scripts/provider_base_store.py"]}
 try:mod.source_drift(ROOT,"a"*40,"c"*40)
 except ValueError:pass
 else:raise AssertionError("global drift must reject external guidance")
finally:
 mod.provider_materialization_scope=orig_scope

print("external Brain LLM v1/v2 guidance import contract passed")

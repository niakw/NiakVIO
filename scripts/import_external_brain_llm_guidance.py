#!/usr/bin/env python3
"""Validate and re-scope the public sanitized Brain-LLM advisor prior."""
from __future__ import annotations
import argparse,json,re,subprocess,sys,tempfile
from pathlib import Path
from typing import Any
SCRIPT_DIR=Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:sys.path.insert(0,str(SCRIPT_DIR))
from brain_llm_experiment import validate_public

ROOT=Path(__file__).resolve().parents[1]
SHA40=re.compile(r"^[0-9a-f]{40}$")
PROVIDER_ID=re.compile(r"^[a-z0-9][a-z0-9._-]{0,159}$")
URLISH=re.compile(r"(?i)(?:https?://|github_pat_|\bgh[pousr]_[A-Za-z0-9]{20,}|\b(?:authorization|cookie|token|secret|password|api[_-]?key)\s*[:=])")
STRATEGY_TO_PROFILE={
 "provider-owned-origin-header-and-domain-replay":"provider_origin_failover_v1",
 "search-detail-player-terminal-traversal":"proven_route_terminal_traversal_v1",
 "terminal-media-extractor-with-playback-validation":"chain_terminal_extractor_v1",
 "same-provider-candidate-program-replay":"retained_candidate_replay_v1",
 "proven-request-program-and-terminal-extraction":"player_media_extractor_v1",
 "discover-api-from-current-page-and-bundles":"search_contract_inference_v1",
}
TOP_LEVEL_FIELDS={"schemaVersion","sourceNiakvioSha","brainLlmSha","publicationAuthority","directMutationAuthority","proofAuthority","rawMutationContentRetained","privateContentRetained","minConfidence","providerCount","rows"}
ROW_FIELDS_V1={"providerId","failureClass","targetLayer","strategy","profile","confidence","priorOnly"}
ROW_FIELDS_V2=ROW_FIELDS_V1|{"experiment","experimentFingerprint"}
NEUTRAL_DRIFT_PREFIXES=(".github/workflows/",".github/triggers/","tests/","assets/","docs/","automation/provider-brain-repair-","automation/provider-targeted-regression-recovery-","automation/provider-repair-batch-refined-")
NEUTRAL_DRIFT_FILES={"MEMORY.md","README.md","README.fr.md","scripts/import_external_brain_llm_guidance.py","scripts/brain_repair_runtime.py","scripts/run_provider_brain_repair.py","scripts/select_provider_materialization_scope.py","scripts/run_provider_repair_pipeline_v6.py","scripts/provider_patches/global_stream_presentation_v1.py","scripts/normalize_stream_presentation_v12.py","scripts/upgrade_stream_language_roles_v1.py","scripts/fix_global_stream_presentation_v23_tests.py","scripts/fix_stream_language_role_proof_v1.py","engine_v2/src/stream-presentation.mjs","engine_v2/scripts/plan-repairs.mjs","automation/brain-repair-memory.json","automation/brain-positive-program-memory.json"}
MATERIALIZATION_SCOPE_SCRIPT=ROOT/"scripts/select_provider_materialization_scope.py"

def canon(value:object)->str:
 return str(value or "").strip().casefold().replace("_","-")

def git(root:Path,*args:str)->subprocess.CompletedProcess[str]:
 return subprocess.run(["git",*args],cwd=root,text=True,capture_output=True,check=False)

def neutral_source_drift(paths:list[str])->tuple[bool,list[str]]:
 blocked=[p for p in paths if p not in NEUTRAL_DRIFT_FILES and not any(p.startswith(x) for x in NEUTRAL_DRIFT_PREFIXES)]
 return not blocked,blocked

def provider_materialization_scope(root:Path,source_sha:str,current_sha:str)->dict[str,Any]:
 if source_sha==current_sha:
  return {"mode":"none","providers":[],"changedPaths":[],"reasons":[]}
 for sha in (source_sha,current_sha):
  if git(root,"cat-file","-e",f"{sha}^{{commit}}").returncode!=0:raise ValueError(f"guidance source commit unavailable: {sha}")
 if git(root,"merge-base","--is-ancestor",source_sha,current_sha).returncode!=0:raise ValueError("guidance source is not an ancestor of current Repair SHA")
 script=root/"scripts/select_provider_materialization_scope.py"
 if not script.is_file():raise ValueError("provider materialization scope selector missing")
 with tempfile.TemporaryDirectory(prefix="niakvio-guidance-scope-") as tmp:
  output=Path(tmp)/"scope.json"
  p=subprocess.run(
   [sys.executable,str(script),"--base",source_sha,"--head",current_sha,"--committed-only","--output",str(output)],
   cwd=root,text=True,capture_output=True,check=False,
  )
  if p.returncode!=0 or not output.is_file():
   raise ValueError("cannot classify provider drift since guidance source")
  scope=json.loads(output.read_text(encoding="utf-8"))
 if not isinstance(scope,dict):raise ValueError("provider drift classifier returned invalid payload")
 return scope

def failed_llm_experiments(memory:dict[str,Any])->set[tuple[str,str,str]]:
 rows=[]
 experiment_memory=memory.get("experimentMemory") if isinstance(memory.get("experimentMemory"),dict) else {}
 if isinstance(experiment_memory.get("entries"),list):rows.extend(experiment_memory.get("entries") or [])
 if isinstance(memory.get("entries"),list):rows.extend(memory.get("entries") or [])
 failed=set()
 for row in rows:
  if not isinstance(row,dict) or int(row.get("consecutiveFailures") or 0)<1:continue
  provider=canon(row.get("providerId"));profile=str(row.get("profile") or "").strip().casefold()
  fp=str(row.get("llmAdvisorExperimentFingerprint") or "").strip().casefold()
  if provider and profile and re.fullmatch(r"[0-9a-f]{64}",fp):failed.add((provider,profile,fp))
 return failed

def filter_failed_guidance(payload:dict[str,Any],memory:dict[str,Any])->tuple[dict[str,Any],int]:
 failed=failed_llm_experiments(memory)
 if not failed:return payload,0
 before=len(payload.get("rows") or [])
 payload["rows"]=[
  row for row in payload.get("rows") or []
  if (
   canon(row.get("providerId")),
   str(row.get("profile") or "").strip().casefold(),
   str(row.get("experimentFingerprint") or "").strip().casefold(),
  ) not in failed
 ]
 payload["providerCount"]=len({row["providerId"] for row in payload["rows"]})
 return payload,before-len(payload["rows"])

def source_drift(root:Path,source_sha:str,current_sha:str)->tuple[list[str],set[str]]:
 scope=provider_materialization_scope(root,source_sha,current_sha)
 mode=str(scope.get("mode") or "all").strip().casefold()
 changed=sorted({str(x).strip() for x in scope.get("changedPaths") or [] if str(x).strip()})
 reasons=[str(x).strip() for x in scope.get("reasons") or [] if str(x).strip()]
 if mode=="none":
  return changed,set()
 if mode=="providers":
  providers={canon(x) for x in scope.get("providers") or [] if canon(x)}
  if not providers:
   raise ValueError(f"provider drift classifier omitted provider ids: reasons={';'.join(reasons) or '-'}")
  return [],providers
 if mode=="all":
  # A global classifier result can be caused by one unowned but network-neutral
  # presentation/docs patch plus ordinary provider-local drift. Preserve the
  # unaffected advisor rows instead of discarding the whole prior.
  providers:set[str]=set()
  blockers:list[str]=[]
  for reason in reasons:
   parts=reason.split(":",2)
   kind=parts[0] if parts else ""
   if kind in {"providers","patch"} and len(parts)==3:
    providers.update(canon(v) for v in parts[2].split(",") if canon(v))
    continue
   if kind in {"global","unowned-patch"} and len(parts)>=2:
    path=reason.split(":",1)[1]
    ok,_=neutral_source_drift([path])
    if ok:continue
   blockers.append(reason)
  if not blockers:
   if providers:return [],providers
   ok,blocked=neutral_source_drift(changed)
   if ok:return changed,set()
   blockers.extend(blocked)
  raise ValueError(
   "global/provider-wide drift since guidance source: "
   f"mode={mode} providers={','.join(sorted(providers)) or '-'} "
   f"reasons={';'.join(blockers or reasons) or '-'}"
  )
 providers=",".join(str(x) for x in scope.get("providers") or [])
 raise ValueError(f"global/provider-wide drift since guidance source: mode={mode} providers={providers or '-'} reasons={';'.join(reasons) or '-'}")

def sanitize(value:dict[str,Any],*,current_sha:str,guidance_commit:str="")->dict[str,Any]:
 if not isinstance(value,dict):raise ValueError("external Brain-LLM guidance must be an object")
 extra=set(value)-TOP_LEVEL_FIELDS
 if extra:raise ValueError("unexpected external guidance fields: "+",".join(sorted(extra)))
 for key in ("publicationAuthority","directMutationAuthority","proofAuthority","rawMutationContentRetained","privateContentRetained"):
  if value.get(key) is not False:raise ValueError(f"unsafe external guidance flag: {key}")
 source_sha=str(value.get("sourceNiakvioSha") or "").strip().casefold()
 brain_sha=str(value.get("brainLlmSha") or "").strip().casefold()
 current_sha=str(current_sha or "").strip().casefold()
 guidance_commit=str(guidance_commit or "").strip().casefold()
 for label,sha in (("source",source_sha),("brain",brain_sha),("current",current_sha)):
  if not SHA40.fullmatch(sha):raise ValueError(f"invalid {label} SHA")
 if guidance_commit and not SHA40.fullmatch(guidance_commit):raise ValueError("invalid guidance branch commit SHA")
 try:minimum=max(.80,min(1.0,float(value.get("minConfidence") or .80)))
 except (TypeError,ValueError):minimum=.80
 rows=value.get("rows")
 if not isinstance(rows,list):raise ValueError("external guidance rows missing")
 safe=[];seen=set()
 schema_version=max(1,int(value.get("schemaVersion") or 1))
 if schema_version not in {1,2}:raise ValueError("unsupported external guidance schema")
 expected_fields=ROW_FIELDS_V2 if schema_version>=2 else ROW_FIELDS_V1
 for raw in rows[:128]:
  if not isinstance(raw,dict) or set(raw)!=expected_fields:raise ValueError("external guidance row shape is not exact")
  provider=canon(raw.get("providerId"));failure=canon(raw.get("failureClass"));strategy=canon(raw.get("strategy"))
  profile=str(raw.get("profile") or "").strip().casefold();target=str(raw.get("targetLayer") or "").strip().casefold()
  try:confidence=max(0.0,min(1.0,float(raw.get("confidence") or 0.0)))
  except (TypeError,ValueError):confidence=0.0
  expected=STRATEGY_TO_PROFILE.get(strategy)
  if not provider or not PROVIDER_ID.fullmatch(provider) or not failure or target!="provider" or raw.get("priorOnly") is not True or confidence<minimum or expected is None or profile!=expected:
   raise ValueError(f"unsafe or inconsistent external guidance row for {provider or '<missing>'}")
  experiment={};experiment_fingerprint=""
  if schema_version>=2:
   experiment,experiment_fingerprint=validate_public(raw.get("experiment"),str(raw.get("experimentFingerprint") or ""))
  key=(provider,profile,experiment_fingerprint)
  if key in seen:continue
  seen.add(key)
  row={"providerId":provider,"failureClass":failure.replace("-","_"),"targetLayer":"provider","strategy":strategy.replace("-","_"),"profile":profile,"confidence":round(confidence,6),"priorOnly":True}
  if experiment_fingerprint:row.update({"experiment":experiment,"experimentFingerprint":experiment_fingerprint})
  safe.append(row)
 payload={"schemaVersion":2,"sourceSha":current_sha,"sourceExternalNiakvioSha":source_sha,"sourceBrainLlmSha":brain_sha,"sourceGuidanceCommit":guidance_commit,"publicationAuthority":False,"directMutationAuthority":False,"proofAuthority":False,"rawMutationContentRetained":False,"privateContentRetained":False,"persistentExternalPrior":True,"providerCount":len({r["providerId"] for r in safe}),"rows":safe}
 if URLISH.search(json.dumps(payload,sort_keys=True)):raise ValueError("URL/credential-shaped text survived external guidance sanitizer")
 return payload

def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--current-sha",required=True);p.add_argument("--guidance-commit",default="");p.add_argument("--negative-memory",type=Path);p.add_argument("--repo-root",type=Path,default=ROOT);a=p.parse_args()
 value=json.loads(a.input.read_text(encoding="utf-8"))
 payload=sanitize(value,current_sha=a.current_sha,guidance_commit=a.guidance_commit)
 changed,drifted_providers=source_drift(a.repo_root,payload["sourceExternalNiakvioSha"],payload["sourceSha"])
 if drifted_providers:
  before=len(payload["rows"])
  payload["rows"]=[row for row in payload["rows"] if canon(row.get("providerId")) not in drifted_providers]
  payload["providerCount"]=len({row["providerId"] for row in payload["rows"]})
  dropped=before-len(payload["rows"])
 else:
  dropped=0
 failed_dropped=0
 if a.negative_memory and a.negative_memory.is_file():
  memory=json.loads(a.negative_memory.read_text(encoding="utf-8"))
  if isinstance(memory,dict):payload,failed_dropped=filter_failed_guidance(payload,memory)
 payload["neutralDriftPaths"]=changed
 payload["droppedFailedExperimentRows"]=failed_dropped
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("FIELD_EXTERNAL_BRAIN_LLM_GUIDANCE "+f"providers={payload['providerCount']} source={payload['sourceExternalNiakvioSha'][:12]} current={payload['sourceSha'][:12]} neutral_drift={len(changed)} provider_drift={len(drifted_providers)} dropped_rows={dropped} failed_fingerprints={failed_dropped} private_content=false")
 return 0
if __name__=="__main__":raise SystemExit(main())

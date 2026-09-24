#!/usr/bin/env python3
"""Convert Brain-LLM output into bounded, executable, non-authoritative guidance."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from typing import Any
from brain_llm_experiment import from_proposal,fingerprint
STRATEGY_TO_PROFILE={
 "provider-owned-origin-header-and-domain-replay":"provider_origin_failover_v1",
 "search-detail-player-terminal-traversal":"proven_route_terminal_traversal_v1",
 "terminal-media-extractor-with-playback-validation":"chain_terminal_extractor_v1",
 "same-provider-candidate-program-replay":"retained_candidate_replay_v1",
 "proven-request-program-and-terminal-extraction":"player_media_extractor_v1",
 "discover-api-from-current-page-and-bundles":"search_contract_inference_v1",
}
ALLOWED_PROFILES=frozenset(STRATEGY_TO_PROFILE.values());PROVIDER_ID=re.compile(r"^[a-z0-9][a-z0-9._-]{0,159}$")
def canon(v):return str(v or "").strip().casefold().replace("_","-")
def safe_sha(v):
 raw=str(v or "").strip().casefold();return raw if re.fullmatch(r"[0-9a-f]{40}",raw) else ""
def load_jsonl(path):
 out=[]
 if not path.is_file():return out
 for line in path.read_text(encoding="utf-8").splitlines():
  if not line.strip():continue
  try:v=json.loads(line)
  except json.JSONDecodeError:continue
  if isinstance(v,dict):out.append(v)
 return out
def sanitize(rows:list[dict[str,Any]],*,source_sha:str,brain_llm_sha:str,min_confidence:float)->dict[str,Any]:
 source_sha=safe_sha(source_sha);brain_llm_sha=safe_sha(brain_llm_sha)
 if not source_sha or not brain_llm_sha:raise ValueError("source and Brain-LLM SHAs must be exact 40-hex commits")
 guidance=[];seen=set()
 for row in rows:
  if row.get("ok") is not True:continue
  provider=canon(row.get("provider"));proposal=row.get("proposal")
  if not provider or not PROVIDER_ID.fullmatch(provider) or not isinstance(proposal,dict) or canon(proposal.get("provider_id"))!=provider:continue
  strategy=canon(proposal.get("strategy"));profile=STRATEGY_TO_PROFILE.get(strategy,"");target=canon(proposal.get("target_layer"));failure=canon(row.get("failure_class"))
  try:confidence=max(0.,min(1.,float(proposal.get("confidence") or 0.)))
  except (TypeError,ValueError):confidence=0.
  if proposal.get("abstain") is True or target!="provider" or confidence<min_confidence or profile not in ALLOWED_PROFILES:continue
  experiment=from_proposal(proposal.get("experiment"),strategy=strategy);fp=fingerprint(experiment);key=(provider,profile,fp)
  if key in seen:continue
  seen.add(key);guidance.append({"providerId":provider,"failureClass":failure,"targetLayer":"provider","strategy":strategy,"profile":profile,"confidence":round(confidence,6),"priorOnly":True,"experiment":experiment,"experimentFingerprint":fp})
 return {"schemaVersion":2,"sourceSha":source_sha,"brainLlmSha":brain_llm_sha,"publicationAuthority":False,"directMutationAuthority":False,"proofAuthority":False,"rawMutationContentRetained":False,"minConfidence":min_confidence,"providerCount":len({r["providerId"] for r in guidance}),"rows":guidance}
def main():
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--source-sha",required=True);p.add_argument("--brain-llm-sha",required=True);p.add_argument("--min-confidence",type=float,default=.8);a=p.parse_args()
 if not 0<=a.min_confidence<=1:raise SystemExit("--min-confidence must be between 0 and 1")
 report=sanitize(load_jsonl(a.input),source_sha=a.source_sha,brain_llm_sha=a.brain_llm_sha,min_confidence=a.min_confidence);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(f"FIELD_BRAIN_LLM_GUIDANCE providers={report['providerCount']} rows={len(report['rows'])} experiments={len(report['rows'])} brain_llm_sha={report['brainLlmSha'][:12]}");return 0
if __name__=="__main__":raise SystemExit(main())

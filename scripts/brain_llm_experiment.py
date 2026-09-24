#!/usr/bin/env python3
"""Shared bounded experiment contract for Brain-LLM -> NiakVIO guidance."""
from __future__ import annotations
import hashlib, json
from typing import Any

ROLES=("search","detail","episode","player","source","api","other")
ROUTE_POLICIES={"owned_only","owned_plus_peer","owned_plus_peer_generic"}
RECIPE_POLICIES={"current_only","current_plus_provider","current_plus_provider_peer"}
PUBLIC_KEYS={"routePolicy","recipePolicy","roleOrder","terminalOnly","aliasSearch","responseSalvage","documentRequestMining","sessionBootstrap","maxDepth","maxPages","maxEmbeds","maxRecipePasses"}
RAW_KEYS={"route_policy","recipe_policy","role_order","terminal_only","alias_search","response_salvage","document_request_mining","session_bootstrap","max_depth","max_pages","max_embeds","max_recipe_passes"}
DEFAULTS={
 "provider-owned-origin-header-and-domain-replay":{"route_policy":"owned_plus_peer","recipe_policy":"current_plus_provider","role_order":["api","detail","search","player","source","episode","other"],"session_bootstrap":True,"max_depth":3,"max_pages":14,"max_embeds":12,"max_recipe_passes":3},
 "search-detail-player-terminal-traversal":{"route_policy":"owned_plus_peer","recipe_policy":"current_plus_provider_peer","role_order":["search","detail","episode","player","source","api","other"],"max_depth":5,"max_pages":24,"max_embeds":24,"max_recipe_passes":4},
 "terminal-media-extractor-with-playback-validation":{"route_policy":"owned_plus_peer","recipe_policy":"current_plus_provider_peer","role_order":["player","source","api","episode","detail","other"],"terminal_only":True,"response_salvage":True,"max_depth":5,"max_pages":20,"max_embeds":28,"max_recipe_passes":4},
 "same-provider-candidate-program-replay":{"route_policy":"owned_only","recipe_policy":"current_plus_provider","role_order":["player","api","source","detail","episode","other"],"max_depth":4,"max_pages":18,"max_embeds":24,"max_recipe_passes":4},
 "proven-request-program-and-terminal-extraction":{"route_policy":"owned_only","recipe_policy":"current_plus_provider","role_order":["api","source","player","episode","detail","other"],"terminal_only":True,"response_salvage":True,"max_depth":5,"max_pages":18,"max_embeds":28,"max_recipe_passes":5},
 "discover-api-from-current-page-and-bundles":{"route_policy":"owned_plus_peer_generic","recipe_policy":"current_plus_provider_peer","role_order":["search","api","detail","player","source","episode","other"],"document_request_mining":True,"max_depth":4,"max_pages":28,"max_embeds":20,"max_recipe_passes":4},
}
def _bounded(value:Any,lo:int,hi:int,default:int)->int:
 try:n=int(value)
 except (TypeError,ValueError):n=default
 return max(lo,min(hi,n))
def from_proposal(value:Any,*,strategy:str)->dict[str,Any]:
 src=value if isinstance(value,dict) else {}
 extra=set(src)-RAW_KEYS
 if extra: raise ValueError("unexpected experiment fields: "+",".join(sorted(extra)))
 default=dict(DEFAULTS.get(strategy) or {})
 route=str(src.get("route_policy") or default.get("route_policy") or "owned_only").strip().casefold()
 recipe=str(src.get("recipe_policy") or default.get("recipe_policy") or "current_only").strip().casefold()
 if route not in ROUTE_POLICIES or recipe not in RECIPE_POLICIES: raise ValueError("invalid experiment policy")
 raw_roles=src.get("role_order");raw_roles=raw_roles if isinstance(raw_roles,list) else default.get("role_order") or list(ROLES)
 roles=[]
 for raw in raw_roles:
  role=str(raw or "").strip().casefold()
  if role not in ROLES: raise ValueError("invalid experiment role")
  if role not in roles:roles.append(role)
 if not roles:roles=list(ROLES)
 return {
  "routePolicy":route,"recipePolicy":recipe,"roleOrder":roles[:7],
  "terminalOnly":bool(src.get("terminal_only",default.get("terminal_only",False))),
  "aliasSearch":bool(src.get("alias_search",default.get("alias_search",False))),
  "responseSalvage":bool(src.get("response_salvage",default.get("response_salvage",False))),
  "documentRequestMining":bool(src.get("document_request_mining",default.get("document_request_mining",False))),
  "sessionBootstrap":bool(src.get("session_bootstrap",default.get("session_bootstrap",False))),
  "maxDepth":_bounded(src.get("max_depth",default.get("max_depth")),2,6,4),
  "maxPages":_bounded(src.get("max_pages",default.get("max_pages")),6,36,18),
  "maxEmbeds":_bounded(src.get("max_embeds",default.get("max_embeds")),6,36,20),
  "maxRecipePasses":_bounded(src.get("max_recipe_passes",default.get("max_recipe_passes")),1,6,4),
 }
def fingerprint(experiment:dict[str,Any])->str:
 return hashlib.sha256(json.dumps(experiment,ensure_ascii=True,sort_keys=True,separators=(",",":")).encode("ascii")).hexdigest()
def validate_public(value:Any,expected_fingerprint:str="")->tuple[dict[str,Any],str]:
 if not isinstance(value,dict) or set(value)!=PUBLIC_KEYS: raise ValueError("external experiment shape is not exact")
 route=str(value.get("routePolicy") or "");recipe=str(value.get("recipePolicy") or "")
 if route not in ROUTE_POLICIES or recipe not in RECIPE_POLICIES: raise ValueError("invalid public experiment policy")
 roles=value.get("roleOrder")
 if not isinstance(roles,list) or not roles or len(roles)>7 or len(set(roles))!=len(roles) or any(str(r) not in ROLES for r in roles): raise ValueError("invalid public experiment roles")
 bools=("terminalOnly","aliasSearch","responseSalvage","documentRequestMining","sessionBootstrap")
 if any(not isinstance(value.get(k),bool) for k in bools): raise ValueError("invalid public experiment boolean")
 bounds={"maxDepth":(2,6),"maxPages":(6,36),"maxEmbeds":(6,36),"maxRecipePasses":(1,6)}
 for key,(lo,hi) in bounds.items():
  raw=value.get(key)
  if isinstance(raw,bool) or not isinstance(raw,int) or not lo<=raw<=hi: raise ValueError("invalid public experiment budget")
 clean=dict(value);fp=fingerprint(clean)
 if expected_fingerprint and str(expected_fingerprint).casefold()!=fp: raise ValueError("experiment fingerprint mismatch")
 return clean,fp

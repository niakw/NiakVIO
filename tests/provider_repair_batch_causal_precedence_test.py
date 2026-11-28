#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"build_provider_repair_batch_plan.py"
spec=importlib.util.spec_from_file_location("batch_plan_causal_precedence",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Deepest current proof wins over stale lower-layer issue text.
assert mod.action_for("CHAIN REACHED","chain","network_http_error")[0]=="terminal-extraction"
assert mod.action_for("ROUTE PROVEN","lookup","network_exception")[0]=="route-to-terminal"
assert mod.action_for("CANDIDATE OK","lookup","network_zero_result")[0]=="candidate-replay"

# Final causal network/harness status still owns its lane.
assert mod.action_for("PROVIDER NETWORK BLOCKED","none","network_http_error")[0]=="transport"
assert mod.action_for("HARNESS MISMATCH","lookup","waf_challenge")[0]=="harness-compatibility"
assert mod.action_for("CLIENT TRANSPORT GAP","none","network_exception")[0]=="harness-compatibility"
assert mod.action_for("HARNESS/ENV BLOCKED","none","network_exception")[0]=="harness-compatibility"

# Only proof-less issue fallback may route an otherwise unclassified row.
assert mod.action_for("NO PROOF","none","waf_challenge")[0]=="harness-compatibility"
assert mod.action_for("NO PROOF","none","network_http_error")[0]=="transport"

reclassified={
    "status":"NO PROOF",
    "repairEligible":True,
    "residentialProviderReplayReclassified":True,
    "residentialProviderReplayEvidence":[
        "movie: status=no_streams, stage=provider_zero_before_provider_network, raw=0, playable=0, verified=0, identitySafe=true"
    ],
}
assert mod.action_for_row(reclassified,"none","waf_challenge")[0]=="learning"
assert mod.causal_issue_for_row(reclassified)=="provider_zero_before_provider_network"
not_reclassified={**reclassified,"residentialProviderReplayReclassified":False}
assert mod.action_for_row(not_reclassified,"none","waf_challenge")[0]=="learning"
missing_flag={k:v for k,v in reclassified.items() if k!="residentialProviderReplayReclassified"}
assert mod.action_for_row(missing_flag,"none","waf_challenge")[0]=="learning"
no_replay={**missing_flag,"residentialProviderReplayEvidence":[]}
assert mod.action_for_row(no_replay,"none","waf_challenge")[0]=="learning"
assert mod.causal_issue_for_row(no_replay)=="unknown"
mixed_replay={
    **reclassified,
    "dominantIssue":"waf_challenge",
    "residentialProviderReplayEvidence":[
        "movie: status=no_streams, stage=provider_zero_before_provider_network, raw=0",
        "tv: status=no_streams, stage=provider_network_http_error, raw=0",
    ],
}
assert mod.causal_issue_for_row(mixed_replay)=="waf_challenge"
allwish_like={
    "status":"NO PROOF",
    "repairEligible":True,
    "dominantIssue":"provider_waf_challenge×2",
    "harnessTransportClass":"not-applicable",
    "residentialProviderReplayEvidence":[],
}
assert mod.action_for_row(allwish_like,"none","waf_challenge")[0]=="learning"
network_only={**allwish_like,"dominantIssue":"provider_network_exception"}
assert mod.action_for_row(network_only,"none","network_exception")[0]=="learning"


# Explicit current census causal queues outrank semantic depth. A provider can
# reach CHAIN and still be owned by authority rediscovery; that must not leak
# into provider mutation. Environment ownership is equally explicit.
chain_row={"status":"CHAIN REACHED","repairEligible":False}
assert mod.causal_scope_for_row(
    "authority",chain_row,"chain","network_zero_result",dynamic_debt=None,brain_required=True,
    authority_rediscovery={"authority"},environment_owned=set(),
)[0]=="transport"
assert mod.causal_scope_for_row(
    "environment",chain_row,"chain","waf_challenge",dynamic_debt=None,brain_required=True,
    authority_rediscovery=set(),environment_owned={"environment"},
)[0]=="harness-compatibility"
assert mod.causal_scope_for_row(
    "repair",{"status":"PROVIDER JS BROKEN","repairEligible":True},"none","provider_returned_wrong_content",
    dynamic_debt=None,brain_required=True,authority_rediscovery=set(),environment_owned=set(),
)[0]=="learning"
assert mod.causal_scope_for_row(
    "green",{"status":"FULL OK","repairEligible":False},"chain","none",dynamic_debt={"missing":1},brain_required=False,
    authority_rediscovery=set(),environment_owned=set(),
)[0]=="variant-coverage"

source=SCRIPT.read_text(encoding="utf-8")
assert "Final causal status is stronger than an older dominantIssue" in source
assert "residential full-provider replay disproved transport ownership" in source
assert "issue-only WAF/network text cannot recreate harness or transport ownership" in source
assert "authorityRediscoveryQueue" in source
assert "causal queue overlap authority/environment" in source
print("provider repair batch causal precedence contract passed")

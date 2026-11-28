#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/build_provider_repair_batch_plan.py"

status={
  "runId":123,
  "triggerSha":"abc",
  "authorityRediscoveryQueue":["e"],
  "providers":[
    {"provider":"a","status":"CHAIN REACHED","brainCheckRequired":True,"declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_zero_result","evidenceDepth":["movie=chain_reached"]},
    {"provider":"b","status":"CHAIN REACHED","brainCheckRequired":True,"declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_zero_result","evidenceDepth":["movie=chain_reached"]},
    {"provider":"c","status":"HARNESS/ENV BLOCKED","brainCheckRequired":True,"declaredLanes":["anime"],"currentVerifiedLanes":[],"dominantIssue":"provider_waf_challenge","evidenceDepth":["anime=none"],"harnessTransportClass":"residential-exit-all-challenged"},
    {"provider":"d","status":"HARNESS MISMATCH","brainCheckRequired":True,"declaredLanes":["anime"],"currentVerifiedLanes":[],"dominantIssue":"provider_waf_challenge","evidenceDepth":["anime=lookup_only"],"harnessTransportClass":"browser-profile-only"},
    {"provider":"e","status":"PROVIDER NETWORK BLOCKED","brainCheckRequired":True,"declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_http_error","evidenceDepth":["movie=lookup_only"]},
    {"provider":"f","status":"PROVIDER NETWORK BLOCKED","brainCheckRequired":True,"declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_exception","evidenceDepth":["movie=none"]},
    {"provider":"green","status":"FULL OK","brainCheckRequired":False,"declaredLanes":["movie"],"currentVerifiedLanes":["movie"],"dominantIssue":"","evidenceDepth":[]},
    {"provider":"carry","status":"FULL OK","brainCheckRequired":False,"declaredLanes":["movie"],"currentVerifiedLanes":["movie"],"dominantIssue":"","evidenceDepth":[]},
    {"provider":"cleared","status":"FULL OK","brainCheckRequired":False,"declaredLanes":["movie"],"currentVerifiedLanes":["movie"],"dominantIssue":"","evidenceDepth":[]},
  ]
}
sharded={
  "rows":[
    {"provider_id":"green","semantic_type":"movie","streams_returned":3,"announced_variant_candidates":20,"announced_quality_heights":[480,720,1080,2160],"variant_fanout_state":"returned-subset"},
    {"provider_id":"cleared","semantic_type":"movie","streams_returned":4,"announced_variant_candidates":1,"announced_quality_heights":[1080],"variant_fanout_state":"fanout-observed"},
  ]
}
fallback={
  "rows":[
    {"provider_id":"carry","semantic_type":"movie","streams_returned":1,"announced_variant_candidates":8,"announced_quality_heights":[480,720,1080],"variant_fanout_state":"returned-subset"},
    {"provider_id":"cleared","semantic_type":"movie","streams_returned":1,"announced_variant_candidates":6,"announced_quality_heights":[480,720,1080],"variant_fanout_state":"returned-subset"},
  ]
}
overrides={
  "provider_patches":{
    "a":{"source_runtime_family":"catalogue-html-embed"},
    "b":{"source_runtime_family":"catalogue-html-embed"},
    "c":{"source_runtime_family":"dle-html"},
    "d":{"source_runtime_family":"dle-html"},
    "e":{"source_runtime_family":"site-html"},
    "f":{"source_runtime_family":"alternate-html"},
  },
  "provider_capabilities":{
    "a":{"strategy":"html_scraper"},
    "b":{"strategy":"html_scraper"},
    "c":{"strategy":"html_scraper"},
    "d":{"strategy":"html_scraper"},
    "e":{"strategy":"html_scraper"},
    "f":{"strategy":"html_scraper"},
  }
}
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    sp=td/"status.json"; cp=td/"sharded.json"; fp=td/"fallback.json"; op=td/"overrides.json"; out=td/"plan.json"
    sp.write_text(json.dumps(status),encoding="utf-8")
    cp.write_text(json.dumps(sharded),encoding="utf-8")
    fp.write_text(json.dumps(fallback),encoding="utf-8")
    op.write_text(json.dumps(overrides),encoding="utf-8")
    subprocess.run([
        "python",str(script),
        "--status",str(sp),
        "--sharded-census",str(cp),
        "--fallback-sharded-census",str(fp),
        "--overrides",str(op),
        "--output",str(out),
    ],check=True)
    plan=json.loads(out.read_text(encoding="utf-8"))

assert plan["unresolvedProviderCount"]==8
assert plan["dynamicVariantProviderCount"]==2
assert plan["dynamicVariantProviders"]==["carry","green"]
assert plan["dynamicVariantCurrentObservedProviders"]==["cleared","green"]
assert plan["dynamicVariantFallbackUsed"] is True
assert plan["groupCount"]==6
groups={row["repairScope"]:row for row in plan["groups"] if row["repairScope"]!="harness-compatibility"}
harness={row["transportSignature"]:row for row in plan["groups"] if row["repairScope"]=="harness-compatibility"}
assert groups["terminal-extraction"]["providers"]==["a","b"]
assert groups["terminal-extraction"]["runtimeFamilySignature"]=="catalogue-html-embed"
assert groups["terminal-extraction"]["providerLocalFallback"]=="only-after-shared-profile-failure"
assert harness["residential-exit-all-challenged"]["providers"]==["c"]
assert harness["browser-profile-only"]["providers"]==["d"]
assert harness["residential-exit-all-challenged"]["harnessTransportClasses"]==["residential-exit-all-challenged"]
assert harness["browser-profile-only"]["harnessTransportClasses"]==["browser-profile-only"]
transport=[row for row in plan["groups"] if row["repairScope"]=="transport"]
assert {row["runtimeFamilySignature"]:row["providers"] for row in transport}=={
    "site-html":["e"], "alternate-html":["f"]
}
assert {row["runtimeFamilySignature"] for row in transport}=={"site-html","alternate-html"}
assert all(row["transportSignature"]=="not-applicable" for row in transport)
assert sorted({depth for row in transport for depth in row["evidenceDepths"]})==["lookup","none"]
assert sorted({issue for row in transport for issue in row["dominantIssues"]})==["network_exception","network_http_error"]
assert groups["variant-coverage"]["providers"]==["carry","green"]
assert groups["variant-coverage"]["dynamicVariantProviders"]==["carry","green"]
assert "cleared" not in plan["dynamicVariantProviders"]
assert groups["variant-coverage"]["selectionAuthorities"]==["provider-census-sharded-latest.json:dynamic-variant-debt"]
print("Provider repair batch plan grouping passed")


# Regression: old completeness evidence must not reintroduce a provider whose
# current lifecycle is DISABLED, including contradictory stale Brain flags.
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    sp=td/"status.json"; cp=td/"sharded.json"; fp=td/"fallback.json"; op=td/"overrides.json"; out=td/"plan.json"
    off_status={"runId":124,"triggerSha":"def","lifecycleDisabledQueue":["ledger-off"],"providers":[
        {"provider":"status-off","status":"DISABLED","brainCheckRequired":True},
        {"provider":"ledger-off","status":"FULL OK","brainCheckRequired":True},
        {"provider":"still-live","status":"FULL OK","brainCheckRequired":False},
    ]}
    def variant(pid):
        return {"provider_id":pid,"semantic_type":"movie","streams_returned":1,"announced_variant_candidates":4,"variant_fanout_state":"returned-subset"}
    sp.write_text(json.dumps(off_status)); cp.write_text(json.dumps({"rows":[variant("status-off"),variant("still-live")]}))
    fp.write_text(json.dumps({"rows":[variant("ledger-off")]})); op.write_text("{}")
    subprocess.run(["python",str(script),"--status",str(sp),"--sharded-census",str(cp),"--fallback-sharded-census",str(fp),"--overrides",str(op),"--output",str(out)],check=True)
    result=json.loads(out.read_text())
    assert result["dynamicVariantProviders"]==["still-live"],result
    assert result["lifecycleSuppressedDynamicProviders"]==["ledger-off","status-off"],result
    assert result["unresolvedProviderCount"]==1,result
    assert result["groups"][0]["providers"]==["still-live"],result
print("Disabled lifecycle overrides retained variant debt")


# Causal family identity must include issue/depth, not only runtime topology.
# Otherwise zero-result, timeout and different evidence frontiers collapse into
# one oracle and unrelated siblings are incorrectly deferred.
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    sp=td/"status.json"; cp=td/"sharded.json"; op=td/"overrides.json"; out=td/"plan.json"
    causal_status={
      "runId":125,
      "triggerSha":"ghi",
      "providers":[
        {"provider":"zero-lookup","status":"NO PROOF","brainCheckRequired":True,"repairEligible":True,
         "declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_zero_result",
         "evidenceDepth":["movie=lookup_only"]},
        {"provider":"timeout-lookup","status":"NO PROOF","brainCheckRequired":True,"repairEligible":True,
         "declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"timeout",
         "evidenceDepth":["movie=lookup_only"]},
        {"provider":"zero-chain","status":"NO PROOF","brainCheckRequired":True,"repairEligible":True,
         "declaredLanes":["movie"],"currentVerifiedLanes":[],"dominantIssue":"provider_network_zero_result",
         "evidenceDepth":["movie=chain_reached"]},
      ],
    }
    causal_overrides={
      "provider_patches":{
        provider:{"source_runtime_family":"mixed-embed-family"}
        for provider in ("zero-lookup","timeout-lookup","zero-chain")
      },
      "provider_capabilities":{
        provider:{"strategy":"mixed_embed_resolver"}
        for provider in ("zero-lookup","timeout-lookup","zero-chain")
      },
    }
    sp.write_text(json.dumps(causal_status)); cp.write_text('{"rows":[]}'); op.write_text(json.dumps(causal_overrides))
    subprocess.run([
        "python",str(script),"--status",str(sp),"--sharded-census",str(cp),
        "--overrides",str(op),"--output",str(out)
    ],check=True)
    causal_plan=json.loads(out.read_text())
    assert causal_plan["groupCount"]==3,causal_plan
    by_provider={row["providers"][0]:row for row in causal_plan["groups"]}
    assert by_provider["zero-lookup"]["causalIssueSignature"]=="network_zero_result",by_provider
    assert by_provider["zero-lookup"]["evidenceDepthSignature"]=="lookup",by_provider
    assert by_provider["timeout-lookup"]["causalIssueSignature"]=="timeout",by_provider
    assert by_provider["timeout-lookup"]["evidenceDepthSignature"]=="lookup",by_provider
    assert by_provider["zero-chain"]["causalIssueSignature"]=="network_zero_result",by_provider
    assert by_provider["zero-chain"]["evidenceDepthSignature"]=="chain",by_provider
    assert all("runtime:mixed-embed-family" in row["groupId"] for row in causal_plan["groups"])
    assert len({row["groupId"] for row in causal_plan["groups"]})==3
print("Provider causal family signature split passed")

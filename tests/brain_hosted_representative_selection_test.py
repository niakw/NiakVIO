#!/usr/bin/env python3
"""Representative is selected by current repair eligibility and retained negative proof."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

root=Path(__file__).resolve().parents[1]
path=root/"scripts/select_brain_hosted_representative.py"
spec=importlib.util.spec_from_file_location("brain_representative",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
rows=[
    {"provider":"allanime","status":"CHAIN REACHED",
     "repairEligible":True,"authorityRepairEligible":True,
     "dominantIssue":"provider_network_zero_result"},
    {"provider":"animevostfr","status":"CANDIDATE OK",
     "repairEligible":True,"authorityRepairEligible":True,
     "historicalProof":["anime:Jujutsu"],"candidateProof":["anime:playable"],
     "dominantIssue":"provider_network_zero_result"},
    {"provider":"animekai","status":"REGRESSION PROVIDER",
     "repairEligible":True,"authorityRepairEligible":True,
     "dominantIssue":"provider_network_exception"},
    {"provider":"waf","status":"ROUTE PROVEN",
     "repairEligible":True,"authorityRepairEligible":True,
     "dominantIssue":"provider_waf_challenge"},
    {"provider":"disabled","status":"DISABLED",
     "repairEligible":False,"authorityRepairEligible":False},
]
state={"providers":rows,"repairQueue":["allanime","animevostfr","animekai","waf"]}
with TemporaryDirectory() as td:
    base=Path(td)
    for idx in range(2):
        (base/(str(42328950352+idx)+".json")).write_text(json.dumps({
            "provider":"allanime","publicationAuthority":False,
            "acceptedProviderCount":0,
            "scopeTrace":[{"scope":"provider_bloc","reason":"no_op"}]}))
    (base/"not-an-archive.json").write_text("{}")
    debt=mod.negative_history(base)
    assert debt["allanime"]==60
    assert mod.choose(state,debt)[0]=="animevostfr"
    assert mod.choose(state,debt,"animekai")[0]=="animekai"
    try:mod.choose(state,debt,"not-a-provider")
    except ValueError:pass
    else:raise AssertionError("invented manual provider accepted")
    try:mod.choose(state,debt,"disabled")
    except ValueError:pass
    else:raise AssertionError("disabled provider accepted")
    try:mod.choose({"providers":rows,"repairQueue":["disabled"]},debt)
    except ValueError:pass
    else:raise AssertionError("ineligible target accepted")
print("BRAIN_REPRESENTATIVE_SELECTION_OK current authority, negative history and no provider writes")

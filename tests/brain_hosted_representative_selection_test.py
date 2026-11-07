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
    assert debt["allanime"]==200
    # The strongest retained CANDIDATE has a replay-only Brain strategy and
    # must NOT be scored as source synthesis: choose eligible regression.
    assert mod.choose(state,debt)[0]=="animekai"
    # One historical regression no-op now causes a representative rotation;
    # the old 30-point penalty still selected the same high-scoring target.
    (base/"42351400247.json").write_text(json.dumps({
        "provider":"uhdmovies","publicationAuthority":False,
        "acceptedProviderCount":0,
        "scopeTrace":[{"scope":"provider_bloc","reason":"no_op"}]}))
    state["providers"].append({
        "provider":"uhdmovies","status":"REGRESSION PROVIDER",
        "repairEligible":True,"authorityRepairEligible":True,
        "historicalProof":["movie:Interstellar"],
        "dominantIssue":"provider_network_zero_result",
    })
    state["repairQueue"].append("uhdmovies")
    debt=mod.negative_history(base)
    assert debt["uhdmovies"]==100
    assert mod.choose(state,debt)[0]=="animekai"
    # A single high score is not authority to consume another unchanged
    # synthesis run; manual targeting still remains explicit/operator-owned.
    assert mod.choose(state,debt,"uhdmovies")[0]=="uhdmovies"
    try:mod.choose(state,debt,"animevostfr")
    except ValueError as error:
        assert "Candidate replay" in str(error)
    else:raise AssertionError("replay-only candidate sent to mutation pipeline")
    assert mod.choose(state,debt,"animekai")[0]=="animekai"
    # Historical candidate data changes failure classification regardless of
    # superficial status; the Brain adapter always selects replay first.
    enriched=dict(rows[2],candidateProof=["a verified sandbox candidate"])
    state["providers"][2]=enriched
    # The replay-only regression is excluded; the next available genuine
    # regression has no replay flag and still outranks exhausted AllAnime.
    assert mod.choose(state,debt)[0]=="uhdmovies"
    state["providers"][2]=rows[2]
    try:mod.choose(state,debt,"waf")
    except ValueError:
        raise AssertionError("known but WAF target is allowed by policy; scorer should downrank")

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

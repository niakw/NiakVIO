#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from brain_layers.declarative_gap_strategy import synthesize_rows

census={
    "repairQueue":["alpha","beta","gamma","delta","epsilon","zeta"],
    "providers":[
        {"provider":"alpha","status":"CHAIN REACHED","dominantIssue":"provider_network_zero_result","evidenceDepth":["movie=chain_reached"]},
        {"provider":"beta","status":"NO PROOF","dominantIssue":"provider_waf_challenge","evidenceDepth":["movie=none"]},
        {"provider":"gamma","status":"CANDIDATE OK","dominantIssue":"provider_network_zero_result","evidenceDepth":["anime=lookup_only"]},
        {"provider":"delta","status":"REGRESSION PROVIDER","dominantIssue":"provider_network_exception","evidenceDepth":["anime=none"]},
        {"provider":"epsilon","status":"REGRESSION PROVIDER","dominantIssue":"provider_network_http_error×2","evidenceDepth":["movie=none","tv=none"]},
        {"provider":"zeta","status":"REGRESSION PROVIDER","dominantIssue":"timeout","evidenceDepth":["anime=none"]},
    ],
}
first=synthesize_rows(census=census,memory={"entries":[]},current_sha="a"*40)
assert [r["providerId"] for r in first]==["alpha","beta","delta","epsilon","gamma","zeta"]
assert {r["failureClass"] for r in first}=={"chain_terminal_gap","provider_transport_gap","candidate_replay_gap"}
assert next(r for r in first if r["providerId"]=="delta")["failureClass"]=="provider_transport_gap"
assert next(r for r in first if r["providerId"]=="epsilon")["failureClass"]=="provider_transport_gap"
assert next(r for r in first if r["providerId"]=="zeta")["failureClass"]=="provider_transport_gap"
assert all(r["guidanceKind"]=="meta-gap-synthesis" for r in first)
assert all(len(r["experimentFingerprint"])==64 for r in first)
failed={"entries":[{
    "providerId":"alpha",
    "profile":first[0]["profile"],
    "llmAdvisorExperimentFingerprint":first[0]["experimentFingerprint"],
    "consecutiveFailures":1,
}]}
second=synthesize_rows(census=census,memory=failed,current_sha="a"*40)
alpha=next(r for r in second if r["providerId"]=="alpha")
assert alpha["experimentFingerprint"] != first[0]["experimentFingerprint"]

# Three distinct executed attempts of one executor are enough. Learning must
# rotate executor family instead of inventing a fourth parameter permutation
# of the same profile.
alpha_first=next(r for r in first if r["providerId"]=="alpha")
bounded_memory={"entries":[
    {
        "providerId":"alpha",
        "failureClass":alpha_first["failureClass"],
        "profile":alpha_first["profile"],
        "llmAdvisorExperimentFingerprint":str(i)*64,
        "consecutiveFailures":1,
        "failures":1,
        "successes":0,
        "executionObserved":True,
    }
    for i in (1,2,3)
]}
rotated=synthesize_rows(census=census,memory=bounded_memory,current_sha="a"*40)
alpha_rotated=next(r for r in rotated if r["providerId"]=="alpha")
assert alpha_rotated["profile"] != alpha_first["profile"], (alpha_first,alpha_rotated)
assert alpha_rotated["profile"]=="player_media_extractor_v1",alpha_rotated
print("Brain declarative meta-gap strategy tests passed")

# Runtime integration is covered separately; this generator remains pure.

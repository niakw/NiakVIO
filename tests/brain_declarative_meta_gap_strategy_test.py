#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from brain_layers.declarative_gap_strategy import synthesize_rows

census={
    "repairQueue":["alpha","beta","gamma"],
    "providers":[
        {"provider":"alpha","status":"CHAIN REACHED","dominantIssue":"provider_network_zero_result","evidenceDepth":["movie=chain_reached"]},
        {"provider":"beta","status":"NO PROOF","dominantIssue":"provider_waf_challenge","evidenceDepth":["movie=none"]},
        {"provider":"gamma","status":"CANDIDATE OK","dominantIssue":"provider_network_zero_result","evidenceDepth":["anime=lookup_only"]},
    ],
}
first=synthesize_rows(census=census,memory={"entries":[]},current_sha="a"*40)
assert [r["providerId"] for r in first]==["alpha","beta","gamma"]
assert {r["failureClass"] for r in first}=={"chain_terminal_gap","provider_transport_gap","candidate_replay_gap"}
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
print("Brain declarative meta-gap strategy tests passed")

# Runtime integration is covered separately; this generator remains pure.

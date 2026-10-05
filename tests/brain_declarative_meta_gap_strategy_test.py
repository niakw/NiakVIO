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

# Causal-class drift must not reset an already-executed executor family. This is
# the representative Moviebox shape: census says route_proven_gap while current
# sandbox evidence says transport_blocked. Three executed proven-route attempts
# under the sibling class must make route_proven synthesis rotate to search
# contract inference instead of replaying proven-route again.
route_census={
    "repairQueue":["moviebox-like"],
    "providers":[{
        "provider":"moviebox-like",
        "status":"ROUTE PROVEN",
        "dominantIssue":"provider_network_zero_result",
        "evidenceDepth":["movie=route_proven","tv=route_proven"],
    }],
}
route_memory={"entries":[
    {
        "providerId":"moviebox-like",
        "failureClass":"transport_blocked",
        "profile":"proven_route_terminal_traversal_v1",
        "llmAdvisorExperimentFingerprint":str(i)*64,
        "executionObserved":True,
        "consecutiveFailures":1,
        "failures":1,
        "progresses":1,
        "successes":0,
    }
    for i in (1,2,3)
]}
route_rotated=synthesize_rows(census=route_census,memory=route_memory,current_sha="a"*40)
route_row=next(r for r in route_rotated if r["providerId"]=="moviebox-like")
assert route_row["failureClass"]=="route_proven_gap",route_row
assert route_row["profile"]=="search_contract_inference_v1",route_row

# The same family semantics apply to terminal/media class drift.
terminal_census={
    "repairQueue":["terminal-like"],
    "providers":[{
        "provider":"terminal-like",
        "status":"CHAIN REACHED",
        "dominantIssue":"provider_network_zero_result",
        "evidenceDepth":["movie=chain_reached"],
    }],
}
terminal_memory={"entries":[
    {
        "providerId":"terminal-like",
        "failureClass":"media_extraction_gap",
        "profile":"chain_terminal_extractor_v1",
        "llmAdvisorExperimentFingerprint":str(i)*64,
        "executionObserved":True,
        "consecutiveFailures":1,
        "failures":1,
        "successes":0,
    }
    for i in (4,5,6)
]}
terminal_rotated=synthesize_rows(census=terminal_census,memory=terminal_memory,current_sha="a"*40)
terminal_row=next(r for r in terminal_rotated if r["providerId"]=="terminal-like")
assert terminal_row["failureClass"]=="chain_terminal_gap",terminal_row
assert terminal_row["profile"]=="player_media_extractor_v1",terminal_row

# Executed Repair diagnosis outranks a coarse census lifecycle floor. This
# models AnimeVost-FR: census still says ROUTE PROVEN while current Repair has
# repeatedly executed terminal-media variant coverage attempts.
repair_specific_census={
    "repairQueue":["omega"],
    "providers":[{
        "provider":"omega",
        "status":"ROUTE PROVEN",
        "dominantIssue":"provider_network_zero_result",
        "evidenceDepth":["anime=route_proven"],
    }],
}
repair_specific_memory={"entries":[
    {
        "providerId":"omega",
        "failureClass":"variant_coverage_gap",
        "profile":"player_media_extractor_v1",
        "llmAdvisorExperimentFingerprint":str(i)*64,
        "experimentVariant":4,
        "experimentGeneration":2,
        "failures":1,
        "consecutiveFailures":1,
        "progresses":1,
        "successes":0,
        "executionObserved":True,
    }
    for i in (1,2,3)
]}
repair_specific=synthesize_rows(
    census=repair_specific_census,
    memory=repair_specific_memory,
    current_sha="a"*40,
)
omega=next(r for r in repair_specific if r["providerId"]=="omega")
assert omega["failureClass"]=="variant_coverage_gap",omega
assert omega["profile"]=="chain_terminal_extractor_v1",omega

# A non-executed hypothesis cannot override the census floor.
repair_specific_memory["entries"][0]["executionObserved"]=False
repair_specific_memory["entries"]=repair_specific_memory["entries"][:1]
nonexecuted=synthesize_rows(
    census=repair_specific_census,
    memory=repair_specific_memory,
    current_sha="a"*40,
)
omega_nonexecuted=next(r for r in nonexecuted if r["providerId"]=="omega")
assert omega_nonexecuted["failureClass"]=="route_proven_gap",omega_nonexecuted

print("Brain declarative meta-gap strategy tests passed")

# Runtime integration is covered separately; this generator remains pure.

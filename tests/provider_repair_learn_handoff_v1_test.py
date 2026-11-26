#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_repair_learn_handoff_v1.py"
spec = importlib.util.spec_from_file_location("handoff", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = {
    "schemaVersion": 1,
    "providers": {
        "old-red": {"owner": "LEARN", "status": "pending", "reason": "target-not-verified", "repairObservations": 2},
        "resolved-now": {"owner": "LEARN", "status": "pending", "reason": "target-not-verified", "repairObservations": 1},
    },
}
summary = {
    "targetedProviders": ["NEW_RED", "resolved-now", "PARTIAL_GREEN"],
    "verifiedProviders": ["resolved-now", "PARTIAL_GREEN"],
    "lostUpstreamPositivePairs": [["NEW_RED", "movie"], ["NEW_RED", "tv"], ["PARTIAL_GREEN", "tv"]],
    "maxAttemptsPerTask": 3,
}
merged = module.merge_summary(base, summary, run_id="12345")
assert set(merged["providers"]) == {"new-red", "old-red", "partial-green"}, merged
row = merged["providers"]["new-red"]
assert row["reason"] == "lost-upstream-positive" and row["mediaTypes"] == ["movie", "tv"]
partial = merged["providers"]["partial-green"]
assert partial["reason"] == "lost-upstream-positive" and partial["mediaTypes"] == ["tv"]
assert merged["providers"].get("resolved-now") is None
assert row["lastRepairRunId"] == "12345" and row["publicationAllowed"] is False
serialized = json.dumps(merged).casefold()
for forbidden in ("http://", "https://", "authorization", "cookie", "requestbody"):
    assert forbidden not in serialized
with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "handoff.json"
    module.write(path, merged)
    assert module.load(path)["providerCount"] == 3


fast_summary = {
    "selectedProviders": ["EXHAUSTED", "remaining-one", "fixed-now"],
    "validatedProviders": ["fixed-now"],
    "brainDeferredLearningProviders": ["EXHAUSTED"],
    "brainRemainingProviders": ["remaining-one"],
    "learnHandoffProviders": ["EXHAUSTED", "remaining-one"],
}
fast = module.merge_summary({"schemaVersion":1,"providers":{}}, fast_summary, run_id="777")
assert set(fast["providers"]) == {"exhausted", "remaining-one"}, fast


# Fast Repair schema v2 may intentionally leave family siblings unvisited. The
# explicit handoff list is therefore authoritative even when brainRemaining
# still contains those siblings.
frontier_summary={
    "selectedProviders":["exhausted","sibling-unvisited"],
    "validatedProviders":[],
    "brainDeferredLearningProviders":["exhausted"],
    "brainRemainingProviders":["exhausted","sibling-unvisited"],
    "learnHandoffProviders":["exhausted"],
}
frontier=module.merge_summary({"schemaVersion":1,"providers":{}},frontier_summary,run_id="778")
assert set(frontier["providers"])=={"exhausted"},frontier
assert frontier["providers"]["exhausted"]["reason"]=="brain-strategy-exhausted",frontier
assert fast["providers"]["exhausted"]["reason"] == "brain-strategy-exhausted", fast
assert fast["providers"]["remaining-one"]["reason"] == "brain-unresolved", fast
assert "fixed-now" not in fast["providers"], fast
assert fast["providers"]["exhausted"]["sourceLane"] == "FAST_REPAIR"

remat_summary = {
    "selectedProviders": ["FRENCH_MANGA", "strict-now", "no-candidate-proof"],
    "statusesAfterRemat": {
        "french-manga": "CANDIDATE OK",
        "strict-now": "FULL OK",
        "no-candidate-proof": "CANDIDATE OK",
    },
    "candidateReplayProvenance": {
        "french-manga": {
            "currentDataRematerialized": True,
            "historicalBrainProgramReplayed": False,
            "currentStrictRetestVerified": False,
            "nextRequiredAction": "locate_exact_candidate_program_or_reconstruct_via_Brain",
        },
        "strict-now": {
            "currentDataRematerialized": True,
            "historicalBrainProgramReplayed": True,
            "currentStrictRetestVerified": True,
            "nextRequiredAction": "",
        },
        "no-candidate-proof": {
            "currentDataRematerialized": True,
            "historicalBrainProgramReplayed": False,
            "currentStrictRetestVerified": False,
            "nextRequiredAction": "stay_in_remat",
        },
    },
    "publicationAllowed": False,
}
remat_base = {
    "schemaVersion": 1,
    "providers": {
        "strict-now": {"owner": "LEARN", "status": "pending", "reason": "old"},
        "no-candidate-proof": {"owner": "LEARN", "status": "pending", "reason": "keep-owner"},
    },
}
remat = module.merge_summary(remat_base, remat_summary, run_id="45908491517")
assert "strict-now" not in remat["providers"], remat
assert remat["providers"]["french-manga"]["reason"] == "remat-candidate-unverified", remat
assert remat["providers"]["french-manga"]["sourceLane"] == "REMAT_TEST", remat
assert remat["providers"]["french-manga"]["publicationAllowed"] is False
assert remat["providers"]["no-candidate-proof"]["reason"] == "keep-owner", remat
serialized_remat = json.dumps(remat).casefold()
for forbidden in ("http://", "https://", "authorization", "cookie", "requestbody",
                  "historicalcandidateproof", "executableprogramprovenance"):
    assert forbidden not in serialized_remat, forbidden

workflow = (ROOT / ".github/workflows/provider-repair-learn-handoff.yml").read_text(encoding="utf-8")
assert '"PROVIDERS - Remat Test"' in workflow
assert "provider-remat-test-latest.json" in workflow
assert "pattern: provider-*-" in workflow and "github.event.workflow_run.id" in workflow

print("provider repair/remat -> LEARN lane-aware handoff tests passed")

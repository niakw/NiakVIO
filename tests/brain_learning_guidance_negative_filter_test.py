#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"filter_brain_learning_guidance.py"
spec=importlib.util.spec_from_file_location("learning_guidance_filter",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

dead="16ad894fc3c03be89539c14fb749def9501831b455f58f6f6f475b20acd36ad6"
live="a"*64
payload={
    "schemaVersion":2,
    "sourceSha":"1"*40,
    "brainLlmSha":"2"*40,
    "publicationAuthority":False,
    "directMutationAuthority":False,
    "proofAuthority":False,
    "rawMutationContentRetained":False,
    "providerCount":2,
    "rows":[
        {
            "providerId":"moviebox",
            "failureClass":"route-proven-gap",
            "targetLayer":"provider",
            "strategy":"search-detail-player-terminal-traversal",
            "profile":"proven_route_terminal_traversal_v1",
            "confidence":0.96,
            "priorOnly":True,
            "experiment":{},
            "experimentFingerprint":dead,
        },
        {
            "providerId":"vidfast",
            "failureClass":"route-proven-gap",
            "targetLayer":"provider",
            "strategy":"discover-api-from-current-page-and-bundles",
            "profile":"search_contract_inference_v1",
            "confidence":0.96,
            "priorOnly":True,
            "experiment":{},
            "experimentFingerprint":live,
        },
    ],
}
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    memory=tmp/"repair-memory.json"
    memory.write_text(json.dumps({
        "entries":[{
            "providerId":"moviebox",
            "profile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":dead,
            "consecutiveFailures":1,
            "failures":1,
            "executionObserved":True,
            "lastOutcome":"rejected",
            "lastReason":"introduced_runtime_error",
        }]
    }),encoding="utf-8")
    filtered,dropped=mod.filter_guidance(payload,[memory])

assert dropped==1,(filtered,dropped)
assert filtered["providerCount"]==1,filtered
assert [r["providerId"] for r in filtered["rows"]]==["vidfast"],filtered
assert filtered["rows"][0]["experimentFingerprint"]==live

# Non-executed/unavailable attempts are not exact negative execution proof and
# must not poison a future executable hypothesis.
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    memory=tmp/"repair-memory.json"
    memory.write_text(json.dumps({
        "entries":[{
            "providerId":"moviebox",
            "profile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":dead,
            # Older memory debited unavailable profiles as failures even
            # though the matching strategy never produced a candidate.
            "consecutiveFailures":4,
            "failures":4,
            "executionObserved":False,
            "lastOutcome":"profile_unavailable",
        }]
    }),encoding="utf-8")
    filtered,dropped=mod.filter_guidance(payload,[memory])
assert dropped==0,(filtered,dropped)
assert filtered["providerCount"]==2,filtered

# Legacy unavailable rows may predate the explicit execution flag. They are
# applicability evidence, and must not blacklist an executable advisor prior.
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    memory=tmp/"repair-memory.json"
    memory.write_text(json.dumps({
        "entries":[{
            "providerId":"moviebox",
            "profile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":dead,
            "consecutiveFailures":2,
            "lastOutcome":"profile_unavailable",
            "lastReason":"planned_profile_not_applicable_to_current_bytes",
        }]
    }),encoding="utf-8")
    filtered,dropped=mod.filter_guidance(payload,[memory])
assert dropped==0,(filtered,dropped)
assert filtered["providerCount"]==2,filtered

# The outer wave scheduler must agree with the import filter. Otherwise an
# imported hypothesis can still be called exhausted without ever executing.
runner_spec=importlib.util.spec_from_file_location(
    "learning_guidance_runner",ROOT/"scripts"/"run_provider_brain_repair.py"
)
assert runner_spec and runner_spec.loader
runner=importlib.util.module_from_spec(runner_spec)
runner_spec.loader.exec_module(runner)
cases=[
    ({"executionObserved":False,"lastOutcome":"profile_unavailable","consecutiveFailures":4},False),
    ({"executionObserved":False,"lastOutcome":"rejected","consecutiveFailures":4},False),
    ({"lastOutcome":"profile_unavailable","consecutiveFailures":2},False),
    ({"lastOutcome":" PROFILE-UNAVAILABLE ","consecutiveFailures":2},False),
    ({"lastOutcome":"not_generated","consecutiveFailures":2},False),
    ({"lastOutcome":"rejected","consecutiveFailures":"invalid"},False),
    ({"executionObserved":True,"lastOutcome":"rejected","consecutiveFailures":1},True),
    ({"lastOutcome":"rejected","consecutiveFailures":1},True),
    ({"executionObserved":True,"lastOutcome":"accepted","consecutiveFailures":0,"successes":1},False),
    ({"executionObserved":True,"lastOutcome":"accepted","consecutiveFailures":1,"successes":1},False),
]
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    memory=tmp/"repair-memory.json"
    guidance=tmp/"guidance.json"
    original_memory=runner.REPAIR_MEMORY
    runner.REPAIR_MEMORY=memory
    try:
        for evidence,failed in cases:
            memory.write_text(json.dumps({"entries":[{
                "providerId":"moviebox",
                "profile":"proven_route_terminal_traversal_v1",
                "llmAdvisorExperimentFingerprint":dead,
                **evidence,
            }]}),encoding="utf-8")
            filtered,dropped=mod.filter_guidance(payload,[memory])
            assert dropped==int(failed),(evidence,filtered,dropped)
            # Check the same raw guidance too: scheduler correctness must not
            # depend on an earlier import having hidden the erroneous debt.
            guidance.write_text(json.dumps(payload),encoding="utf-8")
            pending=runner.untried_advisor_fingerprints(["moviebox"],guidance)
            assert bool(pending.get("moviebox")) is not failed,(evidence,pending)
            guidance.write_text(json.dumps(filtered),encoding="utf-8")
            imported_pending=runner.untried_advisor_fingerprints(["moviebox"],guidance)
            assert imported_pending==pending,(evidence,imported_pending,pending)
    finally:
        runner.REPAIR_MEMORY=original_memory

print("Brain Learning negative-guidance filter contract passed")

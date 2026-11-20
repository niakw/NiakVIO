#!/usr/bin/env python3
"""No legacy Repair or artificial success for a native-attested novel source family."""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/run_brain_learning_queue.py"
spec=importlib.util.spec_from_file_location("queue_source_family",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

provider="sample"
state={"attemptCount":11,"lastStatus":"unresolved",
       "fixtureCursor":{"anime":2}}
info={"provider":provider,"status":"no_streams",
      "server_accessible":True}
queue={"pendingProviders":["sample","sibling","sample"],
       "completedInCycle":["other"],"sourceContractFamilyDeferredProviders":["sample"],
       "sourceContractFamilyExecutableStatus":"new_family_required"}
row=mod.defer_new_source_contract_family(provider,state,info,queue)
assert row["provider"]==provider
assert row["sourceContractFamilyStatus"]=="new_family_required"
assert row["independentSourceEvidenceNotNativePlayback"] is True
assert row["coreHypothesis"] is info
assert row["resolved"] is False
assert row["attempts"]==[]
assert row["finalLab"] is None
assert row["routeSearch"] is None
assert state["lastStatus"]=="new_source_family_executable_required"
assert state["attemptCount"]==11  # no old executor was invoked
assert state["fixtureCursor"]=={"anime":2}  # no fake Lab playback
assert queue["pendingProviders"]==["sibling"]
assert queue["completedInCycle"]==["other","sample"]
assert queue["sourceContractFamilyDeferredProviders"]==["sample"]
assert all(key not in row for key in ("playable", "acceptedRepairs", "playerUrl"))
print("Learning queue source-contract deferral: zero legacy attempts, zero fake playback, sibling pending, debt retained")

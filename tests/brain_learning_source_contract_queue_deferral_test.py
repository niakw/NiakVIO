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

deferred,replay,status=mod.source_contract_capability_state(
    ["sample","sibling"], {"sample":{}}, False
)
assert deferred==["sample"] and replay==[] and status=="new_family_required"
deferred,replay,status=mod.source_contract_capability_state(
    ["sample","sibling"], {"sample":{}}, True
)
assert deferred==[] and replay==["sample"] and status=="parser_installed_replay_required"
deferred,replay,status=mod.source_contract_capability_state(
    ["sample","sibling"], {"sample":{}}, True, {"sample"}, False
)
assert deferred==["sample"] and replay==[] and status=="resolver_family_required"
deferred,replay,status=mod.source_contract_capability_state(
    ["sample","sibling"], {"sample":{}}, True, {"sample"}, True
)
assert deferred==[] and replay==["sample"] and status=="resolver_installed_replay_required"
deferred,replay,status=mod.source_contract_capability_state(
    ["sample","sibling"], {"sample":{}}, True, {"sample"}, True, {"sample"}
)
assert deferred==[] and replay==["sample"] and status=="player_target_observed"
assert mod.source_contract_capability_state(["sample"], {}, True, {"sample"}, False)==([],[],"not_attested")

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

resolver_queue={"pendingProviders":["sample"],"completedInCycle":[],
                "sourceContractFamilyDeferredProviders":["sample"],
                "sourceContractFamilyExecutableStatus":"resolver_family_required"}
resolver_state={"attemptCount":4,"lastStatus":"no_streams"}
resolver_row=mod.defer_new_source_contract_family(
    "sample",resolver_state,info,resolver_queue
)
assert resolver_row["sourceContractFamilyStatus"]=="resolver_family_required"
assert resolver_state["lastStatus"]=="new_source_resolver_executable_required"
assert resolver_state["attemptCount"]==4
print("Learning queue source-contract deferral: zero legacy attempts, zero fake playback, sibling pending, debt retained")

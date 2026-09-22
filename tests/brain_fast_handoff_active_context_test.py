#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/"engine_v2/scripts/learning-lab.mjs"

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    out=td/"out"
    repair=td/"repair.json"
    previous=td/"previous.json"
    native=td/"native.json"
    targeted=td/"targeted.json"
    historical=td/"historical.json"
    queue=td/"queue.json"

    repair.write_text(json.dumps({
        "brain":{"plans":{
            "published:target-a":{
                "providerId":"target-a",
                "failureClass":"route_proven_gap",
                "signature":"sig-a",
                "allowedProfiles":["proven_route_terminal_traversal_v1"],
                "action":"probe-targeted-repair",
            }
        }}
    }),encoding="utf-8")
    previous_memory={
        "readerLearningFailures":{
            "entries":[
                {"providerId":"target-a","failureClass":"media_extraction_gap","occurrences":3,"owner":"provider_learning"},
                {"providerId":"outside-x","failureClass":"playback_timeout","occurrences":99,"owner":"provider_learning"},
            ]
        }
    }
    previous.write_text(json.dumps({
        "publicationAllowed":False,
        "productionWritesAllowed":False,
        "nativeReaderRepairMemory":previous_memory,
        "experimentMemory":{
            "entries":[
                {"providerId":"target-a","failureClass":"route_proven_gap","profile":"adaptive_runtime_recovery","signature":"a","failures":2,"consecutiveFailures":2,"successes":0},
                {"providerId":"outside-x","failureClass":"media_extraction_gap","profile":"adaptive_runtime_recovery","signature":"x","failures":9,"consecutiveFailures":9,"successes":0},
            ]
        },
        "learnedSkills":{},
    }),encoding="utf-8")
    native.write_text(json.dumps({
        "nativeReaderObserved":102,
        "nativeReaderFailures":102,
        "readerFailureClasses":{"media_extraction_gap":3,"playback_timeout":99},
        "readerFailureSignals":[
            {"failureClass":"media_extraction_gap","occurrences":3,"providers":["target-a"],"clients":["tv"]},
            {"failureClass":"playback_timeout","occurrences":99,"providers":["outside-x"],"clients":["desktop"]},
        ],
        "providerReaderFailures":[
            {"provider":"target-a","occurrences":3,"failureClasses":{"media_extraction_gap":3}},
            {"provider":"outside-x","occurrences":99,"failureClasses":{"playback_timeout":99}},
        ],
        "engineSignals":{"repeatedReaderFailures":[
            {"provider":"target-a","failureClass":"media_extraction_gap","occurrences":3},
            {"provider":"outside-x","failureClass":"playback_timeout","occurrences":99},
        ]},
        "policy":{"providerMutationFromIncompleteEvidence":False},
    }),encoding="utf-8")
    targeted.write_text(json.dumps({
        "providers":[{"providerId":"target-a","status":"unresolved","clients":{}}],
    }),encoding="utf-8")
    historical.write_text(json.dumps({
        "baseline":"test",
        "stats":{},
        "cases":[
            {"providerId":"target-a","trainingRole":"unresolved","priority":"high","delta":"unresolved"},
            {"providerId":"outside-x","trainingRole":"unresolved","priority":"critical","delta":"regressed"},
        ],
    }),encoding="utf-8")
    queue.write_text(json.dumps({
        "schemaVersion":1,
        "providers":{"target-a":{"status":"pending"}},
    }),encoding="utf-8")

    subprocess.run([
        "node",str(LAB),
        "--output-dir",str(out),
        "--repair-report",str(repair),
        "--historical-training",str(historical),
        "--native-summary",str(native),
        "--targeted-lab-summary",str(targeted),
        "--learning-queue-state",str(queue),
        "--previous-state",str(previous),
        "--overrides",str(ROOT/"provider-overrides.json"),
        "--provider-filter","target-a",
    ],cwd=ROOT,check=True,capture_output=True,text=True,timeout=30)

    data=json.loads((out/"latest.json").read_text(encoding="utf-8"))
    assert data["activeProviderFilter"]==["target-a"],data["activeProviderFilter"]
    # Long-term reader memory is retained exactly; active reasoning is scoped.
    assert data["nativeReaderRepairMemory"]==previous_memory
    proposals=data.get("proposals") or []
    serialized=json.dumps(proposals,sort_keys=True)
    assert "outside-x" not in serialized,serialized
    assert "target-a" in serialized,serialized
    assert all(
        not row.get("providerId") or row.get("providerId")=="target-a"
        for row in proposals
        if isinstance(row,dict)
    ),proposals
    # The huge out-of-scope reader backlog may not become an active priority.
    assert data["nativeFeedback"]["repairPriorityProviders"]==["target-a"],data["nativeFeedback"]

print("Fast-Handoff active-context isolation contract passed")

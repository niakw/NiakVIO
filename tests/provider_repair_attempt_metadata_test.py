#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/persist_provider_repair_attempt_metadata.py"

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    status=td/"status.json"
    brain=td/"brain.json"
    status.write_text(json.dumps({
        "schemaVersion":3,
        "runId":"authoritative-census",
        "providers":[{"provider":"demo","status":"ROUTE PROVEN"}],
        "repairQueue":["demo"],
    })+"\n",encoding="utf-8")
    brain.write_text(json.dumps({
        "sourceCensusRunId":"earlier-census",
        "selectedProviders":["demo"],
        "fixedInLabProviders":[],
        "acceptedProgramCompiledProviders":[],
        "deferredLearningProviders":["demo"],
        "acceptedRepairCount":0,
        "noProgressReason":"experiment_variants_exhausted",
        "timeBudgetExhausted":False,
    })+"\n",encoding="utf-8")
    subprocess.run([
        sys.executable,str(script),
        "--status",str(status),
        "--brain",str(brain),
        "--run-id","force-123",
        "--mode","force",
        "--canonical-outcome","failure",
        "--candidate-gate-outcome","skipped",
    ],check=True,cwd=ROOT)
    data=json.loads(status.read_text(encoding="utf-8"))
    assert data["runId"]=="authoritative-census"
    assert data["providers"]==[{"provider":"demo","status":"ROUTE PROVEN"}]
    attempt=data["lastRepairAttempt"]
    assert attempt["runId"]=="force-123"
    assert attempt["sourceCensusRunId"]=="earlier-census"
    assert attempt["recordedAgainstCensusRunId"]=="authoritative-census"
    assert attempt["validationBasis"]=="gate-not-passed"
    assert attempt["mode"]=="force"
    assert attempt["selectedProviders"]==["demo"]
    assert attempt["validatedProviders"]==[]
    assert attempt["canonicalOutcome"]=="failure"
    assert attempt["publicationAllowed"] is False

    # A successful aggregate gate is not itself a per-candidate proof record.
    sample=json.loads(brain.read_text(encoding="utf-8"))
    sample.pop("sourceCensusRunId")
    sample["acceptedProgramCompiledProviders"]=["demo"]
    brain.write_text(json.dumps(sample),encoding="utf-8")
    subprocess.run([
        sys.executable,str(script),"--status",str(status),"--brain",str(brain),
        "--run-id","force-124","--mode","force",
        "--canonical-outcome","success","--candidate-gate-outcome","success",
    ],check=True,cwd=ROOT)
    data=json.loads(status.read_text(encoding="utf-8"))
    attempt=data["lastRepairAttempt"]
    assert attempt["sourceCensusRunId"]==""
    assert attempt["recordedAgainstCensusRunId"]=="authoritative-census"
    assert attempt["candidateProviders"]==["demo"]
    assert attempt["validatedProviders"]==[]
    assert attempt["validationBasis"]=="aggregate-gates-only"
    assert data["providers"]==[{"provider":"demo","status":"ROUTE PROVEN"}]
    assert data["repairQueue"]==["demo"]
    sys.path.insert(0,str(ROOT/"scripts"))
    from render_provider_census_status import repair_attempt_notice
    notice=repair_attempt_notice(attempt,data["runId"])
    assert "individual validation **not recorded**" in notice
    assert "source census unknown" in notice

# A source-pinned census may finish after a newer Repair persisted on main.
# Publication must retain the newer numeric GitHub run instead of regressing
# Brain activity memory to the census source snapshot.
sys.path.insert(0,str(ROOT/"scripts"))
from persist_provider_repair_attempt_metadata import preserve_newer_repair_attempt

candidate={"lastRepairAttempt":{"runId":"43580198030","noProgressReason":"old"}}
current={"lastRepairAttempt":{"runId":"43787089404","noProgressReason":"canonical-failure"}}
assert preserve_newer_repair_attempt(candidate,current) is True
assert candidate["lastRepairAttempt"]["runId"]=="43787089404"
assert candidate["lastRepairAttempt"]["noProgressReason"]=="canonical-failure"

already_new={"lastRepairAttempt":{"runId":"43799999999"}}
assert preserve_newer_repair_attempt(already_new,current) is False
assert already_new["lastRepairAttempt"]["runId"]=="43799999999"

missing={}
assert preserve_newer_repair_attempt(missing,current) is True
assert missing["lastRepairAttempt"]["runId"]=="43787089404"

ambiguous={"lastRepairAttempt":{"runId":"manual-force"}}
assert preserve_newer_repair_attempt(ambiguous,current) is False
assert ambiguous["lastRepairAttempt"]["runId"]=="manual-force"
print("newer durable Repair attempt survives stale census publication")

print("provider Repair attempt metadata persistence contract passed")

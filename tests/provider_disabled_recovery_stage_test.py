#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/build_disabled_provider_recovery_stage.py"
queue=json.loads((ROOT/"automation/provider-disabled-recovery-queue.json").read_text(encoding="utf-8"))
assert queue.get("proofAuthority") is False
assert queue.get("executionAuthority") is False
assert queue.get("publicationAuthority") is False
assert int(queue.get("eligibleCount") or 0)==len(queue.get("providers") or [])
with tempfile.TemporaryDirectory() as tmp:
    stage=Path(tmp)/"recovery"
    subprocess.run([sys.executable,str(script),"--stage",str(stage),"--max-providers","2"],cwd=ROOT,check=True)
    registry=json.loads((stage/"candidates.json").read_text(encoding="utf-8"))
    assert registry["candidate_count"]==2
    assert registry["productionExecutionAllowed"] is False
    assert registry["publicationAllowed"] is False
    assert registry["proofAuthority"] is False
    for row in registry["candidates"]:
        assert row["disabled_recovery_exact_bytes"] is True
        assert row["repair_allowed"] is True
        assert row["production_execution_allowed"] is False
        assert row["publication_allowed"] is False
        assert (stage/row["local_path"]).is_file()
print("Disabled provider recovery stage is exact-byte, isolated and non-publishing")

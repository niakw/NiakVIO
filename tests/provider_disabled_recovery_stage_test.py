#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/build_disabled_provider_recovery_stage.py"
workflow=(ROOT/".github/workflows/brain-disabled-recovery-lab.yml").read_text(encoding="utf-8")
assert "group: niakvio-brain-disabled-recovery-lab" in workflow
assert "cancel-in-progress: true" in workflow

assert "Resolve exact current Brain LLM revision" in workflow
assert "repository: niakw/NiakVIO-Brain-LLM" in workflow
assert "--allow-disabled-explicit" in workflow
assert "Synthesize disabled-provider guidance through Brain LLM" in workflow
assert "NIAKVIO_BRAIN_LLM_GUIDANCE=$GITHUB_WORKSPACE/brain-disabled-recovery/brain-llm/guidance.json" in workflow
assert "disabled recovery Brain routing did not select exactly one target" in workflow
assert "Brain LLM produced no guidance row for explicit disabled target" in workflow
assert "publicationAuthority" in workflow and "directMutationAuthority" in workflow
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

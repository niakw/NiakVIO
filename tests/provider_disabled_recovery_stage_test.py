#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/build_disabled_provider_recovery_stage.py"
workflow=(ROOT/".github/workflows/brain-disabled-recovery-lab.yml").read_text(encoding="utf-8")
classifier=(ROOT/"scripts/classify_disabled_recovery_disposition.py").read_text(encoding="utf-8")
assert "group: niakvio-brain-disabled-recovery-lab" in workflow
assert "cancel-in-progress: true" in workflow

assert "Resolve exact current Brain LLM revision" in workflow
assert "repository: niakw/NiakVIO-Brain-LLM" in workflow
assert "--allow-disabled-explicit" in workflow
assert "Synthesize disabled-provider guidance through Brain LLM" in workflow
assert "NIAKVIO_BRAIN_LLM_GUIDANCE=$GITHUB_WORKSPACE/brain-disabled-recovery/brain-llm/guidance.json" in workflow
assert "disabled recovery Brain routing did not select exactly one target" in workflow
assert "classify_disabled_recovery_disposition.py" in workflow
assert "Brain LLM abstained despite deterministic runtime error" in classifier
assert "currentDisabledHealthHealthy" in classifier
assert "identity_inconclusive_replay" in classifier
assert "transport_inconclusive_replay" in classifier
assert "NIAKVIO_DISABLED_RECOVERY_RESIDENTIAL" in workflow
observe_marker="      - name: Observe disabled bytes without production authority"
assert observe_marker in workflow
observe_block = workflow.split(observe_marker, 1)[1].split("      - name:", 1)[0]
assert "TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}" in observe_block
assert "TMDB_ACCESS_TOKEN: ${{ secrets.TMDB_ACCESS_TOKEN }}" in observe_block
assert "tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c" in workflow
assert "id-token: write" in workflow
assert "server_pid=$!" in workflow
assert "seq 1 300" in workflow
assert 'reason=process_exited' in workflow
assert "Clear residential exit before Brain model bootstrap" in workflow
assert "sudo tailscale set --exit-node=" in workflow
assert "Restore residential exit for provider recovery replay" in workflow
assert "FIELD_DISABLED_RECOVERY_RESIDENTIAL_RESTORED active=true" in workflow
assert "--ephemeral-overrides" in workflow
assert 'next_action="exact_playback_identity_replay"' in classifier
assert 'next_action="bounded_learning_repair"' in classifier
assert 'next_action="identity_inconclusive_replay"' in classifier
assert 'next_action="transport_inconclusive_replay"' in classifier
assert "steps.brain_guidance.outputs.has_guidance == 'true'" in workflow
assert "publicationAuthority" in classifier and "directMutationAuthority" in classifier
assert "id-token: write" in workflow
assert 'row.get("canonical_id")' in classifier
assert "--ephemeral-overrides-output staging-disabled-recovery-reconstruction/provider-overrides.ephemeral.json" in workflow
assert "--overrides staging-disabled-recovery-reconstruction/provider-overrides.ephemeral.json" in workflow
assert "--config staging-disabled-recovery-reconstruction/provider-overrides.ephemeral.json" in workflow
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

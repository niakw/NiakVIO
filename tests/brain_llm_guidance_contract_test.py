#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"brain_llm_guidance.py"
spec=importlib.util.spec_from_file_location("brain_llm_guidance",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

rows=[
    {
        "ok":True,
        "provider":"mallumv",
        "failure_class":"chain_terminal_gap",
        "proposal":{
            "provider_id":"mallumv",
            "strategy":"terminal_media_extractor_with_playback_validation",
            "confidence":0.93,
            "target_layer":"provider",
            "abstain":False,
            "diagnosis":"PRIVATE TEXT MUST NOT PERSIST",
            "mutations":[{"content":"SECRET MUTATION MUST NOT PERSIST"}],
            "evidence":["PRIVATE EVIDENCE MUST NOT PERSIST"],
            "tests":["PRIVATE TEST MUST NOT PERSIST"],
        },
    },
    {
        "ok":True,
        "provider":"allwish",
        "failure_class":"transport_environment_gap",
        "proposal":{
            "provider_id":"allwish",
            "strategy":"compare_browser_native_residential_profiles_without_provider_mutation",
            "confidence":0.99,
            "target_layer":"harness",
            "abstain":False,
        },
    },
    {
        "ok":True,
        "provider":"4khdhub",
        "failure_class":"route_proven_gap",
        "proposal":{
            "provider_id":"4khdhub",
            "strategy":"search_detail_player_terminal_traversal",
            "confidence":0.62,
            "target_layer":"provider",
            "abstain":False,
        },
    },
    {
        "ok":True,
        "provider":"animevostfr",
        "failure_class":"candidate_replay_gap",
        "proposal":{
            "provider_id":"animevostfr",
            "strategy":"same_provider_candidate_program_replay",
            "confidence":0.94,
            "target_layer":"provider",
            "abstain":True,
        },
    },
]
report=mod.sanitize(
    rows,
    source_sha="a"*40,
    brain_llm_sha="b"*40,
    min_confidence=0.80,
)
assert report["publicationAuthority"] is False,report
assert report["directMutationAuthority"] is False,report
assert report["proofAuthority"] is False,report
assert report["rawMutationContentRetained"] is False,report
assert report["schemaVersion"]==2,report
assert report["providerCount"]==1,report
assert len(report["rows"])==1,report
row=report["rows"][0]
assert row["providerId"]=="mallumv",row
assert row["profile"]=="chain_terminal_extractor_v1",row
assert row["experiment"]["terminalOnly"] is True,row
assert row["experiment"]["responseSalvage"] is True,row
assert row["experiment"]["routePolicy"]=="owned_plus_peer",row
assert len(row["experimentFingerprint"])==64,row
assert set(row)=={"providerId","failureClass","targetLayer","strategy","profile","confidence","priorOnly","experiment","experimentFingerprint"},row
encoded=json.dumps(report,sort_keys=True)
for forbidden in ("PRIVATE TEXT","SECRET MUTATION","PRIVATE EVIDENCE","PRIVATE TEST"):
    assert forbidden not in encoded,encoded

# The public mapping vocabulary must be bounded and executable by NiakVIO.
assert set(mod.STRATEGY_TO_PROFILE.values())=={
    "provider_origin_failover_v1",
    "proven_route_terminal_traversal_v1",
    "chain_terminal_extractor_v1",
    "retained_candidate_replay_v1",
    "player_media_extractor_v1",
    "search_contract_inference_v1",
}

print("Brain LLM guidance contract passed")


workflow=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert "repository: niakw/NiakVIO-Brain-LLM" in workflow
assert "ref: 1b3cbb5dfdde26d1c30552304807e76a3b55a2df" in workflow
assert "repository: niakw/niakvio-private" in workflow
assert "NIAKVIO_PRIVATE_READ_TOKEN" in workflow
assert "g-p-6a7f1d27495c819182b4081bfccdafd8" in workflow
assert "persist-credentials: false" in workflow
assert "NIAKVIO_BRAIN_LLM_GUIDANCE=" in workflow
assert "brain_llm_guidance.py" in workflow
assert "brain_llm_experiment.py" in workflow
assert "Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M" in workflow
# Ephemeral private documents may feed the model but must never be uploaded.
upload_tail=workflow[workflow.find("Upload sanitized learning and proposal state"):]
assert "private-documents.jsonl" not in upload_tail
assert "brain-llm-private" not in upload_tail

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/reactivate_disabled_from_recovery.py"
spec=importlib.util.spec_from_file_location("reactivate_disabled_from_recovery",script)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/"provider-disabled").mkdir()
    (root/"brain-disabled-recovery/health").mkdir(parents=True)
    (root/"brain-disabled-recovery/brain-llm").mkdir(parents=True)
    (root/"staging-disabled-recovery").mkdir(parents=True)

    asset=root/"provider-disabled/demo.js"
    asset.write_text("console.log('demo')\n",encoding="utf-8")
    digest=hashlib.sha256(asset.read_bytes()).hexdigest()
    manifest={"scrapers":[{
        "id":"demo","enabled":False,"filename":"provider-disabled/demo.js",
        "supportedTypes":["movie","tv"],"lifecycleState":"disabled-retained",
    }]}
    (root/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    (root/"provider_catalog.json").write_text(json.dumps({"providers":[]}),encoding="utf-8")

    stage={"candidates":[{
        "canonical_id":"demo","sha256":digest,
        "disabled_recovery_exact_bytes":True,
        "production_execution_allowed":False,
        "publication_allowed":False,
    }]}
    (root/"staging-disabled-recovery/candidates.json").write_text(json.dumps(stage),encoding="utf-8")

    health={"results":[{
        "canonical_id":"demo","sha256":digest,"status":"healthy",
        "ci_classification":"conclusive_success","verified_max_height":1080,
        "audio_languages":["fr"],
        "candidate_profile":{"required_fixture_categories":["movie","tv"]},
        "evidence":{
            "healthy_fixture_categories":["movie","tv"],
            "streams_playable":2,"payload_verified_streams":2,"identity_verified_streams":2,
            "identity_contradiction_count":0,"duration_identity_mismatch_count":0,
            "playable_identity_contradiction_count":0,"playable_duration_identity_mismatch_count":0,
            "streams_rejected_identity":0,"streams_rejected_duration":0,
            "provider_server_accessible":True,"provider_server_successful_response":True,
        },
        "tests":[
            {
                "fixture":{"category":"movie","label":"Movie","tmdbId":"1"},
                "host_results":[{
                    "host":"movie.example","kind":"hls","playback_verified":True,
                    "payload_verified":True,"content_identity_status":"match",
                    "content_identity_reason":"fixture_duration_match",
                    "duration_identity_mismatch":False,
                }],
            },
            {
                "fixture":{"category":"tv","label":"TV S01E01","tmdbId":"2"},
                "host_results":[{
                    "host":"tv.example","kind":"hls","playback_verified":True,
                    "payload_verified":True,"content_identity_status":"match",
                    "content_identity_reason":"fixture_duration_match",
                    "duration_identity_mismatch":False,
                }],
            },
        ],
    }]}
    (root/"brain-disabled-recovery/health/health-results.json").write_text(json.dumps(health),encoding="utf-8")
    disposition={
        "provider":"demo","brainGuidanceRows":0,"brainAbstained":True,
        "currentDisabledHealthHealthy":True,"residentialTransportActive":True,
        "repairRequired":False,"publicationAuthority":False,"directMutationAuthority":False,
        "nextAction":"exact_playback_identity_replay",
    }
    (root/"brain-disabled-recovery/brain-llm/recovery-disposition.json").write_text(json.dumps(disposition),encoding="utf-8")
    guidance={
        "sourceSha":"abc123","providerCount":0,"rows":[],
        "directMutationAuthority":False,"publicationAuthority":False,
    }
    (root/"brain-disabled-recovery/brain-llm/guidance.json").write_text(json.dumps(guidance),encoding="utf-8")

    proof=mod.validate_recovery(root,"demo",root,proof_run_id="42",proof_head_sha="abc123")
    assert proof["provider"]=="demo"
    assert proof["scope"]=="global"
    assert proof["providerArtifactSha256"]==digest
    assert proof["declaredLanes"]==["movie","tv"]
    assert proof["verifiedLanes"]==["movie","tv"]
    assert proof["identityVerifiedStreams"]==2
    assert proof["proofStatus"]=="terminal_identity_verified"

    # Aggregate identity counts are insufficient: each declared lane must own
    # at least one playable payload-verified identity match.
    health["results"][0]["tests"][1]["host_results"][0]["content_identity_status"]="unknown"
    (root/"brain-disabled-recovery/health/health-results.json").write_text(
        json.dumps(health), encoding="utf-8"
    )
    try:
        mod.validate_recovery(root,"demo",root,proof_run_id="42",proof_head_sha="abc123")
    except RuntimeError as exc:
        assert "missing per-lane identity-verified playable proof" in str(exc)
    else:
        raise AssertionError("per-lane identity proof was accepted")
    health["results"][0]["tests"][1]["host_results"][0]["content_identity_status"]="match"
    (root/"brain-disabled-recovery/health/health-results.json").write_text(
        json.dumps(health), encoding="utf-8"
    )

    # Exact-byte drift must invalidate the proof before any activation write.
    asset.write_text("console.log('drift')\n",encoding="utf-8")
    try:
        mod.validate_recovery(root,"demo",root,proof_run_id="42",proof_head_sha="abc123")
    except RuntimeError as exc:
        assert "drifted" in str(exc)
    else:
        raise AssertionError("byte drift was accepted")

print("disabled recovery proof-bound reactivation contract passed")

source = SCRIPT.read_text(encoding="utf-8")
assert 'manifest_overrides.pop("enabled", None)' in source
assert 'manifest_overrides["enabled"] = True' not in source
assert "Lifecycle/folder state is the activation authority" in source

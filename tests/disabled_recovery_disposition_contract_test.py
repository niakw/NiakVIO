#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"classify_disabled_recovery_disposition.py"
spec=importlib.util.spec_from_file_location("disabled_recovery_disposition",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def host(identity: str) -> dict:
    return {
        "playback_verified": True,
        "payload_verified": True,
        "content_identity_status": identity,
        "duration_identity_mismatch": False,
    }


health={
    "results":[{
        "canonical_id":"demo",
        "status":"healthy",
        "candidate_profile":{"required_fixture_categories":["movie","tv"]},
        "evidence":{"identity_verified_streams":2,"streams_playable":3},
        "tests":[
            {"fixture":{"category":"movie","title":"Movie"},"host_results":[host("unknown")]},
            {"fixture":{"category":"tv","title":"Series"},"host_results":[host("match"),host("match")]},
        ],
    }]
}
guidance={"rows":[],"publicationAuthority":False,"directMutationAuthority":False}
result=mod.classify(health,guidance,"demo",residential_transport_active=True)
assert result["aggregateHealthHealthy"] is True
assert result["currentDisabledHealthHealthy"] is False
assert result["identityVerifiedLanes"]==["tv"],result
assert result["missingIdentityVerifiedLanes"]==["movie"],result
assert result["nextAction"]=="identity_inconclusive_replay",result
assert result["repairRequired"] is False

health["results"][0]["tests"][0]["host_results"]=[host("match")]
result=mod.classify(health,guidance,"demo",residential_transport_active=True)
assert result["currentDisabledHealthHealthy"] is True
assert result["identityVerifiedLanes"]==["movie","tv"],result
assert result["missingIdentityVerifiedLanes"]==[],result
assert result["nextAction"]=="exact_playback_identity_replay",result

with_guidance={
    "rows":[{"providerId":"demo","strategy":"bounded"}],
    "publicationAuthority":False,
    "directMutationAuthority":False,
}
result=mod.classify(health,with_guidance,"demo",residential_transport_active=False)
assert result["nextAction"]=="bounded_learning_repair"
assert result["repairRequired"] is True
assert result["publicationAuthority"] is False
assert result["directMutationAuthority"] is False

health["results"][0]["status"]="runtime_error"
try:
    mod.classify(health,guidance,"demo",residential_transport_active=False)
except RuntimeError as exc:
    assert "abstained despite deterministic runtime error" in str(exc)
else:
    raise AssertionError("runtime-error abstention was accepted")

print("disabled recovery disposition contract passed: per-lane identity required")

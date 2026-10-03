#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from validate_automatic_repair_results import validate

KEY="gowaru:coflix"

def playable_result():
    return {
        "key":KEY,
        "evidence":{
            "streams_playable":2,
            "identity_contradiction_count":0,
            "duration_identity_mismatch_count":0,
        },
        "tests":[
            {
                "fixture":{"label":"movie"},
                "streams_playable":2,
                "identity_contradiction_count":0,
                "duration_identity_mismatch_count":0,
            }
        ],
    }

# Old accepted history must not be counted again by a later round that accepts
# nothing. This was the Coflix Learning failure: report=0 vs cumulative history=1.
registry_old={"candidates":[{"key":KEY,"repair_history":[{"accepted":True,"round":1}]}]}
health_no_new={"mode":"quick","results":[{"key":KEY,"evidence":{"streams_playable":0},"tests":[]}]}
assert validate(
    registry_old,
    health_no_new,
    {"mode":"quick","accepted_repairs":0},
    {KEY:1},
)==[]

# A newly accepted event is counted only as the delta and still must pass the
# current safety gate.
registry_new={"candidates":[{"key":KEY,"repair_history":[
    {"accepted":True,"round":1},
    {"accepted":True,"round":2},
]}]}
assert validate(
    registry_new,
    {"mode":"quick","results":[playable_result()]},
    {"mode":"quick","accepted_repairs":1},
    {KEY:1},
)==[]

failures=validate(
    registry_new,
    health_no_new,
    {"mode":"quick","accepted_repairs":1},
    {KEY:1},
)
assert any("safety_gate:no_playable_proof" in row for row in failures),failures

failures=validate(
    registry_old,
    health_no_new,
    {"mode":"quick","accepted_repairs":0},
    {KEY:2},
)
assert any("repair history regressed below baseline" in row for row in failures),failures

print("automatic repair attempt-delta accounting contract passed")

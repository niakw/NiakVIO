#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/build_brain_repair_experience.py"
spec=importlib.util.spec_from_file_location("brain_repair_experience_history",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

patch={
    "search_request_plan":[{
        "base":"https://green.example",
        "route":"/search?q={query}",
        "requestSpec":{
            "method":"GET",
            "headers":{"Accept":"text/html","User-Agent":"UA/1.0"},
        },
        "proofModelVersion":5,
        "semanticTypes":["movie"],
    }],
    "provider_value_plan":[{
        "proofModelVersion":5,
        "semanticTypes":["tv"],
        "steps":[{
            "base":"https://green.example",
            "route":"/api/player/{id}",
            "requestSpec":{
                "method":"GET",
                "headers":{"Accept":"application/json"},
            },
            "role":"player",
            "responseKind":"json",
            "streamProof":True,
        }],
    }],
    "api_recipe":{
        "proofModelVersion":5,
        "base":"https://api.green.example",
        "movieRoute":"/movie/{tmdbId}",
        "movieRequest":{
            "method":"GET",
            "headers":{"Accept":"application/json","Referer":"https://green.example/"},
        },
    },
}
recipes=mod.proof_owned_patch_recipes(patch)
assert any(row["route"]=="/search?q={query}" and row["semanticType"]=="movie" for row in recipes),recipes
assert any(row["route"]=="/api/player/{id}" and row["semanticType"]=="tv" for row in recipes),recipes
assert any(row["route"]=="/movie/{tmdbId}" and row["semanticType"]=="movie" for row in recipes),recipes
assert all(row["executable"] is True for row in recipes)

with tempfile.TemporaryDirectory() as directory:
    td=Path(directory)
    good=td/"good.json"
    good.write_text(json.dumps({
        "schemaVersion":1,
        "role":"historical-repair-prior-only",
        "sourceScope":"NiakVIO project chats + repository history, technical only",
        "safety":{"directMutationAuthority":False,"publicationAuthority":False},
        "cases":[{
            "id":"case-1",
            "providers":["demo"],
            "symptomFamilies":["no_streams"],
            "failureClass":"route_proven_gap",
            "solutionClass":"replay_proven_routes",
            "transferableSignals":["route exists"],
            "avoid":["blind rediscovery"],
            "evidence":["project-chat","repo-history"],
            "lesson":"Reuse validated NiakVIO technical history as prior only.",
        }],
    }),encoding="utf-8")
    rows=mod.load_historical_cases(good)
    assert len(rows)==1 and rows[0]["id"]=="case-1"

    foreign=td/"foreign.json"
    foreign.write_text(json.dumps({
        "schemaVersion":1,
        "role":"historical-repair-prior-only",
        "sourceScope":"Other GPT project",
        "safety":{"directMutationAuthority":False,"publicationAuthority":False},
        "cases":[],
    }),encoding="utf-8")
    try:
        mod.load_historical_cases(foreign)
    except ValueError as exc:
        assert "NiakVIO-only" in str(exc)
    else:
        raise AssertionError("cross-project historical source was accepted")

    personal=td/"personal.json"
    personal.write_text(json.dumps({
        "schemaVersion":1,
        "role":"historical-repair-prior-only",
        "sourceScope":"NiakVIO project chats + repository history, technical only",
        "safety":{"directMutationAuthority":False,"publicationAuthority":False},
        "cases":[{
            "id":"bad",
            "failureClass":"x",
            "solutionClass":"y",
            "evidence":["project-chat"],
            "personalLocation":"forbidden",
        }],
    }),encoding="utf-8")
    try:
        mod.load_historical_cases(personal)
    except ValueError as exc:
        assert "non-whitelisted" in str(exc)
    else:
        raise AssertionError("non-technical/personal field was accepted")

seed=json.loads((ROOT/"automation/brain-historical-experience-seed.json").read_text(encoding="utf-8"))
assert seed["role"]=="historical-repair-prior-only"
assert seed["sourceScope"].startswith("NiakVIO project chats + repository history")
assert seed["safety"]["directMutationAuthority"] is False
assert seed["safety"]["publicationAuthority"] is False

print("Brain historical NiakVIO experience and privacy-scope contract passed")

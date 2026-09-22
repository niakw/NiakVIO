#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]

san_spec=importlib.util.spec_from_file_location("sanitize_learning", ROOT/"scripts"/"sanitize_brain_learning_memory.py")
assert san_spec and san_spec.loader
san=importlib.util.module_from_spec(san_spec)
san_spec.loader.exec_module(san)

runtime_spec=importlib.util.spec_from_file_location("brain_runtime_learning", ROOT/"scripts"/"brain_repair_runtime.py")
assert runtime_spec and runtime_spec.loader
runtime=importlib.util.module_from_spec(runtime_spec)
runtime_spec.loader.exec_module(runtime)

raw={
    "schemaVersion":5,
    "generatedAt":"2026-09-22T00:00:00Z",
    "publicationAllowed":False,
    "productionWritesAllowed":False,
    "learnedSkills":{
        "trusted-demo":{
            "id":"trusted-demo",
            "failureClass":"search_gap",
            "profile":"adaptive_runtime_recovery",
            "actions":["repair parser"],
            "capabilities":["search"],
            "providers":["a","b"],
            "successCount":4,
            "failureCount":0,
            "validated":True,
            "confidence":0.95,
            "maturity":"trusted",
            "autoApply":True,
            "lastValidatedMode":"learning",
        },
        "candidate-demo":{
            "id":"candidate-demo",
            "failureClass":"search_gap",
            "profile":"adaptive_runtime_recovery",
            "actions":["try candidate"],
            "capabilities":["search"],
            "providers":["a"],
            "successCount":2,
            "failureCount":0,
            "validated":True,
            "confidence":1,
            "maturity":"candidate",
        },
    },
    "proposals":[{"danger":"must not cross"}],
    "experimentMemory":{"entries":[{"providerId":"x"}]},
}
safe=san.sanitize(raw)
assert safe["learnedSkillCount"]==2,safe
assert "proposals" not in safe,safe
assert "experimentMemory" not in safe,safe
assert safe["learnedSkills"]["trusted-demo"]["autoApply"] is False

with TemporaryDirectory() as td:
    p=Path(td)/"learning.json"
    p.write_text(json.dumps(safe),encoding="utf-8")
    runtime.LEARNING_MEMORY_PATH=p
    skills=runtime.learned_skills()
    assert "trusted-demo" in skills,skills
    assert "candidate-demo" in skills,skills
    production=runtime.planner_learned_skills("repair")
    assert "trusted-demo" in production,production
    assert "candidate-demo" not in production,production

unsafe=dict(raw)
unsafe["learnedSkills"]={
    "bad":{
        "id":"bad","failureClass":"search_gap","profile":"adaptive_runtime_recovery",
        "actions":["fetch https://secret.invalid/path"],
        "providers":["a","b"],"validated":True,"confidence":1,"maturity":"trusted",
    }
}
try:
    san.sanitize(unsafe)
except ValueError:
    pass
else:
    raise AssertionError("URL-bearing Learning skill must fail closed")

unsafe_auth=dict(raw)
unsafe_auth["publicationAllowed"]=True
try:
    san.sanitize(unsafe_auth)
except ValueError:
    pass
else:
    raise AssertionError("write-authorized Learning memory must fail closed")

print("sanitized Learning memory -> Fast Repair prior contract passed")

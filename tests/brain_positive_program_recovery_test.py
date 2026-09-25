#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "recover_brain_positive_program_memory.py"
spec = importlib.util.spec_from_file_location("recover_positive", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

program = {
    "schemaVersion": 1,
    "profile": "adaptive_runtime_recovery",
    "revision": 5,
    "options": {
        "base_url": "https://provider.example",
        "types": ["movie"],
        "experiment_failure_class": "media_extraction_gap",
        "experiment_variant": 4,
        "experiment_generation": 2,
        "request_recipes": [
            {
                "route": "/search?q={query}",
                "origin": "https://provider.example",
                "role": "search",
                "method": "GET",
                "bodyKind": "none",
                "body": {},
                "headerNames": ["accept"],
                "response": "html-or-text",
                "semanticType": "movie",
                "requiredBindings": [],
                "streamProof": False,
                "executable": True,
            },
            {
                "route": "/player/{binding:id}",
                "origin": "https://provider.example",
                "role": "player",
                "method": "GET",
                "bodyKind": "none",
                "body": {},
                "headerNames": ["accept", "referer"],
                "response": "json",
                "semanticType": "movie",
                "requiredBindings": ["id"],
                "streamProof": True,
                "executable": True,
            },
        ],
    },
}

accepted = {
    "provider": "demo",
    "profile": "player_media_extractor_v1",
    "reason": "strict_playable_stream_improvement",
    "statusBefore": "no_streams",
    "statusAfter": "healthy",
    "playableBefore": 0,
    "playableAfter": 1,
    "brainPlan": {
        "failureClass": "media_extraction_gap",
        "signature": "demo-positive",
        "experimentVariant": 4,
        "experimentGeneration": 2,
    },
    "acceptedProgram": program,
    "v3ProgramPersistence": {"status": "compiled"},
}

with tempfile.TemporaryDirectory() as raw:
    tmp = Path(raw)
    report = tmp / "provider-brain-repair-1.json"
    report.write_text(json.dumps({
        "acceptedProgramCompiledProviders": ["demo"],
        "acceptedRepairs": [accepted],
    }), encoding="utf-8")
    memory = tmp / "positive.json"

    first = mod.recover([report], memory_path=memory)
    assert first["recoveredRecordCount"] == 1, first
    assert first["durableProviders"] == ["demo"], first
    saved = json.loads(memory.read_text(encoding="utf-8"))
    assert len(saved["entries"]) == 1, saved
    assert saved["entries"][0]["providerId"] == "demo"
    assert saved["entries"][0]["validated"] is True
    assert saved["safety"]["publicationAuthority"] is False

    # Recovery is idempotent and cannot inflate the durable memory.
    second = mod.recover([report], memory_path=memory)
    assert second["recoveredRecordCount"] == 1, second
    assert second["durableRecordCount"] == 1, second

    bad = tmp / "provider-brain-repair-2.json"
    bad_row = dict(accepted)
    bad_row["playableAfter"] = 0
    bad.write_text(json.dumps({
        "acceptedProgramCompiledProviders": ["demo"],
        "acceptedRepairs": [bad_row],
    }), encoding="utf-8")
    third = mod.recover([bad], memory_path=memory)
    assert third["recoveredRecordCount"] == 0, third
    assert third["durableRecordCount"] == 1, third

repair = (ROOT / "scripts" / "run_provider_brain_repair.py").read_text(encoding="utf-8")
assert "recover_positive_program_memory" in repair
assert "FIELD_PROVIDER_BRAIN_POSITIVE_RECOVERY" in repair
assert '"positiveProgramRecovery"' in repair

print("Brain positive program recovery contract passed")

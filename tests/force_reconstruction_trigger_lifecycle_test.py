#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "consume_force_clean_reconstruction_trigger.py"

spec = importlib.util.spec_from_file_location("consume_force_reconstruction", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

trigger = {
    "schema_version": 1,
    "mode": "explicit-one-shot",
    "providers": ["purstream", "vidlove"],
    "remove_after_materialization": True,
}
stage = {
    "candidates": [
        {
            "canonical_id": "purstream",
            "clean_reconstruction_mode": True,
            "candidate_code_origin": "new-niakvio-clean-seed",
            "provider_base_reconstruction_required": True,
            "upstream_code_executed": False,
            "legacy_provider_js_executed_for_reconstruction": False,
        },
        {
            "canonical_id": "vidlove",
            "clean_reconstruction_mode": True,
            "candidate_code_origin": "new-niakvio-clean-seed",
            "provider_base_reconstruction_required": True,
            "upstream_code_executed": False,
            "legacy_provider_js_executed_for_reconstruction": False,
        },
    ]
}
provenance = {
    "providers": {
        "purstream": {
            "base_source": "niakvio-clean-reconstruction-v2-candidate",
            "clean_reconstruction_candidate": True,
            "clean_reconstruction_verified": False,
            "clean_reconstruction_authoring_version": 2,
            "clean_reconstruction_candidate_origin": "new-niakvio-clean-seed",
        },
        "vidlove": {
            "base_source": "niakvio-clean-reconstruction-v2",
            "clean_reconstruction_verified": True,
            "clean_reconstruction_authoring_version": 2,
            "clean_reconstruction_candidate_origin": "new-niakvio-clean-seed",
        },
    }
}
complete, reasons = mod.completion_status(trigger, stage, provenance)
assert complete is True, reasons

broken_stage = json.loads(json.dumps(stage))
broken_stage["candidates"][1]["candidate_code_origin"] = "pending-niakvio-clean-reconstruction-v2"
complete, reasons = mod.completion_status(trigger, broken_stage, provenance)
assert complete is False
assert "vidlove:not-rebuilt-this-run" in reasons

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    trigger_path = root / "trigger.json"
    stage_path = root / "candidates.json"
    provenance_path = root / "PROVENANCE.json"
    trigger_path.write_text(json.dumps(trigger), encoding="utf-8")
    stage_path.write_text(json.dumps(stage), encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")

    import subprocess, sys
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--trigger",
            str(trigger_path),
            "--stage",
            str(stage_path),
            "--provenance",
            str(provenance_path),
            "--consume",
        ],
        check=True,
    )
    assert not trigger_path.exists(), "completed one-shot trigger must be consumed"

print("forced reconstruction trigger lifecycle passed")

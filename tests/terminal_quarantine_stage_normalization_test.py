#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / "scripts" / "normalize_terminal_quarantine_stage.py"
spec = importlib.util.spec_from_file_location("normalize_terminal_quarantine_stage", module_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    stage = root / "staging"
    providers = stage / "providers"
    providers.mkdir(parents=True)

    (providers / "quarantined.js").write_text(
        "// NUVIO_PROVIDER_QUARANTINE_V1\nasync function getStreams(){return []}\n",
        encoding="utf-8",
    )
    (providers / "healthy.js").write_text(
        "async function getStreams(){return []}\n",
        encoding="utf-8",
    )

    registry = {
        "candidates": [
            {
                "key": "upstream:quarantined",
                "canonical_id": "quarantined",
                "local_path": "providers/quarantined.js",
                "local_patches": [
                    {"type": "replace", "from": "old.example", "to": "new.example"},
                    {"type": "script", "script": "quarantine_provider_v1.py"},
                ],
            },
            {
                "key": "upstream:healthy",
                "canonical_id": "healthy",
                "local_path": "providers/healthy.js",
                "local_patches": [
                    {"type": "replace", "from": "a.example", "to": "b.example"},
                ],
            },
        ]
    }
    overrides = {
        "provider_patches": {
            "quarantined": {
                "replacements": {"old.example": "new.example"},
                "route_replacements": {"/old": "/new"},
                "runtime_domain_replacements": {"old.example": "new.example"},
            },
            "healthy": {
                "replacements": {"a.example": "b.example"},
            },
        }
    }
    registry_path = stage / "candidates.json"
    overrides_path = root / "provider-overrides.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    overrides_path.write_text(json.dumps(overrides), encoding="utf-8")

    stats = module.normalize(root, stage, overrides_path)
    assert stats == {"providers": 1, "mappings": 3, "records": 1}, stats

    normalized_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    normalized_overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
    quarantine_row = normalized_registry["candidates"][0]
    healthy_row = normalized_registry["candidates"][1]

    assert quarantine_row["local_patches"] == [
        {"type": "script", "script": "quarantine_provider_v1.py"}
    ]
    assert healthy_row["local_patches"] == [
        {"type": "replace", "from": "a.example", "to": "b.example"}
    ]
    assert normalized_overrides["provider_patches"]["quarantined"]["replacements"] == {}
    assert normalized_overrides["provider_patches"]["quarantined"]["route_replacements"] == {}
    assert normalized_overrides["provider_patches"]["quarantined"]["runtime_domain_replacements"] == {}
    assert normalized_overrides["provider_patches"]["healthy"]["replacements"] == {"a.example": "b.example"}

print("terminal quarantine stage normalization test passed")

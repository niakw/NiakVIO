#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


patch = load("adaptive_domain_patch", ROOT / "scripts" / "provider_patches" / "adaptive_domain_recovery.py")
reapply = load("reapply", ROOT / "scripts" / "reapply_published_overrides.py")

source = 'module.exports={getStreams:async()=>fetch("https://old.example/api/item?id=42")};'
groups = [{"hosts": ["old.example"], "candidates": ["https://new.example"]}]
options = {"groups": groups}
current = patch.apply(source, options=options)
current_payload = base64.b64encode(
    json.dumps(
        {"revision": patch.IMPLEMENTATION_REVISION, "groups": groups},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
).decode()
legacy_payload = base64.b64encode(
    json.dumps(groups, separators=(",", ":"), sort_keys=True).encode()
).decode()
legacy = current.replace(current_payload, legacy_payload)
assert legacy != current
assert legacy_payload in legacy and current_payload not in legacy

migrated, records = reapply.reapply_adaptive_domain_revision(legacy.encode("utf-8"))
assert migrated.decode("utf-8") == current
assert records
assert records[-1]["name"] == "adaptive_domain_implementation_revision"
assert records[-1]["runtime_revision"] == patch.IMPLEMENTATION_REVISION

again, again_records = reapply.reapply_adaptive_domain_revision(migrated)
assert again == migrated
assert again_records == []

plain, plain_records = reapply.reapply_adaptive_domain_revision(source.encode("utf-8"))
assert plain == source.encode("utf-8")
assert plain_records == []

print("published adaptive domain revision reapply test passed")

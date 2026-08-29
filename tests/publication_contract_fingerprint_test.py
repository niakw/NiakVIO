#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "reapply_published_overrides.py"

spec = importlib.util.spec_from_file_location("reapply_publication_fingerprint", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.PUBLICATION_CONTRACT_SCHEMA == 2

base = {
    "name": "fixture",
    "version": "5.21.8",
    "lockfileVersion": 3,
    "requires": True,
    "packages": {
        "": {
            "name": "fixture",
            "version": "5.21.8",
            "dependencies": {"alpha": "1.0.0"},
        },
        "node_modules/alpha": {
            "version": "1.0.0",
            "resolved": "https://registry.npmjs.org/alpha/-/alpha-1.0.0.tgz",
            "integrity": "sha512-original",
        },
    },
}

with tempfile.TemporaryDirectory() as raw:
    path = Path(raw) / "package-lock.json"

    path.write_text(json.dumps(base), encoding="utf-8")
    first = module._publication_file_sha("package-lock.json", path)

    release_only = json.loads(json.dumps(base))
    release_only["version"] = "9.99.1"
    release_only["packages"][""]["version"] = "9.99.1"
    path.write_text(json.dumps(release_only), encoding="utf-8")
    second = module._publication_file_sha("package-lock.json", path)
    assert second == first, (first, second)

    dependency_changed = json.loads(json.dumps(release_only))
    dependency_changed["packages"]["node_modules/alpha"]["version"] = "1.0.1"
    dependency_changed["packages"]["node_modules/alpha"]["integrity"] = "sha512-changed"
    path.write_text(json.dumps(dependency_changed), encoding="utf-8")
    third = module._publication_file_sha("package-lock.json", path)
    assert third != first, (first, third)

print("publication contract fingerprint v2 tests passed")
